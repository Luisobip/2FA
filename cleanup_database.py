"""
Script para limpiar y verificar la base de datos
"""

import sqlite3
from database import DatabaseManager
from config import Config

def analyze_database():
    """Analiza el estado actual de la base de datos"""
    print("\n" + "="*60)
    print("   ANÁLISIS DE BASE DE DATOS")
    print("="*60)
    
    conn = sqlite3.connect(Config.DATABASE_NAME)
    cursor = conn.cursor()
    
    # Verificar registros corruptos
    cursor.execute('''
        SELECT id, username, success, method, timestamp 
        FROM login_attempts 
        WHERE typeof(success) = 'blob'
    ''')
    corrupted = cursor.fetchall()
    
    if corrupted:
        print(f"\n⚠️  Se encontraron {len(corrupted)} registros con valores corruptos:")
        print("\nID | Usuario | Success | Método | Timestamp")
        print("-" * 60)
        for record in corrupted[:10]:  # Mostrar solo los primeros 10
            print(f"{record[0]} | {record[1]} | {record[2]} | {record[3]} | {record[4]}")
        if len(corrupted) > 10:
            print(f"... y {len(corrupted) - 10} registros más")
    else:
        print("\n✅ No se encontraron registros corruptos")
    
    # Estadísticas generales
    cursor.execute('SELECT COUNT(*) FROM login_attempts')
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM login_attempts WHERE success = 1')
    successful = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM login_attempts WHERE success = 0')
    failed = cursor.fetchone()[0]
    
    print("\n📊 Estadísticas generales:")
    print(f"   Total de intentos: {total}")
    print(f"   Exitosos: {successful}")
    print(f"   Fallidos: {failed}")
    print(f"   Corruptos: {len(corrupted)}")
    
    conn.close()
    return len(corrupted)

def clean_database():
    """Limpia los registros corruptos"""
    print("\n" + "="*60)
    print("   LIMPIEZA DE BASE DE DATOS")
    print("="*60)
    
    db = DatabaseManager()
    affected = db.clean_corrupted_records()
    
    if affected > 0:
        print(f"\n✅ Se limpiaron {affected} registros corruptos")
        print("   • b'\\x01' → 1 (éxito)")
        print("   • b'\\x00' → 0 (fallo)")
    else:
        print("\n✅ No había registros que limpiar")

def view_all_attempts():
    """Muestra todos los intentos de login"""
    print("\n" + "="*60)
    print("   HISTORIAL COMPLETO DE INTENTOS")
    print("="*60)
    
    conn = sqlite3.connect(Config.DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, success, method, timestamp 
        FROM login_attempts 
        ORDER BY timestamp DESC
    ''')
    
    attempts = cursor.fetchall()
    
    if attempts:
        print("\nID | Usuario | Éxito | Método | Timestamp")
        print("-" * 80)
        for attempt in attempts:
            success_str = "✅ SÍ" if attempt[2] == 1 else "❌ NO"
            print(f"{attempt[0]:3d} | {attempt[1]:15s} | {success_str:6s} | {attempt[3]:10s} | {attempt[4]}")
    else:
        print("\n📭 No hay intentos de login registrados")
    
    conn.close()

def view_user_stats():
    """Muestra estadísticas por usuario"""
    print("\n" + "="*60)
    print("   ESTADÍSTICAS POR USUARIO")
    print("="*60)
    
    conn = sqlite3.connect(Config.DATABASE_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT username,
               COUNT(*) as total,
               SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful,
               SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed
        FROM login_attempts
        GROUP BY username
        ORDER BY total DESC
    ''')
    
    stats = cursor.fetchall()
    
    if stats:
        print("\nUsuario | Total | Exitosos | Fallidos | Tasa de Éxito")
        print("-" * 70)
        for stat in stats:
            username, total, successful, failed = stat
            success_rate = (successful / total * 100) if total > 0 else 0
            print(f"{username:15s} | {total:5d} | {successful:8d} | {failed:8d} | {success_rate:6.1f}%")
    else:
        print("\n📭 No hay estadísticas disponibles")
    
    conn.close()

def main():
    """Menú principal"""
    while True:
        print("\n" + "="*60)
        print("   UTILIDAD DE GESTIÓN DE BASE DE DATOS")
        print("="*60)
        print("\n  1. 🔍 Analizar base de datos")
        print("  2. 🧹 Limpiar registros corruptos")
        print("  3. 📋 Ver todos los intentos de login")
        print("  4. 📊 Ver estadísticas por usuario")
        print("  5. 🚪 Salir")
        print("\n" + "="*60)
        
        choice = input("Elige una opción: ").strip()
        
        if choice == '1':
            analyze_database()
        elif choice == '2':
            corrupted_count = analyze_database()
            if corrupted_count > 0:
                confirm = input(f"\n¿Deseas limpiar {corrupted_count} registros? (s/n): ")
                if confirm.lower() == 's':
                    clean_database()
                    print("\n✅ Limpieza completada. Analizando de nuevo...")
                    analyze_database()
            else:
                print("\n✅ No hay nada que limpiar")
        elif choice == '3':
            view_all_attempts()
        elif choice == '4':
            view_user_stats()
        elif choice == '5':
            print("\n👋 ¡Hasta luego!\n")
            break
        else:
            print("❌ Opción no válida")

if __name__ == "__main__":
    main()