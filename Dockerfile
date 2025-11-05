# Dockerfile

# Usamos la última versión estable de Python
FROM python:3.12-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de requerimientos e instálalos
# CRÍTICO: Debes tener instalado PyJWT y Flask
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación, incluyendo el backend y el JSON de datos
COPY app_backend.py .
# Los JSON iniciales (solo se usan si el volumen está vacío al inicio)
COPY cultivos.json .
COPY index.html .
COPY scripts.js .
COPY styles.css .

# 🚨 CRÍTICO para Fly.io: Usamos el puerto estándar 8080
EXPOSE 8080

# El comando para iniciar el servidor (usa Gunicorn)
# Usamos el formato de array y puerto fijo para evitar errores de shell
CMD ["gunicorn", "app_backend:app", "--bind", "0.0.0.0:8080"]