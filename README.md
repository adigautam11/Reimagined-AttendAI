# Face Recognition Attendance System

A complete web-based attendance system using facial recognition technology built with Flask, OpenCV, and dlib.

## 🌟 Features

- **Admin Authentication**: Secure login system with session management
- **Student Registration**: Register students with face encoding
- **Face Recognition**: Accurate face detection and recognition using dlib
- **Attendance Marking**: 
  - Mark IN time on first scan
  - Mark OUT time on second scan
  - Automatic early dismissal detection (before 4:00 PM)
  - Prevents duplicate scanning
- **Auto Recognition Mode**: Continuous face detection and attendance marking
- **Multi-face Support**: Can process multiple faces simultaneously
- **Attendance Logs**: Complete history with filtering options
- **Live Camera Feed**: Real-time video feed with face labeling
- **Responsive UI**: Clean, modern interface that works on all devices

## 📋 Prerequisites

Before installation, ensure you have:

- Python 3.7 or higher
- pip (Python package manager)
- Webcam/Camera
- Visual Studio Code (recommended)

### System-specific Requirements

**Windows:**
- Microsoft Visual C++ 14.0 or greater (for dlib)
- Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install build-essential cmake
sudo apt-get install libopenblas-dev liblapack-dev
sudo apt-get install libx11-dev libgtk-3-dev
```

**macOS:**
```bash
brew install cmake
```

## 🚀 Installation Steps

### Step 1: Clone/Download the Project

Download the project or navigate to the project directory:
```bash
cd face_recognition_attendance
```

### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

**Important**: Install packages in this specific order to avoid conflicts:

```bash
# Install CMake first (required for dlib)
pip install cmake

# Install dlib (this may take 5-10 minutes)
pip install dlib

# Install remaining packages
pip install Flask==2.3.3
pip install opencv-python==4.8.0.76
pip install face-recognition==1.3.0
pip install numpy==1.24.3
pip install Pillow==10.0.0
```

**OR** install all at once:
```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation

Test if all packages are installed correctly:
```bash
python -c "import cv2, face_recognition, flask; print('All packages installed successfully!')"
```

## 🎮 Running the Application

### Step 1: Start the Server

```bash
python app.py
```

You should see output like:
```
============================================================
Face Recognition Attendance System
============================================================
Admin Username: admin
Admin Password: admin123
============================================================
Starting server...
Access the application at: http://127.0.0.1:5000
============================================================
```

### Step 2: Access the Application

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

or
```
http://localhost:5000
```

### Step 3: Login

Use the default credentials:
- **Username**: admin
- **Password**: admin123

## 📖 How to Use

### 1. Register Students

1. Click **"Register Student"** in the sidebar
2. Fill in the form:
   - Student Name (required)
   - Course (e.g., Computer Science)
   - Section (e.g., A, B, C)
3. Position the student in front of the camera
4. Click **"Capture & Register"**
5. The system will:
   - Detect the face
   - Generate face encoding
   - Store in database

**Important Notes:**
- Only one face should be visible during registration
- Ensure good lighting
- Student should face the camera directly
- Remove glasses/masks for better accuracy

### 2. Mark Attendance (Manual Mode)

1. Click **"Mark Attendance"** in the sidebar
2. Position student(s) in front of the camera
3. Click **"Scan Face & Mark Attendance"**
4. The system will:
   - First scan: Mark IN time
   - Second scan: Mark OUT time
   - Status determined by OUT time:
     - Before 4:00 PM → "Early Dismissal"
     - After 4:00 PM → "Present"
   - Third scan: "Attendance already completed"

### 3. Auto Recognition Mode

1. Toggle the **"Auto Recognition"** switch in the sidebar
2. The system will:
   - Continuously scan for faces
   - Automatically mark attendance when faces are detected
   - Add a 3-second delay between scans to avoid duplicates
3. Toggle off to disable

### 4. Early Dismissal

- Students leaving before 4:00 PM are automatically marked as "Early Dismissal"
- No separate action needed - the system handles this automatically
- Check the "Early Dismissal" section for information

### 5. View Attendance Logs

1. Click **"View Logs"** in the sidebar
2. The table shows:
   - Student Name
   - Course
   - Section
   - Date
   - Time In
   - Time Out
   - Status (Present/Early Dismissal/Pending)
3. Click **"Refresh"** to update the logs

## 🗄️ Database Structure

The system uses SQLite database with two tables:

### Students Table
```sql
- id (Primary Key)
- name (Text)
- course (Text)
- section (Text)
- face_encoding (Blob - pickled numpy array)
- created_at (Timestamp)
```

### Attendance Table
```sql
- id (Primary Key)
- student_id (Foreign Key → students.id)
- date (Date)
- time_in (Time)
- time_out (Time)
- status (Text: Pending/Present/Early Dismissal)
- Unique constraint on (student_id, date)
```

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin123'  # Change this!

