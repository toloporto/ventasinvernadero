import os  # <-- Asegúrate de que esta línea esté al principio
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
from datetime import date, datetime
from dateutil import parser # Para parsear fechas de forma flexible

app = Flask(__name__)
CORS(app) # Habilita CORS para el desarrollo del frontend

RUTA_DATOS = 'cultivos.json'

# --- Funciones de Utilidad ---

def cargar_cultivos():
    """Carga los datos de cultivos desde el archivo JSON."""
    try:
        with open(RUTA_DATOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print("Advertencia: El archivo JSON está vacío o mal formado. Inicializando lista vacía.")
        return []

def guardar_cultivos(cultivos):
    """Guarda la lista de cultivos en el archivo JSON."""
    with open(RUTA_DATOS, 'w', encoding='utf-8') as f:
        json.dump(cultivos, f, indent=4, ensure_ascii=False)

def calcular_dias_restantes(fecha_cosecha_str, dias_alerta):
    """Calcula los días restantes para la cosecha y el estado de alerta."""
    try:
        fecha_cosecha = parser.parse(fecha_cosecha_str).date()
    except ValueError:
        return "Fecha inválida"

    hoy = date.today()
    diferencia = fecha_cosecha - hoy
    dias = diferencia.days

    if dias < 0:
        return f"Cosechado hace {-dias} días"
    elif dias == 0:
        return "COSECHA HOY"
    elif dias <= dias_alerta:
        return f"¡ALERTA! Quedan {dias} días"
    else:
        return f"{dias} días"

def procesar_cultivo(cultivo):
    """Añade el campo 'dias_restantes' a un cultivo."""
    cultivo_procesado = cultivo.copy()
    cultivo_procesado['dias_restantes'] = calcular_dias_restantes(
        cultivo.get('fecha_cosecha'),
        cultivo.get('dias_alerta', 7)
    )
    # Convertir floats a formato de dos decimales para consistencia
    cultivo_procesado['precio_compra'] = float(cultivo.get('precio_compra', 0.0))
    cultivo_procesado['precio_venta'] = float(cultivo.get('precio_venta', 0.0))
    return cultivo_procesado

# --- Rutas de la API (Backend) ---

@app.route('/api/v1/cultivos', methods=['GET'])
def obtener_cultivos():
    """Ruta para obtener todos los cultivos, procesando las fechas."""
    cultivos = cargar_cultivos()
    cultivos_procesados = [procesar_cultivo(c) for c in cultivos]
    return jsonify(cultivos_procesados)

@app.route('/api/v1/cultivos', methods=['POST'])
def crear_cultivo():
    """Ruta para crear un nuevo cultivo."""
    nuevo_cultivo = request.json
    cultivos = cargar_cultivos()

    # Validar nombre único
    if any(c['nombre'] == nuevo_cultivo.get('nombre') for c in cultivos):
        return jsonify({"error": "Ya existe un cultivo con este nombre."}), 400
    
    # Validar campos requeridos
    if not nuevo_cultivo.get('nombre') or not nuevo_cultivo.get('fecha_cosecha'):
        return jsonify({"error": "Faltan campos obligatorios (nombre, fecha_cosecha)."}), 400

    cultivos.append(nuevo_cultivo)
    guardar_cultivos(cultivos)
    return jsonify({"mensaje": "Cultivo añadido.", "cultivo": nuevo_cultivo}), 201

@app.route('/api/v1/cultivos/<string:nombre>', methods=['PUT'])
def actualizar_cultivo(nombre):
    """Ruta para actualizar un cultivo existente por nombre."""
    datos_actualizados = request.json
    cultivos = cargar_cultivos()
    
    # Encontrar el índice del cultivo
    indice = next((i for i, c in enumerate(cultivos) if c['nombre'] == nombre), None)

    if indice is None:
        return jsonify({"error": "Cultivo no encontrado."}), 404
    
    # Actualizar los datos (manteniendo el nombre original si no se cambia en los datos)
    cultivos[indice].update(datos_actualizados)

    # Si el nombre fue cambiado en los datos, aseguramos que el registro se mueva a la nueva clave
    # y que el nuevo nombre no colisione con otro existente.
    nuevo_nombre = datos_actualizados.get('nombre')
    if nuevo_nombre and nuevo_nombre != nombre:
        if any(c['nombre'] == nuevo_nombre for i, c in enumerate(cultivos) if i != indice):
            return jsonify({"error": f"El nombre '{nuevo_nombre}' ya está en uso."}), 400
        # Renombrar si es necesario
        cultivos[indice]['nombre'] = nuevo_nombre

    guardar_cultivos(cultivos)
    return jsonify({"mensaje": f"Cultivo {nombre} actualizado."}), 200

@app.route('/api/v1/cultivos/<string:nombre>', methods=['DELETE'])
def eliminar_cultivo(nombre):
    """Ruta para eliminar un cultivo por nombre."""
    cultivos = cargar_cultivos()
    
    cultivos_filtrados = [c for c in cultivos if c['nombre'] != nombre]
    
    if len(cultivos_filtrados) == len(cultivos):
        return jsonify({"error": "Cultivo no encontrado."}), 404
        
    guardar_cultivos(cultivos_filtrados)
    return jsonify({"mensaje": f"Cultivo {nombre} eliminado."}), 200


# --- Ruta para servir el Frontend (Opcional, pero bueno para Heroku) ---
# Sirve el archivo index.html cuando se accede a la raíz del sitio
@app.route('/')
def serve_frontend():
    return send_from_directory('app_frontend', 'index.html')

# Sirve los archivos estáticos (CSS, JS) desde la carpeta del frontend
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('app_frontend', filename)


# --- Bloque de Ejecución (Modificado para Heroku) ---

if __name__ == '__main__':
    # Usa el puerto definido por la variable de entorno PORT de Heroku, 
    # o 5000 si se ejecuta localmente.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)