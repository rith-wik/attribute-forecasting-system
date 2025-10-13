#!/bin/bash

# AFS Setup Script
# Run this after installing python3-venv and python3-pip

set -e  # Exit on error

echo "================================================"
echo "Attribute Forecasting System - Setup Script"
echo "================================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found"
    exit 1
fi
echo "✅ Python3: $(python3 --version)"

if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 not found - Please run: sudo apt install python3-pip"
    exit 1
fi
echo "✅ pip3: $(pip3 --version)"

# Check if venv module is available
if ! python3 -m venv --help &> /dev/null; then
    echo "❌ python3-venv not available - Please run: sudo apt install python3-venv"
    exit 1
fi
echo "✅ python3-venv is available"

echo ""
echo "Setting up backend..."

cd backend

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install dependencies
echo "Installing Python packages (this may take 2-3 minutes)..."
pip install --quiet \
    fastapi \
    uvicorn[standard] \
    pydantic \
    pydantic-settings \
    pandas \
    numpy \
    scikit-learn \
    xgboost \
    python-multipart \
    pytest

echo ""
echo "✅ Backend setup complete!"
echo ""
echo "================================================"
echo "Setup Complete! 🎉"
echo "================================================"
echo ""
echo "To run the backend:"
echo "  cd backend"
echo "  source .venv/bin/activate"
echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "Then test with:"
echo "  curl http://localhost:8000/health"
echo ""
echo "Or use the quick start script:"
echo "  ./start_backend.sh"
echo ""
