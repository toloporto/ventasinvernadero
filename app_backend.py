import json
import time
from flask import Flask, jsonify, request, send_file, make_response
from flask_cors import CORS
from functools import wraps
from datetime import datetime, timedelta
import jwt
import os # Necesario para crear la carpeta si no existe

app = Flask(__name__)

# --- Rutas de Archivos (Persistencia para Fly.io) ---
# 🚨 CRÍTICO: Usamos la ruta del VOLUMEN PERSISTENTE de Fly.io
RUTA_PERSISTENCIA = '/vol/data'
RUTA_DATOS_CULTIVOS = os.path.join(RUTA_PERSISTENCIA, 'cultivos.json')
RUTA_DATOS_USUARIOS = os.path.join(RUTA_PERSISTENCIA, 'usuarios.json')

# Aseguramos que la carpeta exista al iniciar
os.makedirs(RUTA_PERSISTENCIA, exist_ok=True)


# --- Configuración de Seguridad y CORS ---
# 🚨 CRÍTICO: Reemplaza con tu dominio real de Fly.io (ej: https://ventas-invernadero.fly.dev)
FLYIO_DOMAIN = "https://[TU-APP-FLYIO].fly.dev" 
SECRET_KEY = 'tu_clave_secreta_aqui' 
app.config['SECRET_KEY'] = SECRET_KEY

# Configuración de CORS
CORS(app, 
     resources={r"/*": {"origins": FLYIO_DOMAIN, 
                       "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}}, 
     supports_credentials=True)

# --- Funciones de Persistencia (Volvemos a JSON) ---

def cargar_datos(ruta):
    """Carga datos de un archivo JSON, o devuelve una lista vacía si no existe."""
    try:
        with open(ruta, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        # Esto puede ocurrir si el archivo está vacío.
        return []

def guardar_datos(datos, ruta):
    """Guarda datos en un archivo JSON."""
    with open(ruta, 'w') as f:
        json.dump(datos, f, indent=4)

def get_next_id(datos):
    """Calcula el siguiente ID basado en la lista actual."""
    if not datos:
        return 1
    # Asume que el ID es un entero
    return max(item.get('id', 0) for item in datos) + 1

# --- Token Required (Se mantiene igual) ---

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
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido'}), 401
        return f(*args, **kwargs)
    return decorated

# --- Rutas del Frontend (Servir la Interfaz de Usuario) ---

@app.route('/', methods=['GET'])
def servir_index():
    """Sirve la página principal (index.html)."""
    try:
        return send_file('index.html')
    except FileNotFoundError:
        return "Error: index.html no encontrado.", 404

@app.route('/<path:path>', methods=['GET'])
def servir_recursos(path):
    """Sirve archivos estáticos (scripts.js, styles.css)."""
    try:
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
    
    # Nota: No necesitamos ID para el usuario.
    usuarios.append(data)
    guardar_datos(usuarios, RUTA_DATOS_USUARIOS)
    
    return jsonify({'message': 'Registro exitoso'}), 201

@app.route('/auth/login', methods=['POST'])
def login():
    """Endpoint para iniciar sesión."""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    usuarios = cargar_datos(RUTA_DATOS_USUARIOS)
    user = next((u for u in usuarios if u['username'] == username and u['password'] == password), None)
    
    if user:
        token_payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm="HS256")
        
        response = make_response(jsonify({'message': 'Inicio de sesión exitoso'}))
        response.set_cookie(
            'token', 
            token, 
            httponly=True, 
            secure=True, 
            samesite='None', # CRÍTICO para CORS
            expires=datetime.now() + timedelta(hours=24)
        )
        return response, 200
    
    return jsonify({'message': 'Credenciales inválidas'}), 401

@app.route('/auth/logout', methods=['POST'])
def logout():
    """Endpoint para cerrar sesión."""
    response = make_response(jsonify({'message': 'Sesión cerrada'}))
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

@app.route('/api/v1/cultivos', methods=['POST'])
@token_required
def crear_cultivo():
    """Crea un nuevo cultivo y lo guarda en el volumen persistente."""
    data = request.json
    cultivos = cargar_datos(RUTA_DATOS_CULTIVOS)
    
    data['id'] = get_next_id(cultivos)
    cultivos.append(data)
    guardar_datos(cultivos, RUTA_DATOS_CULTIVOS)
    
    return jsonify(data), 201

@app.route('/api/v1/cultivos/<int:cultivo_id>', methods=['PUT'])
@token_required
def actualizar_cultivo(cultivo_id):
    """Actualiza un cultivo existente."""
    updates = request.json
    cultivos = cargar_datos(RUTA_DATOS_CULTIVOS)
    
    for i, cultivo in enumerate(cultivos):
        if cultivo.get('id') == cultivo_id:
            # Mantener el ID original, actualizar el resto
            updates.pop('id', None) 
            cultivos[i].update(updates)
            guardar_datos(cultivos, RUTA_DATOS_CULTIVOS)
            return jsonify({'message': f'Cultivo {cultivo_id} actualizado', 'cultivo': cultivos[i]}), 200
    
    return jsonify({'message': 'Cultivo no encontrado'}), 404

@app.route('/api/v1/cultivos/<int:cultivo_id>', methods=['DELETE'])
@token_required
def eliminar_cultivo(cultivo_id):
    """Elimina un cultivo."""
    cultivos = cargar_datos(RUTA_DATOS_CULTIVOS)
    cultivos = [c for c in cultivos if c.get('id') != cultivo_id]
    guardar_datos(cultivos, RUTA_DATOS_CULTIVOS)
    
    return jsonify({'message': f'Cultivo {cultivo_id} eliminado'}), 200

if __name__ == '__main__':
    app.run(debug=True)