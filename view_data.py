import sqlite3

conn = sqlite3.connect("users_2fa.db")
cursor = conn.cursor()

# Listar todas las tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tablas = cursor.fetchall()
print("Tablas:", tablas)

# Ver contenido de cada tabla
for tabla in tablas:
    nombre_tabla = tabla[0]
    print(f"\nContenido de {nombre_tabla}:")
    cursor.execute(f"SELECT * FROM {nombre_tabla};")
    for row in cursor.fetchall():
        print(row)

conn.close()
