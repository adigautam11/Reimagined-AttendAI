# Quick Start Guide - Face Recognition Attendance System

## ⚡ Fast Setup (5 Minutes)

### 1. Install Python Dependencies

```bash
# Navigate to project folder
cd face_recognition_attendance

# Create virtual environment (optional but recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

**Note**: dlib installation may take 5-10 minutes. Be patient!

### 2. Run the Application

```bash
python app.py
```

### 3. Access the System

Open browser and go to: **http://localhost:5000**

**Login Credentials:**
- Username: `admin`
- Password: `admin123`

---

## 🎯 Quick Usage Guide

### Register a Student
1. Click **"Register Student"** (sidebar)
2. Fill: Name, Course, Section
3. Position face in camera
4. Click **"Capture & Register"**

### Mark Attendance
1. Click **"Mark Attendance"** (sidebar)
2. Position student in front of camera
3. Click **"Scan Face & Mark Attendance"**

**First scan** = IN time  
**Second scan** = OUT time + Status (Present/Early Dismissal)  
**Third scan** = "Already completed"

### Auto Mode
Toggle **"Auto Recognition"** switch in sidebar
- System automatically scans and marks attendance
- 3-second delay between scans

### View Logs
Click **"View Logs"** to see all attendance records

---

## 🔧 Common Issues

**dlib won't install?**
```bash
# Windows: Install Visual C++ Build Tools first
# Then: pip install cmake
# Then: pip install dlib
```

**Camera not working?**
- Close other apps using camera
- Grant browser camera permissions
- Try refreshing the page

**Face not detected?**
- Ensure good lighting
- Face camera directly
- Move closer to camera

---

## 📞 Need Help?

Check the full README.md for:
- Detailed troubleshooting
- Configuration options
- Security notes
- Complete feature list

---

**That's it! You're ready to use the system.** 🎉
