from database import DatabaseManager
from facial_auth import FacialAuth
from voice_auth import VoiceAuthChallenge
from touchid_auth import TouchIDAuth
from config import Config
import time

class Auth2FASystem:
    """Sistema principal de autenticación de doble factor"""

    def __init__(self):
        Config.ensure_directories()
        self.db = DatabaseManager()
        self.facial_auth = FacialAuth()
        self.voice_auth = VoiceAuthChallenge()
        
        print("\n" + "="*60)
        print("   SISTEMA DE AUTENTICACIÓN 2FA - INICIALIZADO")
        print("="*60)
    
    def _print_header(self, title):
        """Imprime un encabezado formateado"""
        print("\n" + "="*60)
        print(f"   {title}")
        print("="*60)
    
    def _print_separator(self):
        """Imprime un separador"""
        print("-"*60)
    
    def register(self):
        """Registro de nuevo usuario"""
        self._print_header("REGISTRO DE NUEVO USUARIO")
        
        username = input("\n📝 Nombre de usuario: ").strip()
        
        if not username:
            print("❌ El nombre de usuario no puede estar vacío")
            return
        
        if self.db.user_exists(username):
            print(f"❌ El usuario '{username}' ya existe")
            return
        
        password = input("🔒 Contraseña: ")
        password_confirm = input("🔒 Confirmar contraseña: ")
        
        if password != password_confirm:
            print("❌ Las contraseñas no coinciden")
            return
        
        if len(password) < 6:
            print("❌ La contraseña debe tener al menos 6 caracteres")
            return
        
        if self.db.register_user(username, password):
            print(f"\n✅ Usuario '{username}' registrado correctamente")
            
            self._print_separator()
            print("CONFIGURACIÓN DE MÉTODOS DE AUTENTICACIÓN 2FA")
            self._print_separator()
            
            print("\nElige los métodos que deseas configurar:")
            print("  1. 👤 Reconocimiento facial (con detección de vivacidad)")
            print("  2. 🎤 Reconocimiento de voz")
            if TouchIDAuth.is_available():
                print("  3. 👆 Touch ID (Huella dactilar)")
            
            print("\nPuedes elegir uno o varios métodos (ej: 1,2 o 1 o 2)")
            choice = input("\nMétodo(s): ").strip()
            
            methods_configured = []
            
            if '1' in choice:
                print("\n" + "-"*60)
                encoding = self.facial_auth.capture_and_encode_face(username)
                if encoding is not None:
                    self.db.save_face_encoding(username, encoding)
                    methods_configured.append("Reconocimiento facial")
                    print("✅ Reconocimiento facial configurado")
                else:
                    print("⚠️  No se pudo configurar el reconocimiento facial")
            
            if '2' in choice:
                print("\n" + "-"*60)
                features = self.voice_auth.record_voice_sample(username)
                if features:
                    self.db.save_voice_sample(username, features)
                    methods_configured.append("Reconocimiento de voz")
                    print("✅ Reconocimiento de voz configurado")
                else:
                    print("⚠️  No se pudo configurar el reconocimiento de voz")
            
            if '3' in choice and TouchIDAuth.is_available():
                methods_configured.append("Touch ID")
                print("✅ Touch ID disponible para autenticación")
            
            print("\n" + "="*60)
            print("✅ REGISTRO COMPLETADO EXITOSAMENTE")
            if methods_configured:
                print(f"   Métodos configurados: {', '.join(methods_configured)}")
            print("="*60)
        else:
            print("❌ Error al registrar el usuario")
    
    def login(self):
        """Proceso de inicio de sesión con 2FA"""
        self._print_header("INICIO DE SESIÓN - AUTENTICACIÓN 2FA")
        
        # FASE 1: Credenciales
        print("\n📋 FASE 1: Credenciales")
        self._print_separator()
        
        username = input("Nombre de usuario: ").strip()
        password = input("Contraseña: ")
        
        if not self.db.verify_password(username, password):
            print("\n❌ Usuario o contraseña incorrectos")
            self.db.log_login_attempt(username, False, "password")
            return False
        
        print("✅ Fase 1 completada: Credenciales correctas")
        
        # FASE 2: Autenticación biométrica
        print("\n🔐 FASE 2: Autenticación Biométrica")
        self._print_separator()
        
        available_methods = []
        print("\nMétodos disponibles:")
        
        if self.db.get_face_encoding(username) is not None:
            available_methods.append("facial")
            print("  1. 👤 Reconocimiento facial")
        if self.db.get_voice_sample(username) is not None:
            available_methods.append("voice")
            print("  2. 🎤 Reconocimiento de voz")
        if TouchIDAuth.is_available():
            available_methods.append("touchid")
            print("  3. 👆 Touch ID (Huella dactilar)")
        
        if not available_methods:
            print("⚠️ No tienes ningún método biométrico configurado.")
            print("Por favor, regístrate de nuevo y configura uno.")
            return False
        
        choice = input("\nElige el método (1/2/3): ").strip()
        success = False
        method_name = ""

        if choice == '1' and "facial" in available_methods:
            method_name = "facial"
            stored_encoding = self.db.get_face_encoding(username)
            success = self.facial_auth.verify_with_liveness(username, stored_encoding)
        elif choice == '2' and "voice" in available_methods:
            method_name = "voice"
            stored_features = self.db.get_voice_sample(username)
            success = self.voice_auth.verify_voice(username, stored_features)
        elif choice == '3' and "touchid" in available_methods:
            method_name = "touchid"
            success = TouchIDAuth.verify_touchid()
        else:
            print("❌ Opción no válida.")
            return False
        
        # Registrar intento
        self.db.log_login_attempt(username, success, method_name)
        
        if success:
            self.db.update_last_login(username)
            self._print_header("✅ AUTENTICACIÓN EXITOSA")
            print(f"\n   ¡Bienvenido, {username}!")
            print(f"   Método utilizado: {method_name}")
            print("\n" + "="*60)
            
            # Iniciar sesión del usuario
            self.session(username)
            return True
        else:
            print("\n" + "="*60)
            print("❌ AUTENTICACIÓN FALLIDA")
            print("="*60)
            return False

    def session(self, username):
        """Menú de sesión activa: añadir métodos o cerrar sesión"""
        while True:
            self._print_header(f"SESIÓN ACTIVA: {username}")
            print("\n  1. ➕ Añadir/Re-registrar método 2FA")
            print("  2. 🚪 Cerrar sesión")
            print("\n" + "="*60)

            choice = input("Elige una opción: ").strip()

            if choice == '1':
                self.add_auth_method(username)
            elif choice == '2':
                print(f"\n👋 Cerrando sesión de {username}...")
                time.sleep(1)
                print("✅ Sesión cerrada correctamente.\n")
                break
            else:
                print("❌ Opción no válida. Intenta nuevamente.")
    
    def add_auth_method(self, username):
        """Permite agregar o re-registrar métodos biométricos al usuario"""
        self._print_header("AÑADIR/RE-REGISTRAR MÉTODO DE AUTENTICACIÓN")

        print("\nMétodos disponibles:")
        print("  1. 👤 Reconocimiento facial")
        print("  2. 🎤 Reconocimiento de voz")
        if TouchIDAuth.is_available():
            print("  3. 👆 Touch ID (Huella dactilar)")

        choice = input("\nElige el método (1/2/3): ").strip()

        if choice == '1':
            if self.db.get_face_encoding(username) is not None:
                confirm = input("⚠️ Ya tienes reconocimiento facial. ¿Deseas re-registrarlo? (s/n): ")
                if confirm.lower() != 's':
                    return
            encoding = self.facial_auth.capture_and_encode_face(username)
            if encoding is not None:
                self.db.save_face_encoding(username, encoding)
                print("✅ Reconocimiento facial configurado correctamente.")
            else:
                print("❌ No se pudo configurar el reconocimiento facial.")

        elif choice == '2':
            if self.db.get_voice_sample(username) is not None:
                confirm = input("⚠️ Ya tienes reconocimiento de voz. ¿Deseas re-registrarlo? (s/n): ")
                if confirm.lower() != 's':
                    return
            features = self.voice_auth.record_voice_sample(username)
            if features:
                self.db.save_voice_sample(username, features)
                print("✅ Reconocimiento de voz configurado correctamente.")
            else:
                print("❌ No se pudo configurar el reconocimiento de voz.")

        elif choice == '3' and TouchIDAuth.is_available():
            print("✅ Touch ID habilitado como método de autenticación.")
        else:
            print("❌ Opción no válida.")
    
    def run(self):
        """Menú principal del sistema"""
        while True:
            self._print_header("MENÚ PRINCIPAL")
            print("\n  1. 📝 Registrar nuevo usuario")
            print("  2. 🔐 Iniciar sesión")
            print("  3. 🚪 Salir")
            print("\n" + "="*60)
            
            choice = input("Elige una opción: ").strip()
            
            if choice == '1':
                self.register()
            elif choice == '2':
                self.login()
            elif choice == '3':
                print("\n👋 ¡Hasta luego!")
                print("="*60 + "\n")
                break
            else:
                print("❌ Opción no válida. Intenta nuevamente.")