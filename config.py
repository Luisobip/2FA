import os

class Config:
    """Configuración centralizada del sistema"""

    # Base de datos
    DATABASE_NAME = os.getenv("DATABASE_NAME", "users_2fa.db")
    
    # Autenticación facial
    FACE_RECOGNITION_TOLERANCE = 0.5
    FACE_MOVEMENT_THRESHOLD = 50
    FACE_CENTER_THRESHOLD = 30
    
    # Autenticación de voz
    VOICE_SAMPLE_RATE = 16000  # Reducido para mejor procesamiento
    VOICE_DURATION = 6  # segundos (aumentado para capturar más audio)
    VOICE_SIMILARITY_THRESHOLD = 0.50  # Usuario ~58-62%, otros ~30% (margen 20-30%)
    VOICE_PHRASE = "Mi voz es mi contraseña, verificar mi identidad"
    VOICE_CHALLENGE_TYPE = "numeric"  # SOLO NÚMEROS para simplificar

    # Parámetros avanzados de voz (detección de vivacidad)
    VOICE_ENABLE_LIVENESS = True       # ACTIVADO para mayor seguridad
    VOICE_MIN_ENERGY_VARIANCE = 0.012  # MUY ESTRICTO (antes 0.008)
    VOICE_MIN_ZCR_VARIANCE = 0.0015    # MUY ESTRICTO (antes 0.001)
    VOICE_MIN_PITCH_VARIANCE = 8       # MUY ESTRICTO (antes 5)
    
    # Sistema
    PLATFORM = os.sys.platform
    IS_MAC = PLATFORM == 'darwin'
    
    # Directorios
    DATA_DIR = "data"
    
    @classmethod
    def ensure_directories(cls):
        """Crea los directorios necesarios si no existen"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
