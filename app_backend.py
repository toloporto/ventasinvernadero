import json
import time
from flask import Flask, jsonify, request, send_file, make_response
from flask_cors import CORS
from functools import wraps
from datetime import datetime, timedelta
import jwt

# 🚨 NUEVA IMPORTACIÓN: Deta
from deta import Deta 

app = Flask(__name__)

# --- Configuración de Deta Base ---
# Deta inyecta el proyecto key automáticamente.
deta = Deta()
db_cultivos = deta.Base("cultivos_db")
db_usuarios = deta.Base("usuarios_db")

# --- Configuración de Seguridad y CORS ---
# Deta te dará un dominio público final (ej: https://[nombre-proyecto].deta.app)
# Usaremos un placeholder seguro para CORS por ahora, lo ajustaremos en el frontend.
DUMMY_DOMAIN = "https://tu-proyecto.deta.app" 
SECRET_KEY = 'tu_clave_secreta_aqui' # Usa una clave segura y cámbiala
app.config['SECRET_KEY'] = SECRET_KEY

# Configuración de CORS
CORS(app, 
     resources={r"/*": {"origins": DUMMY_DOMAIN, 
                       "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}}, 
     supports_credentials=True)

# --- Funciones de Persistencia (Ahora usan Deta Base) ---

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

def cargar_cultivos():
    """Carga todos los ítems de la base de datos de cultivos (incluye el 'key' como 'id')."""
    # fetch devuelve los resultados como una lista de diccionarios
    res = db_cultivos.fetch()
    # Reemplazamos 'key' por 'id' para compatibilidad con el frontend
    cultivos = [{'id': item['key'], **{k: v for k, v in item.items() if k != 'key'}} for item in res.items]
    return cultivos

def cargar_usuarios():
    """Carga todos los ítems de la base de datos de usuarios."""
    res = db_usuarios.fetch()
    return res.items

# --- Rutas del Frontend (Servir la Interfaz de Usuario) ---
# Deta Space maneja el servir archivos estáticos con su "public folder", 
# pero mantenemos estas rutas si el frontend está en la carpeta raíz.

@app.route('/', methods=['GET'])
def servir_index():
    """Sirve la página principal (index.html) que contiene la aplicación."""
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
    usuarios = cargar_usuarios()
    
    if any(u['username'] == data['username'] for u in usuarios):
        return jsonify({'message': 'El usuario ya existe'}), 400
    
    # Guardar en Deta Base (Deta asigna el ID)
    db_usuarios.put(data)
    
    return jsonify({'message': 'Registro exitoso'}), 201

@app.route('/auth/login', methods=['POST'])
def login():
    """Endpoint para iniciar sesión."""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    usuarios = cargar_usuarios()
    user = next((u for u in usuarios if u['username'] == username and u['password'] == password), None)
    
    if user:
        token_payload = {
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm="HS256")
        
        response = make_response(jsonify({'message': 'Inicio de sesión exitoso'}))
        # samesite='None' es CRÍTICO para CORS
        response.set_cookie(
            'token', 
            token, 
            httponly=True, 
            secure=True, 
            samesite='None', 
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
    cultivos = cargar_cultivos()
    return jsonify(cultivos)

@app.route('/api/v1/cultivos', methods=['POST'])
@token_required
def crear_cultivo():
    """Crea un nuevo cultivo y lo guarda en Deta Base."""
    data = request.json
    
    # Deta Base genera el ID (key)
    item = db_cultivos.put(data)
    
    # Devolvemos el ítem creado con el ID
    response_item = {'id': item['key'], **{k: v for k, v in item.items() if k != 'key'}}
    return jsonify(response_item), 201

@app.route('/api/v1/cultivos/<cultivo_id>', methods=['PUT'])
@token_required
def actualizar_cultivo(cultivo_id):
    """Actualiza un cultivo existente usando su ID (key)."""
    updates = request.json
    
    # No se puede actualizar el 'id', solo los campos
    updates.pop('id', None) 
    
    # Actualiza el ítem en Deta Base usando el ID como key
    db_cultivos.update(updates, key=cultivo_id)
    
    return jsonify({'message': f'Cultivo {cultivo_id} actualizado'}), 200

@app.route('/api/v1/cultivos/<cultivo_id>', methods=['DELETE'])
@token_required
def eliminar_cultivo(cultivo_id):
    """Elimina un cultivo usando su ID (key)."""
    
    # Borra el ítem de Deta Base usando el ID como key
    db_cultivos.delete(cultivo_id)
    
    return jsonify({'message': f'Cultivo {cultivo_id} eliminado'}), 200

if __name__ == '__main__':
    app.run(debug=True)