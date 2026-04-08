#!/bin/bash

# Title equivalent
echo "==================================================="
echo "          Starting LLM Council..."
echo "==================================================="

# Check for virtual environment
if [ ! -d "server/venv" ]; then
    echo "[ERROR] Virtual environment not found."
    echo "Please run 'setup.sh' (or ensure server/venv exists) first."
    exit 1
fi

echo ""
echo "1. Launching Backend (Port 8000)..."
# Start backend in background
(cd server && source venv/bin/activate && uvicorn main:app --reload) &
BACKEND_PID=$!

echo "2. Launching Frontend (Port 5173)..."
# Start frontend in background
(cd client && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "==================================================="
echo "          App is Running! 🚀"
echo "==================================================="
echo ""
echo "Frontend: http://localhost:5173"
echo "Backend:  http://localhost:8000/docs (Swagger UI)"
echo ""
echo "Press Ctrl+C to stop both servers."

# Trap SIGINT (Ctrl+C) to kill background processes
trap "kill $BACKEND_PID $FRONTEND_PID; exit" SIGINT

# Wait for processes
wait
