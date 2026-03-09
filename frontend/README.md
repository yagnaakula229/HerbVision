# HerbVision Frontend

A modern React.js frontend for the HerbVision medicinal plant classification system.

## Features

- **User Authentication**: Login and registration with session management
- **Image Upload**: Drag-and-drop interface for plant image uploads
- **Real-time Results**: Instant plant identification and detailed information display
- **Responsive Design**: Mobile-friendly interface with modern UI
- **API Integration**: Seamless communication with Flask backend

## Technology Stack

- **React 18** with Vite for fast development
- **React Router** for client-side routing
- **Axios** for API communication
- **CSS Modules** for component styling

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn

### Installation

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The React app will be available at `http://localhost:5173`

### Building for Production

```bash
npm run build
```

## Project Structure

```
frontend/
├── public/
│   └── vite.svg
├── src/
│   ├── components/
│   │   ├── Navbar.jsx/css
│   │   ├── Home.jsx/css
│   │   ├── Login.jsx
│   │   ├── Register.jsx
│   │   ├── Upload.jsx/css
│   │   ├── About.jsx/css
│   │   └── Auth.css
│   ├── App.jsx/css
│   ├── main.jsx
│   └── index.css
├── package.json
├── vite.config.js
└── README.md
```

## API Integration

The frontend communicates with the Flask backend through the following endpoints:

- `POST /api/register` - User registration
- `POST /api/login` - User authentication
- `POST /api/logout` - User logout
- `GET /api/check-auth` - Check authentication status
- `POST /api/upload` - Image upload and classification
- `GET /upload/<filename>` - Serve uploaded images

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Key Components

- **App.jsx**: Main application with routing and authentication state
- **Navbar.jsx**: Navigation bar with conditional rendering
- **Upload.jsx**: Main functionality for image upload and results display
- **Login/Register.jsx**: Authentication forms
- **Home/About.jsx**: Static informational pages

## Deployment

For production deployment, build the React app and serve the static files from your web server or integrate with the Flask backend to serve the built files.
