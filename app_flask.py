"""
Sistema 2FA Biométrico - Aplicación Flask con Socket.IO
Streaming de video en tiempo real para verificación facial sin lag
"""

from flask import Flask, render_template, request, session, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import face_recognition
from database import DatabaseManager
from facial_auth import FacialAuth
from voice_auth import VoiceAuthChallenge
from config import Config
import secrets

app = Flask(__name__)
SECRET_KEY = secrets.token_hex(32)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=True)

# Inicializar servicios
db = DatabaseManager()
facial_auth = FacialAuth()
voice_auth = VoiceAuthChallenge()

# Variables globales para el proceso de verificación facial
verification_state = {}

@app.route('/')
def index():
    """Página principal - redirige según autenticación"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if db.verify_password(username, password):
            # Limpiar sesión previa
            session.clear()
            # Establecer nueva sesión
            session['username'] = username
            session['password_verified'] = True
            return redirect(url_for('verify_2fa'))
        else:
            return render_template('login.html', error="Usuario o contraseña incorrectos")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            return render_template('register.html', error="Las contraseñas no coinciden")

        if len(password) < 6:
            return render_template('register.html', error="La contraseña debe tener al menos 6 caracteres")

        if db.user_exists(username):
            return render_template('register.html', error="El usuario ya existe")

        if db.create_user(username, password):
            session['username'] = username
            session['registering'] = True
            return redirect(url_for('setup_biometrics'))
        else:
            return render_template('register.html', error="Error al crear usuario")

    return render_template('register.html')

@app.route('/setup_biometrics')
def setup_biometrics():
    """Configuración de métodos biométricos (registro o después de autenticado)"""
    if 'username' not in session:
        return redirect(url_for('login'))

    # Permitir acceso si está registrando O si ya está autenticado
    if not session.get('registering') and not session.get('authenticated'):
        return redirect(url_for('login'))

    username = session['username']
    has_facial = db.get_face_encoding(username) is not None
    has_voice = db.get_voice_sample(username) is not None

    return render_template('setup_biometrics.html',
                         username=username,
                         has_facial=has_facial,
                         has_voice=has_voice,
                         is_authenticated=session.get('authenticated', False))

@app.route('/verify_2fa')
def verify_2fa():
    """Página de verificación 2FA"""
    if 'username' not in session or not session.get('password_verified'):
        return redirect(url_for('login'))

    username = session['username']
    has_facial = db.get_face_encoding(username) is not None
    has_voice = db.get_voice_sample(username) is not None

    if not has_facial and not has_voice:
        return redirect(url_for('setup_biometrics'))

    return render_template('verify_2fa.html',
                         username=username,
                         has_facial=has_facial,
                         has_voice=has_voice)

@app.route('/facial_verification')
def facial_verification():
    """Página de verificación facial con streaming de video"""
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    stored_encoding = db.get_face_encoding(username)

    if stored_encoding is None:
        return redirect(url_for('verify_2fa'))

    # Inicializar estado de verificación
    verification_state[username] = {
        'identity_verified': False,
        'frames_verified': 0,
        'blink_detected': False,
        'mouth_detected': False,
        'stored_encoding': stored_encoding
    }

    return render_template('facial_verification.html', username=username)

@app.route('/facial_registration')
def facial_registration():
    """Página de registro facial"""
    if 'username' not in session:
        return redirect(url_for('login'))

    return render_template('facial_registration.html', username=session['username'])

@app.route('/voice_verification')
def voice_verification():
    """Página de verificación de voz"""
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    stored_sample = db.get_voice_sample(username)

    if stored_sample is None:
        return redirect(url_for('verify_2fa'))

    # Generar frase de desafío
    challenge_phrase = voice_auth.generate_challenge()

    return render_template('voice_verification.html',
                         username=username,
                         challenge_phrase=challenge_phrase)

@app.route('/voice_registration')
def voice_registration():
    """Página de registro de voz"""
    if 'username' not in session:
        return redirect(url_for('login'))

    # Generar frase de desafío
    challenge_phrase = voice_auth.generate_challenge()

    return render_template('voice_registration.html',
                         username=session['username'],
                         challenge_phrase=challenge_phrase)

@app.route('/verify_token')
def verify_token():
    """Verifica el token temporal y establece la sesión HTTP"""
    token = request.args.get('token')

    if not token:
        print("❌ No token provided")
        return redirect(url_for('login'))

    # Verificar token
    if not hasattr(app, 'auth_tokens') or token not in app.auth_tokens:
        print(f"❌ Invalid token: {token[:8] if token else 'None'}...")
        return redirect(url_for('login'))

    username = app.auth_tokens[token]

    # Establecer sesión HTTP
    session.clear()
    session['username'] = username
    session['authenticated'] = True
    session.permanent = True

    # Eliminar token (un solo uso)
    del app.auth_tokens[token]

    print(f"✓ Token verified for {username}, session established")
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Dashboard del usuario autenticado"""
    print(f"Dashboard access attempt - username: {session.get('username')}, authenticated: {session.get('authenticated')}")

    if 'username' not in session or not session.get('authenticated'):
        print("❌ Dashboard access denied - redirecting to login")
        return redirect(url_for('login'))

    username = session['username']
    has_facial = db.get_face_encoding(username) is not None
    has_voice = db.get_voice_sample(username) is not None

    print(f"✓ Dashboard access granted for {username}")
    return render_template('dashboard.html',
                         username=username,
                         has_facial=has_facial,
                         has_voice=has_voice)

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    return redirect(url_for('login'))

