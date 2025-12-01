# Imagen base con Python 3.11
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5001

# Instalar dependencias del sistema necesarias para face-recognition, dlib, opencv y audio
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libboost-python-dev \
    libboost-thread-dev \
    # Dependencias para OpenCV
    libopencv-dev \
    python3-opencv \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Dependencias para procesamiento de audio
    libsndfile1 \
    libportaudio2 \
    portaudio19-dev \
    ffmpeg \
    # Utilidades
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt
COPY requirements.txt .

# Instalar dependencias de Python
# Nota: face-recognition y dlib pueden tardar en compilar
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorio para datos persistentes
RUN mkdir -p /app/data

# Exponer el puerto
EXPOSE ${PORT}

# Comando por defecto para ejecutar la aplicación Flask
CMD ["python", "app_flask.py"]
