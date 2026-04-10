from flask import Flask, request, send_from_directory, session, jsonify
from flask_cors import CORS
import os
import sqlite3
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
from werkzeug.security import generate_password_hash, check_password_hash

from model_utils import get_predictor
from plant_info import get_plant_description_and_uses

app = Flask(__name__)
app.secret_key = 'admin'
CORS(app)

# ================= DATABASE =================
db_path = 'users.db'

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


# ================= DEVICE =================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class MobileNetModel(nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.mobilenet = models.mobilenet_v2(weights=None)  # ✅ IMPORTANT
        num_features = self.mobilenet.classifier[1].in_features
        self.mobilenet.classifier[1] = nn.Linear(num_features, num_classes)

    def forward(self, x):
        return self.mobilenet(x)


irrelevant_model = MobileNetModel(2)
irrelevant_model.load_state_dict(torch.load('mobilenet_irrelevent.pt', map_location=device))
irrelevant_model.to(device)
irrelevant_model.eval()

# SAME normalization as Kaggle
relevance_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])


def predict_relevance(image_path):
    image = Image.open(image_path).convert("RGB")
    image = relevance_transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = irrelevant_model(image)
        probs = torch.softmax(output, dim=1)
        _, pred = torch.max(probs, 1)

    return pred.item()  # 0 or 1


# ================= DENSENET =================
plant_predictor = get_predictor()


def predict_classification(image_path):
    predictions = plant_predictor.predict(image_path, top_k=3)

    main = predictions[0]['plant']
    description, uses = get_plant_description_and_uses(main)

    return predictions, main, description, uses


# ================= ROUTES =================

@app.route("/api/upload", methods=["POST"])
def api_upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        filename = file.filename

        if not filename or '.' not in filename:
            return jsonify({'error': 'Invalid file'}), 400

        ext = filename.split('.')[-1].lower()
        if ext not in ['jpg', 'jpeg', 'png', 'jfif']:
            return jsonify({'error': 'Invalid format'}), 400

        upload_dir = 'static/uploaded_images'
        os.makedirs(upload_dir, exist_ok=True)

        path = os.path.join(upload_dir, filename)
        file.save(path)

        # STEP 1: relevance
        relevance = predict_relevance(path)

        if relevance == 1:
            return jsonify({
                'prediction': 'Not a medicinal plant image',
                'image': filename
            }), 200

        # STEP 2: plant prediction (Kaggle same)
        predictions, plant, desc, uses = predict_classification(path)

        return jsonify({
            'predictions': predictions,
            'main_prediction': {
                'plant': plant,
                'description': desc,
                'uses': uses
            },
            'image': filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/upload/<filename>')
def send_image(filename):
    return send_from_directory("static/uploaded_images", filename)


# ================= AUTHENTICATION ROUTES =================

@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        address = request.form.get('address', '')
        mobile_number = request.form.get('mobile_number', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'User already exists'}), 400

        # Hash password and insert user
        hashed_password = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (email, password, address, mobile_number)
            VALUES (?, ?, ?, ?)
        ''', (email, hashed_password, address, mobile_number))
        conn.commit()
        conn.close()

        return jsonify({'message': 'User registered successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            return jsonify({
                'message': 'Login successful',
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'address': user['address'],
                    'mobile_number': user['mobile_number']
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/check-auth', methods=['GET'])
def api_check_auth():
    try:
        if 'user_id' in session:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, email, address, mobile_number FROM users WHERE id = ?', (session['user_id'],))
            user = cursor.fetchone()
            conn.close()

            if user:
                return jsonify({
                    'authenticated': True,
                    'user': {
                        'id': user['id'],
                        'email': user['email'],
                        'address': user['address'],
                        'mobile_number': user['mobile_number']
                    }
                }), 200

        return jsonify({'authenticated': False}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/logout', methods=['POST'])
def api_logout():
    try:
        session.clear()
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)