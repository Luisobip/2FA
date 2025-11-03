"""
Sistema de Autenticación 2FA con Métodos Biométricos
Autor: Sistema modular
Versión: 2.0
"""

import sys
from auth_system import Auth2FASystem

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas"""
    print("\n🔍 Verificando dependencias...")
    
    dependencies = {
        'cv2': 'OpenCV',
        'face_recognition': 'Face Recognition',
        'numpy': 'NumPy',
        'bcrypt': 'Bcrypt',
        'sounddevice': 'SoundDevice',
        'scipy': 'SciPy'
    }
    
    missing = []
    
    for module, name in dependencies.items():
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - NO INSTALADO")
            missing.append(module)
    
    # Verificar Touch ID (solo en Mac)
    if sys.platform == 'darwin':
        try:
            __import__('LocalAuthentication')
            print(f"  ✓ LocalAuthentication (Touch ID)")
        except ImportError:
            print(f"  ⚠️  LocalAuthentication (Touch ID) - NO INSTALADO")
            print(f"      Instala con: pip install pyobjc-framework-LocalAuthentication")
    
    if missing:
        print("\n❌ Faltan dependencias. Instala con:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    print("\n✅ Todas las dependencias están instaladas\n")
    return True


def main():
    """Función principal"""
    print("\n" + "="*60)
    print("   SISTEMA DE AUTENTICACIÓN 2FA - VERSIÓN MODULAR")
    print("="*60)
    
    if not check_dependencies():
        print("\nPor favor instala las dependencias faltantes")
        sys.exit(1)
    
    try:
        system = Auth2FASystem()
        system.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Programa interrumpido por el usuario")
        print("¡Hasta luego!\n")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()