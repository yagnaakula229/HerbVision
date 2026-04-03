import datetime
import json
import os
from functools import wraps

import bcrypt
import jwt
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image
from tensorflow.keras import Input, Model
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array

from models import Prediction, User, db
from plant_tips import PLANT_CLASSES, PLANT_TIPS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")
MODEL_PATH = os.path.join(BASE_DIR, "plant_model.h5")
JWT_SECRET = os.environ.get("JWT_SECRET", "super-secret-key")
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Enhanced CORS configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False
    }
})

db.init_app(app)
model = None


def build_model():
    inputs = Input(shape=(128, 128, 3))
    x = GlobalAveragePooling2D()(inputs)
    outputs = Dense(len(PLANT_CLASSES), activation="softmax")(x)
    compiled = Model(inputs, outputs)
    compiled.compile(optimizer="adam", loss="categorical_crossentropy")
    return compiled


def load_or_create_model():
    global model
    if os.path.exists(MODEL_PATH):
        model = load_model(MODEL_PATH)
        return
    model = build_model()
    model.save(MODEL_PATH)


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
    image = image.resize((128, 128))
    array = img_to_array(image) / 255.0
    return np.expand_dims(array, axis=0)


@app.route("/health", methods=["GET", "OPTIONS"])
def health():
    print(f"[HEALTH] Request from {request.remote_addr}")
    return jsonify({"status": "ok"}), 200


@app.before_request
def log_request():
    print(f"[REQUEST] {request.method} {request.path} from {request.remote_addr}")


@app.route("/register", methods=["POST", "OPTIONS"])
def register():
    if request.method == "OPTIONS":
        return {}, 200
    
    print(f"[REGISTER] Request from {request.remote_addr}")
    try:
        data = request.get_json(force=True)
        username = data.get("username", "").strip()
        password = data.get("password", "")
        if not username or not password:
            return jsonify({"error": "Username and password are required."}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already exists."}), 409
        new_user = User(username=username, password_hash=hash_password(password))
        db.session.add(new_user)
        db.session.commit()
        token = create_token(new_user.id)
        print(f"[REGISTER] User {username} registered successfully")
        return jsonify({"token": token, "username": username}), 201
    except Exception as exc:
        print(f"[REGISTER ERROR] {str(exc)}")
        app.logger.error(f"Register error: {str(exc)}")
        return jsonify({"error": "Registration failed"}), 500


@app.route("/login", methods=["POST", "OPTIONS"])
def login():
    if request.method == "OPTIONS":
        return {}, 200
    
    print(f"[LOGIN] Request from {request.remote_addr}")
    try:
        data = request.get_json(force=True)
        username = data.get("username", "").strip()
        password = data.get("password", "")
        if not username or not password:
            return jsonify({"error": "Username and password are required."}), 400
        user = User.query.filter_by(username=username).first()
        if not user or not verify_password(password, user.password_hash):
            print(f"[LOGIN] Invalid credentials for user {username}")
            return jsonify({"error": "Invalid credentials."}), 401
        token = create_token(user.id)
        print(f"[LOGIN] User {username} logged in successfully")
        return jsonify({"token": token, "username": username}), 200
    except Exception as exc:
        print(f"[LOGIN ERROR] {str(exc)}")
        app.logger.error(f"Login error: {str(exc)}")
        return jsonify({"error": "Login failed"}), 500


@app.route("/predict", methods=["POST"])
@token_required
def predict(current_user):
    if "image" not in request.files:
        return jsonify({"error": "Image file is required."}), 400
    image_file = request.files["image"]
    if image_file.filename == "":
        return jsonify({"error": "No image selected."}), 400
    try:
        image_data = preprocess_image(image_file.stream)
        predictions = model.predict(image_data)
        best_idx = int(np.argmax(predictions[0]))
        plant_name = PLANT_CLASSES[best_idx]
        confidence = float(predictions[0][best_idx])
        tips = PLANT_TIPS.get(plant_name, [])
        record = Prediction(
            user_id=current_user.id,
            plant=plant_name,
            confidence=confidence,
            tips=json.dumps(tips),
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({
            "plant": plant_name,
            "confidence": round(confidence, 4),
            "tips": tips,
        })
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
    app.run(host="0.0.0.0", port=5000, debug=True)
