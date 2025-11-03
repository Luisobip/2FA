import sys
from config import Config

# Importar LocalAuthentication solo en Mac
if Config.IS_MAC:
    try:
        from LocalAuthentication import (
            LAContext, 
            LAPolicyDeviceOwnerAuthenticationWithBiometrics
        )
        TOUCHID_AVAILABLE = True
    except ImportError:
        TOUCHID_AVAILABLE = False
else:
    TOUCHID_AVAILABLE = False


class TouchIDAuth:
    """Autenticación por Touch ID (exclusivo para Mac)"""
    
    @staticmethod
    def is_available():
        """Verifica si Touch ID está disponible en el sistema"""
        return TOUCHID_AVAILABLE
    
    @staticmethod
    def verify_touchid():
        """Verifica la identidad usando Touch ID"""
        if not TOUCHID_AVAILABLE:
            print("❌ Touch ID no está disponible en este sistema")
            print("   Solo disponible en macOS con hardware compatible")
            return False
        
        print("\n👆 Autenticación con Touch ID")
        print("Coloca tu dedo en el sensor Touch ID...")
        
        try:
            context = LAContext.alloc().init()
            
            # Verificar si el dispositivo puede usar biometría
            can_evaluate, error = context.canEvaluatePolicy_error_(
                LAPolicyDeviceOwnerAuthenticationWithBiometrics, None
            )
            
            if not can_evaluate:
                print("❌ Touch ID no está configurado en este Mac")
                print("   Configúralo en Preferencias del Sistema > Touch ID")
                return False
            
            # Variable para almacenar el resultado
            result = {'success': False, 'completed': False}
            
            def completion_handler(success, error):
                result['success'] = success
                result['completed'] = True
                if error:
                    print(f"   Error: {error.localizedDescription()}")
            
            # Solicitar autenticación
            context.evaluatePolicy_localizedReason_reply_(
                LAPolicyDeviceOwnerAuthenticationWithBiometrics,
                "Se requiere autenticación para acceder al sistema 2FA",
                completion_handler
            )
            
            # Esperar resultado
            import time
            timeout = 30  # 30 segundos de timeout
            elapsed = 0
            while not result['completed'] and elapsed < timeout:
                time.sleep(0.1)
                elapsed += 0.1
            
            if not result['completed']:
                print("❌ Tiempo de espera agotado")
                return False
            
            if result['success']:
                print("✅ Touch ID verificado correctamente")
                return True
            else:
                print("❌ Touch ID no pudo ser verificado")
                return False
                
        except Exception as e:
            print(f"❌ Error al usar Touch ID: {e}")
            return False