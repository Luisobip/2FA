"""
Aplicación web de autenticación 2FA con Streamlit
Interfaz moderna para registro y login con biometría
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import sounddevice as sd
from database import DatabaseManager
from facial_auth import FacialAuth
from voice_auth import VoiceAuthChallenge
from touchid_auth import TouchIDAuth
from config import Config
from challenge_generator import ChallengeGenerator
import time
import subprocess
import sys

# Configuración de la página
st.set_page_config(
    page_title="Sistema 2FA Biométrico",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar estado de la sesión
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.current_page = 'login'

# Inicializar servicios
@st.cache_resource
def init_services():
    Config.ensure_directories()
    return {
        'db': DatabaseManager(),
        'facial_auth': FacialAuth(),
        'voice_auth': VoiceAuthChallenge()
    }

services = init_services()

def capture_webcam_photo():
    """Captura una foto desde la webcam"""
    camera_placeholder = st.empty()

    with camera_placeholder:
        camera_input = st.camera_input("Toma tu foto para autenticación facial")

    if camera_input is not None:
        # Convertir la imagen de PIL a numpy array
        image = Image.open(camera_input)
        image_array = np.array(image)

        # Convertir RGB a BGR para OpenCV
        image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)

        return image_bgr

    return None

def verify_with_liveness_streamlit(username, stored_encoding):
    """
    Lanza la verificación facial con detección de vivacidad usando la versión de terminal
    que es mucho más rápida y fluida que procesar video en Streamlit
    """
    st.markdown("""
    <div class="info-box">
        <h3>🎬 Verificación Facial con Detección de Vivacidad</h3>
        <p><strong>Se abrirá una ventana de OpenCV donde deberás:</strong></p>
        <ul>
            <li>👁️ <strong>Parpadear:</strong> Cierra y abre los ojos completamente</li>
            <li>👄 <strong>Abrir la boca:</strong> Abre bien la boca y luego ciérrala</li>
        </ul>
        <p><em>La ventana se cerrará automáticamente al completar la verificación</em></p>
    </div>
    """, unsafe_allow_html=True)

    st.info("💡 **Nota:** Se abrirá una ventana separada de OpenCV (más rápida que el navegador)")

    if st.button("🎥 Iniciar Verificación Facial", use_container_width=True, type="primary"):
        with st.spinner("Abriendo ventana de verificación..."):
            # Ejecutar verificación directamente usando FacialAuth
            try:
                facial_auth = services['facial_auth']
                success = facial_auth.verify_with_liveness(username, stored_encoding, skip_prompt=True)

                if success:
                    st.balloons()
                    st.success("🎉 ¡Verificación exitosa! Todos los gestos detectados.")
                    return True
                else:
                    st.error("❌ Verificación fallida. Intenta nuevamente.")
                    return False

            except cv2.error as e:
                st.error(f"❌ Error de OpenCV: {e}")
                st.warning("💡 Asegúrate de que:")
                st.markdown("""
                - La cámara no esté siendo usada por otra aplicación
                - Python tenga permisos de cámara en macOS (Preferencias del Sistema → Seguridad y Privacidad → Cámara)
                - No haya otras instancias de la aplicación usando la cámara
                """)
                return False
            except Exception as e:
                st.error(f"❌ Error durante la verificación: {e}")
                import traceback
                st.code(traceback.format_exc())
                return False

    return False

def record_audio_challenge(duration=5):
    """Graba audio con un desafío aleatorio que se muestra DESPUÉS de hacer clic"""

    st.markdown("""
    <div class="info-box">
        <h3>🎲 Desafío de Voz Aleatorio</h3>
        <p><strong>⚠️ Medida de seguridad:</strong> El desafío se mostrará DESPUÉS de presionar el botón</p>
        <p>Esto previene que se prepare un audio con anticipación</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🎙️ Iniciar Grabación", use_container_width=True, type="primary"):
        # GENERAR EL DESAFÍO SOLO DESPUÉS DE HACER CLIC
        challenge, display = ChallengeGenerator.generate_challenge('numeric')

        # Placeholder para mostrar el desafío y el estado
        challenge_display = st.empty()
        status_text = st.empty()
        progress_bar = st.empty()

        # Mostrar el desafío AHORA
        challenge_display.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 2rem;
                    border-radius: 1rem;
                    margin: 1rem 0;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <h2 style="text-align: center;
                       color: white;
                       font-size: 3.5rem;
                       margin: 0;
                       text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
                       letter-spacing: 0.5rem;">
                {challenge}
            </h2>
            <p style="text-align: center;
                      color: rgba(255,255,255,0.9);
                      margin-top: 1rem;
                      font-size: 1.2rem;">
                ¡DI ESTOS NÚMEROS CLARAMENTE!
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Countdown visual
        for i in range(3, 0, -1):
            status_text.markdown(f"""
            <div style="text-align: center; font-size: 2rem; color: #ff6b6b; font-weight: bold;">
                ⏱️ Grabando en {i}...
            </div>
            """, unsafe_allow_html=True)
            time.sleep(1)

        status_text.markdown("""
        <div style="text-align: center; font-size: 2rem; color: #ff0000; font-weight: bold; animation: blink 1s infinite;">
            🔴 ¡GRABANDO AHORA!
        </div>
        <style>
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }
        </style>
        """, unsafe_allow_html=True)

        # Grabar audio
        sample_rate = Config.VOICE_SAMPLE_RATE
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.float32
        )

        # Barra de progreso durante la grabación
        progress_container = progress_bar.container()
        with progress_container:
            prog = st.progress(0)
            for i in range(100):
                time.sleep(duration / 100)
                prog.progress(i + 1)

        sd.wait()

        status_text.markdown("""
        <div style="text-align: center; font-size: 1.5rem; color: #51cf66; font-weight: bold;">
            ✅ Grabación completada
        </div>
        """, unsafe_allow_html=True)

        return recording.flatten(), challenge

    return None, None

