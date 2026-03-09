#!/bin/bash

# HerbVision Development Runner
# This script starts both the Flask backend and React frontend

echo "Starting HerbVision development environment..."

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "Port $1 is already in use. Please free it or change the port."
        exit 1
    fi
}

# Check if ports are available
check_port 5000
check_port 5173

# Start Flask backend in background
echo "Starting Flask backend on port 5000..."
cd backend
python app.py &
FLASK_PID=$!

# Wait a moment for Flask to start
sleep 3

# Start React frontend in background
echo "Starting React frontend on port 5173..."
cd ../frontend
npm run dev &
REACT_PID=$!

echo ""
echo "HerbVision is now running!"
echo "Backend: http://localhost:5000"
echo "Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop both servers"

# Function to kill both processes on exit
cleanup() {
    echo ""
    echo "Stopping servers..."
    kill $FLASK_PID 2>/dev/null
    kill $REACT_PID 2>/dev/null
    exit 0
}

# Set trap to cleanup on exit
trap cleanup SIGINT SIGTERM

# Wait for both processes
wait