import os

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database', 'attendance.db')
    
    # Encodings directory
    ENCODINGS_DIR = os.path.join(os.path.dirname(__file__), 'encodings')
    
    # Admin credentials (in production, use hashed passwords)
    ADMIN_USERNAME = 'admin'
    ADMIN_PASSWORD = 'admin123'
    
    # Face recognition settings
    TOLERANCE = 0.6  # Lower is more strict (0.4 = strict, 0.6 = default, 0.7 = lenient)
    MODEL = 'hog'   # 'hog' for CPU  |  'cnn' only if you have an NVIDIA GPU with CUDA

    # Auto recognition delay (seconds between re-marking the same person)
    AUTO_RECOGNITION_DELAY = 3

    # Early dismissal time (24-hour format)
    EARLY_DISMISSAL_HOUR   = 16  # 4:00 PM
    EARLY_DISMISSAL_MINUTE = 0

# Create necessary directories on import
os.makedirs(os.path.join(os.path.dirname(__file__), 'database'), exist_ok=True)
os.makedirs(Config.ENCODINGS_DIR, exist_ok=True)