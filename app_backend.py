import os
import json
import uuid
import datetime
from functools import wraps 
# Importaciones clave
from werkzeug.security import generate_password_hash, check_password_hash 
# Se añade send_from_directory para servir el frontend
from flask import Flask, request, jsonify, make_response, send_from_directory 
from flask_cors import CORS

# --- CONFIGURACIÓN DE PERSISTENCIA ---
RUTA_DATOS_CULTIVOS = '/vol/data/cultivos.json' 
RUTA_DATOS_USUARIOS = '/vol/data/usuarios.json' 

app = Flask(__name__)

# 🚩 CONFIGURACIÓN CORS (CORRECCIÓN FINAL):
# 1. supports_credentials=True está fuera del diccionario resources. (CORREGIDO el TypeError 502)
# 2. origins usa el dominio EXACTO (para solucionar el error de conexión de API con cookies).
# CORS(app, 
     #resources={r"/*": {"origins": "https://nombre-unico-de-tu-api-flask.fly.dev", 
                       #"methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}}, 
     #supports_credentials=True)
# CÁMBIALO A ESTO TEMPORALMENTE (PERMITE CUALQUIER ORIGEN)
#CORS(app, 
     #resources={r"/*": {"origins": "*", 
                       #"methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}}, 
     #supports_credentials=True)

     # app_backend.py (Línea de CORS)
CORS(app, 
     resources={r"/*": {"origins": "https://web-production-8930b.up.railway.app", # <-- ¡DOMINIO RAILWAY!
                       "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]}}, 
     supports_credentials=True)

# Variables globales para los datos
CULTIVOS = [] 
USUARIOS = [] 

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

# --- MANEJO DE USUARIOS (EXISTENTE) ---

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

# -------------------------------------
# --- MIDDLEWARE DE AUTENTICACIÓN CON COOKIE ---
# -------------------------------------

def token_requerido(f):
    """
    Decorador que verifica la existencia y validez de la 'session_token' 
    en las cookies de la petición.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Intentar obtener el token de la cookie
        token_usuario_id = request.cookies.get('session_token') # <-- Buscamos el token en la cookie
        
        if not token_usuario_id:
            # No hay token en la cookie: No autenticado
            return jsonify({'error': 'No autenticado. Inicie sesión.'}), 401
        
        # 2. Verificar que el token (que es el ID de usuario) sea válido
        usuario_actual = next((u for u in USUARIOS if u['id'] == token_usuario_id), None)
        
        if not usuario_actual:
            # Token inválido o ID de usuario no existe
            return jsonify({'error': 'Token inválido o sesión expirada'}), 401
        
        # Guardamos el usuario para usarlo si es necesario
        request.current_user = usuario_actual 
        
        # Continuar con la función de la ruta original
        return f(*args, **kwargs)

    return decorated


# ----------------------------------
# --- RUTAS DE AUTENTICACIÓN ---
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
        return jsonify({"error": "El usuario ya existe"}), 409 

    # 2. Hashear la contraseña (Seguridad)
    hashed_password = generate_password_hash(contraseña)

    # 3. Crear nuevo usuario y guardar
    nuevo_usuario = {
        'id': str(uuid.uuid4()),
        'usuario': usuario,
        'contraseña_hash': hashed_password 
    }
    
    USUARIOS.append(nuevo_usuario)
    guardar_usuarios()
    
    return jsonify({"mensaje": f"Usuario {usuario} registrado con éxito"}), 201

@app.route('/auth/login', methods=['POST'])
def login():
    """Ruta para iniciar sesión. Devuelve una cookie HttpOnly con el ID de usuario."""
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
            
            # --- CONFIGURACIÓN DE LA COOKIE ---
            token_valor = user['id'] 
            
            # 3. Creamos la respuesta con el mensaje de éxito
            response = make_response(jsonify({"mensaje": "Inicio de sesión exitoso", "usuario": usuario}), 200)

            # 4. Configuramos la Cookie Segura (espacios limpiados para evitar SyntaxError U+00A0)
            response.set_cookie(
                'session_token',              # Nombre de la cookie
                token_valor,                  # Valor (el ID de usuario)
                httponly=True,                # Impide acceso desde JS (SEGURIDAD)
                secure=True,                  # Solo se envía a través de HTTPS (SEGURIDAD)
                samesite='Lax',               # Funciona bien en peticiones CORS
                max_age=3600 * 24 * 7         # Caducidad: 7 días
            )
            
            return response # Devolvemos la respuesta con la cookie configurada
            # ------------------------------------------------
            
        else:
            return jsonify({"error": "Contraseña incorrecta"}), 401 
    else:
        return jsonify({"error": "Usuario no encontrado"}), 404 

# ----------------------------------
# --- RUTAS DE CULTIVOS (PROTEGIDAS) ---
# ----------------------------------

@app.route('/api/v1/cultivos', methods=['GET'])
@token_requerido # <-- PROTEGIDA
def listar_cultivos():
    """GET: Lista todos los cultivos."""
    return jsonify(CULTIVOS)

@app.route('/api/v1/cultivos', methods=['POST'])
@token_requerido # <-- PROTEGIDA
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

@app.route('/api/v1/cultivos/<id_cultivo>', methods=['PUT']) 
@token_requerido # <-- PROTEGIDA
def actualizar_cultivo(id_cultivo):
    """PUT: Actualiza un cultivo existente."""
    global CULTIVOS
    data = request.get_json()
    cultivo_encontrado = next((c for c in CULTIVOS if c.get('id') == id_cultivo), None)

    if not cultivo_encontrado:
        return jsonify({"error": "Cultivo no encontrado"}), 404

    # Actualizar solo los campos proporcionados
    for key, value in data.items():
        if key != 'id':
            cultivo_encontrado[key] = value

    guardar_cultivos()
    return jsonify({"mensaje": "Cultivo actualizado con éxito"}, cultivo_encontrado), 200

@app.route('/api/v1/cultivos/<id_cultivo>', methods=['DELETE'])
@token_requerido # <-- PROTEGIDA
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
        
# ----------------------------------------------------
# --- RUTAS PARA SERVIR EL FRONTEND (CORRECCIÓN 404) ---
# ----------------------------------------------------

# 1. Ruta principal para servir el index.html al acceder a la URL base
@app.route('/')
def serve_index():
    # Asume que index.html está en el directorio raíz del proyecto
    return send_from_directory('.', 'index.html')

# 2. Ruta genérica para servir archivos estáticos (js, css, etc.)
@app.route('/<path:filename>')
def serve_static(filename):
    # Asume que los archivos estáticos están en el directorio raíz del proyecto
    if os.path.exists(os.path.join('.', filename)):
        return send_from_directory('.', filename)
    else:
        # Devuelve el 404 si el archivo estático no se encuentra
        return jsonify({"error": f"Archivo estático {filename} no encontrado"}), 404

# ----------------------------------
# --- INICIALIZACIÓN ---
# ----------------------------------

# Cargar los datos al iniciar la aplicación (se ejecutan al inicio de Gunicorn)
cargar_cultivos()
cargar_usuarios() 

if __name__ == '__main__':
    # Esto es solo para ejecución local
    app.run(debug=True, host='0.0.0.0', port=5000)