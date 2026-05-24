#!/usr/bin/env python3
"""
Installation Verification Script
Tests if all required packages are installed correctly
"""

import sys
import warnings

def test_imports():
    """Test if all required packages can be imported"""
    
    print("=" * 60)
    print("Face Recognition Attendance System - Installation Test")
    print("=" * 60)
    print()
    
    tests_passed = 0
    tests_failed = 0
    
    # Test Flask
    print("Testing Flask...", end=" ")
    try:
        import flask
        print(f"✓ OK (version {flask.__version__})")
        tests_passed += 1
    except ImportError as e:
        print(f"✗ FAILED: {e}")
        tests_failed += 1
    
    # Test OpenCV
    print("Testing OpenCV...", end=" ")
    try:
        import cv2
        print(f"✓ OK (version {cv2.__version__})")
        tests_passed += 1
    except ImportError as e:
        print(f"✗ FAILED: {e}")
        tests_failed += 1
    
    # Test dlib
    print("Testing dlib...", end=" ")
    try:
        import dlib
        print(f"✓ OK (version {dlib.__version__})")
        tests_passed += 1
    except ImportError as e:
        print(f"✗ FAILED: {e}")
        tests_failed += 1
    
    # Test face_recognition (suppress warning)
    print("Testing face_recognition...", end=" ")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            import face_recognition
        print(f"✓ OK (version {face_recognition.__version__})")
        tests_passed += 1
    except ImportError as e:
        print(f"✗ FAILED: {e}")
        tests_failed += 1
    
    # Test numpy
    print("Testing numpy...", end=" ")
    try:
        import numpy
        print(f"✓ OK (version {numpy.__version__})")
        tests_passed += 1
    except ImportError as e:
        print(f"✗ FAILED: {e}")
        tests_failed += 1
    
    # Test PIL
    print("Testing Pillow...", end=" ")
    try:
        import PIL
        print(f"✓ OK (version {PIL.__version__})")
        tests_passed += 1
    except ImportError as e:
        print(f"✗ FAILED: {e}")
        tests_failed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {tests_passed} passed, {tests_failed} failed")
    print("=" * 60)
    
    if tests_failed == 0:
        print("✓ All packages installed successfully!")
        print()
        print("Next steps:")
        print("1. Run: python app.py")
        print("2. Open browser: http://localhost:5000")
        print("3. Login with: admin / admin123")
        print()
        return True
    else:
        print("✗ Some packages are missing or failed to import")
        print()
        print("Please run: pip install -r requirements.txt")
        print()
        return False

def test_camera():
    """Test if camera is available"""
    print("Testing camera availability...", end=" ")
    try:
        import cv2
        camera = cv2.VideoCapture(0)
        if camera.isOpened():
            print("✓ Camera is available")
            camera.release()
            return True
        else:
            print("✗ Camera not available or in use")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

def test_database():
    """Test database creation"""
    print("Testing database setup...", end=" ")
    try:
        from models import Database
        db = Database()
        print("✓ Database initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print()
    
    # Test imports
    imports_ok = test_imports()
    
    if imports_ok:
        print()
        
        # Test camera
        test_camera()
        
        print()
        
        # Test database
        test_database()
        
        print()
        print("=" * 60)
        print("🎉 System is ready to use!")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("⚠️  Please fix the errors above before running the application")
        print("=" * 60)
        sys.exit(1)