def register_page():
    """Página de registro de usuario"""
    st.markdown('<p class="main-header">📝 Registro de Usuario</p>', unsafe_allow_html=True)

    with st.form("register_form"):
        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input("👤 Nombre de usuario")
            password = st.text_input("🔒 Contraseña", type="password")
            password_confirm = st.text_input("🔒 Confirmar contraseña", type="password")

        with col2:
            st.markdown("### Métodos de autenticación 2FA")
            use_facial = st.checkbox("👤 Reconocimiento facial", value=True)
            use_voice = st.checkbox("🎤 Reconocimiento de voz", value=True)
            if TouchIDAuth.is_available():
                use_touchid = st.checkbox("👆 Touch ID", value=False)
            else:
                use_touchid = False

        submitted = st.form_submit_button("Registrar Usuario", use_container_width=True)

        if submitted:
            # Validaciones
            if not username:
                st.error("El nombre de usuario no puede estar vacío")
                return

            if services['db'].user_exists(username):
                st.error(f"El usuario '{username}' ya existe")
                return

            if password != password_confirm:
                st.error("Las contraseñas no coinciden")
                return

            if len(password) < 6:
                st.error("La contraseña debe tener al menos 6 caracteres")
                return

            if not (use_facial or use_voice or use_touchid):
                st.error("Debes seleccionar al menos un método de autenticación")
                return

            # Registrar usuario
            if services['db'].register_user(username, password):
                st.success(f"Usuario '{username}' creado correctamente")

                # Configurar métodos biométricos
                st.session_state.registering_user = username
                st.session_state.registration_methods = {
                    'facial': use_facial,
                    'voice': use_voice,
                    'touchid': use_touchid
                }
                st.session_state.current_page = 'setup_biometrics'
                st.rerun()
            else:
                st.error("Error al registrar el usuario")

