# Sistema 2FA Biométrico con Flask + Socket.IO

Sistema de autenticación de dos factores (2FA) con verificación biométrica en tiempo real usando Flask, Socket.IO y OpenCV.

## 🌟 Características

- **Autenticación de usuario** con contraseña
- **Verificación facial** con detección de vivacidad (liveness detection)
- **Streaming de video en tiempo real** sin lag usando Socket.IO
- **Detección anti-spoofing**: parpadeo de ojos y apertura de boca
- **Interfaz web moderna** y responsive
- **Sistema tolerante a gestos** que mantiene el progreso durante expresiones faciales

## 🚀 Inicio Rápido

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Ejecutar la aplicación

```bash
python app_flask.py
```

### 3. Abrir en el navegador

Visita: **http://localhost:5001**

## 📖 Guía de Uso

### Registro de Usuario

1. Haz clic en "Regístrate aquí"
2. Ingresa un nombre de usuario y contraseña
3. Serás redirigido a configurar métodos biométricos

### Configurar Verificación Facial

1. Haz clic en "📹 Registrar Rostro"
2. Permite el acceso a tu cámara
3. Coloca tu rostro frente a la cámara
4. Espera a que el recuadro se ponga **verde**
5. Haz clic en "Capturar Rostro"

### Iniciar Sesión con 2FA

1. Ingresa tu usuario y contraseña
2. Selecciona "Verificación Facial"
3. La cámara se abrirá en el navegador
4. Sigue las instrucciones:
   - ✓ Espera a que se detecte y verifique tu rostro
   - ✓ **Parpadea** (cierra y abre los ojos)
   - ✓ **Abre y cierra la boca**
5. Una vez completadas las 3 verificaciones, accederás al dashboard

### Añadir/Actualizar Métodos Biométricos

1. Desde el dashboard, haz clic en "⚙️ Configurar Métodos Biométricos"
2. Verás el estado actual de tus métodos
3. Puedes actualizar o añadir nuevos métodos en cualquier momento

## 🔧 Arquitectura Técnica

### Backend (Flask + Socket.IO)

- **Flask**: Framework web principal
- **Socket.IO**: Comunicación bidireccional en tiempo real
- **OpenCV**: Procesamiento de video y detección facial
- **face_recognition**: Reconocimiento facial basado en dlib
- **bcrypt**: Hash seguro de contraseñas
- **SQLite**: Base de datos para usuarios y encodings

### Frontend

- **HTML/CSS**: Interfaz moderna con gradientes
- **JavaScript**: Manejo de webcam y Socket.IO
- **Socket.IO Client**: Streaming de video al servidor

### Flujo de Verificación Facial

```
1. Cliente captura frame de la webcam (10 FPS)
2. Frame se convierte a base64 y se envía por Socket.IO
3. Servidor procesa frame:
   - Detecta rostro con DNN
   - Verifica identidad con face_recognition
   - Detecta gestos de vivacidad (EAR/MAR)
4. Servidor envía estado actualizado al cliente
5. Cliente actualiza UI en tiempo real
```

### Sistema de Tolerancia a Gestos

El sistema implementa un mecanismo tolerante que:

- **Mantiene el progreso** cuando haces gestos extremos
- **Decremento gradual** en lugar de reseteo total
- **Protección de estado** una vez verificada la identidad
- No pierde el progreso por pérdida temporal de detección

## 📊 Detección de Vivacidad

### Eye Aspect Ratio (EAR)
- Detecta parpadeo mediante el ratio de aspecto del ojo
- Umbral: **0.15**
- Detecta transición: abierto → cerrado → abierto

### Mouth Aspect Ratio (MAR)
- Detecta apertura de boca
- Umbral: **0.26**
- Detecta transición: cerrada → abierta → cerrada

## 🔒 Seguridad

- Contraseñas hasheadas con bcrypt
- Sesiones seguras con tokens
- Verificación en dos pasos (contraseña + biometría)
- Anti-spoofing con detección de vivacidad
- No se almacenan imágenes, solo encodings matemáticos

## 🎨 Interfaz de Usuario

### Páginas Disponibles

| Ruta | Descripción |
|------|-------------|
| `/` | Redirecciona a login o dashboard |
| `/login` | Inicio de sesión |
| `/register` | Registro de nuevos usuarios |
| `/verify_2fa` | Selección de método 2FA |
| `/facial_verification` | Verificación facial con streaming |
| `/facial_registration` | Registro de rostro |
| `/setup_biometrics` | Configuración de métodos biométricos |
| `/dashboard` | Dashboard del usuario autenticado |
| `/logout` | Cerrar sesión |

## 📱 Compatibilidad

- ✅ Chrome/Edge (mejor compatibilidad)
- ✅ Firefox
- ✅ Safari (requiere permisos de cámara)
- ✅ Responsive (funciona en desktop y móvil)

## ⚙️ Configuración

### Ajustar parámetros de detección

Edita `config.py`:

```python
FACE_RECOGNITION_TOLERANCE = 0.5  # Menor = más estricto
```

Edita `facial_auth.py`:

```python
self.EAR_THRESHOLD = 0.15  # Umbral de parpadeo
self.MAR_THRESHOLD = 0.26  # Umbral de boca
```

### Cambiar FPS de streaming

Edita `templates/facial_verification.html`:

```javascript
frameInterval = setInterval(() => {
    // Enviar frames cada 100ms (10 FPS)
    socket.emit('video_frame', { image: imageData });
}, 100);
```

## 🐛 Solución de Problemas

### La cámara no se activa

1. Verifica permisos de cámara en tu navegador
2. En macOS: Preferencias del Sistema → Privacidad → Cámara
3. Asegúrate de que no haya otra aplicación usando la cámara

### Error "sequence index must be integer"

Este error se solucionó almacenando el historial en el objeto `state` en lugar de usar `deque`.

### Pérdida de progreso al hacer gestos

El sistema ahora es tolerante - mantiene el progreso durante gestos extremos.

## 📝 Diferencias con Streamlit

| Aspecto | Streamlit | Flask + Socket.IO |
|---------|-----------|-------------------|
| **Video en tiempo real** | ❌ Lag significativo | ✅ Sin lag (10 FPS) |
| **Compatibilidad cámara** | ❌ Problemas frecuentes | ✅ Nativa con WebRTC |
| **Control de UI** | ❌ Limitado | ✅ Control total |
| **Velocidad** | ❌ Recarga páginas | ✅ Actualización en tiempo real |
| **Producción** | ❌ No recomendado | ✅ Escalable |

## 👥 Autores

Sistema desarrollado con Claude Code

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.
