FROM python:3.11-slim AS builder
WORKDIR /app

# Instalar dependencias del sistema necesarias para OpenCV, face_recognition y librosa
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ffmpeg \
        libsndfile1 \
        portaudio19-dev \
        build-essential \
        cmake \
        libopencv-dev \
        libgl1 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Copiar requisitos e instalar
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Stage final
FROM python:3.11-slim
WORKDIR /app

# Instalar librerías de runtime necesarias
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        portaudio19-dev \
        libgl1 \
        libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Copiar paquetes instalados y código
COPY --from=builder /usr/local /usr/local
COPY . .

# Crear directorio para datos persistentes
RUN mkdir -p /app/data

# Crear usuario no-root
RUN groupadd -r app && useradd -r -g app app && \
    chown -R app:app /app
USER app

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app_flask.py
ENV DATABASE_NAME=/app/data/users_2fa.db
ENV NUMBA_CACHE_DIR=/tmp
ENV NUMBA_DISABLE_JIT=0

# Volumen para datos persistentes
VOLUME /app/data

# Exponer puerto 5001
EXPOSE 5001

# Comando para ejecutar la aplicación Flask
CMD ["python", "app_flask.py"]
