import subprocess
import cv2
import face_recognition as fr
import os
import numpy as np
from datetime import datetime

# limpiar .DS_Store
def clean_ds_store(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file == '.DS_Store':
                file_path = os.path.join(root, file)
                os.remove(file_path)
                print(f"Removed file: {file_path}")

# crear base de datos
ruta = 'Empleados'
mis_imagenes = []
nombres_empleados = []
lista_empleados = os.listdir(ruta)

clean_ds_store(ruta)

for nombre in lista_empleados:
    imagen_actual = cv2.imread(f'{ruta}/{nombre}')
    if imagen_actual is None:
        print(f"⚠️ No se pudo leer la imagen {nombre}")
        continue
    mis_imagenes.append(imagen_actual)
    nombres_empleados.append(os.path.splitext(nombre)[0])

print("Empleados en la base de datos:", nombres_empleados)

# codificar imagenes
def codificar(imagenes):
    lista_codificada = []
    for imagen in imagenes:
        imagen = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
        codificado = fr.face_encodings(imagen)
        if len(codificado) > 0:
            lista_codificada.append(codificado[0])
        else:
            print("⚠️ No se detectó un rostro en una imagen de la base de datos.")
    return lista_codificada

# registrar los ingresos
def registrar_ingresos(persona):
    with open('registro.csv', 'a+') as f:
        f.seek(0)
        lista_datos = f.readlines()
        nombres_registro = [linea.split(',')[0] for linea in lista_datos]

        if persona not in nombres_registro:
            ahora = datetime.now().strftime('%H:%M:%S')
            f.write(f'\n{persona}, {ahora}')

lista_empleados_codificada = codificar(mis_imagenes)

# Capturar una imagen usando imagesnap
subprocess.run(["imagesnap", "captura.jpg"])

# Leer la imagen capturada
imagen = cv2.imread("captura.jpg")

if imagen is None:
    print("❌ No se pudo tomar la captura")
    exit()
else:
    print('Si se ha tomado captura')
    # reconocer cara en captura
    cara_captura = fr.face_locations(imagen)
    print(f'Caras detectadas: {len(cara_captura)}')

    if len(cara_captura) == 0:
        print("⚠️ No se detectaron rostros en la imagen capturada.")
    else:
        # codificar cara capturada
        cara_captura_codificada = fr.face_encodings(imagen, cara_captura)
        print(f'Caras codificadas: {len(cara_captura_codificada)}')

        # buscar coincidencias 
        for cara_codif, cara_ubic in zip(cara_captura_codificada, cara_captura):
            coincidencias = fr.compare_faces(lista_empleados_codificada, cara_codif)
            distancias = fr.face_distance(lista_empleados_codificada, cara_codif)
            print(f'Distancias: {distancias}')

            indice_coincidencia = np.argmin(distancias)

            # mostrar coincidencias si las hay
            if distancias[indice_coincidencia] > 0.5:
                print('No coincide con ninguno de nuestros empleados')
            else:
                # buscar el nombre del empleado encontrado
                nombre = nombres_empleados[indice_coincidencia]

                y1, x2, y2, x1 = cara_ubic
                cv2.rectangle(imagen, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(imagen, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(imagen, nombre, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

                registrar_ingresos(nombre)

                # mostrar la imagen obtenida
                cv2.imshow('Imagen web', imagen)

                # mantener ventana abierta
                cv2.waitKey(0)