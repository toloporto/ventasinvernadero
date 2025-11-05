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
COPY index.html .
COPY scripts.js .
COPY styles.css .

# Render prefiere el puerto 10000 si usas $PORT
EXPOSE 10000

# El comando para iniciar el servidor (usa Gunicorn)
# Render inyectará el valor de $PORT automáticamente.
CMD ["gunicorn", "app_backend:app", "--bind", "0.0.0.0:$PORT"]