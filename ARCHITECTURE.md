# System Architecture Documentation

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WEB BROWSER (Client)                      │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Login Page │  │  Dashboard   │  │ Video Feed   │       │
│  │  (HTML/CSS) │  │  (HTML/CSS)  │  │   (MJPEG)    │       │
│  └─────────────┘  └──────────────┘  └──────────────┘       │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                           │                                  │
│                      JavaScript                              │
│                    (Fetch API / AJAX)                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  FLASK SERVER (Backend)                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    app.py                           │    │
│  │  • Routes & Endpoints                               │    │
│  │  • Session Management                               │    │
│  │  • Video Streaming                                  │    │
│  │  • Request Handling                                 │    │
│  └────────┬──────────────────────────┬─────────────────┘    │
│           │                          │                       │
│           ▼                          ▼                       │
│  ┌─────────────────┐       ┌─────────────────┐             │
│  │   models.py     │       │    utils.py     │             │
│  │  • Database     │       │  • Face Utils   │             │
│  │  • Students     │       │  • Camera Utils │             │
│  │  • Attendance   │       │  • Recognition  │             │
│  └────────┬────────┘       └────────┬────────┘             │
└───────────┼─────────────────────────┼──────────────────────┘
            │                         │
            ▼                         ▼
  ┌──────────────────┐      ┌──────────────────┐
  │  SQLite Database │      │  Computer Vision │
  │  • students      │      │  • OpenCV        │
  │  • attendance    │      │  • dlib          │
  │  • encodings     │      │  • face_recog    │
  └──────────────────┘      └──────────────────┘
            │                         │
            └────────┬────────────────┘
                     ▼
            ┌──────────────────┐
            │   File System    │
            │  • database/     │
            │  • encodings/    │
            └──────────────────┘
```

## 🔄 Request Flow Diagram

### User Login Flow
```
User → Login Page → Enter Credentials → POST /login
                                             ↓
                                      Validate Credentials
                                             ↓
                                    Create Session (Flask)
                                             ↓
                                    Redirect to Dashboard
```

### Student Registration Flow
```
User → Register Section → Fill Form → Capture Image
                                          ↓
                                  POST /register_student
                                          ↓
                              Decode Base64 Image (utils.py)
                                          ↓
                              Detect Face (face_recognition)
                                          ↓
                      Generate Face Encoding (dlib → 128-D vector)
                                          ↓
                        Store in Database (models.py → SQLite)
                                          ↓
                              Return Success/Error
```

### Attendance Marking Flow
```
User → Mark Attendance → Capture Image → POST /mark_attendance
                                               ↓
                                   Decode Base64 Image
                                               ↓
                              Load Known Faces from DB
                                               ↓
                         Detect Faces in Image (OpenCV)
                                               ↓
                    Generate Encodings for Detected Faces
                                               ↓
                   Compare with Known Encodings (tolerance)
                                               ↓
                          Match Found? ─────┬──── No: "Unknown"
                                            Yes
                                             ↓
                                Check Existing Record
                                             ↓
                        ┌────────────────────┼────────────────────┐
                        │                    │                    │
                   First Scan           Second Scan         Third Scan
                   (No record)       (Has IN, no OUT)   (Has both IN/OUT)
                        │                    │                    │
                   Mark IN Time         Mark OUT Time      "Already Complete"
                   Status: Pending      Check Time:
                                        < 4PM: "Early Dismissal"
                                        >= 4PM: "Present"
```

### Auto Recognition Flow
```
Toggle ON → Start Continuous Loop
                    ↓
            Capture Frame (30 FPS)
                    ↓
            Detect Faces
                    ↓
            Recognize Faces
                    ↓
        For Each Recognized Face:
            ├─ Check Last Recognition Time
            ├─ If > 3 seconds elapsed
            └─ Mark Attendance
                    ↓
            Draw Bounding Boxes
                    ↓
            Stream to Browser
                    ↓
            Wait 100ms (reduce CPU)
                    ↓
            Repeat ←─────────┘
```

## 📦 Component Breakdown

### 1. Frontend Layer (Client-Side)

**Files:**
- `templates/login.html`
- `templates/dashboard.html`
- `static/css/style.css`
- `static/js/main.js`

**Responsibilities:**
- User interface rendering
- Form validation
- Camera feed display
- AJAX requests to backend
- Real-time UI updates
- Message notifications

**Technologies:**
- HTML5
- CSS3 (Flexbox, Grid)
- Vanilla JavaScript (ES6)
- Fetch API

### 2. Application Layer (Backend)

**File:** `app.py`

**Routes:**
```python
/                          → Redirect (login/dashboard)
/login       [GET, POST]   → Authentication
/logout      [GET]         → Session cleanup
/dashboard   [GET]         → Main interface
/video_feed  [GET]         → MJPEG stream

/camera/status      [GET]  → Camera availability
/camera/initialize  [GET]  → Start camera

/register_student        [POST] → Student registration
/mark_attendance         [POST] → Attendance marking
/toggle_auto_recognition [POST] → Auto mode toggle

