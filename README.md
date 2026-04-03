# HerbVision

A complete Medicinal Plant Detection web application with a React frontend, Flask backend, and TensorFlow/Keras model inference.

## Project Structure

- `backend/` - Flask API, SQLite database, Keras model loader, user authentication, prediction history
- `frontend/` - React + Vite app with login, register, upload, and dashboard pages

## Backend Files

- `backend/app.py` - Flask application with `/register`, `/login`, `/predict`, and `/predictions`
- `backend/models.py` - SQLAlchemy models for `User` and `Prediction`
- `backend/plant_tips.py` - Medicinal plant names and tips map
- `backend/requirements.txt` - Python dependencies for backend services

## Frontend Files

- `frontend/package.json` - React and Vite dependencies
- `frontend/vite.config.js` - Vite configuration
- `frontend/index.html` - Application HTML entrypoint
- `frontend/src/main.jsx` - React entrypoint
- `frontend/src/App.jsx` - Routing and protected route logic
- `frontend/src/api.js` - Axios API client with JWT headers
- `frontend/src/components/Navbar.jsx` - Navigation and logout
- `frontend/src/components/ImageUpload.jsx` - Image upload, preview, and submit
- `frontend/src/components/ResultCard.jsx` - Prediction result display
- `frontend/src/pages/Login.jsx` - Login page
- `frontend/src/pages/Register.jsx` - Register page
- `frontend/src/pages/Dashboard.jsx` - Dashboard with prediction UI and history
- `frontend/src/styles.css` - Styling for the app

## Setup

### Backend

```bash
cd backend
python -m pip install -r requirements.txt
python app.py
```

The Flask backend listens on `http://127.0.0.1:5000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

## API Endpoints

- `POST /register` - Register a new user
- `POST /login` - Login and receive a JWT
- `POST /predict` - Upload an image for medicinal plant prediction
- `GET /predictions` - Fetch user prediction history

## Application Features

- React frontend using hooks and functional components
- JWT authentication with protected dashboard route
- Image upload with preview and server-side prediction
- Results display with plant name, confidence progress bar, and tips
- Prediction history saved per user
- Logout support

## Notes

- The backend creates a Keras model file at `backend/plant_model.h5` when first run.
- User data and prediction history are stored in `backend/app.db`.
- The Flask backend accepts JWT tokens in the `Authorization: Bearer <token>` header.