# ============================================================================
# Socket.IO Events - Streaming de video en tiempo real
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Cliente conectado"""
    print(f"Cliente conectado: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    print(f"Cliente desconectado: {request.sid}")

@socketio.on('video_frame')
def handle_video_frame(data):
    """
    Procesa frame de video para verificación facial en tiempo real
    """
    try:
        if 'username' not in session:
            emit('verification_error', {'error': 'No autenticado'})
            return

        username = session['username']

        if username not in verification_state:
            emit('verification_error', {'error': 'Estado de verificación no inicializado'})
            return

        state = verification_state[username]

        # Decodificar imagen desde base64
        img_data = base64.b64decode(data['image'].split(',')[1])
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return

        # Procesar frame con facial_auth
        result = facial_auth.process_verification_frame(
            frame,
            state['stored_encoding'],
            state
        )

        # Enviar resultado al cliente
        emit('verification_update', result)

        # Si la verificación es exitosa, generar token temporal y marcar como autenticado
        if result.get('success'):
            print(f"✓ Verificación exitosa para {username}")

            # Generar token temporal
            import uuid
            temp_token = str(uuid.uuid4())

            # Guardar token en variable global (podrías usar Redis en producción)
            if not hasattr(app, 'auth_tokens'):
                app.auth_tokens = {}
            app.auth_tokens[temp_token] = username

            db.log_login_attempt(username, True, "facial")
            db.update_last_login(username)

            print(f"✓ Token generado para {username}: {temp_token[:8]}...")
            emit('verification_complete', {
                'success': True,
                'redirect': url_for('verify_token', token=temp_token)
            })

            # Limpiar estado
            if username in verification_state:
                del verification_state[username]

    except Exception as e:
        print(f"Error procesando frame: {e}")
        import traceback
        traceback.print_exc()
        emit('verification_error', {'error': str(e)})

@socketio.on('register_frame')
def handle_register_frame(data):
    """
    Procesa frame de video para registro facial
    """
    try:
        if 'username' not in session:
            emit('registration_error', {'error': 'No autenticado'})
            return

        username = session['username']

        # Decodificar imagen desde base64
        img_data = base64.b64decode(data['image'].split(',')[1])
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return

        # Detectar rostro
        face = facial_auth._detect_face_dnn(frame)

        if face:
            x1, y1, x2, y2, conf = face
            face_data = {
                'detected': True,
                'confidence': float(conf),
                'box': {'x1': int(x1), 'y1': int(y1), 'x2': int(x2), 'y2': int(y2)},
                'ready': conf > 0.7
            }
            emit('face_detected', face_data)
        else:
            emit('face_detected', {'detected': False})

    except Exception as e:
        print(f"Error en registro: {e}")
        emit('registration_error', {'error': str(e)})

@socketio.on('capture_face')
def handle_capture_face(data):
    """
    Captura y guarda el encoding facial
    """
    try:
        if 'username' not in session:
            emit('registration_error', {'error': 'No autenticado'})
            return

        username = session['username']

        # Decodificar imagen desde base64
        img_data = base64.b64decode(data['image'].split(',')[1])
        nparr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            emit('registration_error', {'error': 'Error al decodificar imagen'})
            return

        # Extraer encoding
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb, model="hog")

        if locations:
            import face_recognition
            encodings = face_recognition.face_encodings(rgb, locations)

            if encodings:
                encoding = encodings[0]
                db.save_face_encoding(username, encoding)

                # Limpiar flag de registro si está registrándose
                if session.get('registering'):
                    session.pop('registering', None)

                emit('registration_complete', {'success': True})
            else:
                emit('registration_error', {'error': 'No se pudo codificar el rostro'})
        else:
            emit('registration_error', {'error': 'No se detectó rostro'})

    except Exception as e:
        print(f"Error capturando rostro: {e}")
        emit('registration_error', {'error': str(e)})

@socketio.on('request_challenge')
def handle_request_challenge():
    """
    Genera una nueva frase de desafío para verificación de voz
    """
    try:
        challenge_phrase = voice_auth.generate_challenge()
        emit('new_challenge', {'challenge': challenge_phrase})
    except Exception as e:
        print(f"Error generando desafío: {e}")
        emit('voice_error', {'error': str(e)})

@socketio.on('verify_voice')
def handle_verify_voice(data):
    """
    Verifica la voz del usuario con desafío aleatorio
    """
    try:
        if 'username' not in session:
            emit('voice_error', {'error': 'No autenticado'})
            return

        username = session['username']
        stored_sample = db.get_voice_sample(username)

        if stored_sample is None:
            emit('voice_error', {'error': 'No hay muestra de voz registrada'})
            return

        # Decodificar audio desde base64
        import base64
        audio_data = base64.b64decode(data['audio'].split(',')[1])

        # Guardar temporalmente
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_audio:
            temp_audio.write(audio_data)
            temp_path = temp_audio.name

        # Convertir webm a wav usando ffmpeg o librosa
        import librosa
        import soundfile as sf

        audio, sr = librosa.load(temp_path, sr=16000)

        # Guardar como wav temporal
        wav_path = temp_path.replace('.webm', '.wav')
        sf.write(wav_path, audio, sr)

        # Procesar audio con voice_auth
        import numpy as np

        # Normalizar y procesar
        audio = voice_auth._normalize_audio(audio)
        audio = voice_auth._apply_bandpass_filter(audio)
        audio = voice_auth._remove_silence(audio)

        # Extraer características
        mfcc_features, speaker_embedding, prosodic_features = voice_auth._process_audio(audio)

        if mfcc_features is None:
            import os
            os.remove(temp_path)
            os.remove(wav_path)
            emit('voice_verification_result', {
                'success': False,
                'message': 'Audio muy corto o inválido'
            })
            return

        # Verificar vivacidad
        if voice_auth.enable_liveness:
            is_live, confidence, messages = voice_auth._check_liveness(prosodic_features)
            print(f"Liveness check: {is_live}, confidence: {confidence}")

        # Comparar con muestras almacenadas
        version = stored_sample.get('version', 'unknown')
        stored_samples = stored_sample.get('samples', [])

        similarities = []
        use_embeddings = version == 'challenge-response-v2'

        for sample in stored_samples:
            if use_embeddings and 'embedding' in sample:
                stored_embedding = sample['embedding']
                similarity = voice_auth._compare_embeddings(speaker_embedding, stored_embedding)
            else:
                stored_mfcc = sample['mfcc']
                similarity, _ = voice_auth._compare_features_dtw(mfcc_features, stored_mfcc)

            similarities.append(similarity)

        # Calcular similitud final
        if similarities:
            top_3_similarities = sorted(similarities, reverse=True)[:3]
            final_similarity = np.mean(top_3_similarities)

            is_match = final_similarity >= voice_auth.similarity_threshold

            print(f"Voice verification: {final_similarity*100:.2f}% (threshold: {voice_auth.similarity_threshold*100:.2f}%)")

            # Limpiar archivos temporales
            import os
            os.remove(temp_path)
            os.remove(wav_path)

            if is_match:
                # Generar token temporal
                import uuid
                temp_token = str(uuid.uuid4())

                if not hasattr(app, 'auth_tokens'):
                    app.auth_tokens = {}
                app.auth_tokens[temp_token] = username

                db.log_login_attempt(username, True, "voice")
                db.update_last_login(username)

                print(f"✓ Voice verification successful for {username}")
                emit('voice_verification_result', {
                    'success': True,
                    'redirect': url_for('verify_token', token=temp_token)
                })
            else:
                db.log_login_attempt(username, False, "voice")
                emit('voice_verification_result', {
                    'success': False,
                    'message': f'Similitud insuficiente ({final_similarity*100:.2f}%)'
                })
        else:
            import os
            os.remove(temp_path)
            os.remove(wav_path)
            emit('voice_verification_result', {
                'success': False,
                'message': 'Error en comparación de voz'
            })

    except Exception as e:
        print(f"Error en verificación de voz: {e}")
        import traceback
        traceback.print_exc()
        emit('voice_error', {'error': str(e)})

@socketio.on('register_voice')
def handle_register_voice(data):
    """
    Registra múltiples muestras de voz del usuario
    """
    try:
        if 'username' not in session:
            emit('voice_error', {'error': 'No autenticado'})
            return

        username = session['username']
        samples_data = data.get('samples', [])

        if len(samples_data) != 5:
            emit('voice_error', {'error': 'Se requieren 5 muestras'})
            return

        import base64
        import tempfile
        import librosa
        import soundfile as sf
        import numpy as np

        processed_samples = []

        for idx, sample_data in enumerate(samples_data):
            # Decodificar audio
            audio_data = base64.b64decode(sample_data['audio'].split(',')[1])

            # Guardar temporalmente
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_audio:
                temp_audio.write(audio_data)
                temp_path = temp_audio.name

            # Convertir a wav
            audio, sr = librosa.load(temp_path, sr=16000)

            # Procesar audio
            audio = voice_auth._normalize_audio(audio)
            audio = voice_auth._apply_bandpass_filter(audio)
            audio = voice_auth._remove_silence(audio)

            # Extraer características
            mfcc_features, speaker_embedding, prosodic_features = voice_auth._process_audio(audio)

            if mfcc_features is None:
                import os
                os.remove(temp_path)
                emit('voice_error', {'error': f'Muestra {idx+1} inválida'})
                return

            # Calcular calidad
            quality = (
                prosodic_features['rms_variance'] * 100 +
                prosodic_features['zcr_variance'] * 1000 +
                prosodic_features['pitch_variance']
            )

            processed_samples.append({
                'mfcc': mfcc_features.tolist(),
                'embedding': speaker_embedding.tolist(),
                'prosodic': {
                    'rms_variance': float(prosodic_features['rms_variance']),
                    'zcr_variance': float(prosodic_features['zcr_variance']),
                    'pitch_variance': float(prosodic_features['pitch_variance'])
                },
                'quality': float(quality),
                'challenge': sample_data['challenge']
            })

            # Limpiar
            import os
            os.remove(temp_path)

            print(f"Processed sample {idx+1}/5 - Quality: {quality:.2f}")

        # Guardar todas las muestras
        voice_data = {
            'samples': processed_samples,
            'num_samples': len(processed_samples),
            'challenge_type': voice_auth.challenge_type,
            'version': 'challenge-response-v2'
        }

        db.save_voice_sample(username, voice_data)

        # Limpiar flag de registro si está registrándose
        if session.get('registering'):
            session.pop('registering', None)

        print(f"✓ Voice profile registered for {username}")
        emit('voice_registration_complete', {'success': True})

    except Exception as e:
        print(f"Error en registro de voz: {e}")
        import traceback
        traceback.print_exc()
        emit('voice_error', {'error': str(e)})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("   SISTEMA 2FA BIOMÉTRICO - FLASK + SOCKET.IO")
    print("="*60)
    print("\n🚀 Iniciando servidor en http://localhost:5001")
    print("📹 Streaming de video en tiempo real habilitado")
    print("\n")

    socketio.run(app, debug=True, host='0.0.0.0', port=5001, allow_unsafe_werkzeug=True)
