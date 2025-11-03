import sqlite3
import bcrypt
import pickle
from datetime import datetime
from config import Config

class DatabaseManager:
    """Gestión de la base de datos de usuarios"""
    
    def __init__(self, db_name=None):
        self.db_name = db_name or Config.DATABASE_NAME
        self.init_database()
    
    def init_database(self):
        """Inicializa la base de datos con las tablas necesarias"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                face_encoding BLOB,
                voice_sample BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                method TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Base de datos inicializada: {self.db_name}")
    
    def register_user(self, username, password):
        """Registra un nuevo usuario"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        try:
            cursor.execute(
                'INSERT INTO users (username, password_hash) VALUES (?, ?)',
                (username, password_hash)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def verify_password(self, username, password):
        """Verifica la contraseña del usuario"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return bcrypt.checkpw(password.encode('utf-8'), result[0])
        return False
    
    def user_exists(self, username):
        """Verifica si un usuario existe"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def save_face_encoding(self, username, encoding):
        """Guarda el encoding facial del usuario"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        encoding_bytes = pickle.dumps(encoding)
        cursor.execute(
            'UPDATE users SET face_encoding = ? WHERE username = ?',
            (encoding_bytes, username)
        )
        conn.commit()
        conn.close()
    
    def get_face_encoding(self, username):
        """Obtiene el encoding facial del usuario"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT face_encoding FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return pickle.loads(result[0])
        return None
    
    def save_voice_sample(self, username, voice_features):
        """Guarda las características de voz del usuario"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        voice_bytes = pickle.dumps(voice_features)
        cursor.execute(
            'UPDATE users SET voice_sample = ? WHERE username = ?',
            (voice_bytes, username)
        )
        conn.commit()
        conn.close()
    
    def get_voice_sample(self, username):
        """Obtiene las características de voz del usuario"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('SELECT voice_sample FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            return pickle.loads(result[0])
        return None
    
    def update_last_login(self, username):
        """Actualiza la fecha del último inicio de sesión"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE users SET last_login = ? WHERE username = ?',
            (datetime.now(), username)
        )
        conn.commit()
        conn.close()
    
    def log_login_attempt(self, username, success, method):
        """Registra un intento de inicio de sesión"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO login_attempts (username, success, method) VALUES (?, ?, ?)',
            (username, success, method)
        )
        conn.commit()
        conn.close()