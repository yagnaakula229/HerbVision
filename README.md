# HerbVision

A comprehensive web application for medicinal plant identification using AI and machine learning.

## Overview

HerbVision combines a powerful Flask backend with a modern React frontend to provide users with an intuitive interface for identifying medicinal plants through image upload. The system uses advanced deep learning models to classify plants and provide detailed information about their traditional medicinal uses.

## Architecture

### Backend (Flask)
- **Location**: `backend/`
- **Technology**: Python Flask with PyTorch
- **Features**:
  - User authentication and session management
  - Image upload and processing
  - Two-stage AI classification (relevance check + species identification)
  - MySQL database integration
  - RESTful API endpoints

### Frontend (React)
- **Location**: `frontend/`
- **Technology**: React 18 with Vite
- **Features**:
  - Modern, responsive user interface
  - Client-side routing
  - Real-time API integration
  - Image upload with preview
  - User authentication flows

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- MySQL database

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up MySQL database:
   - Create database: `medical_plant`
   - Update database credentials in `app.py`

4. Start the Flask server:
   ```bash
   python app.py
   ```

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the React development server:
   ```bash
   npm run dev
   ```

4. Open your browser to `http://localhost:5173`

### Running Both Services

You can run both backend and frontend simultaneously using the provided script:

```bash
./run.sh
```

This will start:
- Flask backend on `http://localhost:5000`
- React frontend on `http://localhost:5173`

## API Documentation

### Authentication Endpoints
- `POST /api/register` - Register new user
- `POST /api/login` - User login
- `POST /api/logout` - User logout
- `GET /api/check-auth` - Check authentication status

### Classification Endpoints
- `POST /api/upload` - Upload and classify plant image
- `GET /upload/<filename>` - Serve uploaded images

## AI Models

The system uses two PyTorch models:
1. **Relevance Classifier**: Determines if an image contains a medicinal plant
2. **Species Classifier**: Identifies specific plant species (40+ supported plants)

## Supported Plants

The database includes detailed information for plants such as:
- Wood Sorrel, Brahmi, Basale, Lemon Grass
- Insulin Plant, Amruta Balli, Aloe Vera
- Tulasi, Neem, and many more...

## Development

### Backend Development
- Located in `backend/` directory
- Uses Flask for API development
- PyTorch for machine learning inference
- MySQL for user data storage

### Frontend Development
- Located in `frontend/` directory
- React with modern hooks and functional components
- React Router for navigation
- Vite for fast development and building

## Deployment

For production deployment:
1. Build the React frontend: `npm run build` (in frontend directory)
2. Configure Flask to serve static React files
3. Set up production database and environment variables
4. Deploy to your preferred hosting platform

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test both backend and frontend
5. Submit a pull request

## License

This project is open source and available under the MIT License.