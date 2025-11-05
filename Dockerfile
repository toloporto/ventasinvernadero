# Dockerfile

# Usamos la última versión estable de Python
FROM python:3.12-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de requerimientos e instálalos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación, incluyendo el backend y el JSON de datos
COPY app_backend.py .
COPY cultivos.json .
# COPY app_frontend/ ./app_frontend/  # Aseguramos que la carpeta del frontend también se copie

# El comando para iniciar el servidor (usa Gunicorn)
# CMD gunicorn app_backend:app --bind 0.0.0.0:8080
# Cámbiala a:
CMD gunicorn app_backend:app --bind 0.0.0.0:$PORT