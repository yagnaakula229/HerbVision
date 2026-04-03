from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_session import Session
import os
import time
import logging
from werkzeug.utils import secure_filename
from utils import load_models, preprocess_image, predict_irrelevant, predict_plant, cleanup_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app setup
app = Flask(__name__)
CORS(app, supports_credentials=True)  # Enable CORS for frontend communication
app.secret_key = 'herbvision_secret_key_2024'  # Change this in production

# Configure session
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Simple in-memory user storage (use database in production)
users = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'HerbVision API is running',
        'timestamp': time.time()
    })

@app.route('/api/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.form
        email = data.get('email', '').strip()
        password = data.get('password', '')
        confirm_password = data.get('confirm_password', '')
        address = data.get('address', '').strip()
        mobile_number = data.get('mobile_number', '').strip()

        # Validation
        if not email or not password or not confirm_password:
            return jsonify({'error': 'Email and password are required'}), 400

        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400

        if email in users:
            return jsonify({'error': 'Email already registered'}), 400

        # Store user (in production, hash the password!)
        users[email] = {
            'password': password,  # WARNING: Plain text for demo only!
            'address': address,
            'mobile_number': mobile_number,
            'created_at': time.time()
        }

        logger.info(f"New user registered: {email}")
        return jsonify({'message': 'Registration successful'}), 201

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.form
        email = data.get('email', '').strip()
        password = data.get('password', '')

        # Validation
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Check user exists and password matches
        if email not in users or users[email]['password'] != password:
            return jsonify({'error': 'Invalid email or password'}), 401

        # Set session
        session['user'] = {
            'email': email,
            'address': users[email]['address'],
            'mobile_number': users[email]['mobile_number']
        }

        logger.info(f"User logged in: {email}")
        return jsonify({
            'message': 'Login successful',
            'user': session['user']
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout endpoint"""
    session.pop('user', None)
    return jsonify({'message': 'Logout successful'}), 200

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check authentication status"""
    if 'user' in session:
        return jsonify({
            'authenticated': True,
            'user': session['user']
        }), 200
    else:
        return jsonify({
            'authenticated': False
        }), 200

@app.route('/predict', methods=['POST'])
def predict():
    """Main prediction endpoint"""
    start_time = time.time()

    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'No file uploaded'
            }), 400

        file = request.files['file']

        # Check if file has a name
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No file selected'
            }), 400

        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'status': 'error',
                'message': 'Invalid file format. Allowed: png, jpg, jpeg, gif, bmp'
            }), 400

        # Secure filename and save
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        logger.info(f"Processing image: {filename}")

        # Preprocess image
        image_tensor = preprocess_image(filepath)

        # Step 1: Check if image is relevant using MobileNet
        is_relevant, irrelevant_confidence = predict_irrelevant(image_tensor)

        if not is_relevant:
            cleanup_file(filepath)
            processing_time = time.time() - start_time
            logger.info(".2f")
            return jsonify({
                'status': 'rejected',
                'message': 'Uploaded image is not a valid plant',
                'confidence': round(irrelevant_confidence * 100, 2),
                'processing_time': round(processing_time, 2)
            })

        # Step 2: If relevant, classify plant using DenseNet
        plant_name, confidence, top_predictions = predict_plant(image_tensor, top_k=3)

        # Cleanup uploaded file
        cleanup_file(filepath)

        processing_time = time.time() - start_time
        logger.info(".2f")

        return jsonify({
            'status': 'success',
            'prediction': plant_name,
            'confidence': confidence,
            'top_predictions': top_predictions,
            'processing_time': round(processing_time, 2)
        })

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        # Cleanup file in case of error
        if 'filepath' in locals() and os.path.exists(filepath):
            cleanup_file(filepath)

        return jsonify({
            'status': 'error',
            'message': f'Prediction failed: {str(e)}'
        }), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    return jsonify({
        'status': 'error',
        'message': 'File too large. Maximum size is 16MB'
    }), 413

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({
        'status': 'error',
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    # Load models at startup
    logger.info("Starting HerbVision API server...")
    load_models()
    logger.info("Models loaded successfully")

    # Create uploads directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Start server
    app.run(host='0.0.0.0', port=5000, debug=False)