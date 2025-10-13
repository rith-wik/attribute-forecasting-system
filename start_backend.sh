#!/bin/bash

# Quick start script for backend

echo "Starting AFS Backend..."

cd backend

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate venv
source .venv/bin/activate

# Start server
echo "Starting Uvicorn server on http://0.0.0.0:8000"
echo "API Docs: http://localhost:8000/docs"
echo "Press CTRL+C to stop"
echo ""

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
