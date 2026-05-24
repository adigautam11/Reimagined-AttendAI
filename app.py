import warnings
warnings.filterwarnings('ignore')

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
import cv2
import base64
import numpy as np
from datetime import datetime
import time
from config import Config
from models import Database
from utils import FaceRecognitionUtil, CameraUtil, encode_frame_to_jpeg

app = Flask(__name__)
app.config.from_object(Config)

# Initialize components
db = Database()
face_util = FaceRecognitionUtil()
camera_util = CameraUtil()

# Global variables
auto_recognition_active = False
last_recognition_time = {}


def decode_base64_image(image_data):
    """
    Decode a base64 image string (with or without data-URL prefix) into a
    clean BGR uint8 numpy array that OpenCV and our utils are happy with.

    Crucially we run cv2.cvtColor(frame, cv2.COLOR_BGR2BGR) — which is a
    no-op colour-wise but forces OpenCV to allocate a fresh, fully-owned
    contiguous buffer, eliminating the JPEG-decode internal-flag quirks that
    confuse dlib's HOG detector.
    """
    try:
        if not image_data:
            print("[ERROR] decode_base64_image: No image data provided")
            return None
            
        # Remove data-URL prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Validate base64 format
        if not image_data.strip():
            print("[ERROR] decode_base64_image: Image data is empty after prefix removal")
            return None
        
        # Decode base64
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            print(f"[ERROR] decode_base64_image: Base64 decode failed - {str(e)}")
            return None
        
        if not image_bytes:
            print("[ERROR] decode_base64_image: No bytes decoded from base64")
            return None
        
        # Convert to numpy array and decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            print("[ERROR] decode_base64_image: cv2.imdecode failed - invalid image format")
            return None
        
        if frame.size == 0:
            print("[ERROR] decode_base64_image: Decoded frame is empty")
            return None

        # Force a clean, owned BGR buffer — this is the key fix for the dlib error
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        print(f"[DEBUG] Image decoded successfully: shape={frame.shape}, dtype={frame.dtype}")
        return frame
        
    except Exception as e:
        print(f"[ERROR] decode_base64_image: Unexpected error - {str(e)}")
        import traceback
        traceback.print_exc()
        return None


# ==================== AUTHENTICATION ROUTES ====================

@app.route('/')
def index():
    """Redirect to login page"""
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            return jsonify({'success': True, 'message': 'Login successful'})
        else:
            return jsonify({'success': False, 'message': 'Invalid credentials'})

    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    return redirect(url_for('login'))


# ==================== DASHBOARD ROUTE ====================

@app.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    return render_template('dashboard.html')


# ==================== CAMERA ROUTES ====================

@app.route('/camera/status')
def camera_status():
    """Check camera status"""
    if 'logged_in' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    status = camera_util.get_camera_status()
    return jsonify({'available': status})


@app.route('/camera/initialize')
def initialize_camera():
    """Initialize camera"""
    if 'logged_in' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    success, message = camera_util.initialize_camera()
    return jsonify({'success': success, 'message': message})


@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    if 'logged_in' not in session:
        return "Unauthorized", 401

    def generate():
        """Video streaming generator function"""
        while True:
            frame = camera_util.capture_frame()

            if frame is not None:
                if auto_recognition_active:
                    students = db.get_all_students()
                    face_util.load_known_faces(students)

                    recognized_faces = face_util.recognize_faces(frame)
                    frame = face_util.draw_face_boxes(frame, recognized_faces)

                    current_time = time.time()
                    for face in recognized_faces:
                        if face['student_id'] is not None:
                            last_time = last_recognition_time.get(face['student_id'], 0)
                            if current_time - last_time >= Config.AUTO_RECOGNITION_DELAY:
                                db.mark_attendance(face['student_id'])
                                last_recognition_time[face['student_id']] = current_time

                jpeg = encode_frame_to_jpeg(frame)
                if jpeg:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg + b'\r\n')

            time.sleep(0.1)

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


# ==================== STUDENT REGISTRATION ROUTES ====================

