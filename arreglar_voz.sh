#!/bin/bash
# Script todo-en-uno para arreglar el sistema de voz

echo "============================================================"
echo "   🔧 ARREGLO AUTOMÁTICO DEL SISTEMA DE VOZ"
echo "============================================================"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# 1. Solicitar nombre de usuario
echo "Para re-registrar tu voz, necesito tu nombre de usuario"
read -p "Nombre de usuario: " username

if [ -z "$username" ]; then
    echo -e "${RED}❌ Nombre de usuario vacío${NC}"
    exit 1
fi

echo ""
echo "Usuario: $username"
echo ""

# 2. Confirmar
echo -e "${YELLOW}⚠️  Esto eliminará los datos de voz antiguos de '$username'${NC}"
echo "Después podrás re-registrar tu voz en el formato nuevo"
read -p "¿Continuar? (s/n): " confirm

if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
    echo -e "${RED}❌ Operación cancelada${NC}"
    exit 0
fi

echo ""

# 3. Limpiar datos de voz
echo "🗑️  Limpiando datos de voz antiguos..."

python3 << EOF
import sqlite3

try:
    conn = sqlite3.connect('users_2fa.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE users SET voice_sample = NULL WHERE username = ?",
        ("$username",)
    )
    
    if cursor.rowcount > 0:
        conn.commit()
        print("✅ Datos de voz eliminados correctamente")
    else:
        print("⚠️  Usuario no encontrado o sin datos de voz")
    
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error al limpiar datos${NC}"
    exit 1
fi

echo ""

# 4. Desactivar vivacidad temporalmente (opcional)
echo "🔧 ¿Deseas desactivar temporalmente la detección de vivacidad?"
echo "   Esto hará más fácil el registro (puedes reactivarla después)"
read -p "Desactivar vivacidad? (s/n): " disable_liveness

if [ "$disable_liveness" = "s" ] || [ "$disable_liveness" = "S" ]; then
    if [ -f "config.py" ]; then
        # Hacer backup
        cp config.py config.py.backup.liveness
        
        # Desactivar vivacidad
        sed -i.bak 's/VOICE_ENABLE_LIVENESS = True/VOICE_ENABLE_LIVENESS = False/' config.py
        
        echo -e "${GREEN}✅ Vivacidad desactivada temporalmente${NC}"
        echo "   (Backup en config.py.backup.liveness)"
    else
        echo -e "${YELLOW}⚠️  Archivo config.py no encontrado${NC}"
    fi
fi

echo ""
echo "============================================================"
echo "   ✅ DATOS LIMPIADOS EXITOSAMENTE"
echo "============================================================"
echo ""
echo "📝 SIGUIENTE PASO: Re-registrar tu voz"
echo ""
echo "Ejecuta:"
echo "  python main.py"
echo ""
echo "Luego:"
echo "  1. Iniciar sesión con '$username' y contraseña"
echo "  2. Elegir 'Añadir nuevo método 2FA'"
echo "  3. Seleccionar 'Reconocimiento de voz'"
echo "  4. Seguir las instrucciones"
echo ""

if [ "$disable_liveness" = "s" ] || [ "$disable_liveness" = "S" ]; then
    echo "⚠️  Recuerda reactivar la vivacidad después:"
    echo "   Edita config.py y cambia:"
    echo "   VOICE_ENABLE_LIVENESS = False → True"
    echo ""
fi

echo "============================================================"
echo ""