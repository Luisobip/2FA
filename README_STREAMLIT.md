# Sistema 2FA Biométrico - Interfaz Web con Streamlit

## 🚀 Descripción

Aplicación web moderna para autenticación de doble factor (2FA) con reconocimiento facial y de voz, construida con Streamlit.

## ✨ Características

- **👤 Reconocimiento Facial** - Captura y verificación de rostros con detección de vivacidad
- **🎤 Reconocimiento de Voz** - Sistema challenge-response independiente del texto
- **👆 Touch ID** - Autenticación biométrica en macOS (opcional)
- **🔐 Autenticación 2FA** - Doble capa de seguridad: credenciales + biometría
- **🌐 Interfaz Web** - UI moderna y responsiva con Streamlit

## 📦 Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Verificar instalación

Asegúrate de que todas las dependencias estén instaladas:

```bash
python -c "import streamlit, cv2, face_recognition, librosa, sounddevice; print('✅ Todas las dependencias instaladas')"
```

## 🎯 Uso

### Iniciar la aplicación web

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador en `http://localhost:8501`

### Terminal (versión original)

Si prefieres usar la versión de terminal:

```bash
python main.py
```

## 📖 Guía de uso

### Registro de nuevo usuario

1. En la página principal, haz clic en **"¿No tienes cuenta? Regístrate aquí"**
2. Completa el formulario con:
   - Nombre de usuario
   - Contraseña (mínimo 6 caracteres)
   - Confirmación de contraseña
   - Selección de métodos 2FA deseados
3. Configura los métodos biométricos:
   - **Facial**: Toma una foto clara de tu rostro
   - **Voz**: Graba 5 muestras diciendo secuencias de números aleatorias

### Inicio de sesión

1. Ingresa tu nombre de usuario y contraseña
2. Selecciona el método biométrico para verificar
3. Completa el desafío biométrico:
   - **Facial**: Toma una foto de tu rostro
   - **Voz**: Di la secuencia de números que aparece en pantalla

### Dashboard

Una vez autenticado:
- **Añadir/Re-registrar métodos 2FA** - Agrega nuevos métodos o actualiza los existentes
- **Cerrar sesión** - Finaliza tu sesión actual

## 🔧 Configuración

### Ajustar umbrales

Edita el archivo `config.py` para personalizar:

```python
# Reconocimiento facial
FACE_RECOGNITION_TOLERANCE = 0.5  # Menor = más estricto

# Reconocimiento de voz
VOICE_SIMILARITY_THRESHOLD = 0.75  # Mayor = más estricto
VOICE_DURATION = 5  # Segundos de grabación
```

### Tipo de desafío de voz

En `config.py`:

```python
VOICE_CHALLENGE_TYPE = 'numeric'  # Opciones: 'numeric', 'phonetic', 'sentence'
```

## 🛠️ Tecnologías utilizadas

- **Streamlit** - Framework de aplicaciones web
- **OpenCV** - Procesamiento de imágenes y video
- **face_recognition** - Reconocimiento facial
- **librosa** - Procesamiento de audio
- **sounddevice** - Captura de audio
- **bcrypt** - Hashing seguro de contraseñas
- **SQLite** - Base de datos embebida

## 🔒 Seguridad

- Las contraseñas se almacenan hasheadas con bcrypt
- Los encodings faciales se normalizan para prevenir ataques
- El sistema de voz usa challenge-response para prevenir replay attacks
- Todos los intentos de login se registran para auditoría

## 📝 Estructura del proyecto

```
2FA/
├── app.py                 # Aplicación web Streamlit
├── main.py               # Versión terminal
├── auth_system.py        # Sistema de autenticación
├── facial_auth.py        # Reconocimiento facial
├── voice_auth.py         # Reconocimiento de voz
├── touchid_auth.py       # Touch ID (macOS)
├── database.py           # Gestión de base de datos
├── config.py             # Configuración
├── challenge_generator.py # Generador de desafíos
├── requirements.txt      # Dependencias
└── users_2fa.db         # Base de datos SQLite
```

## 🐛 Solución de problemas

### La cámara no funciona en Streamlit

Streamlit usa `st.camera_input()` que requiere permisos de cámara en el navegador. Asegúrate de permitir el acceso cuando el navegador lo solicite.

### El micrófono no graba

Verifica que Python tenga permisos de micrófono en:
- **macOS**: Preferencias del Sistema → Seguridad y Privacidad → Micrófono
- **Windows**: Configuración → Privacidad → Micrófono

### Error al cargar modelos DNN

Los modelos de detección facial se descargan automáticamente. Si falla:

```bash
mkdir -p models
# Descarga manual desde:
# https://github.com/opencv/opencv/blob/master/samples/dnn/face_detector/
```

## 📄 Licencia

Este proyecto es de código abierto para fines educativos.

## 👨‍💻 Autor

Bernardo Quindimil

## 🙏 Agradecimientos

- OpenCV por los modelos de detección facial
- face_recognition por la librería de reconocimiento
- Streamlit por el framework de aplicaciones web
