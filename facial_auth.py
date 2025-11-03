# Autenticación facial con detección de vivacidad

import cv2
import face_recognition
import numpy as np
from config import Config
import os
import urllib.request
import time

class FacialAuth:
    """Autenticación facial con detección de vivacidad usando DNN"""
    
    def __init__(self):
        self.tolerance = Config.FACE_RECOGNITION_TOLERANCE
        self.movement_threshold = Config.FACE_MOVEMENT_THRESHOLD
        self.center_threshold = Config.FACE_CENTER_THRESHOLD
        
        # Cargar el detector DNN de OpenCV (mucho mejor que Haar Cascades)
        self.face_detector = self._load_dnn_detector()
        
        # Parámetros de detección
        self.confidence_threshold = 0.5
        self.min_face_size = 80  # Tamaño mínimo del rostro en píxeles
    
    def _load_dnn_detector(self):
        """Carga el detector DNN de rostros de OpenCV"""
        model_dir = "models"
        os.makedirs(model_dir, exist_ok=True)
        
        # Archivos del modelo
        prototxt_path = os.path.join(model_dir, "deploy.prototxt")
        model_path = os.path.join(model_dir, "res10_300x300_ssd_iter_140000.caffemodel")
        
        # URLs de descarga
        prototxt_url = "https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt"
        model_url = "https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel"
        
        # Descargar archivos si no existen
        try:
            if not os.path.exists(prototxt_path):
                print("📥 Descargando modelo DNN (prototxt)...")
                urllib.request.urlretrieve(prototxt_url, prototxt_path)
                print("✅ Prototxt descargado")
            
            if not os.path.exists(model_path):
                print("📥 Descargando modelo DNN (caffemodel) - esto puede tardar...")
                urllib.request.urlretrieve(model_url, model_path)
                print("✅ Modelo descargado")
            
            # Cargar el modelo
            net = cv2.dnn.readNetFromCaffe(prototxt_path, model_path)
            print("✅ Detector DNN cargado correctamente")
            return net
        except Exception as e:
            print(f"⚠️  Error al cargar DNN: {e}")
            print("   Se usará detección básica de face_recognition")
            return None
    
    def _detect_faces_dnn(self, frame):
        """Detecta rostros usando DNN (más preciso que Haar Cascades)"""
        if self.face_detector is None:
            return []
        
        h, w = frame.shape[:2]
        
        # Preparar la imagen para DNN
        blob = cv2.dnn.blobFromImage(
            cv2.resize(frame, (300, 300)), 
            1.0, 
            (300, 300), 
            (104.0, 177.0, 123.0)
        )
        
        self.face_detector.setInput(blob)
        detections = self.face_detector.forward()
        
        faces = []
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > self.confidence_threshold:
                box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                (x1, y1, x2, y2) = box.astype("int")
                
                # Asegurar que las coordenadas estén dentro de la imagen
                x1 = max(0, x1)
                y1 = max(0, y1)
                x2 = min(w, x2)
                y2 = min(h, y2)
                
                # Filtrar rostros muy pequeños
                if (x2 - x1) >= self.min_face_size and (y2 - y1) >= self.min_face_size:
                    faces.append((x1, y1, x2, y2, confidence))
        
        return faces
    
    def _draw_face_box(self, frame, box, label="", color=(0, 255, 0)):
        """Dibuja un rectángulo mejorado alrededor del rostro"""
        x1, y1, x2, y2 = box[:4]
        
        # Rectángulo principal
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        # Esquinas decorativas
        corner_length = 20
        thickness = 3
        
        # Esquina superior izquierda
        cv2.line(frame, (x1, y1), (x1 + corner_length, y1), color, thickness)
        cv2.line(frame, (x1, y1), (x1, y1 + corner_length), color, thickness)
        
        # Esquina superior derecha
        cv2.line(frame, (x2, y1), (x2 - corner_length, y1), color, thickness)
        cv2.line(frame, (x2, y1), (x2, y1 + corner_length), color, thickness)
        
        # Esquina inferior izquierda
        cv2.line(frame, (x1, y2), (x1 + corner_length, y2), color, thickness)
        cv2.line(frame, (x1, y2), (x1, y2 - corner_length), color, thickness)
        
        # Esquina inferior derecha
        cv2.line(frame, (x2, y2), (x2 - corner_length, y2), color, thickness)
        cv2.line(frame, (x2, y2), (x2, y2 - corner_length), color, thickness)
        
        # Etiqueta
        if label:
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0] + 10, y1), color, -1)
            cv2.putText(frame, label, (x1 + 5, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    def capture_and_encode_face(self, username):
        """Captura la cara del usuario y guarda su encoding"""
        print("\n📸 Capturando tu rostro para registro...")
        print("Instrucciones:")
        print("• Colócate frente a la cámara con buena iluminación")
        print("• Mira directamente a la cámara")
        print("• Mantén el rostro dentro del recuadro verde")
        print("• Presiona 'ESPACIO' para capturar")
        print("• Presiona 'q' para cancelar")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ No se pudo acceder a la cámara")
            return None
        
        # Mejorar calidad de captura
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        encoding = None
        frame_count = 0
        stable_frames = 0
        required_stable_frames = 15
        
        # CORRECCIÓN: Mantener la última detección para evitar parpadeo
        last_faces = []
        
        print("\n⏳ Iniciando cámara...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("❌ Error al leer de la cámara")
                break
            
            frame_count += 1
            display_frame = frame.copy()
            h, w = frame.shape[:2]
            
            # Detectar caras cada 3 frames (optimización)
            # CORRECCIÓN: Mantener last_faces para evitar parpadeo
            if frame_count % 3 == 0:
                faces_dnn = self._detect_faces_dnn(frame)
                if faces_dnn:
                    last_faces = faces_dnn
            
            # Usar la última detección válida
            if last_faces:
                # Tomar el rostro más grande (más cercano)
                largest_face = max(last_faces, key=lambda f: (f[2]-f[0]) * (f[3]-f[1]))
                x1, y1, x2, y2, conf = largest_face
                
                # Verificar estabilidad del rostro
                face_area = (x2 - x1) * (y2 - y1)
                if face_area > (self.min_face_size ** 2):
                    stable_frames += 1
                else:
                    stable_frames = max(0, stable_frames - 1)
                
                # Color según estabilidad
                if stable_frames >= required_stable_frames:
                    color = (0, 255, 0)  # Verde: listo para capturar
                    label = f"LISTO - Presiona ESPACIO ({conf:.2f})"
                else:
                    color = (0, 165, 255)  # Naranja: esperando estabilidad
                    label = f"Estabilizando {stable_frames}/{required_stable_frames}"
                
                self._draw_face_box(display_frame, (x1, y1, x2, y2), label, color)
            else:
                stable_frames = 0
                cv2.putText(display_frame, "No se detecta rostro", (10, 40),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # Indicador de estabilidad
            stability_bar_width = int((stable_frames / required_stable_frames) * 400)
            cv2.rectangle(display_frame, (10, h - 40), 
                         (410, h - 20), (50, 50, 50), -1)
            cv2.rectangle(display_frame, (10, h - 40), 
                         (10 + stability_bar_width, h - 20), (0, 255, 0), -1)
            
            cv2.imshow('Registro Facial', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(' ') and stable_frames >= required_stable_frames:
                print("\n⏳ Procesando captura...")
                
                # CORRECCIÓN: Mostrar mensaje de procesamiento
                process_frame = display_frame.copy()
                cv2.putText(process_frame, "PROCESANDO...", (w//2 - 150, h//2),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)
                cv2.imshow('Registro Facial', process_frame)
                cv2.waitKey(1)  # Actualizar ventana
                
                # Convertir a RGB para face_recognition
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")
                
                if face_locations:
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    if face_encodings:
                        encoding = face_encodings[0]
                        
                        # CORRECCIÓN: Mostrar éxito en la ventana
                        success_frame = display_frame.copy()
                        cv2.putText(success_frame, "EXITO!", (w//2 - 100, h//2),
                                   cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
                        cv2.imshow('Registro Facial', success_frame)
                        cv2.waitKey(1000)  # Mostrar durante 1 segundo
                        
                        print("✅ Rostro capturado y codificado correctamente")
                        break
                    else:
                        print("⚠️  No se pudo codificar el rostro, intenta de nuevo")
                        stable_frames = 0
                else:
                    print("⚠️  No se detectó rostro para codificar, intenta de nuevo")
                    stable_frames = 0
            
            elif key == ord('q'):
                print("❌ Captura cancelada")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        # CORRECCIÓN: Asegurar que todas las ventanas se cierren
        cv2.waitKey(1)
        
        return encoding
    
    def verify_with_liveness(self, username, stored_encoding):
        """Verifica la identidad con detección de vivacidad mejorada"""
        print("\n🔍 Verificación facial con detección de vivacidad")
        print("\nInstrucciones:")
        print("1. Mira a la cámara (CENTRO)")
        print("2. Gira tu cabeza LENTAMENTE a la IZQUIERDA")
        print("3. Luego gira LENTAMENTE a la DERECHA")
        print("4. Vuelve al CENTRO")
        print("\n⚠️  Los movimientos deben ser lentos y suaves")
        print("Presiona 'q' para cancelar en cualquier momento\n")
        
        input("Presiona ENTER para comenzar...")
        
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ No se pudo acceder a la cámara")
            return False
        
        # Mejorar calidad de captura
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        stages = {
            'center_initial': False,
            'left': False,
            'right': False,
            'center_final': False
        }
        
        stage_order = ['center_initial', 'left', 'right', 'center_final']
        stage_names = {
            'center_initial': 'CENTRO',
            'left': 'IZQUIERDA',
            'right': 'DERECHA',
            'center_final': 'CENTRO FINAL'
        }
        
        current_stage_idx = 0
        current_stage = stage_order[current_stage_idx]
        face_verified = False
        identity_confirmed = False
        positions = []
        frame_count = 0
        frames_in_position = 0
        required_frames = 10
        
        # CORRECCIÓN: Mantener última detección válida
        last_face_location = None
        
        print("⏳ Iniciando verificación...\n")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_count += 1
            display_frame = frame.copy()
            h, w = frame.shape[:2]
            
            # Procesar cada 2 frames para mejor rendimiento
            if frame_count % 2 == 0:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame, model="hog")
                
                if face_locations:
                    last_face_location = face_locations[0]
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    
                    if face_encodings:
                        # Verificar identidad
                        matches = face_recognition.compare_faces(
                            [stored_encoding], face_encodings[0], tolerance=self.tolerance
                        )
                        face_distance = face_recognition.face_distance(
                            [stored_encoding], face_encodings[0]
                        )
                        
                        if matches[0] and face_distance[0] < self.tolerance:
                            identity_confirmed = True
                            face_verified = True
                            
                            # Calcular posición del rostro
                            top, right, bottom, left = face_locations[0]
                            face_center_x = (left + right) // 2
                            frame_center_x = w // 2
                            offset = face_center_x - frame_center_x
                            
                            positions.append(offset)
                            if len(positions) > 15:
                                positions.pop(0)
                            
                            avg_offset = np.mean(positions) if positions else 0
                            
                            # Determinar si está en la posición correcta
                            in_correct_position = False
                            
                            if current_stage == 'center_initial' and abs(avg_offset) < self.center_threshold:
                                in_correct_position = True
                            elif current_stage == 'left' and avg_offset < -self.movement_threshold:
                                in_correct_position = True
                            elif current_stage == 'right' and avg_offset > self.movement_threshold:
                                in_correct_position = True
                            elif current_stage == 'center_final' and abs(avg_offset) < self.center_threshold:
                                in_correct_position = True
                            
                            # Contar frames en posición
                            if in_correct_position:
                                frames_in_position += 1
                            else:
                                frames_in_position = 0
                            
                            # Avanzar a siguiente etapa
                            if frames_in_position >= required_frames:
                                stages[current_stage] = True
                                print(f"✓ {stage_names[current_stage]} completado")
                                
                                current_stage_idx += 1
                                if current_stage_idx >= len(stage_order):
                                    print("✅ ¡Verificación de vivacidad completada!")
                                    
                                    # Mostrar éxito en pantalla
                                    success_frame = display_frame.copy()
                                    cv2.putText(success_frame, "VERIFICACION EXITOSA!", 
                                               (w//2 - 250, h//2),
                                               cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 4)
                                    cv2.imshow('Verificacion Facial - Deteccion de Vivacidad', success_frame)
                                    cv2.waitKey(2000)  # Mostrar 2 segundos
                                    break
                                
                                current_stage = stage_order[current_stage_idx]
                                frames_in_position = 0
                                print(f"→ Mueve tu cabeza a: {stage_names[current_stage]}")
                        else:
                            face_verified = False
                            identity_confirmed = False
                            frames_in_position = 0
            
            # Dibujar usando última posición válida conocida
            if last_face_location and identity_confirmed:
                top, right, bottom, left = last_face_location
                face_center_x = (left + right) // 2
                frame_center_x = w // 2
                offset = face_center_x - frame_center_x
                
                if len(positions) > 0:
                    avg_offset = np.mean(positions)
                else:
                    avg_offset = offset
                
                # Determinar color
                in_correct_position = False
                if current_stage == 'center_initial' and abs(avg_offset) < self.center_threshold:
                    in_correct_position = True
                elif current_stage == 'left' and avg_offset < -self.movement_threshold:
                    in_correct_position = True
                elif current_stage == 'right' and avg_offset > self.movement_threshold:
                    in_correct_position = True
                elif current_stage == 'center_final' and abs(avg_offset) < self.center_threshold:
                    in_correct_position = True
                
                color = (0, 255, 0) if in_correct_position else (0, 165, 255)
                self._draw_face_box(display_frame, 
                                  (left, top, right, bottom), 
                                  f"{stage_names[current_stage]} ({frames_in_position}/{required_frames})",
                                  color)
                
                # Indicador de offset
                cv2.circle(display_frame, (frame_center_x, 30), 5, (255, 255, 255), -1)
                offset_x = frame_center_x + int(avg_offset)
                cv2.circle(display_frame, (offset_x, 30), 8, color, -1)
                cv2.line(display_frame, (frame_center_x, 30), (offset_x, 30), color, 2)
            elif last_face_location and not identity_confirmed:
                cv2.putText(display_frame, "ROSTRO NO RECONOCIDO", (10, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
            else:
                cv2.putText(display_frame, "No se detecta rostro", (10, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                frames_in_position = 0
            
            # Barra de progreso
            progress = sum(stages.values()) / len(stages)
            bar_width = int(progress * 600)
            cv2.rectangle(display_frame, (10, h - 50), (610, h - 20), (50, 50, 50), -1)
            cv2.rectangle(display_frame, (10, h - 50), (10 + bar_width, h - 20), (0, 255, 0), -1)
            cv2.putText(display_frame, f"Progreso: {int(progress * 100)}%", (620, h - 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow('Verificacion Facial - Deteccion de Vivacidad', display_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("❌ Verificación cancelada")
                break
        
        cap.release()
        cv2.destroyAllWindows()
        cv2.waitKey(1)  # Asegurar cierre
        
        success = all(stages.values()) and face_verified and identity_confirmed
        
        if success:
            print("\n" + "="*60)
            print("✅ VERIFICACIÓN EXITOSA")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("❌ VERIFICACIÓN FALLIDA")
            if not identity_confirmed:
                print("   Motivo: Identidad no confirmada")
            elif not all(stages.values()):
                print("   Motivo: No se completaron todas las etapas de vivacidad")
            print("="*60)
        
        return success