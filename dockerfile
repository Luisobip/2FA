FROM python:3.11-slim AS builder
WORKDIR /app

# Instalar dependencias del sistema mínimas
RUN apt-get update && \
    apt-get install -y --no-install-recommends git ffmpeg build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copiar requisitos e instalar (y auditar)
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel pip-audit && \
    pip install --no-cache-dir -r requirements.txt && \
    pip-audit --fail-on=high

# Stage final más pequeño
FROM python:3.11-slim
WORKDIR /app

# Sólo copiar paquetes instalados y el código
COPY --from=builder /usr/local /usr/local
COPY . .

# Crear usuario no-root
RUN groupadd -r app && useradd -r -g app app && chown -R app:app /app
USER app

ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py"]