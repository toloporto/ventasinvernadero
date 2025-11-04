import os
import json
import uuid
import datetime
# NUEVAS IMPORTACIONES CLAVE para Autenticación
from werkzeug.security import generate_password_hash, check_password_hash 
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CONFIGURACIÓN DE PERSISTENCIA ---
RUTA_DATOS_CULTIVOS = '/vol/data/cultivos.json' 
# ¡Nueva ruta para los usuarios!
RUTA_DATOS_USUARIOS = '/vol/data/usuarios.json' 

app = Flask(__name__)
# 🚩 CORRECCIÓN CORS: Configuración explícita y permisiva para asegurar que POST y OPTIONS funcionen en todos los endpoints
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}})

# Variables globales para los datos
CULTIVOS = [] 
USUARIOS = [] # Nueva variable global para usuarios

# -------------------------------------
# --- FUNCIONES DE MANEJO DE DATOS ---
# -------------------------------------

# --- MANEJO DE CULTIVOS (CRUD EXISTENTE) ---

def cargar_cultivos():
    """Carga los datos de cultivos. Crea el archivo y directorio si no existen."""
    global CULTIVOS
    data_dir = os.path.dirname(RUTA_DATOS_CULTIVOS)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        
    if not os.path.exists(RUTA_DATOS_CULTIVOS):
        with open(RUTA_DATOS_CULTIVOS, 'w', encoding='utf-8') as f:
            json.dump([], f)
        CULTIVOS = []
        return []
    
    try:
        with open(RUTA_DATOS_CULTIVOS, 'r', encoding='utf-8') as f:
            CULTIVOS = json.load(f)
            return CULTIVOS
    except json.JSONDecodeError:
        CULTIVOS = []
        return []

def guardar_cultivos():
    """Guarda la lista global CULTIVOS en el archivo JSON persistente."""
    try:
        with open(RUTA_DATOS_CULTIVOS, 'w', encoding='utf-8') as f:
            json.dump(CULTIVOS, f, indent=4)
        return True
    except Exception as e:
        print(f"Error al guardar cultivos: {e}")
        return False

# --- MANEJO DE USUARIOS (NUEVO) ---

def cargar_usuarios():
    """Carga los datos de usuarios del archivo JSON. Crea el archivo si no existe."""
    global USUARIOS
    data_dir = os.path.dirname(RUTA_DATOS_USUARIOS)
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        
    if not os.path.exists(RUTA_DATOS_USUARIOS):
        with open(RUTA_DATOS_USUARIOS, 'w', encoding='utf-8') as f:
            json.dump([], f)
        USUARIOS = []
        return []
    
    try:
        with open(RUTA_DATOS_USUARIOS, 'r', encoding='utf-8') as f:
            USUARIOS = json.load(f)
            return USUARIOS
    except json.JSONDecodeError:
        USUARIOS = []
        return []

def guardar_usuarios():
    """Guarda la lista global USUARIOS en el archivo JSON persistente."""
    try:
        with open(RUTA_DATOS_USUARIOS, 'w', encoding='utf-8') as f:
            json.dump(USUARIOS, f, indent=4)
        return True
    except Exception as e:
        print(f"Error al guardar usuarios: {e}")
        return False

# ----------------------------------
# --- RUTAS DE AUTENTICACIÓN (NUEVAS) ---
# ----------------------------------

@app.route('/auth/registro', methods=['POST'])
def registro():
    """Ruta para registrar un nuevo usuario."""
    data = request.get_json()
    usuario = data.get('usuario')
    contraseña = data.get('contraseña')

    if not usuario or not contraseña:
        return jsonify({"error": "Faltan usuario o contraseña"}), 400

    # 1. Verificar si el usuario ya existe
    if any(u['usuario'] == usuario for u in USUARIOS):
        return jsonify({"error": "El usuario ya existe"}), 409 # 409 Conflict

    # 2. Hashear la contraseña (Seguridad)
    hashed_password = generate_password_hash(contraseña)

    # 3. Crear nuevo usuario y guardar
    nuevo_usuario = {
        'id': str(uuid.uuid4()),
        'usuario': usuario,
        'contraseña_hash': hashed_password # Guardar el hash, no la contraseña original
    }
    
    USUARIOS.append(nuevo_usuario)
    guardar_usuarios()
    
    return jsonify({"mensaje": f"Usuario {usuario} registrado con éxito"}), 201

@app.route('/auth/login', methods=['POST'])
def login():
    """Ruta para iniciar sesión."""
    data = request.get_json()
    usuario = data.get('usuario')
    contraseña = data.get('contraseña')

    if not usuario or not contraseña:
        return jsonify({"error": "Faltan usuario o contraseña"}), 400

    # 1. Buscar usuario
    user = next((u for u in USUARIOS if u['usuario'] == usuario), None)

    if user:
        # 2. Verificar la contraseña hasheada
        if check_password_hash(user['contraseña_hash'], contraseña):
            return jsonify({"mensaje": "Inicio de sesión exitoso", "usuario": usuario}), 200
        else:
            return jsonify({"error": "Contraseña incorrecta"}), 401 # 401 Unauthorized
    else:
        return jsonify({"error": "Usuario no encontrado"}), 404 # 404 Not Found

# ----------------------------------
# --- RUTAS DE CULTIVOS (EXISTENTES) ---
# ----------------------------------

@app.route('/api/v1/cultivos', methods=['GET'])
def listar_cultivos():
    """GET: Lista todos los cultivos."""
    return jsonify(CULTIVOS)

@app.route('/api/v1/cultivos', methods=['POST'])
def agregar_cultivo():
    """POST: Agrega un nuevo cultivo."""
    try:
        data = request.get_json()
        if not all(k in data for k in ('nombre', 'fecha_siembra', 'fecha_cosecha')):
            return jsonify({"error": "Faltan campos requeridos (nombre, fecha_siembra, fecha_cosecha)"}), 400
        
        # Validación básica de existencia
        if any(c['nombre'] == data['nombre'] for c in CULTIVOS):
            return jsonify({"error": "El cultivo ya existe."}), 409
        
        nuevo_cultivo = data
        nuevo_cultivo['id'] = str(uuid.uuid4())
        
        CULTIVOS.append(nuevo_cultivo)
        guardar_cultivos() 
        
        return jsonify(nuevo_cultivo), 201
    except Exception as e:
        return jsonify({"error": f"Error interno al agregar: {str(e)}"}), 500

@app.route('/api/v1/cultivos/<id_cultivo>', methods=['DELETE'])
def eliminar_cultivo(id_cultivo):
    """DELETE: Elimina un cultivo por ID."""
    global CULTIVOS
    
    cultivos_antes = len(CULTIVOS)
    CULTIVOS = [c for c in CULTIVOS if c.get('id') != id_cultivo]
    
    if len(CULTIVOS) < cultivos_antes:
        guardar_cultivos() 
        return jsonify({"mensaje": f"Cultivo {id_cultivo} eliminado"}), 200
    else:
        return jsonify({"error": "Cultivo no encontrado"}), 404
        
# ----------------------------------
# --- INICIALIZACIÓN ---
# ----------------------------------

# Cargar los datos al iniciar la aplicación (se ejecutan al inicio de Gunicorn)
cargar_cultivos()
cargar_usuarios() # ¡NUEVO: Cargar los usuarios para la persistencia!

if __name__ == '__main__':
    # Esto es solo para ejecución local
    app.run(debug=True, host='0.0.0.0', port=5000)