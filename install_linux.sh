#!/bin/bash

# Face Recognition Attendance System - Linux/Mac Installation Script

echo "============================================================"
echo "Face Recognition Attendance System - Installation"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.7+ first"
    exit 1
fi

echo "Python found. Checking version..."
python3 --version

echo ""
echo "Creating virtual environment..."
python3 -m venv venv

echo ""
echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Installing dependencies..."
echo "This may take 5-10 minutes, please be patient..."
echo ""

# Install in order to avoid conflicts
echo "Installing CMake..."
pip install cmake

echo ""
echo "Installing dlib (this will take a while)..."
pip install dlib

echo ""
echo "Installing remaining packages..."
pip install Flask==2.3.3
pip install opencv-python==4.8.0.76
pip install face-recognition==1.3.0
pip install numpy==1.24.3
pip install Pillow==10.0.0

echo ""
echo "============================================================"
echo "Installation Complete!"
echo "============================================================"
echo ""
echo "To start the application:"
echo "1. source venv/bin/activate"
echo "2. python app.py"
echo "3. Open browser: http://localhost:5000"
echo "4. Login: admin / admin123"
echo ""
echo "============================================================"
