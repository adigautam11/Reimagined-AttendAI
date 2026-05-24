import cv2
import dlib
import face_recognition
import numpy as np
from config import Config
import os

# ---------------------------------------------------------------------------
# Load dlib models directly — bypasses face_recognition's broken pose_predictor
# call on Windows/Python 3.10
# ---------------------------------------------------------------------------

# These model files ship with the face_recognition_models package
import face_recognition_models

_detector  = dlib.get_frontal_face_detector()
_predictor = dlib.shape_predictor(face_recognition_models.pose_predictor_model_location())
_encoder   = dlib.face_recognition_model_v1(face_recognition_models.face_recognition_model_location())


def _rect_to_tuple(rect):
    """Convert dlib rectangle to (top, right, bottom, left) ints."""
    return (int(rect.top()), int(rect.right()), int(rect.bottom()), int(rect.left()))


def _get_encoding_dlib(rgb_img, rect):
    """
    Use dlib directly to get a 128-d face encoding.
    rgb_img : numpy uint8 RGB array
    rect    : dlib.rectangle for the face
    Returns numpy array (128,) or None.
    """
    try:
        shape    = _predictor(rgb_img, rect)
        encoding = _encoder.compute_face_descriptor(rgb_img, shape)
        return np.array(encoding)
    except Exception as e:
        print(f"[DEBUG] dlib encoding error: {e}")
        return None


def _cv2_rect_to_dlib(x, y, w, h):
    """Convert OpenCV (x,y,w,h) to a dlib rectangle."""
    return dlib.rectangle(left=x, top=y, right=x + w, bottom=y + h)


# ---------------------------------------------------------------------------
# FaceRecognitionUtil
# ---------------------------------------------------------------------------

class FaceRecognitionUtil:
    def __init__(self):
        self.known_encodings = []
        self.known_ids       = []
        self.known_names     = []

        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def load_known_faces(self, students):
        self.known_encodings = []
        self.known_ids       = []
        self.known_names     = []
        for student in students:
            self.known_encodings.append(student['face_encoding'])
            self.known_ids.append(student['id'])
            self.known_names.append(student['name'])

    def _to_rgb(self, frame):
        """Convert BGR frame to a fresh, owned RGB uint8 array."""
        try:
            if frame is None:
                print("[ERROR] _to_rgb: Frame is None")
                return None
            
            if not hasattr(frame, 'shape') or len(frame.shape) < 2:
                print(f"[ERROR] _to_rgb: Invalid frame shape - {frame.shape if hasattr(frame, 'shape') else 'no shape'}")
                return None
            
            if frame.size == 0:
                print("[ERROR] _to_rgb: Frame is empty")
                return None
            
            # Ensure uint8
            if frame.dtype != np.uint8:
                print(f"[DEBUG] _to_rgb: Converting dtype {frame.dtype} to uint8")
                frame = frame.astype(np.uint8)
            
            if len(frame.shape) == 2:
                rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            elif frame.shape[2] == 4:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
            elif frame.shape[2] == 3:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                print(f"[ERROR] _to_rgb: Unsupported number of channels - {frame.shape[2]}")
                return None
            
            # np.array with copy=True gives dlib a fully owned buffer
            result = np.array(rgb, dtype=np.uint8, copy=True)
            print(f"[DEBUG] _to_rgb: Converted successfully - shape={result.shape}, dtype={result.dtype}")
            return result
            
        except cv2.error as e:
            print(f"[ERROR] _to_rgb: OpenCV error - {str(e)}")
            return None
        except Exception as e:
            print(f"[ERROR] _to_rgb: Unexpected error - {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _detect_faces_haar(self, frame):
        """Return list of (x, y, w, h) plain Python ints from Haar Cascade."""
        try:
            if frame is None:
                print("[ERROR] _detect_faces_haar: Frame is None")
                return []
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces_cv = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
            )
            if len(faces_cv) == 0:
                return []
            
            result = [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces_cv]
            print(f"[DEBUG] _detect_faces_haar: Detected {len(result)} face(s)")
            return result
            
        except cv2.error as e:
            print(f"[ERROR] _detect_faces_haar: OpenCV error - {str(e)}")
            return []
        except Exception as e:
            print(f"[ERROR] _detect_faces_haar: {str(e)}")
            return []

    def detect_and_encode_face(self, frame):
        """
        Detect a single face and return its 128-d encoding.
        Uses dlib directly — bypasses face_recognition.face_encodings() which
        crashes on Windows/Python 3.10 due to a dlib buffer bug.

        Returns: (success: bool, encoding | error_str, face_location | None)
        """
        try:
            if frame is None:
                return False, "Invalid frame received", None

            rgb = self._to_rgb(frame)
            if rgb is None:
                return False, "Failed to convert frame to RGB", None

            print(f"[DEBUG] RGB — shape:{rgb.shape} dtype:{rgb.dtype} "
                  f"C_CONT:{rgb.flags['C_CONTIGUOUS']} OWNDATA:{rgb.flags['OWNDATA']}")

            faces = self._detect_faces_haar(frame)

            if len(faces) == 0:
                return False, "No face detected. Please position your face clearly in front of the camera.", None
            if len(faces) > 1:
                return False, "Multiple faces detected. Please ensure only one person is in frame.", None

            x, y, w, h    = faces[0]
            face_location  = (y, x + w, y + h, x)          # (top, right, bottom, left)
            dlib_rect      = _cv2_rect_to_dlib(x, y, w, h)

            print(f"[DEBUG] Face at (top,right,bottom,left): {face_location}")

            encoding = _get_encoding_dlib(rgb, dlib_rect)
            if encoding is None:
                return False, "Could not generate face encoding. Try better lighting or move closer.", None

            print("[DEBUG] Encoding generated successfully via dlib direct call")
            return True, encoding, face_location

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Error processing image: {str(e)}", None

    def recognize_faces(self, frame):
        """Detect and recognize all faces in a BGR frame."""
        try:
            if frame is None:
                return []

            rgb   = self._to_rgb(frame)
            if rgb is None:
                return []

            faces            = self._detect_faces_haar(frame)
            recognized_faces = []

            for (x, y, w, h) in faces:
                face_location = (y, x + w, y + h, x)
                dlib_rect     = _cv2_rect_to_dlib(x, y, w, h)
                face_encoding = _get_encoding_dlib(rgb, dlib_rect)

                if face_encoding is None:
                    continue

                student_id   = None
                student_name = "Unknown"

                if self.known_encodings:
                    # compare_faces / face_distance work fine — only encoding is broken
                    matches   = face_recognition.compare_faces(
                        self.known_encodings, face_encoding, tolerance=Config.TOLERANCE
                    )
                    if True in matches:
                        distances = face_recognition.face_distance(self.known_encodings, face_encoding)
                        best      = int(np.argmin(distances))
                        if matches[best]:
                            student_id   = self.known_ids[best]
                            student_name = self.known_names[best]

                recognized_faces.append({
                    'student_id':    student_id,
                    'student_name':  student_name,
                    'face_location': face_location,
                    'encoding':      face_encoding
                })

            return recognized_faces

        except Exception as e:
            print(f"Error in recognize_faces: {e}")
            import traceback
            traceback.print_exc()
            return []

    def draw_face_boxes(self, frame, recognized_faces):
        for face in recognized_faces:
            top, right, bottom, left = face['face_location']
            color = (0, 255, 0) if face['student_id'] is not None else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, top - 35), (right, top), color, cv2.FILLED)
            cv2.putText(frame, face['student_name'],
                        (left + 6, top - 6), cv2.FONT_HERSHEY_DUPLEX,
                        0.6, (255, 255, 255), 1)
        return frame