@app.route('/register_student', methods=['POST'])
def register_student():
    """Register a new student"""
    if 'logged_in' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        course = data.get('course', '').strip()
        section = data.get('section', '').strip()
        image_data = data.get('image')

        print(f"[DEBUG] Registration attempt - Name: {name}, Course: {course}, Section: {section}")

        if not name or not course or not section:
            return jsonify({'success': False, 'message': 'All fields are required'})

        if not image_data:
            return jsonify({'success': False, 'message': 'No image captured'})

        try:
            frame = decode_base64_image(image_data)
            if frame is None:
                return jsonify({'success': False, 'message': 'Failed to decode image'})

            print(f"[DEBUG] Image decoded. Shape: {frame.shape}, dtype: {frame.dtype}, "
                  f"C-contiguous: {frame.flags['C_CONTIGUOUS']}, OWNDATA: {frame.flags['OWNDATA']}")

        except Exception as e:
            print(f"[DEBUG] Image decode error: {str(e)}")
            return jsonify({'success': False, 'message': f'Image decode error: {str(e)}'})

        print("[DEBUG] Starting face detection...")
        success, result, face_location = face_util.detect_and_encode_face(frame)
        print(f"[DEBUG] Face detection result - Success: {success}, "
              f"Result: {result if not success else 'Encoding generated'}")

        if not success:
            return jsonify({'success': False, 'message': result})

        face_encoding = result
        print(f"[DEBUG] Face encoding shape: {face_encoding.shape}")

        print("[DEBUG] Registering in database...")
        registration_result = db.register_student(name, course, section, face_encoding)
        print(f"[DEBUG] Database result: {registration_result}")

        return jsonify(registration_result)

    except Exception as e:
        print(f"[DEBUG] Exception in register_student: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# ==================== ATTENDANCE ROUTES ====================

@app.route('/mark_attendance', methods=['POST'])
def mark_attendance():
    """Mark attendance using face recognition"""
    if 'logged_in' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    try:
        data = request.get_json()
        image_data = data.get('image')

        if not image_data:
            return jsonify({'success': False, 'message': 'No image captured'})

        try:
            frame = decode_base64_image(image_data)
            if frame is None:
                return jsonify({'success': False, 'message': 'Failed to decode image'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Image decode error: {str(e)}'})

        students = db.get_all_students()
        face_util.load_known_faces(students)

        recognized_faces = face_util.recognize_faces(frame)

        if len(recognized_faces) == 0:
            return jsonify({'success': False, 'message': 'No face detected'})

        results = []
        for face in recognized_faces:
            if face['student_id'] is not None:
                result = db.mark_attendance(face['student_id'])
                results.append(result)
            else:
                results.append({
                    'success': False,
                    'message': 'Unknown person detected',
                    'student_name': 'Unknown'
                })

        if len(results) == 1:
            return jsonify(results[0])
        else:
            messages = [r['message'] for r in results]
            return jsonify({
                'success': True,
                'message': ' | '.join(messages),
                'multiple': True,
                'results': results
            })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/toggle_auto_recognition', methods=['POST'])
def toggle_auto_recognition():
    """Toggle auto recognition mode"""
    if 'logged_in' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    global auto_recognition_active

    data = request.get_json()
    auto_recognition_active = data.get('active', False)

    if not auto_recognition_active:
        last_recognition_time.clear()

    return jsonify({
        'success': True,
        'active': auto_recognition_active,
        'message': f"Auto recognition {'enabled' if auto_recognition_active else 'disabled'}"
    })


# ==================== LOGS ROUTES ====================

@app.route('/get_logs')
def get_logs():
    """Get attendance logs"""
    if 'logged_in' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    logs = db.get_attendance_logs()
    return jsonify({'success': True, 'logs': logs})


# ==================== STATISTICS ROUTES ====================

@app.route('/get_stats')
def get_stats():
    """Get dashboard statistics"""
    if 'logged_in' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401

    student_count = db.get_student_count()

    return jsonify({
        'success': True,
        'stats': {
            'total_students': student_count
        }
    })


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ==================== MAIN ====================

if __name__ == '__main__':
    print("=" * 60)
    print("Face Recognition Attendance System")
    print("=" * 60)
    print(f"Admin Username: {Config.ADMIN_USERNAME}")
    print(f"Admin Password: {Config.ADMIN_PASSWORD}")
    print("=" * 60)
    print("Starting server...")
    print("Access the application at: http://127.0.0.1:5000")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