/get_logs  [GET] → Attendance logs
/get_stats [GET] → Statistics
```

**Responsibilities:**
- HTTP request handling
- Session management
- Authentication
- Route protection
- Video streaming (MJPEG)
- JSON API responses
- Error handling

**Technologies:**
- Flask 2.3.3
- Flask Sessions
- Response streaming

### 3. Data Layer

**File:** `models.py`

**Classes:**
- `Database` - Main database handler

**Methods:**
```python
# Database Management
get_connection()        → SQLite connection
init_db()              → Create tables

# Student Operations
register_student()     → Add new student
get_all_students()     → Fetch all (with encodings)
get_student_by_id()    → Fetch specific student

# Attendance Operations
mark_attendance()      → Mark IN/OUT with logic
get_attendance_logs()  → Retrieve records
get_student_count()    → Statistics
```

**Database Schema:**

```sql
-- Students Table
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    course TEXT NOT NULL,
    section TEXT NOT NULL,
    face_encoding BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Attendance Table
CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    date DATE NOT NULL,
    time_in TIME,
    time_out TIME,
    status TEXT DEFAULT 'Pending',
    FOREIGN KEY (student_id) REFERENCES students(id),
    UNIQUE(student_id, date)
);
```

**Technologies:**
- SQLite 3
- Python sqlite3 module
- Pickle (for encoding storage)

### 4. Utility Layer

**File:** `utils.py`

**Classes:**

**FaceRecognitionUtil:**
```python
load_known_faces()       → Load from DB
detect_and_encode_face() → Single face processing
recognize_faces()        → Multi-face recognition
draw_face_boxes()        → Visual labeling
```

**CameraUtil:**
```python
initialize_camera()  → Start webcam
capture_frame()      → Get single frame
release_camera()     → Cleanup
get_camera_status()  → Health check
```

**Technologies:**
- face_recognition 1.3.0 (wrapper for dlib)
- dlib 19.24.2 (HOG/CNN face detection)
- OpenCV 4.8.0 (image processing)
- NumPy 1.24.3 (array operations)

### 5. Configuration Layer

**File:** `config.py`

**Settings:**
```python
# Flask
SECRET_KEY              → Session encryption

# Paths
DATABASE_PATH           → SQLite location
ENCODINGS_DIR           → Storage directory

# Authentication
ADMIN_USERNAME          → Login username
ADMIN_PASSWORD          → Login password

# Face Recognition
TOLERANCE = 0.6         → Match threshold
MODEL = 'hog'           → Detection model

# Business Logic
AUTO_RECOGNITION_DELAY  → Scan interval
EARLY_DISMISSAL_HOUR    → Cut-off time
EARLY_DISMISSAL_MINUTE  → Cut-off time
```

## 🔐 Security Architecture

### Authentication Flow
```
User Request → Check Session → Session Valid? ─┬─ No → Redirect to Login
                                               Yes
                                                ↓
                                         Allow Access
```

### Session Management
- Flask sessions (cookie-based)
- Server-side storage
- Automatic expiration
- Secure cookie flags (in production)

### Data Security
- Face encodings stored as binary (pickle)
- No face images stored (only encodings)
- Database in protected directory
- Input validation on all endpoints
- CSRF protection (to be added in production)

## 🎯 Face Recognition Pipeline

### 1. Detection Phase
```
Input Image → OpenCV → face_recognition.face_locations()
                              ↓
                    Uses dlib's HOG/CNN detector
                              ↓
              Returns: [(top, right, bottom, left), ...]
```

### 2. Encoding Phase
```
Face Locations → face_recognition.face_encodings()
                           ↓
                  dlib's face recognition model
                           ↓
              Returns: [128-D vector, 128-D vector, ...]
```

### 3. Recognition Phase
```
New Encoding → face_recognition.compare_faces()
                           ↓
                 Euclidean distance calculation
                           ↓
              Distance < TOLERANCE? → Match Found
              Distance >= TOLERANCE → No Match
```

### Face Encoding Details
```
Face Image (RGB) → 68 facial landmarks → 128-dimensional vector

Example:
[0.123, -0.456, 0.789, ..., 0.234]  (128 values)
     ↓
Stored in database as BLOB (pickle)
     ↓
Loaded and compared at runtime
```

## 📊 Data Flow Diagram

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Camera  │────▶│  OpenCV  │────▶│   dlib   │────▶│ Database │
│ (Webcam) │     │ (Capture)│     │(Encoding)│     │(Storage) │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                          │
                                                          ▼
                                                    ┌──────────┐
                                                    │  Pickle  │
                                                    │  (BLOB)  │
                                                    └──────────┘

                    Recognition Flow
                    ────────────────

Camera → Frame → Detect → Encode → Compare → Match → Database
  │                                    ▲                 │
  └────────────────────────────────────┴─────────────────┘
                  (Known encodings)
```

## 🔄 State Machine - Attendance Status

