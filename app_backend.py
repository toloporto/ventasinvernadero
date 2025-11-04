import os
import json # Asegúrate de tener estas importaciones si tu código las usa
import uuid
import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CONFIGURACIÓN DE PERSISTENCIA ---
# ¡Ruta modificada para usar el Volume persistente de Fly.io!
RUTA_DATOS = '/vol/data/cultivos.json' 

app = Flask(__name__)
CORS(app) 

# Variable global para almacenar los datos en memoria al inicio.
CULTIVOS = [] 

# --- FUNCIONES DE MANEJO DE DATOS ---

def cargar_cultivos():
    """Carga los datos del archivo JSON. Crea el archivo y directorio si no existen."""
    global CULTIVOS
    
    # 1. Asegurar que el directorio del volumen existe
    data_dir = os.path.dirname(RUTA_DATOS)
    if not os.path.exists(data_dir):
        # En el primer inicio, /vol/data puede no existir, lo creamos de forma segura.
        os.makedirs(data_dir, exist_ok=True)
        
    # 2. Inicializar el archivo JSON si no existe
    if not os.path.exists(RUTA_DATOS):
        # Escribimos una lista JSON vacía para evitar JSONDecodeError al inicio
        with open(RUTA_DATOS, 'w', encoding='utf-8') as f:
            json.dump([], f)
        CULTIVOS = []
        return []
    
    # 3. Cargar los datos existentes
    try:
        with open(RUTA_DATOS, 'r', encoding='utf-8') as f:
            CULTIVOS = json.load(f)
            return CULTIVOS
    except json.JSONDecodeError:
        # Maneja el caso de un archivo vacío o corrupto
        CULTIVOS = []
        return []

def guardar_cultivos():
    """Guarda la lista global CULTIVOS en el archivo JSON persistente."""
    try:
        with open(RUTA_DATOS, 'w', encoding='utf-8') as f:
            json.dump(CULTIVOS, f, indent=4)
        return True
    except Exception as e:
        print(f"Error al guardar datos: {e}")
        return False

# --- RUTAS (ENDPOINTS) DE LA API ---

@app.route('/api/v1/cultivos', methods=['GET'])
def listar_cultivos():
    """GET: Lista todos los cultivos."""
    return jsonify(CULTIVOS)

@app.route('/api/v1/cultivos', methods=['POST'])
def agregar_cultivo():
    """POST: Agrega un nuevo cultivo."""
    try:
        data = request.get_json()
        #if not all(k in data for k in ('nombre', 'tipo', 'fecha_plantacion')):
            #return jsonify({"error": "Faltan campos requeridos"}), 400
        # Validar los campos esenciales de tu formulario
        if not all(k in data for k in ('nombre', 'fecha_siembra', 'fecha_cosecha')):
            return jsonify({"error": "Faltan campos requeridos (nombre, fecha_siembra, fecha_cosecha)"}), 400
        # Validación básica de existencia (opcional, si el frontend no valida)
        if any(c['nombre'] == data['nombre'] for c in CULTIVOS):
            return jsonify({"error": "El cultivo ya existe."}), 409
        
        # Asignar ID único
        nuevo_cultivo = data
        nuevo_cultivo['id'] = str(uuid.uuid4())
        
        CULTIVOS.append(nuevo_cultivo)
        guardar_cultivos() # Guardar el cambio en el volumen persistente
        
        return jsonify(nuevo_cultivo), 201
    except Exception as e:
        # Este error es solo para fines de depuración; en producción, usa un mensaje genérico.
        return jsonify({"error": f"Error interno al agregar: {str(e)}"}), 500

@app.route('/api/v1/cultivos/<id_cultivo>', methods=['DELETE'])
def eliminar_cultivo(id_cultivo):
    """DELETE: Elimina un cultivo por ID."""
    global CULTIVOS
    
    cultivos_antes = len(CULTIVOS)
    # Filtramos la lista, manteniendo solo los que NO coinciden con el ID
    CULTIVOS = [c for c in CULTIVOS if c.get('id') != id_cultivo]
    
    if len(CULTIVOS) < cultivos_antes:
        guardar_cultivos() # Guardar el cambio en el volumen persistente
        return jsonify({"mensaje": f"Cultivo {id_cultivo} eliminado"}), 200
    else:
        return jsonify({"error": "Cultivo no encontrado"}), 404

# --- INICIALIZACIÓN ---

# Cargar los datos al iniciar la aplicación (usa la lógica de persistencia)
cargar_cultivos()

if __name__ == '__main__':
    # Esto es solo para ejecución local
    app.run(debug=True, host='0.0.0.0', port=5000)