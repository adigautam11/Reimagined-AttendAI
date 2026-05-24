import sqlite3
import pickle
from datetime import datetime, date
from config import Config

class Database:
    def __init__(self):
        self.db_path = Config.DATABASE_PATH
        self.init_db()
    
    def get_connection(self):
        """Create and return a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                course TEXT NOT NULL,
                section TEXT NOT NULL,
                face_encoding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time_in TEXT,
                time_out TEXT,
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY (student_id) REFERENCES students(id),
                UNIQUE(student_id, date)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ==================== STUDENT OPERATIONS ====================
    
    def register_student(self, name, course, section, face_encoding):
        """Register a new student with face encoding"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            encoding_blob = pickle.dumps(face_encoding)
            
            cursor.execute('''
                INSERT INTO students (name, course, section, face_encoding)
                VALUES (?, ?, ?, ?)
            ''', (name, course, section, encoding_blob))
            
            conn.commit()
            student_id = cursor.lastrowid
            conn.close()
            
            return {'success': True, 'student_id': student_id, 'message': 'Student registered successfully'}
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_all_students(self):
        """Get all students with their encodings"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM students')
        rows = cursor.fetchall()
        
        students = []
        for row in rows:
            student = {
                'id': row['id'],
                'name': row['name'],
                'course': row['course'],
                'section': row['section'],
                'face_encoding': pickle.loads(row['face_encoding'])
            }
            students.append(student)
        
        conn.close()
        return students
    
    def get_student_by_id(self, student_id):
        """Get student by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM students WHERE id = ?', (student_id,))
        row = cursor.fetchone()
        
        if row:
            student = {
                'id': row['id'],
                'name': row['name'],
                'course': row['course'],
                'section': row['section']
            }
            conn.close()
            return student
        
        conn.close()
        return None
    
    # ==================== ATTENDANCE OPERATIONS ====================
    
    def mark_attendance(self, student_id, scan_type='in'):
        """
        Mark attendance for a student.
        All date/time values stored as plain strings — avoids SQLite
        'Error binding parameter' with Python date/time objects.
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            now = datetime.now()
            
            # Store as plain strings so SQLite never sees a Python date/time object
            today_str        = now.strftime('%Y-%m-%d')          # e.g. "2026-04-11"
            current_time_str = now.strftime('%H:%M:%S')          # e.g. "12:34:56"
            current_hour     = now.hour
            current_minute   = now.minute
            
            # Check if attendance record exists for today
            cursor.execute('''
                SELECT * FROM attendance 
                WHERE student_id = ? AND date = ?
            ''', (student_id, today_str))
            
            existing_record = cursor.fetchone()
            
            if not existing_record:
                # First scan — mark IN
                cursor.execute('''
                    INSERT INTO attendance (student_id, date, time_in, status)
                    VALUES (?, ?, ?, 'In Progress')
                ''', (student_id, today_str, current_time_str))
                
                conn.commit()
                conn.close()
                
                student = self.get_student_by_id(student_id)
                return {
                    'success': True,
                    'message': f"Welcome {student['name']}! Attendance marked (IN)",
                    'type': 'in',
                    'student_name': student['name']
                }
            
            elif existing_record['time_out'] is None:
                # Second scan — mark OUT
                if (current_hour < Config.EARLY_DISMISSAL_HOUR or
                    (current_hour == Config.EARLY_DISMISSAL_HOUR and
                     current_minute < Config.EARLY_DISMISSAL_MINUTE)):
                    status = 'Early Dismissal'
                else:
                    status = 'Present'
                
                cursor.execute('''
                    UPDATE attendance 
                    SET time_out = ?, status = ?
                    WHERE student_id = ? AND date = ?
                ''', (current_time_str, status, student_id, today_str))
                
                conn.commit()
                conn.close()
                
                student = self.get_student_by_id(student_id)
                return {
                    'success': True,
                    'message': f"Goodbye {student['name']}! Marked OUT - Status: {status}",
                    'type': 'out',
                    'status': status,
                    'student_name': student['name']
                }
            
            else:
                # Already marked both IN and OUT
                conn.close()
                student = self.get_student_by_id(student_id)
                return {
                    'success': False,
                    'message': f"{student['name']}: Attendance already completed for today",
                    'type': 'completed',
                    'student_name': student['name']
                }
        
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}
    
    def get_attendance_logs(self, limit=100):
        """Get attendance logs with student details"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                a.id,
                s.name as student_name,
                s.course,
                s.section,
                a.date,
                a.time_in,
                a.time_out,
                a.status
            FROM attendance a
            JOIN students s ON a.student_id = s.id
            ORDER BY a.date DESC, a.time_in DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        
        logs = []
        for row in rows:
            log = {
                'id': row['id'],
                'student_name': row['student_name'],
                'course': row['course'],
                'section': row['section'],
                'date': row['date'],
                'time_in': row['time_in'] if row['time_in'] else 'N/A',
                'time_out': row['time_out'] if row['time_out'] else 'N/A',
                'status': row['status']
            }
            logs.append(log)
        
        conn.close()
        return logs
    
    def get_student_count(self):
        """Get total number of registered students"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM students')
        count = cursor.fetchone()['count']
        
        conn.close()
        return count