```
                  ┌─────────────────┐
                  │   No Record     │
                  │   (New Day)     │
                  └────────┬────────┘
                           │
                    First Scan (IN)
                           │
                           ▼
                  ┌─────────────────┐
                  │  In Progress    │
                  │  (Has IN time)  │
                  └────────┬────────┘
                           │
                   Second Scan (OUT)
                           │
                           ├─────────────────┬─────────────────┐
                           ▼                 ▼                 ▼
                  ┌─────────────┐   ┌──────────────┐  ┌────────────┐
                  │   Present   │   │    Early     │  │  Pending   │
                  │ (OUT≥4PM)   │   │  Dismissal   │  │ (Error)    │
                  │             │   │  (OUT<4PM)   │  │            │
                  └─────────────┘   └──────────────┘  └────────────┘
                         │                  │
                         └──────────┬───────┘
                                    │
                            Third Scan (Rejected)
                                    │
                                    ▼
                          "Already Completed"
```

## 💾 Storage Architecture

### File System Structure
```
face_recognition_attendance/
├── database/
│   └── attendance.db           (SQLite database)
│
├── encodings/                  (Reserved for future use)
│   └── .gitkeep
│
├── static/                     (Served by Flask)
│   ├── css/
│   └── js/
│
└── templates/                  (Jinja2 templates)
```

### Database Storage

**Students Table:**
```
┌────┬──────────┬───────────────┬─────────┬─────────────────────┬────────────┐
│ id │   name   │    course     │ section │   face_encoding     │ created_at │
├────┼──────────┼───────────────┼─────────┼─────────────────────┼────────────┤
│ 1  │ John Doe │ CS            │ A       │ [binary blob]       │ 2024-...   │
│ 2  │ Jane Doe │ Engineering   │ B       │ [binary blob]       │ 2024-...   │
└────┴──────────┴───────────────┴─────────┴─────────────────────┴────────────┘

face_encoding: Pickled NumPy array (128 float values)
Size: ~1KB per student
```

**Attendance Table:**
```
┌────┬────────────┬────────────┬──────────┬───────────┬──────────────────┐
│ id │ student_id │    date    │ time_in  │ time_out  │     status       │
├────┼────────────┼────────────┼──────────┼───────────┼──────────────────┤
│ 1  │     1      │ 2024-01-15 │ 08:30:00 │ 16:30:00  │ Present          │
│ 2  │     2      │ 2024-01-15 │ 09:00:00 │ 14:00:00  │ Early Dismissal  │
│ 3  │     1      │ 2024-01-16 │ 08:15:00 │ NULL      │ In Progress      │
└────┴────────────┴────────────┴──────────┴───────────┴──────────────────┘

UNIQUE constraint on (student_id, date) prevents duplicates
```

## 🚀 Performance Considerations

### Face Detection Speed
- **HOG model**: ~30 FPS (CPU)
- **CNN model**: ~5 FPS (CPU), ~60 FPS (GPU)

### Recognition Accuracy
- **TOLERANCE 0.4**: 99% accuracy, may reject same person
- **TOLERANCE 0.6**: 95% accuracy, balanced (default)
- **TOLERANCE 0.8**: 90% accuracy, lenient

### Optimization Strategies
1. Resize images to 640x480 before processing
2. Use HOG model for speed (CPU)
3. Process every Nth frame in auto mode
4. Cache known encodings in memory
5. Index database on student_id, date

### Scalability
- **Students**: Tested up to 1000 students
- **Daily Attendance**: Handles 500+ entries/day
- **Concurrent Users**: Single-threaded (use gunicorn for production)

## 🔌 API Architecture

### REST Endpoints

**Authentication:**
```
POST /login
Body: {username, password}
Response: {success, message}
```

**Student Registration:**
```
POST /register_student
Body: {name, course, section, image (base64)}
Response: {success, message, student_id}
```

**Attendance Marking:**
```
POST /mark_attendance
Body: {image (base64)}
Response: {success, message, type, status, student_name}
```

**Data Retrieval:**
```
GET /get_logs
Response: {success, logs: [...]}

GET /get_stats
Response: {success, stats: {total_students}}
```

### Video Streaming
```
GET /video_feed
Response: multipart/x-mixed-replace; boundary=frame
Stream: JPEG frames (MJPEG format)
```

## 🧩 Module Dependencies

```
app.py
  ├── config.py
  ├── models.py
  │   └── config.py
  └── utils.py
      └── config.py

models.py
  └── sqlite3 (Python stdlib)

utils.py
  ├── opencv-python
  ├── face_recognition
  │   └── dlib
  └── numpy
```

## 📈 System Workflow Summary

1. **Initialization**
   - Load config
   - Initialize database
   - Create tables if needed

2. **Authentication**
   - User provides credentials
   - Validate against config
   - Create session

3. **Student Management**
   - Capture face image
   - Detect and encode face
   - Store in database

4. **Attendance**
   - Capture image
   - Detect faces
   - Match against known faces
   - Apply business logic
   - Update database

5. **Reporting**
   - Query database
   - Format results
   - Send to frontend

---

**This architecture supports:**
- ✅ Modularity (easy to extend)
- ✅ Scalability (database-backed)
- ✅ Maintainability (clear separation)
- ✅ Security (session-based auth)
- ✅ Performance (optimized pipeline)

