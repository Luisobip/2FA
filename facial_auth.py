# Autenticación facial con detección de vivacidad

import cv2
import face_recognition
import numpy as np
from config import Config

class FacialAuth:
    """Autenticación facial con detección de vivacidad"""
    
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.tolerance = Config.FACE_RECOGNITION_TOLERANCE
        self.movement_threshold = Config.FACE_MOVEMENT_THRESHOLD
        self.center_threshold = Config.FACE_CENTER_THRESHOLD
    
    def capture_and_encode_face(self, username):
        """Captura la cara del usuario y guarda su encoding"""
        print("\n📸 Capturando tu rostro para registro...")
        print("Instrucciones:")
        print("• Colócate frente a la cámara con buena iluminación")
        print("• Mira directamente a la cámara")
        print("• Presiona 'c' para capturar cuando veas el recuadro verde")
        print("• Presiona 'q' para cancelar")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ No se pudo acceder a la cámara")
            return None
        
        encoding = None
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Error al leer de la cámara")
                break
            
            frame_count += 1
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detectar caras cada 3 frames (optimización)
            if frame_count % 3 == 0:
                face_locations = face_recognition.face_locations(rgb_frame)
            
                if face_locations:
                    for (top, right, bottom, left) in face_locations:
                        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                        cv2.putText(frame, "Cara detectada - Presiona 'c'", 
                                   (left, top - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                else:
                    cv2.putText(frame, "No se detecta rostro", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow('Registro Facial', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('c') and face_locations:
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                if face_encodings:
                    encoding = face_encodings[0]
                    print("✅ Rostro capturado correctamente")
                    break
                else:
                    print("⚠️  No se pudo codificar el rostro, intenta de nuevo")
            elif key == ord('q'):
                print("❌ Captura cancelada")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        return encoding
    
    def verify_with_liveness(self, username, stored_encoding):
        """Verifica la identidad con detección de vivacidad"""
        print("\n🔍 Verificación facial con detección de vivacidad")
        print("\nInstrucciones:")
        print("1. Mira a la cámara (centro)")
        print("2. Gira tu cabeza LENTAMENTE a la IZQUIERDA")
        print("3. Luego gira LENTAMENTE a la DERECHA")
        print("4. Vuelve al CENTRO")
        print("\nPresiona 'q' para cancelar en cualquier momento\n")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ No se pudo acceder a la cámara")
            return False
        
        stages = {
            'center_initial': False,
            'left': False,
            'right': False,
            'center_final': False
        }
        
        current_stage = 'center_initial'
        face_verified = False
        positions = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Procesar cada 2 frames para mejor rendimiento
            if frame_count % 2 == 0:
                face_locations = face_recognition.face_locations(rgb_frame)
                
                if face_locations:
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    
                    if face_encodings:
                        matches = face_recognition.compare_faces(
                            [stored_encoding], face_encodings[0], tolerance=self.tolerance
                        )
                        face_distance = face_recognition.face_distance(
                            [stored_encoding], face_encodings[0]
                        )
                        
                        if matches[0] and face_distance[0] < self.tolerance:
                            face_verified = True
                            
                            top, right, bottom, left = face_locations[0]
                            face_center_x = (left + right) // 2
                            frame_center_x = frame.shape[1] // 2
                            offset = face_center_x - frame_center_x
                            
                            positions.append(offset)
                            if len(positions) > 10:
                                positions.pop(0)
                            
                            avg_offset = np.mean(positions) if positions else 0
                            
                            # Máquina de estados para detección de vivacidad
                            if current_stage == 'center_initial' and abs(avg_offset) < self.center_threshold:
                                stages['center_initial'] = True
                                current_stage = 'left'
                                print("✓ Centro inicial detectado → Gira a la IZQUIERDA")
                            
                            elif current_stage == 'left' and avg_offset < -self.movement_threshold:
                                stages['left'] = True
                                current_stage = 'right'
                                print("✓ Izquierda detectada → Gira a la DERECHA")
                            
                            elif current_stage == 'right' and avg_offset > self.movement_threshold:
                                stages['right'] = True
                                current_stage = 'center_final'
                                print("✓ Derecha detectada → Vuelve al CENTRO")
                            
                            elif current_stage == 'center_final' and abs(avg_offset) < self.center_threshold:
                                stages['center_final'] = True
                                print("✅ ¡Verificación de vivacidad completada!")
                                break
                            
                            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                            cv2.putText(frame, f"Etapa: {current_stage}", (10, 30),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                            cv2.putText(frame, f"Offset: {int(avg_offset)}", (10, 60),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                        else:
                            cv2.putText(frame, "Rostro no reconocido", (10, 30),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                            face_verified = False
                else:
                    cv2.putText(frame, "No se detecta rostro", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow('Verificacion Facial - Deteccion de Vivacidad', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("❌ Verificación cancelada")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        return all(stages.values()) and face_verified