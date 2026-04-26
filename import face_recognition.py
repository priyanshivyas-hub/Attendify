import face_recognition
import cv2
import numpy as np
from PIL import Image
import io
import base64
from database import get_db_connection
import pickle

class FaceRecognitionSystem:
    def __init__(self):
        self.known_faces = []
        self.known_names = []
        self.load_known_faces()
    
    def load_known_faces(self):
        """Load known faces from database"""
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT u.user_id, u.full_name, uf.face_encoding
            FROM users u
            JOIN user_faces uf ON u.user_id = uf.user_id
            WHERE uf.is_active = 1
        """)
        
        for row in cursor.fetchall():
            try:
                encoding = pickle.loads(row[2])
                self.known_faces.append(encoding)
                self.known_names.append({'id': row[0], 'name': row[1]})
            except:
                continue
        
        cursor.close()
        conn.close()
    
    def register_face(self, user_id, image_base64):
        """Register new face for user"""
        try:
            # Decode base64 image
            image_data = base64.b64decode(image_base64.split(',')[1])
            image = Image.open(io.BytesIO(image_data))
            image_np = np.array(image)
            
            # Detect face and get encoding
            face_locations = face_recognition.face_locations(image_np)
            if not face_locations:
                return False, "No face detected"
            
            face_encodings = face_recognition.face_encodings(image_np, face_locations)
            if not face_encodings:
                return False, "Could not encode face"
            
            # Store in database
            encoding_binary = pickle.dumps(face_encodings[0])
            
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_faces (user_id, face_encoding, is_active)
                VALUES (?, ?, 1)
            """, (user_id, encoding_binary))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            # Reload faces
            self.load_known_faces()
            
            return True, "Face registered successfully"
            
        except Exception as e:
            return False, str(e)
    
    def recognize_face(self, image_base64):
        """Recognize face from image"""
        try:
            # Decode image
            image_data = base64.b64decode(image_base64.split(',')[1])
            image = Image.open(io.BytesIO(image_data))
            image_np = np.array(image)
            
            # Find faces
            face_locations = face_recognition.face_locations(image_np)
            face_encodings = face_recognition.face_encodings(image_np, face_locations)
            
            results = []
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(
                    self.known_faces, 
                    face_encoding,
                    tolerance=0.6
                )
                
                if True in matches:
                    first_match_index = matches.index(True)
                    user = self.known_names[first_match_index]
                    results.append({
                        'recognized': True,
                        'user_id': user['id'],
                        'name': user['name']
                    })
                else:
                    results.append({
                        'recognized': False,
                        'user_id': None,
                        'name': 'Unknown'
                    })
            
            return True, results
            
        except Exception as e:
            return False, str(e)
    
    def mark_attendance_by_face(self, class_instance_id, image_base64):
        """Mark attendance using face recognition"""
        success, results = self.recognize_face(image_base64)
        
        if not success:
            return False, results
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for result in results:
            if result['recognized']:
                # Mark attendance
                cursor.execute("""
                    IF NOT EXISTS (
                        SELECT 1 FROM attendance 
                        WHERE instance_id = ? AND student_id = ?
                    )
                    INSERT INTO attendance (instance_id, student_id, status, marked_by)
                    VALUES (?, ?, 'present', ?)
                    ELSE
                    UPDATE attendance 
                    SET status = 'present' 
                    WHERE instance_id = ? AND student_id = ?
                """, (class_instance_id, result['user_id'],
                      class_instance_id, result['user_id'], 'SYSTEM',
                      class_instance_id, result['user_id']))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return True, f"Attendance marked for {len(results)} students"

face_recognition_system = FaceRecognitionSystem()