# Face recognition settings
TOLERANCE = 0.6  # Lower = more strict (0.0-1.0)
MODEL = 'hog'    # 'hog' (faster) or 'cnn' (more accurate, needs GPU)

# Auto recognition delay
AUTO_RECOGNITION_DELAY = 3  # seconds

# Early dismissal time
EARLY_DISMISSAL_HOUR = 16    # 4:00 PM (24-hour format)
EARLY_DISMISSAL_MINUTE = 0
```

## 🔧 Troubleshooting

### Problem: dlib installation fails

**Solution**:
- **Windows**: Install Visual C++ Build Tools
- **Linux**: `sudo apt-get install build-essential cmake`
- **Alternative**: Try `pip install dlib-binary`

### Problem: Camera not detected

**Solutions**:
1. Check if camera is connected and working
2. Close other applications using the camera
3. Try changing camera index in `utils.py`:
   ```python
   self.camera = cv2.VideoCapture(1)  # Try different numbers: 0, 1, 2
   ```
4. Grant camera permissions to your browser

### Problem: "No face detected" error

**Solutions**:
- Ensure good lighting
- Face the camera directly
- Move closer to the camera
- Remove obstructions (glasses, masks)
- Check if camera is working in video feed

### Problem: Face recognition not accurate

**Solutions**:
1. Increase tolerance in `config.py`:
   ```python
   TOLERANCE = 0.7  # Higher = less strict
   ```
2. Re-register the student with better lighting
3. Use CNN model for better accuracy:
   ```python
   MODEL = 'cnn'  # Requires GPU
   ```

### Problem: Video feed not loading

**Solutions**:
1. Refresh the page
2. Check browser console for errors (F12)
3. Ensure camera permissions are granted
4. Try a different browser (Chrome recommended)
5. Check if another application is using the camera

### Problem: Port 5000 already in use

**Solution**:
```bash
# Change port in app.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

## 📁 Project Structure

```
face_recognition_attendance/
│
├── app.py                      # Main Flask application
├── models.py                   # Database models and operations
├── utils.py                    # Face recognition utilities
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
│
├── database/
│   └── attendance.db          # SQLite database (auto-created)
│
├── encodings/                  # Face encodings storage (auto-created)
│
├── static/
│   ├── css/
│   │   └── style.css          # Stylesheet
│   └── js/
│       └── main.js            # JavaScript functionality
│
└── templates/
    ├── login.html             # Login page
    └── dashboard.html         # Main dashboard
```

## 🔐 Security Notes

**For Production Use:**

1. **Change default credentials** in `config.py`
2. **Use environment variables** for sensitive data:
   ```python
   SECRET_KEY = os.environ.get('SECRET_KEY')
   ```
3. **Hash passwords** instead of plain text
4. **Use HTTPS** for secure communication
5. **Add CSRF protection** to forms
6. **Implement rate limiting** for API endpoints
7. **Add input validation** and sanitization

## 🎯 Features Implemented

✅ Admin authentication with Flask sessions  
✅ Student registration with face encoding  
✅ Face detection using dlib  
✅ Face recognition with tolerance settings  
✅ Attendance marking (IN/OUT)  
✅ Early dismissal detection (before 4:00 PM)  
✅ Duplicate scan prevention  
✅ Auto recognition mode with delay  
✅ Multi-face support  
✅ Live camera feed with face labeling  
✅ Attendance logs with filtering  
✅ Responsive UI design  
✅ Error handling for edge cases  
✅ SQLite database with proper schema  
✅ Modular code structure  

## 📊 Testing Checklist

- [ ] Login with correct credentials ✓
- [ ] Login with wrong credentials (should fail) ✓
- [ ] Register student with all fields ✓
- [ ] Register student with missing fields (should fail) ✓
- [ ] Register with no face visible (should fail) ✓
- [ ] Register with multiple faces (should fail) ✓
- [ ] Mark attendance (first scan - IN) ✓
- [ ] Mark attendance (second scan - OUT) ✓
- [ ] Mark attendance (third scan - should fail) ✓
- [ ] Early dismissal (OUT before 4 PM) ✓
- [ ] Enable auto recognition mode ✓
- [ ] Disable auto recognition mode ✓
- [ ] View attendance logs ✓
- [ ] Multiple face recognition ✓
- [ ] Unknown face detection ✓

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify all dependencies are installed correctly
3. Check browser console for JavaScript errors (F12)
4. Check terminal for Python errors
5. Ensure camera permissions are granted

## 📝 License

This project is for educational purposes.

## 🙏 Credits

Built using:
- Flask (Web Framework)
- OpenCV (Computer Vision)
- dlib (Face Detection)
- face_recognition (Face Recognition Library)
- SQLite (Database)

---

**Version**: 1.0.0  
**Last Updated**: 2024

**Developed for**: Complete Face Recognition Attendance System