def setup_biometrics_page():
    """Página de configuración de métodos biométricos"""
    st.markdown('<p class="main-header">🔐 Configuración de Métodos Biométricos</p>', unsafe_allow_html=True)

    username = st.session_state.registering_user
    methods = st.session_state.registration_methods

    st.info(f"Configurando métodos para el usuario: **{username}**")

    # Reconocimiento Facial
    if methods.get('facial'):
        st.markdown("---")
        st.markdown("### 👤 Reconocimiento Facial")
        st.write("Toma una foto clara de tu rostro. Asegúrate de tener buena iluminación.")

        photo = capture_webcam_photo()

        if photo is not None:
            with st.spinner("Procesando imagen facial..."):
                encoding = services['facial_auth'].encode_face_from_image(photo)

                if encoding is not None:
                    services['db'].save_face_encoding(username, encoding)
                    st.success("✅ Reconocimiento facial configurado")
                    methods['facial'] = False  # Marcar como completado
                else:
                    st.error("❌ No se detectó un rostro válido. Intenta de nuevo.")

    # Reconocimiento de Voz
    if methods.get('voice'):
        st.markdown("---")
        st.markdown("### 🎤 Reconocimiento de Voz")
        st.write("Grabarás 5 muestras de voz diciendo diferentes secuencias de números.")

        if 'voice_samples' not in st.session_state:
            st.session_state.voice_samples = []

        samples_needed = 5 - len(st.session_state.voice_samples)

        if samples_needed > 0:
            st.info(f"Muestras restantes: {samples_needed}/5")

            audio, challenge = record_audio_challenge()

            if audio is not None:
                with st.spinner("Procesando audio..."):
                    mfcc, embedding, prosodic = services['voice_auth']._process_audio(audio)

                    if mfcc is not None:
                        quality = (
                            prosodic['rms_variance'] * 100 +
                            prosodic['zcr_variance'] * 1000 +
                            prosodic['pitch_variance']
                        )

                        st.session_state.voice_samples.append({
                            'mfcc': mfcc,
                            'embedding': embedding,
                            'prosodic': prosodic,
                            'quality': quality,
                            'challenge': challenge
                        })

                        st.success(f"✅ Muestra {len(st.session_state.voice_samples)}/5 guardada (Calidad: {quality:.2f})")
                        st.rerun()
                    else:
                        st.error("❌ Audio inválido. Intenta de nuevo.")
        else:
            # Todas las muestras recolectadas
            voice_data = {
                'samples': st.session_state.voice_samples,
                'num_samples': len(st.session_state.voice_samples),
                'challenge_type': 'numeric',
                'version': 'challenge-response-v2'
            }

            services['db'].save_voice_sample(username, voice_data)
            st.success("✅ Reconocimiento de voz configurado")
            methods['voice'] = False
            del st.session_state.voice_samples

    # Touch ID
    if methods.get('touchid'):
        st.markdown("---")
        st.markdown("### 👆 Touch ID")
        st.success("✅ Touch ID disponible para autenticación")
        methods['touchid'] = False

    # Verificar si todo está completado
    if not any(methods.values()):
        st.markdown("---")
        st.markdown('<div class="success-box"><h2>✅ Registro Completado</h2><p>Todos los métodos biométricos han sido configurados correctamente.</p></div>', unsafe_allow_html=True)

        if st.button("Ir al Login", use_container_width=True):
            del st.session_state.registering_user
            del st.session_state.registration_methods
            st.session_state.current_page = 'login'
            st.rerun()

def login_page():
    """Página de inicio de sesión"""
    st.markdown('<p class="main-header">🔐 Inicio de Sesión</p>', unsafe_allow_html=True)

    with st.form("login_form"):
        st.markdown("### 📋 Fase 1: Credenciales")
        username = st.text_input("👤 Nombre de usuario")
        password = st.text_input("🔒 Contraseña", type="password")

        submitted = st.form_submit_button("Continuar", use_container_width=True)

        if submitted:
            if services['db'].verify_password(username, password):
                st.success("✅ Credenciales correctas")
                st.session_state.login_username = username
                st.session_state.current_page = 'biometric_auth'
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
                services['db'].log_login_attempt(username, False, "password")

    st.markdown("---")
    if st.button("¿No tienes cuenta? Regístrate aquí"):
        st.session_state.current_page = 'register'
        st.rerun()

