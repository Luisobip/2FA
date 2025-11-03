import os

class Config:
    """Configuración centralizada del sistema"""
    
    # Base de datos
    DATABASE_NAME = "users_2fa.db"
    
    # Autenticación facial
    FACE_RECOGNITION_TOLERANCE = 0.5
    FACE_MOVEMENT_THRESHOLD = 50
    FACE_CENTER_THRESHOLD = 30
    
    # Autenticación de voz
    VOICE_SAMPLE_RATE = 44100
    VOICE_DURATION = 5  # segundos
    VOICE_SIMILARITY_THRESHOLD = 0.85
    VOICE_PHRASE = "Mi voz es mi contraseña, verificar mi identidad"
    
    # Sistema
    PLATFORM = os.sys.platform
    IS_MAC = PLATFORM == 'darwin'
    
    # Directorios
    DATA_DIR = "data"
    
    @classmethod
    def ensure_directories(cls):
        """Crea los directorios necesarios si no existen"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        