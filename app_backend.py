import json
import time
from flask import Flask, jsonify, request, send_file, make_response
from flask_cors import CORS
from functools import wraps
from datetime import datetime, timedelta
import jwt

app = Flask(__name__)

# --- Configuración de Seguridad y CORS ---
# Usar tu nombre de servicio elegido en Render:
RENDER_DOMAIN = "https://ventas-invernadero-antolin.onrender.com" # <--- ¡CÁMBIALO!
SECRET_KEY = 'tu_clave_secreta_aqui' # Usa una clave segura y cámbiala
app.config['SECRET_KEY'] = SECRET_KEY

# Configuración de CORS con tu dominio de Render
CORS(app, 
     resources={r"/*": {"origins": RENDER_DOMAIN, 
                       "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}}, 
     supports_credentials=True)

# --- Rutas de Archivos (Modificadas para Render sin Volúmenes) ---
# 🚨 ADVERTENCIA: Los datos se perderán cuando el servicio de Render se reinicie por inactividad.
RUTA_DATOS_CULTIVOS = 'cultivos.json'
RUTA_DATOS_USUARIOS = 'usuarios.json'

# --- Funciones de Utilidad ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'token' in request.cookies:
            token = request.cookies.get('token')

        if not token:
            return jsonify({'message': 'Token de autenticación faltante'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            # Opcional: cargar el usuario si es necesario
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido'}), 401

        return f(*args, **kwargs)
    return decorated

def cargar_datos(ruta):
    """Carga datos de un archivo JSON, o devuelve una lista vacía si el archivo no existe."""
    try:
        with open(ruta, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        # Esto puede ocurrir si el archivo está vacío o mal formado.
        return []

def guardar_datos(datos, ruta):
    """Guarda datos en un archivo JSON."""
    with open(ruta, 'w') as f:
        json.dump(datos, f, indent=4)

# --- Rutas del Frontend (Servir la Interfaz de Usuario) ---
@app.route('/', methods=['GET'])
def servir_index():
    """Sirve la página principal (index.html) que contiene la aplicación."""
    try:
        # Suponiendo que index.html está en el mismo directorio raíz del contenedor
        return send_file('index.html')
    except FileNotFoundError:
        return "Error: index.html no encontrado.", 404

@app.route('/<path:path>', methods=['GET'])
def servir_recursos(path):
    """Sirve archivos estáticos (scripts.js, styles.css)."""
    try:
        # Intenta servir archivos estáticos (scripts.js, styles.css, etc.)
        return send_file(path)
    except FileNotFoundError:
        return "Recurso no encontrado.", 404

# --- Rutas de Autenticación ---
@app.route('/auth/register', methods=['POST'])
def register():
    """Endpoint para registrar un nuevo usuario."""
    data = request.json
    usuarios = cargar_datos(RUTA_DATOS_USUARIOS)
    
    if any(u['username'] == data['username'] for u in usuarios):
        return jsonify({'message': 'El usuario ya existe'}), 400
    
    # Nota: En producción real, la contraseña debe ser hasheada
    usuarios.append(data)
    guardar_datos(usuarios, RUTA_DATOS_USUARIOS)
    
    return jsonify({'message': 'Registro exitoso'}), 201

@app.route('/auth/login', methods=['POST'])
def login():
    """Endpoint para iniciar sesión y emitir un token JWT."""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    usuarios = cargar_datos(RUTA_DATOS_USUARIOS)
    user = next((u for u in usuarios if u['username'] == username and u['password'] == password), None)
    
    if user:
        # Generar Token JWT con expiración de 24 horas
        token_payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm="HS256")
        
        # Crear la respuesta y establecer la cookie
        response = make_response(jsonify({'message': 'Inicio de sesión exitoso'}))
        response.set_cookie(
            'token', 
            token, 
            httponly=True, 
            secure=True, 
            samesite='None', # CRÍTICO para CORS entre dominios Render
            expires=datetime.now() + timedelta(hours=24)
        )
        return response, 200
    
    return jsonify({'message': 'Credenciales inválidas'}), 401

@app.route('/auth/logout', methods=['POST'])
def logout():
    """Endpoint para cerrar sesión y eliminar el token JWT."""
    response = make_response(jsonify({'message': 'Sesión cerrada'}))
    # Eliminar la cookie
    response.set_cookie(
        'token', 
        '', 
        httponly=True, 
        secure=True, 
        samesite='None',
        expires=0
    )
    return response, 200

# --- Rutas de API (CRUD de Cultivos) ---
@app.route('/api/v1/cultivos', methods=['GET'])
@token_required
def obtener_cultivos():
    """Obtiene la lista completa de cultivos."""
    cultivos = cargar_datos(RUTA_DATOS_CULTIVOS)
    return jsonify(cultivos)

# ... (otras rutas PUT, POST, DELETE irían aquí y usarían token_required) ...

if __name__ == '__main__':
    # Esta parte no se usa en Gunicorn, pero es buena para pruebas locales.
    app.run(debug=True)