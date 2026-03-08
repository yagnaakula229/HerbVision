# Medicinal Plant Image Classifier - Flask REST API Backend

This is a Flask REST API for classifying medicinal plant images using PyTorch models with MySQL database.

## Features

- User registration and login (session-based)
- Image upload and classification
- Relevance check (medicinal plant or not)
- CORS enabled for React frontend
- JSON API responses

## API Endpoints

### Authentication
- `POST /api/register` - Register new user
  - Required: `email`, `password`, `confirm_password`, `address`, `mobile_number`
  
- `POST /api/login` - Login user
  - Required: `email`, `password`
  
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