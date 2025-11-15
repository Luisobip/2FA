# Autenticación facial optimizada con detección de vivacidad simple

import cv2
import face_recognition
import numpy as np
from config import Config
import os
import urllib.request
from scipy.spatial import distance as dist
from collections import deque

class FacialAuth:
    """Autenticación facial optimizada con detección de vivacidad mediante gestos simples"""
    
    def __init__(self):
        self.tolerance = Config.FACE_RECOGNITION_TOLERANCE
        
        # Optimización: usar búfer para suavizar detecciones
        self.face_buffer = deque(maxlen=3)
        self.encoding_buffer = deque(maxlen=3)
        
        # Umbrales para detección de vivacidad
        self.EAR_THRESHOLD = 0.15  # Umbral para parpadeo
        self.MAR_THRESHOLD = 0.27  # Umbral para boca abierta
        self.CONSECUTIVE_FRAMES = 3  # Frames necesarios para confirmar gesto
        
        # Estados para detectar transiciones
        self.eye_state_history = deque(maxlen=10)  # Historia de estados de ojos
        self.mouth_state_history = deque(maxlen=10)  # Historia de estados de boca
        
        # Cargar detector DNN
        self.face_detector = self._load_dnn_detector()
        self.confidence_threshold = 0.6
        self.min_face_size = 100
    
    def _load_dnn_detector(self):
        """Carga el detector DNN de rostros de OpenCV"""
        model_dir = "models"
        os.makedirs(model_dir, exist_ok=True)
        
        prototxt_path = os.path.join(model_dir, "deploy.prototxt")
        model_path = os.path.join(model_dir, "res10_300x300_ssd_iter_140000.caffemodel")
        
        prototxt_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
        model_url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
        
        try:
            if not os.path.exists(prototxt_path):
                print("📥 Descargando modelo DNN (prototxt)...")
                urllib.request.urlretrieve(prototxt_url, prototxt_path)
            
            if not os.path.exists(model_path):
                print("📥 Descargando modelo DNN (caffemodel)...")
                urllib.request.urlretrieve(model_url, model_path)
            
            net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
            print("✅ Detector DNN cargado")
            return net
        except Exception as e:
            print(f"⚠️ Error al cargar DNN: {e}")
            return None
    
    def _detect_face_dnn(self, frame):
        """Detecta el rostro principal usando DNN (optimizado)"""
        if self.face_detector is None:
            return None
        
        h, w = frame.shape[:2]
        
        # Reducir resolución para detección rápida
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 
            1.0, 
            (300, 300), 
            (104.0, 177.0, 123.0)
        )
        
        self.face_detector.setInput(blob)
        detections = self.face_detector.forward()
        
        # Encontrar el rostro con mayor confianza
        best_face = None
        max_confidence = 0
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > self.confidence_threshold and confidence > max_confidence:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x1, y1, x2, y2) = box.astype("int")
                
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                
                if (x2 - x1) >= self.min_face_size and (y2 - y1) >= self.min_face_size:
                    best_face = (x1, y1, x2, y2, confidence)
                    max_confidence = confidence
        
        return best_face
    
    def _smooth_face_location(self, face):
        """Suaviza la ubicación del rostro usando un búfer"""
        if face is None:
            return None
        
        self.face_buffer.append(face[:4])
        
        if len(self.face_buffer) < 2:
            return face
        
        # Promediar las últimas detecciones
        avg_face = np.mean(self.face_buffer, axis=0).astype(int)
        return tuple(avg_face) + (face[4],)
    
    def _draw_face_box(self, frame, box, label="", color=(0, 255, 0)):
        """Dibuja un rectángulo elegante alrededor del rostro"""
        x1, y1, x2, y2 = box[:4]
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Esquinas decorativas
        corner_len = 20
        thick = 3
        
        # Superior izquierda
        cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color, thick)
        cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color, thick)
        
        # Superior derecha
        cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color, thick)
        cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color, thick)
        
        # Inferior izquierda
        cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color, thick)
        cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color, thick)
        
        # Inferior derecha
        cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color, thick)
        cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color, thick)
        
        if label:
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 15), 
                         (x1 + label_size[0] + 15, y1), color, -1)
            cv2.putText(frame, label, (x1 + 7, y1 - 7),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    def _detect_blink_transition(self, ear):
        """Detecta una transición completa de ojos: abierto -> cerrado -> abierto"""
        # Determinar estado actual
        current_state = "open" if ear >= self.EAR_THRESHOLD else "closed"
        self.eye_state_history.append(current_state)
        
        # Necesitamos al menos 7 estados para detectar una transición
        if len(self.eye_state_history) < 7:
            return False, "Inicializando..."
        
        # Buscar patrón: abierto -> cerrado -> abierto
        states = list(self.eye_state_history)
        
        # Contar estados consecutivos al final
        open_count_end = 0
        for state in reversed(states):
            if state == "open":
                open_count_end += 1
            else:
                break
        
        # Si hay al menos 2 frames abiertos al final
        if open_count_end >= 2:
            # Buscar si hubo un cierre antes
            closed_found = False
            open_found_before = False
            
            for i in range(len(states) - open_count_end - 1, -1, -1):
                if states[i] == "closed" and not closed_found:
                    closed_found = True
                elif states[i] == "open" and closed_found:
                    open_found_before = True
                    break
            
            if open_found_before and closed_found:
                return True, "Parpadeo completo detectado!"
        
        # Estados de progreso
        if current_state == "closed":
            return False, "Cerrando ojos..."
        elif open_count_end >= 1 and any(s == "closed" for s in states[:-open_count_end]):
            return False, "Abriendo ojos..."
        else:
            return False, "Esperando parpadeo..."
    
    def _detect_mouth_transition(self, mar):
        """Detecta una transición completa de boca: cerrada -> abierta -> cerrada (MÁS FLEXIBLE)"""
        # Determinar estado actual
        current_state = "open" if mar > self.MAR_THRESHOLD else "closed"
        self.mouth_state_history.append(current_state)
        
        # Necesitamos al menos 5 estados (reducido de 7 para ser más flexible)
        if len(self.mouth_state_history) < 5:
            return False, "Inicializando..."
        
        # Buscar patrón: cerrada -> abierta -> cerrada
        states = list(self.mouth_state_history)
        
        # Contar estados consecutivos al final
        closed_count_end = 0
        for state in reversed(states):
            if state == "closed":
                closed_count_end += 1
            else:
                break
        
        # Si hay al menos 1 frame cerrado al final (más flexible)
        if closed_count_end >= 1:
            # Buscar si hubo una apertura antes
            open_found = False
            closed_found_before = False
            
            for i in range(len(states) - closed_count_end - 1, -1, -1):
                if states[i] == "open" and not open_found:
                    open_found = True
                elif states[i] == "closed" and open_found:
                    closed_found_before = True
                    break
            
            if closed_found_before and open_found:
                return True, "Boca: transición completa!"
        
        # Estados de progreso
        if current_state == "open":
            return False, "Boca abierta, ahora cierra!"
        elif closed_count_end >= 1 and any(s == "open" for s in states[:-closed_count_end]):
            return False, "Cerrando boca..."
        else:
            return False, "Abre la boca ampliamente..."
    
    def _eye_aspect_ratio(self, eye):
        """Calcula el EAR (Eye Aspect Ratio) para detectar parpadeos"""
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)
    
    def _mouth_aspect_ratio(self, mouth):
        """Calcula el MAR (Mouth Aspect Ratio) para detectar boca abierta"""
        A = dist.euclidean(mouth[2], mouth[10])  # Vertical
        B = dist.euclidean(mouth[4], mouth[8])   # Vertical
        C = dist.euclidean(mouth[0], mouth[6])   # Horizontal
        return (A + B) / (2.0 * C)
    
        """Calcula el EAR (Eye Aspect Ratio) para detectar parpadeos"""
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])
        C = dist.euclidean(eye[0], eye[3])
        return (A + B) / (2.0 * C)
    
    def _mouth_aspect_ratio(self, mouth):
        """Calcula el MAR (Mouth Aspect Ratio) para detectar boca abierta"""
        A = dist.euclidean(mouth[2], mouth[10])  # Vertical
        B = dist.euclidean(mouth[4], mouth[8])   # Vertical
        C = dist.euclidean(mouth[0], mouth[6])   # Horizontal
        return (A + B) / (2.0 * C)
    
    def _detect_liveness_gesture(self, frame, draw_keypoints=False):
        """Detecta gestos de vivacidad: parpadeo o boca abierta"""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        landmarks = face_recognition.face_landmarks(rgb)
        
        if not landmarks:
            return None, 0.0, None
        
        # Obtener landmarks
        left_eye = landmarks[0]['left_eye']
        right_eye = landmarks[0]['right_eye']
        mouth = landmarks[0]['bottom_lip'] + landmarks[0]['top_lip']
        
        # Calcular ratios
        left_ear = self._eye_aspect_ratio(left_eye)
        right_ear = self._eye_aspect_ratio(right_eye)
        ear = (left_ear + right_ear) / 2.0
        
        mar = self._mouth_aspect_ratio(mouth)
        
        # Preparar datos de keypoints
        keypoints_data = {
            'left_eye': left_eye,
            'right_eye': right_eye,
            'mouth': mouth,
            'ear': ear,
            'mar': mar
        }
        
        # Determinar gesto
        if ear < self.EAR_THRESHOLD:
            return "blink", ear, keypoints_data
        elif mar > self.MAR_THRESHOLD:
            return "mouth", mar, keypoints_data
        
        return None, 0.0, keypoints_data
    
    def _draw_keypoints(self, frame, keypoints_data):
        """Dibuja los keypoints de ojos y boca con valores"""
        if not keypoints_data:
            return
        
        left_eye = keypoints_data['left_eye']
        right_eye = keypoints_data['right_eye']
        mouth = keypoints_data['mouth']
        ear = keypoints_data['ear']
        mar = keypoints_data['mar']
        
        # Color según si está cerrado/abierto
        eye_color = (0, 255, 0) if ear >= self.EAR_THRESHOLD else (0, 0, 255)
        mouth_color = (0, 255, 0) if mar >= self.MAR_THRESHOLD else (100, 100, 100)
        
        # Dibujar ojo izquierdo
        for point in left_eye:
            cv2.circle(frame, point, 2, eye_color, -1)
        # Contorno del ojo izquierdo
        for i in range(len(left_eye)):
            pt1 = left_eye[i]
            pt2 = left_eye[(i + 1) % len(left_eye)]
            cv2.line(frame, pt1, pt2, eye_color, 1)
        
        # Dibujar ojo derecho
        for point in right_eye:
            cv2.circle(frame, point, 2, eye_color, -1)
        # Contorno del ojo derecho
        for i in range(len(right_eye)):
            pt1 = right_eye[i]
            pt2 = right_eye[(i + 1) % len(right_eye)]
            cv2.line(frame, pt1, pt2, eye_color, 1)
        
        # Dibujar boca
        for point in mouth:
            cv2.circle(frame, point, 2, mouth_color, -1)
        # Contorno de la boca
        half = len(mouth) // 2
        for i in range(half - 1):
            cv2.line(frame, mouth[i], mouth[i + 1], mouth_color, 1)
        for i in range(half, len(mouth) - 1):
            cv2.line(frame, mouth[i], mouth[i + 1], mouth_color, 1)
        cv2.line(frame, mouth[0], mouth[half], mouth_color, 1)
        cv2.line(frame, mouth[half - 1], mouth[-1], mouth_color, 1)
        
        # Mostrar valores EAR y MAR con indicadores visuales
        ear_status = "CERRADOS" if ear < self.EAR_THRESHOLD else "ABIERTOS"
        mar_status = "ABIERTA" if mar > self.MAR_THRESHOLD else "CERRADA"
        
        cv2.putText(frame, f"Ojos: {ear:.3f} ({ear_status})", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, eye_color, 2)
        cv2.putText(frame, f"Boca: {mar:.3f} ({mar_status})", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, mouth_color, 2)
        
        # Indicador de umbral
        cv2.putText(frame, f"Umbral boca: >{self.MAR_THRESHOLD:.2f}", (10, 90),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    def capture_and_encode_face(self, username):
        """Captura la cara del usuario y guarda su encoding (OPTIMIZADO)"""
        print("\n📸 Capturando tu rostro para registro...")
        print("• Colócate frente a la cámara con buena iluminación")
        print("• Mantén el rostro dentro del recuadro verde")
        print("• Presiona 'ESPACIO' cuando el sistema esté listo")
        print("• Presiona 'q' para cancelar\n")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ No se pudo acceder a la cámara")
            return None
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Resolución reducida para fluidez
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        encoding = None
        frame_count = 0
        stable_frames = 0
        required_stable = 10
        last_face = None
        
        print("⏳ Iniciando cámara...\n")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            display = frame.copy()
            h, w = display.shape[:2]
            
            # Detectar rostro cada 3 frames (optimización)
            if frame_count % 3 == 0:
                face = self._detect_face_dnn(frame)
                if face:
                    last_face = self._smooth_face_location(face)
            
            # Usar última detección válida
            if last_face:
                x1, y1, x2, y2, conf = last_face
                face_area = (x2 - x1) * (y2 - y1)
                
                if face_area > (self.min_face_size ** 2):
                    stable_frames += 1
                else:
                    stable_frames = max(0, stable_frames - 2)
                
                # Color según estabilidad
                if stable_frames >= required_stable:
                    color = (0, 255, 0)
                    label = f"LISTO! Presiona ESPACIO"
                else:
                    color = (0, 165, 255)
                    label = f"Estabilizando... {stable_frames}/{required_stable}"
                
                self._draw_face_box(display, (x1, y1, x2, y2), label, color)
                
                # Barra de estabilidad
                bar_w = int((stable_frames / required_stable) * 400)
                cv2.rectangle(display, (10, h - 40), (410, h - 20), (50, 50, 50), -1)
                cv2.rectangle(display, (10, h - 40), (10 + bar_w, h - 20), (0, 255, 0), -1)
            else:
                stable_frames = 0
                cv2.putText(display, "Coloca tu rostro frente a la camara", 
                           (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            
            cv2.imshow('Registro Facial', display)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' ') and stable_frames >= required_stable:
                print("⏳ Procesando captura...")
                
                # Mostrar mensaje de procesamiento
                process = display.copy()
                cv2.putText(process, "PROCESANDO...", (w//2 - 120, h//2),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
                cv2.imshow('Registro Facial', process)
                cv2.waitKey(100)
                
                # Codificar rostro
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                locations = face_recognition.face_locations(rgb, model="hog")
                
                if locations:
                    encodings = face_recognition.face_encodings(rgb, locations)
                    if encodings:
                        encoding = encodings[0]
                        
                        # Mostrar éxito con animación
                        success = display.copy()
                        overlay = success.copy()
                        
                        # Fondo semitransparente verde
                        cv2.rectangle(overlay, (0, 0), (w, h), (0, 255, 0), -1)
                        cv2.addWeighted(overlay, 0.3, success, 0.7, 0, success)
                        
                        # Mensaje
                        cv2.putText(success, "ROSTRO", (w//2 - 100, h//2 - 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4)
                        cv2.putText(success, "CAPTURADO!", (w//2 - 150, h//2 + 30),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4)
                        
                        # Icono check
                        center_x, center_y = w//2, h//2 + 90
                        cv2.circle(success, (center_x, center_y), 30, (255, 255, 255), 3)
                        cv2.line(success, (center_x - 10, center_y), 
                                (center_x - 3, center_y + 10), (255, 255, 255), 3)
                        cv2.line(success, (center_x - 3, center_y + 10), 
                                (center_x + 15, center_y - 10), (255, 255, 255), 3)
                        
                        cv2.imshow('Registro Facial', success)
                        cv2.waitKey(1500)
                        
                        print("✅ Rostro capturado correctamente")
                        break
                
                print("⚠️ No se pudo codificar, intenta de nuevo")
                stable_frames = 0
            
            elif key == ord('q'):
                print("❌ Captura cancelada")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)
        
        return encoding
    
    def verify_with_liveness(self, username, stored_encoding):
        """Verifica identidad con detección de vivacidad por TRANSICIONES (MEJORADO)"""
        print("\n🔍 Verificación facial con detección de vivacidad")
        print("\nInstrucciones:")
        print("1. Mira a la cámara y espera a que se reconozca tu rostro")
        print("2. Cuando se te indique, DEBES realizar AMBAS transiciones:")
        print("   👁️  PARPADEAR: Ojos abiertos → cerrados → abiertos")
        print("   👄  BOCA: Cerrada → abierta → cerrada")
        print("\n🚨 IMPORTANTE: Se detectan MOVIMIENTOS, no estados estáticos")
        print("Presiona 'q' para cancelar\n")
        
        input("Presiona ENTER para comenzar...")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ No se pudo acceder a la cámara")
            return False
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Estados de verificación
        identity_verified = False
        blink_transition_detected = False
        mouth_transition_detected = False
        
        frames_verified = 0
        required_verified = 10
        
        last_face = None
        frame_count = 0
        timeout_frames = 0
        max_timeout = 900  # 30 segundos de timeout
        
        # Reiniciar historiales
        self.eye_state_history.clear()
        self.mouth_state_history.clear()
        
        blink_status_msg = "Esperando..."
        mouth_status_msg = "Esperando..."
        
        print("⏳ Iniciando verificación...\n")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            timeout_frames += 1
            display = frame.copy()
            h, w = display.shape[:2]
            
            # Timeout de seguridad
            if timeout_frames > max_timeout:
                print("⏱️ Tiempo de verificación agotado")
                break
            
            # Detectar rostro cada 3 frames
            if frame_count % 3 == 0:
                face = self._detect_face_dnn(frame)
                if face:
                    last_face = self._smooth_face_location(face)
            
            # Verificar identidad si hay rostro detectado
            if last_face and frame_count % 5 == 0:
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                locations = face_recognition.face_locations(rgb, model="hog")
                
                if locations:
                    encodings = face_recognition.face_encodings(rgb, locations)
                    
                    if encodings:
                        matches = face_recognition.compare_faces(
                            [stored_encoding], encodings[0], tolerance=self.tolerance
                        )
                        distance = face_recognition.face_distance(
                            [stored_encoding], encodings[0]
                        )[0]
                        
                        if matches[0] and distance < self.tolerance:
                            identity_verified = True
                            frames_verified += 1
                        else:
                            identity_verified = False
                            frames_verified = 0
            
            # Dibujar rostro y estado
            if last_face:
                x1, y1, x2, y2, conf = last_face
                
                if identity_verified and frames_verified >= required_verified:
                    # Identidad confirmada, detectar transiciones
                    if not (blink_transition_detected and mouth_transition_detected):
                        # Detectar gestos en cada frame
                        gesture, value, keypoints = self._detect_liveness_gesture(frame)
                        
                        # Dibujar keypoints siempre que haya datos
                        if keypoints:
                            self._draw_keypoints(display, keypoints)
                            
                            ear = keypoints['ear']
                            mar = keypoints['mar']
                            
                            # Detectar transición de parpadeo
                            if not blink_transition_detected:
                                blink_complete, blink_status_msg = self._detect_blink_transition(ear)
                                if blink_complete:
                                    blink_transition_detected = True
                                    print("✅ Parpadeo completo detectado")
                                    self.eye_state_history.clear()  # Limpiar para evitar re-detección
                            
                            # Detectar transición de boca
                            if not mouth_transition_detected:
                                mouth_complete, mouth_status_msg = self._detect_mouth_transition(mar)
                                if mouth_complete:
                                    mouth_transition_detected = True
                                    print("✅ Apertura/cierre de boca completo detectado")
                                    self.mouth_state_history.clear()  # Limpiar para evitar re-detección
                        
                        # Determinar mensaje principal
                        if not blink_transition_detected and not mouth_transition_detected:
                            color = (0, 165, 255)
                            label = "Realiza ambos gestos"
                        elif blink_transition_detected and not mouth_transition_detected:
                            color = (0, 255, 255)
                            label = "Ahora: Abre y cierra la BOCA"
                        elif not blink_transition_detected and mouth_transition_detected:
                            color = (0, 255, 255)
                            label = "Ahora: PARPADEA"
                        
                        # Mostrar checklist con estados
                        check_y = y1 - 110
                        
                        # Estado del parpadeo
                        blink_icon = "✓" if blink_transition_detected else "⟳"
                        blink_color = (0, 255, 0) if blink_transition_detected else (0, 165, 255)
                        cv2.putText(display, f"{blink_icon} Parpadeo: {blink_status_msg}", (x1, check_y),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, blink_color, 2)
                        
                        # Estado de la boca
                        mouth_icon = "✓" if mouth_transition_detected else "⟳"
                        mouth_color = (0, 255, 0) if mouth_transition_detected else (0, 165, 255)
                        cv2.putText(display, f"{mouth_icon} Boca: {mouth_status_msg}", (x1, check_y + 25),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, mouth_color, 2)
                        
                    else:
                        color = (0, 255, 0)
                        label = "VERIFICACION EXITOSA!"
                    
                    self._draw_face_box(display, (x1, y1, x2, y2), label, color)
                    
                    # Terminar si ambas transiciones fueron detectadas
                    if blink_transition_detected and mouth_transition_detected:
                        # Crear pantalla de éxito animada
                        success_frame = display.copy()
                        overlay = success_frame.copy()
                        
                        # Fondo semitransparente verde
                        cv2.rectangle(overlay, (0, 0), (w, h), (0, 255, 0), -1)
                        cv2.addWeighted(overlay, 0.3, success_frame, 0.7, 0, success_frame)
                        
                        # Mensaje principal
                        cv2.putText(success_frame, "AUTENTICACION", 
                                   (w//2 - 200, h//2 - 60),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 4)
                        cv2.putText(success_frame, "EXITOSA!", 
                                   (w//2 - 120, h//2 + 20),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1.8, (255, 255, 255), 5)
                        
                        # Icono de check
                        center_x, center_y = w//2, h//2 + 100
                        cv2.circle(success_frame, (center_x, center_y), 40, (255, 255, 255), 4)
                        cv2.line(success_frame, (center_x - 15, center_y), 
                                (center_x - 5, center_y + 15), (255, 255, 255), 4)
                        cv2.line(success_frame, (center_x - 5, center_y + 15), 
                                (center_x + 20, center_y - 15), (255, 255, 255), 4)
                        
                        cv2.imshow('Verificacion Facial', success_frame)
                        cv2.waitKey(2500)
                        break
                    
                elif identity_verified:
                    color = (0, 165, 255)
                    label = f"Verificando identidad... {frames_verified}/{required_verified}"
                    self._draw_face_box(display, (x1, y1, x2, y2), label, color)
                else:
                    color = (0, 0, 255)
                    label = "Rostro no reconocido"
                    self._draw_face_box(display, (x1, y1, x2, y2), label, color)
                    frames_verified = 0
            else:
                cv2.putText(display, "Coloca tu rostro frente a la camara", 
                           (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                frames_verified = 0
            
            # Barra de progreso mejorada
            if identity_verified and frames_verified >= required_verified:
                progress = 33
                if blink_transition_detected:
                    progress += 33
                if mouth_transition_detected:
                    progress += 34
            else:
                progress = min((frames_verified / required_verified) * 33, 33)
            
            bar_w = int((progress / 100) * 600)
            cv2.rectangle(display, (10, h - 40), (610, h - 20), (50, 50, 50), -1)
            cv2.rectangle(display, (10, h - 40), (10 + bar_w, h - 20), (0, 255, 0), -1)
            cv2.putText(display, f"Progreso: {int(progress)}%", (620, h - 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            cv2.imshow('Verificacion Facial', display)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("❌ Verificación cancelada")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)
        
        success = identity_verified and blink_transition_detected and mouth_transition_detected
        
        if success:
            print("\n" + "="*60)
            print("✅ VERIFICACIÓN EXITOSA")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("❌ VERIFICACIÓN FALLIDA")
            if not identity_verified:
                print("   Motivo: Identidad no confirmada")
            elif not blink_transition_detected:
                print("   Motivo: No se detectó transición de parpadeo completa")
            elif not mouth_transition_detected:
                print("   Motivo: No se detectó transición de boca completa")
            print("="*60)
        
        return success