def biometric_auth_page():
    """Página de autenticación biométrica"""
    st.markdown('<p class="main-header">🔐 Autenticación Biométrica</p>', unsafe_allow_html=True)

    username = st.session_state.login_username
    st.info(f"Usuario: **{username}**")

    # Detectar métodos disponibles
    available_methods = []
    if services['db'].get_face_encoding(username) is not None:
        available_methods.append("Reconocimiento Facial")
    if services['db'].get_voice_sample(username) is not None:
        available_methods.append("Reconocimiento de Voz")
    if TouchIDAuth.is_available():
        available_methods.append("Touch ID")

    if not available_methods:
        st.error("No tienes métodos biométricos configurados")
        return

    st.markdown("### Selecciona el método de autenticación")
    method = st.radio("Métodos disponibles:", available_methods)

    if method == "Reconocimiento Facial":
        st.markdown("---")

        stored_encoding = services['db'].get_face_encoding(username)

        # Inicializar estado de verificación
        if 'facial_verification_complete' not in st.session_state:
            st.session_state.facial_verification_complete = False

        success = verify_with_liveness_streamlit(username, stored_encoding)

        if success and not st.session_state.facial_verification_complete:
            st.session_state.facial_verification_complete = True
            services['db'].log_login_attempt(username, True, "facial")
            services['db'].update_last_login(username)
            st.session_state.authenticated = True
            st.session_state.username = username
            st.session_state.current_page = 'dashboard'

            # Botón para continuar
            if st.button("✅ Continuar al Dashboard", use_container_width=True, type="primary"):
                st.rerun()

    elif method == "Reconocimiento de Voz":
        st.markdown("---")

        audio, challenge = record_audio_challenge()

        if audio is not None:
            with st.spinner("Verificando identidad..."):
                stored_features = services['db'].get_voice_sample(username)

                # Procesar audio
                mfcc, embedding, prosodic = services['voice_auth']._process_audio(audio)

                if mfcc is not None:
                    # Comparar con muestras almacenadas
                    version = stored_features.get('version')
                    use_embeddings = version == 'challenge-response-v2'

                    similarities = []
                    for sample in stored_features['samples']:
                        if use_embeddings and 'embedding' in sample:
                            similarity = services['voice_auth']._compare_embeddings(embedding, sample['embedding'])
                        else:
                            similarity, _ = services['voice_auth']._compare_features_dtw(mfcc, sample['mfcc'])
                        similarities.append(similarity)

                    top_3_similarities = sorted(similarities, reverse=True)[:3]
                    final_similarity = np.mean(top_3_similarities)

                    threshold = 0.75
                    success = final_similarity >= threshold

                    if success:
                        st.success(f"✅ Identidad confirmada ({final_similarity*100:.2f}%)")
                        services['db'].log_login_attempt(username, True, "voice")
                        services['db'].update_last_login(username)
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.current_page = 'dashboard'
                        st.rerun()
                    else:
                        st.error(f"❌ Verificación fallida (Similitud: {final_similarity*100:.2f}%)")
                        services['db'].log_login_attempt(username, False, "voice")
                else:
                    st.error("❌ Audio inválido")

    elif method == "Touch ID":
        if st.button("🔐 Usar Touch ID"):
            success = TouchIDAuth.verify_touchid()
            if success:
                services['db'].log_login_attempt(username, True, "touchid")
                services['db'].update_last_login(username)
                st.session_state.authenticated = True
                st.session_state.username = username
                st.session_state.current_page = 'dashboard'
                st.rerun()
            else:
                st.error("❌ Touch ID fallido")
                services['db'].log_login_attempt(username, False, "touchid")

def dashboard_page():
    """Dashboard principal después de autenticarse"""
    st.markdown('<p class="main-header">✅ Sesión Activa</p>', unsafe_allow_html=True)

    username = st.session_state.username
    st.markdown(f'<div class="success-box"><h2>¡Bienvenido, {username}!</h2><p>Has iniciado sesión correctamente.</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("➕ Añadir/Re-registrar método 2FA", use_container_width=True):
            st.session_state.current_page = 'manage_methods'
            st.rerun()

    with col2:
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.current_page = 'login'
            st.rerun()

# Navegación principal
def main():
    if st.session_state.current_page == 'register':
        register_page()
    elif st.session_state.current_page == 'setup_biometrics':
        setup_biometrics_page()
    elif st.session_state.current_page == 'login':
        login_page()
    elif st.session_state.current_page == 'biometric_auth':
        biometric_auth_page()
    elif st.session_state.current_page == 'dashboard':
        dashboard_page()

if __name__ == "__main__":
    main()