# ---------------------------------------------------------------------------
# CameraUtil
# ---------------------------------------------------------------------------

class CameraUtil:
    def __init__(self):
        self.camera = None

    def initialize_camera(self, camera_index=0):
        try:
            if self.camera is not None:
                self.camera.release()
                self.camera = None

            # DirectShow is far more compatible than MSMF on Windows
            self.camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            if not self.camera.isOpened():
                self.camera = cv2.VideoCapture(camera_index)
            if not self.camera.isOpened():
                return False, "Could not open camera. Check it is connected and not in use."

            # Try resolutions from high to low
            for rw, rh in [(1280, 720), (640, 480), (320, 240)]:
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH,  rw)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, rh)
                ok, test = self.camera.read()
                if ok and test is not None and test.size > 0:
                    aw = int(self.camera.get(cv2.CAP_PROP_FRAME_WIDTH))
                    ah = int(self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    print(f"[DEBUG] Camera opened at {aw}x{ah}")
                    return True, f"Camera initialized at {aw}x{ah}"

            ok, test = self.camera.read()
            if ok and test is not None and test.size > 0:
                return True, "Camera initialized"

            self.camera.release()
            self.camera = None
            return False, "Camera opened but could not read frames."

        except Exception as e:
            return False, f"Error initializing camera: {str(e)}"

    def capture_frame(self):
        try:
            if self.camera is None:
                print("[ERROR] capture_frame: Camera is None")
                return None
            
            if not self.camera.isOpened():
                print("[ERROR] capture_frame: Camera is not open")
                return None
            
            ret, frame = self.camera.read()
            
            if not ret:
                print("[ERROR] capture_frame: cv2.read() returned False - camera may be disconnected")
                return None
            
            if frame is None:
                print("[ERROR] capture_frame: cv2.read() returned None frame")
                return None
            
            if frame.size == 0:
                print("[ERROR] capture_frame: Frame is empty")
                return None
            
            if frame.dtype != np.uint8:
                print(f"[DEBUG] capture_frame: Converting frame dtype {frame.dtype} to uint8")
                frame = frame.astype(np.uint8)
            
            return frame
            
        except cv2.error as e:
            print(f"[ERROR] capture_frame: OpenCV error - {str(e)}")
            return None
        except Exception as e:
            print(f"[ERROR] capture_frame: Unexpected error - {str(e)}")
            return None

    def release_camera(self):
        if self.camera is not None:
            self.camera.release()
            self.camera = None

    def get_camera_status(self):
        return self.camera is not None and self.camera.isOpened()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def encode_frame_to_jpeg(frame):
    """
    Encode an OpenCV frame to JPEG bytes with error handling.
    """
    try:
        if frame is None:
            print("[ERROR] encode_frame_to_jpeg: Frame is None")
            return None
        
        if frame.size == 0:
            print("[ERROR] encode_frame_to_jpeg: Frame is empty")
            return None
        
        if frame.dtype != np.uint8:
            print(f"[DEBUG] encode_frame_to_jpeg: Converting dtype {frame.dtype} to uint8")
            frame = frame.astype(np.uint8)
        
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
        
        if not ret:
            print("[ERROR] encode_frame_to_jpeg: cv2.imencode failed")
            return None
        
        jpeg_bytes = buffer.tobytes()
        if not jpeg_bytes:
            print("[ERROR] encode_frame_to_jpeg: No bytes from encoded buffer")
            return None
        
        return jpeg_bytes
        
    except Exception as e:
        print(f"[ERROR] encode_frame_to_jpeg: {str(e)}")
        import traceback
        traceback.print_exc()
        return None