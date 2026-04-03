# HerbVision - Flask REST API Backend

A production-ready Flask REST API for dual-model image classification of medicinal plants using PyTorch.

## Features

- **Dual-Model Pipeline**: MobileNet for irrelevant image filtering + DenseNet121 for plant classification
- **Health Check Endpoint**: `/` - API status monitoring
- **Prediction Endpoint**: `POST /predict` - Image classification with confidence scores
- **Production Standards**: Proper error handling, logging, file cleanup, CORS support
- **Security**: File type validation, size limits, secure filename handling

## API Endpoints

### Health Check
- `GET /` - Check API status
  - Response: `{"status": "healthy", "message": "HerbVision API is running", "timestamp": 1234567890.123}`

### Authentication
- `POST /api/register` - Register new user
  - Content-Type: `application/x-www-form-urlencoded`
  - Required: `email`, `password`, `confirm_password`, `address`, `mobile_number`
  - Response: `{"message": "Registration successful"}`

- `POST /api/login` - Login user
  - Content-Type: `application/x-www-form-urlencoded`
  - Required: `email`, `password`
  - Response: `{"message": "Login successful", "user": {...}}`

- `POST /api/logout` - Logout user
  - Response: `{"message": "Logout successful"}`

### Image Classification
- `POST /predict` - Classify uploaded plant image
  - Content-Type: `multipart/form-data`
  - Parameter: `file` (image file)
  - Supported formats: PNG, JPG, JPEG, GIF, BMP
  - Max file size: 16MB

#### Success Response (Plant Detected):
```json
{
  "status": "success",
  "prediction": "Aloe Vera",
  "confidence": 87.5,
  "top_predictions": [
    {"name": "Aloe Vera", "confidence": 87.5},
    {"name": "Snake Plant", "confidence": 12.3},
    {"name": "ZZ Plant", "confidence": 0.2}
  ],
  "processing_time": 1.23
}
```

#### Rejection Response (Irrelevant Image):
```json
{
  "status": "rejected",
  "message": "Uploaded image is not a valid plant",
  "confidence": 95.2,
  "processing_time": 0.89
}
```

#### Error Response:
```json
{
  "status": "error",
  "message": "Prediction failed: [error details]"
}
```

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Model Files**:
   Place the following model files in the `models/` directory:
   - `mobilenet_irrelevant.pth` - MobileNet model for irrelevant image detection
   - `densenet_model.pth` - DenseNet121 model for plant classification

3. **Run the Server**:
   ```bash
   python app.py
   ```

   The API will be available at `http://localhost:5000`

## Project Structure

```
backend/
├── app.py              # Main Flask application
├── utils.py            # Model loading and prediction utilities
├── requirements.txt    # Python dependencies
├── models/             # PyTorch model files
│   ├── mobilenet_irrelevant.pth
│   └── densenet_model.pth
├── uploads/            # Temporary uploaded files (auto-created)
└── README.md           # This file
```

## Architecture

### Model Pipeline
1. **Preprocessing**: Images are resized to 224x224 and normalized
2. **Relevance Check**: MobileNet determines if image contains a plant
3. **Classification**: If relevant, DenseNet121 classifies the plant species
4. **Response**: JSON response with prediction results and confidence scores

### Error Handling
- File validation (type, size)
- Model loading errors
- Prediction failures
- Automatic file cleanup

### Security Features
- File extension validation
- Secure filename handling
- File size limits (16MB)
- CORS enabled for frontend integration

## Dependencies

- Flask 2.3.3 - Web framework
- Flask-CORS 4.0.0 - CORS support
- Flask-Session 0.5.0 - Session management
- PyTorch 2.4.1 - Deep learning framework
- Torchvision 0.19.1 - Computer vision utilities
- Pillow 10.0.0 - Image processing
- Werkzeug 2.3.7 - WSGI utilities

## Development

### Testing the API

```bash
# Health check
curl http://localhost:5000/

# Prediction (replace with actual image file)
curl -X POST -F "file=@plant_image.jpg" http://localhost:5000/predict
```

### Logs
The application uses Python's logging module. Logs include:
- Model loading status
- Prediction requests and results
- Error details
- Processing times

## Production Deployment

For production deployment, consider:
- Using a WSGI server (Gunicorn, uWSGI)
- Setting `app.config['DEBUG'] = False`
- Using environment variables for configuration
- Implementing proper authentication/authorization
- Adding rate limiting
- Using a reverse proxy (nginx)
  
- `POST /api/logout` - Logout user
  
- `GET /api/check-auth` - Check if user is authenticated

### Image Classification
- `POST /api/upload` - Upload and classify image
  - Required: `file` (image file)
  - Returns: `prediction`, `description`, `uses`, `image`

### Static Files
- `GET /upload/<filename>` - Serve uploaded image

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up MySQL database:
   - Create database: `medical_plant`
   - Create users table:
   ```sql
   CREATE TABLE users (
     id INT AUTO_INCREMENT PRIMARY KEY,
     email VARCHAR(255) UNIQUE NOT NULL,
     password VARCHAR(255) NOT NULL,
     address TEXT,
     mobile_number VARCHAR(10)
   );
   ```

3. Place model files in backend directory:
   - `mobilenet_irrelevent.pt` (relevance classifier)
   - `best_model_rnn.pth` (plant classifier)
   - `Medicinal plant dataset/` (folder with class subfolders)

4. Run the app:
   ```bash
   python app.py
   ```

API will be available at `http://localhost:5000`

## Notes

- CORS is enabled for all origins
- Sessions are stored in-memory (use production session backend for deployment)
- Requires CUDA-compatible GPU for optimal PyTorch performance
- Update database credentials in app.py if different from defaults