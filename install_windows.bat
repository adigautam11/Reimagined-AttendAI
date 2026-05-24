@echo off
REM Face Recognition Attendance System - Windows Installation Script

echo ============================================================
echo Face Recognition Attendance System - Installation
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://www.python.org/
    pause
    exit /b 1
)

echo Python found. Checking version...
python --version

echo.
echo Creating virtual environment...
python -m venv venv

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
echo This may take 5-10 minutes, please be patient...
echo.

REM Install in order to avoid conflicts
echo Installing CMake...
pip install cmake

echo.
echo Installing dlib (this will take a while)...
pip install dlib

echo.
echo Installing remaining packages...
pip install Flask==2.3.3
pip install opencv-python==4.8.0.76
pip install face-recognition==1.3.0
pip install numpy==1.24.3
pip install Pillow==10.0.0

echo.
echo ============================================================
echo Installation Complete!
echo ============================================================
echo.
echo To start the application:
echo 1. venv\Scripts\activate.bat
echo 2. python app.py
echo 3. Open browser: http://localhost:5000
echo 4. Login: admin / admin123
echo.
echo ============================================================
pause
