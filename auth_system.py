from database import DatabaseManager
from facial_auth import FacialAuth
from voice_auth import VoiceAuth
from touchid_auth import TouchIDAuth
from config import Config

class Auth2FASystem:
    """Sistema principal de autenticación de doble factor"""
    
    def __init__(self):
        Config.ensure_directories()
        self.db = DatabaseManager()
        self.facial_auth = FacialAuth()
        self.voice_auth = VoiceAuth()
        
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
        
        print("\nMétodos disponibles:")
        print("  1. 👤 Reconocimiento facial (con detección de vivacidad)")
        print("  2. 🎤 Reconocimiento de voz")
        if TouchIDAuth.is_available():
            print("  3. 👆 Touch ID (Huella dactilar)")
        
        choice = input("\nElige el método (1/2/3): ").strip()
        
        method_name = ""
        success = False
        
        if choice == '1':
            method_name = "facial"
            stored_encoding = self.db.get_face_encoding(username)
            if stored_encoding is None:
                print("❌ No tienes reconocimiento facial configurado")
                print("   Regístrate nuevamente para configurarlo")
            else:
                success = self.facial_auth.verify_with_liveness(username, stored_encoding)
        
        elif choice == '2':
            method_name = "voice"
            stored_features = self.db.get_voice_sample(username)
            if stored_features is None:
                print("❌ No tienes reconocimiento de voz configurado")
                print("   Regístrate nuevamente para configurarlo")
            else:
                success = self.voice_auth.verify_voice(username, stored_features)
        
        elif choice == '3' and TouchIDAuth.is_available():
            method_name = "touchid"
            success = TouchIDAuth.verify_touchid()
        
        else:
            print("❌ Opción no válida")
            return False
        
        # Registrar intento
        self.db.log_login_attempt(username, success, method_name)
        
        if success:
            self.db.update_last_login(username)
            self._print_header("✅ AUTENTICACIÓN EXITOSA")
            print(f"\n   ¡Bienvenido, {username}!")
            print(f"   Método utilizado: {method_name}")
            print("\n" + "="*60)
            return True
        else:
            print("\n" + "="*60)
            print("❌ AUTENTICACIÓN FALLIDA")
            print("="*60)
            return False
    
    def show_menu(self):
        """Muestra el menú principal"""
        self._print_header("SISTEMA DE AUTENTICACIÓN 2FA")
        print("\n  1. 📝 Registrar nuevo usuario")
        print("  2. 🔐 Iniciar sesión")
        print("  3. ❌ Salir")
        print("\n" + "="*60)
    
    def run(self):
        """Ejecuta el sistema"""
        while True:
            self.show_menu()
            choice = input("Elige una opción: ").strip()
            
            if choice == '1':
                self.register()
            elif choice == '2':
                self.login()
            elif choice == '3':
                print("\n" + "="*60)
                print("   ¡Hasta luego! Sesión cerrada")
                print("="*60 + "\n")
                break
            else:
                print("❌ Opción no válida. Intenta de nuevo.")
            
            if choice in ['1', '2']:
                input("\nPresiona ENTER para continuar...")

                