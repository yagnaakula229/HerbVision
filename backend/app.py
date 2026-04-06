from flask import Flask, request, send_from_directory, session, jsonify, redirect
from flask_cors import CORS
import os
import sqlite3
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
from torchvision import models
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'admin'
CORS(app)

# ================== PATH SETUP ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================== DATABASE ==================
db_path = os.path.join(BASE_DIR, 'users.db')

if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            address TEXT,
            mobile_number TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# ================== DEVICE ==================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ================== TRANSFORMS ==================
image_transform_main = transforms.Compose([
    transforms.Resize(224),
    transforms.CenterCrop(224),
    transforms.ToTensor()
])

image_transform_normalization = transforms.Compose([
    transforms.Resize(224),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# ================== MODELS ==================
class MobileNetModel(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.mobilenet = models.mobilenet_v2(pretrained=True)
        num_features = self.mobilenet.classifier[1].in_features
        self.mobilenet.classifier[1] = nn.Linear(num_features, num_classes)

    def forward(self, x):
        return self.mobilenet(x)

class DenseNetPlantClassifier(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.densenet = models.densenet121(weights=models.DenseNet121_Weights.DEFAULT)
        num_ftrs = self.densenet.classifier.in_features
        self.densenet.classifier = nn.Linear(num_ftrs, num_classes)

    def forward(self, x):
        return self.densenet(x)

# Load models safely
irrelevant_model_path = os.path.join(BASE_DIR, 'mobilenet_irrelevent.pt')
dense_model_path = os.path.join(BASE_DIR, 'densenet121_pso_medicinal_plants.pth')

irrelevant_model = MobileNetModel(2)
irrelevant_model.load_state_dict(torch.load(irrelevant_model_path, map_location=device))
irrelevant_model.to(device).eval()

model = DenseNetPlantClassifier(num_classes=40)
checkpoint = torch.load(dense_model_path, map_location=device)

if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
    model.load_state_dict(checkpoint['model_state_dict'], strict=False)
else:
    model.load_state_dict(checkpoint, strict=False)

model.to(device).eval()

# ================== CLASS NAMES ==================
class_names = ['Wood_sorel','Brahmi','Basale','Lemon_grass','Lemon','Insulin','Amruta_Balli',
'Betel','Castor','Ashoka','Aloevera','Tulasi','Henna','Curry_Leaf','Arali',
'Hibiscus','Betel_Nut','Neem','Jasmine','Nithyapushpa','Mint','Nooni',
'Pomegranate','Pepper','Geranium','Mango','Honge','Amla','Ekka','Raktachandini',
'Rose','Ashwagandha','Gauva','Ganike','Avocado','Sapota','Doddapatre',
'Nagadali','Pappaya','Bamboo']

# ================== PREDICTION ==================
def predict_relevance(image_path):
    image = Image.open(image_path).convert('RGB')
    image = image_transform_normalization(image).unsqueeze(0).to(device)
    with torch.no_grad():
        output = irrelevant_model(image)
        _, predicted = torch.max(output, 1)
    return predicted.item()

def predict_classification(image_path):
    image = Image.open(image_path).convert('RGB')
    image = image_transform_main(image).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(image)
        probs = F.softmax(outputs, dim=1)
        top3_probs, top3_indices = torch.topk(probs, 3)

    predictions = []
    for i in range(3):
        idx = top3_indices[0][i].item()
        predictions.append({
            "plant": class_names[idx],
            "confidence": float(top3_probs[0][i])
        })

    return predictions

# ================== ROUTES ==================

@app.route("/")
def home():
    return "🌿 HerbVision Backend Running on Render!"

@app.route('/api/register', methods=["POST"])
def api_register():
    try:
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return jsonify({'error': 'Missing fields'}), 400

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)",
                       (email, hashed_password))
        conn.commit()
        conn.close()

        return jsonify({'message': 'Registered successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=["POST"])
def api_login():
    email = request.form.get('email')
    password = request.form.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE email=?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[0], password):
        session['user_email'] = email
        return jsonify({'message': 'Login successful'}), 200

    return jsonify({'error': 'Invalid credentials'}), 401

@app.route("/api/upload", methods=["POST"])
def api_upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file'}), 400

        file = request.files['file']
        filename = file.filename

        upload_dir = os.path.join(BASE_DIR, 'static/uploaded_images')
        os.makedirs(upload_dir, exist_ok=True)

        path = os.path.join(upload_dir, filename)
        file.save(path)

        relevance = predict_relevance(path)

        if relevance == 1:
            return jsonify({'prediction': 'Not a medicinal plant'}), 200

        predictions = predict_classification(path)

        return jsonify({'predictions': predictions}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload/<filename>')
def send_image(filename):
    return send_from_directory(os.path.join(BASE_DIR, "static/uploaded_images"), filename)

# ================== RUN ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)