import datetime
import json
import logging
import os
from functools import wraps

import bcrypt
import jwt
import torch
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image
from sqlalchemy.exc import IntegrityError
from torchvision import models, transforms

from models import Prediction, User, db
from plant_tips import PLANT_CLASSES, PLANT_TIPS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")
MODEL_PATH = os.path.join(BASE_DIR, "models", "densenet_model.pth")
JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-key")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24
USERNAME_MIN_LENGTH = 3
PASSWORD_MIN_LENGTH = 8
USERNAME_MAX_LENGTH = 50
PASSWORD_MAX_LENGTH = 128

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
CORS(app)
db.init_app(app)

logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)
model = None
idx_to_label = {}
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


with app.app_context():
    db.create_all()


def load_or_create_model():
    global model, idx_to_label
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Trained model file not found at {MODEL_PATH}")

    checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
    state_dict = checkpoint["model_state_dict"] if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint else checkpoint
    num_classes = checkpoint.get("num_classes", len(PLANT_CLASSES)) if isinstance(checkpoint, dict) else len(PLANT_CLASSES)
    label_to_idx = checkpoint.get("label_to_idx") if isinstance(checkpoint, dict) else None

    if label_to_idx:
        idx_to_label = {idx: label for label, idx in label_to_idx.items()}
    else:
        idx_to_label = {idx: label for idx, label in enumerate(PLANT_CLASSES)}

    model = models.densenet121(pretrained=False)
    model.classifier = torch.nn.Linear(model.classifier.in_features, num_classes)
    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(user_id: int) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_token_data(token: str):
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization token missing"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            data = get_token_data(token)
            user = User.query.get(data["sub"])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except Exception:
            return jsonify({"error": "Invalid token"}), 401
        if not user:
            return jsonify({"error": "User not found"}), 401
        return f(user, *args, **kwargs)

    return wrapper


def preprocess_image(file_stream):
    image = Image.open(file_stream).convert("RGB")
    image = MODEL_TRANSFORM(image)
    return image.unsqueeze(0).to(DEVICE)


def get_medicinal_info(plant_name: str):
    plant_info = PLANT_TIPS.get(plant_name)
    default_uses = ["No medicinal usage data available for this plant."]
    default_precautions = [
        "Use caution and consult a healthcare professional before using unknown medicinal plants.",
    ]

    if not plant_info:
        return default_uses, default_precautions

    if isinstance(plant_info, dict):
        uses = plant_info.get("uses", default_uses)
        precautions = plant_info.get("precautions", default_precautions)
    else:
        uses = plant_info
        precautions = default_precautions

    return uses, precautions


@app.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json(force=True)
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"error": "Username and password are required."}), 400

        if len(username) < USERNAME_MIN_LENGTH or len(username) > USERNAME_MAX_LENGTH:
            return jsonify({"error": f"Username must be {USERNAME_MIN_LENGTH}-{USERNAME_MAX_LENGTH} characters."}), 400

        if len(password) < PASSWORD_MIN_LENGTH or len(password) > PASSWORD_MAX_LENGTH:
            return jsonify({"error": f"Password must be at least {PASSWORD_MIN_LENGTH} characters."}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists."}), 409

        new_user = User(username=username, password_hash=hash_password(password))
        db.session.add(new_user)
        db.session.commit()
        token = create_token(new_user.id)
        return jsonify({"token": token, "username": username}), 201
    except IntegrityError as exc:
        db.session.rollback()
        app.logger.exception("Database integrity error during registration")
        return jsonify({"error": "Username already exists."}), 409
    except Exception as exc:
        app.logger.exception("Failed to register user")
        return jsonify({"error": "Unable to register. Please try again."}), 500


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400
    user = User.query.filter_by(username=username).first()
    if not user or not verify_password(password, user.password_hash):
        return jsonify({"error": "Invalid credentials."}), 401
    token = create_token(user.id)
    return jsonify({"token": token, "username": username}), 200


@app.route("/predict", methods=["POST"])
@token_required
def predict(current_user):
    if "image" not in request.files:
        return jsonify({"error": "Image file is required."}), 400
    image_file = request.files["image"]
    if image_file.filename == "":
        return jsonify({"error": "No image selected."}), 400
    try:
        image_tensor = preprocess_image(image_file.stream)
        with torch.no_grad():
            outputs = model(image_tensor)
            probabilities = torch.softmax(outputs, dim=1)

        top_probs, top_idxs = torch.topk(probabilities[0], k=3)
        predictions = []
        for prob, idx in zip(top_probs, top_idxs):
            idx_val = int(idx.item())
            plant_name = idx_to_label.get(idx_val, PLANT_CLASSES[idx_val])
            uses, precautions = get_medicinal_info(plant_name)
            predictions.append({
                "plant": plant_name,
                "confidence": round(float(prob.item()), 4),
                "uses": uses,
                "precautions": precautions,
            })

        main_prediction = predictions[0]
        record = Prediction(
            user_id=current_user.id,
            plant=main_prediction["plant"],
            confidence=main_prediction["confidence"],
            tips=json.dumps({"uses": main_prediction["uses"], "precautions": main_prediction["precautions"]}),
        )
        db.session.add(record)
        db.session.commit()
        return jsonify(predictions)
    except Exception as exc:
        return jsonify({"error": f"Prediction failed: {str(exc)}"}), 500


@app.route("/predictions", methods=["GET"])
@token_required
def user_predictions(current_user):
    entries = (
        Prediction.query.filter_by(user_id=current_user.id)
        .order_by(Prediction.created_at.desc())
        .limit(20)
        .all()
    )
    return jsonify(
        [
            {
                "id": entry.id,
                "plant": entry.plant,
                "confidence": round(entry.confidence, 4),
                "tips": json.loads(entry.tips),
                "createdAt": entry.created_at.isoformat(),
            }
            for entry in entries
        ]
    )


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        load_or_create_model()
    app.run(host="127.0.0.1", port=5000, debug=True)
