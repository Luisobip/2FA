# biometric/face_auth.py
import face_recognition
import cv2
from database_manager import DatabaseManager
import numpy as np

class FaceAuth:
    @staticmethod
    def register(username):
        db = DatabaseManager()
        cap = cv2.VideoCapture(0)
        print("Mira a la cámara...")
        ret, frame = cap.read()
        cap.release()
        if not ret:
            print("❌ Error al capturar imagen.")
            return False

        encodings = face_recognition.face_encodings(frame)
        if not encodings:
            print("❌ No se detectó rostro.")
            return False
        
        db.save_face_encoding(username, encodings[0])
        return True

    @staticmethod
    def verify(username):
        db = DatabaseManager()
        known_encoding = db.get_face_encoding(username)
        if known_encoding is None:
            print("⚠️ No hay datos faciales guardados.")
            return False

        cap = cv2.VideoCapture(0)
        print("Verificando rostro...")
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return False

        encodings = face_recognition.face_encodings(frame)
        if not encodings:
            return False

        match = face_recognition.compare_faces([known_encoding], encodings[0])[0]
        return match
