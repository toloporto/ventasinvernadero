// scripts.js

// --- CONFIGURACIÓN ---
const API_BASE_URL = 'https://nombre-unico-de-tu-api-flask.fly.dev/api/v1/cultivos';
const tableBody = document.getElementById('cultivoList');
const form = document.getElementById('cultivoForm');
const submitButton = document.getElementById('submitButton');
// Campo para guardar el ID o Nombre Original (lo usaremos para identificar la edición)
const originalNameInput = document.getElementById('cultivoNombreOriginal'); 
const loadingMessage = document.getElementById('loading-message');
const searchInput = document.getElementById('cultivoSearch'); 

let modoEdicion = false; 
let cultivosData = []; 

// --- FUNCIONES DE MANEJO DE LA API (CRUD) ---

/**
 * 1. GET (Leer): Carga, procesa y renderiza todos los cultivos.
 */
async function cargarCultivos() {
    loadingMessage.textContent = 'Cargando datos de la API...';
    try {
        const response = await fetch(API_BASE_URL);
        
        if (!response.ok) {
            // Manejar errores de la API (500, 404 de API, etc.)
            const errorText = await response.text();
            throw new Error(`Error de la API: ${response.status} - ${errorText}`);
        }
        
        const cultivos = await response.json();
        
        cultivosData = cultivos; 
        
        loadingMessage.style.display = 'none'; 
        renderizarTabla(cultivosData); 
        
        actualizarKpis(cultivosData); // Actualiza los KPIs después de la carga

    } catch (error) {
        console.error('Error al cargar cultivos:', error);
        // Mensaje actualizado para el despliegue en la nube
        loadingMessage.textContent = `❌ ERROR DE CONEXIÓN: ${error.message}. Verifica que la URL de Fly.io sea correcta.`;
        loadingMessage.style.color = 'var(--color-danger)';
    }
}

/**
 * 2. POST / PUT (Crear / Actualizar): Envía datos del formulario a la API.
 */
async function manejarEnvioFormulario(event) {
    event.preventDefault(); 

    const datosCultivo = obtenerDatosFormulario();

    // 🚩 CORRECCIÓN CRÍTICA 1: Usar los campos del Frontend para la validación local
    if (!datosCultivo.nombre || !datosCultivo.fecha_siembra || !datosCultivo.fecha_cosecha) {
        alert('Por favor, rellena el nombre, la fecha de siembra y la fecha de cosecha.');
        return;
    }
    
    // VALIDACIÓN DE FECHAS (Frontend)
    if (!validarFechas(datosCultivo.fecha_siembra, datosCultivo.fecha_cosecha)) {
        alert('❌ Error: La fecha de cosecha no puede ser anterior a la fecha de siembra.');
        return; 
    }

    // Usaremos el ID único del Backend para PUT, no el nombre original
    const idOriginal = originalNameInput.value; 
    let url = API_BASE_URL;
    let method = 'POST';
    
    if (modoEdicion) {
        // 🚩 CORRECCIÓN CRÍTICA 2: El Backend usa el ID para DELETE/PUT
        url = `${API_BASE_URL}/${idOriginal}`; 
        method = 'PUT';
        // Incluir el ID en los datos enviados para la actualización
        datosCultivo.id = idOriginal; 
    }

    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(datosCultivo),
        });

        const resultado = await response.json();

        if (response.ok) {
            alert(resultado.mensaje || (modoEdicion ? 'Cultivo actualizado.' : 'Cultivo añadido.'));
            resetFormulario();
            cargarCultivos(); 
        } else {
            // Esto capturará el error "Faltan campos requeridos" que viene del Backend
            alert(`Error ${response.status}: ${resultado.error || 'Algo salió mal en el servidor.'}`);
        }
    } catch (error) {
        console.error('Error al enviar el formulario:', error);
        alert('Error de conexión con la API. Asegúrate de que Fly.io esté funcionando.');
    }
}

/**
 * 3. DELETE (Eliminar): Elimina un cultivo por su ID.
 */
async function eliminarCultivo(idCultivo) {
    // Buscar el nombre para la confirmación visual
    const cultivo = cultivosData.find(c => c.id === idCultivo);
    const nombreCultivo = cultivo ? cultivo.nombre : 'este cultivo';
    
    if (!confirm(`¿Estás seguro de que deseas eliminar el cultivo: ${nombreCultivo}?`)) {
        return;
    }

    // 🚩 CORRECCIÓN CRÍTICA 3: El Backend usa el ID, no el nombre, para la eliminación
    try {
        const response = await fetch(`${API_BASE_URL}/${idCultivo}`, { 
            method: 'DELETE',
        });

        const resultado = await response.json();

        if (response.ok) {
            alert(resultado.mensaje || 'Cultivo eliminado.');
            cargarCultivos(); 
        } else {
            alert(`Error ${response.status}: ${resultado.error || 'No se pudo eliminar el cultivo.'}`);
        }
    } catch (error) {
        console.error('Error al eliminar:', error);
        alert('Error de conexión con la API.');
    }
}

/**
 * 4. FILTRAR: Filtra los cultivos mostrados en la tabla basándose en el texto de búsqueda.
 */
function filtrarCultivos() {
    const textoBusqueda = searchInput.value.toLowerCase().trim();
    
    if (textoBusqueda === '') {
        renderizarTabla(cultivosData);
        return;
    }
    
    const cultivosFiltrados = cultivosData.filter(cultivo => {
        const contenido = (
            (cultivo.nombre || '') + 
            (cultivo.zona || '') + 
            (cultivo.notas || '') + 
            (cultivo.fecha_cosecha || '')
        ).toLowerCase();
        
        return contenido.includes(textoBusqueda);
    });
    
    renderizarTabla(cultivosFiltrados);
}

/**
 * 5. KPIs: Calcula y actualiza los KPIs financieros.
 */
function actualizarKpis(cultivos) {
    let costoTotal = 0;
    let ventaTotal = 0;

    cultivos.forEach(cultivo => {
        costoTotal += parseFloat(cultivo.precio_compra) || 0;
        ventaTotal += parseFloat(cultivo.precio_venta) || 0;
    });
    
    const gananciaPotencial = ventaTotal - costoTotal;

    // Actualizar los elementos del DOM
    document.getElementById('kpiCosto').textContent = `€${costoTotal.toFixed(2)}`;
    document.getElementById('kpiVenta').textContent = `€${ventaTotal.toFixed(2)}`;
    document.getElementById('kpiGanancia').textContent = `€${gananciaPotencial.toFixed(2)}`;
    
    // Estilo condicional para la ganancia
    const gananciaElement = document.getElementById('kpiGanancia');
    gananciaElement.style.color = gananciaPotencial >= 0 ? 'var(--color-primary)' : 'var(--color-danger)';
}


// --- FUNCIONES DE UTILIDAD Y RENDERIZADO ---

/**
 * Valida que la fecha de cosecha sea posterior o igual a la fecha de siembra.
 */
function validarFechas(siembraStr, cosechaStr) {
    const siembra = Date.parse(siembraStr);
    const cosecha = Date.parse(cosechaStr);

    if (siembra > cosecha) {
        return false;
    }
    return true;
}

/**
 * Recopila los datos del formulario.
 */
function obtenerDatosFormulario() {
    return {
        nombre: document.getElementById('nombre').value.trim(),
        zona: document.getElementById('zona').value.trim(),
        fecha_siembra: document.getElementById('fecha_siembra').value,
        fecha_cosecha: document.getElementById('fecha_cosecha').value,
        precio_compra: parseFloat(document.getElementById('precio_compra').value) || 0.0,
        precio_venta: parseFloat(document.getElementById('precio_venta').value) || 0.0,
        dias_alerta: parseInt(document.getElementById('dias_alerta').value) || 0,
        notas: document.getElementById('notas').value.trim(),
    };
}

/**
 * Pinta la tabla HTML con los datos pasados.
 */
function renderizarTabla(cultivos) {
    tableBody.innerHTML = '';
    
    if (cultivos.length === 0) {
        const row = tableBody.insertRow();
        const cell = row.insertCell();
        cell.colSpan = 7;
        cell.textContent = 'No se encontraron cultivos.';
        cell.style.textAlign = 'center';
        return;
    }

    cultivos.forEach(cultivo => {
        const row = tableBody.insertRow();
        let claseCosecha = 'cosecha-futura';
        let isAlert = false;
        
        // Clases para estado de cosecha
        if (cultivo.dias_restantes && cultivo.dias_restantes.includes('COSECHA HOY')) {
            claseCosecha = 'cosecha-hoy';
        } else if (cultivo.dias_restantes && cultivo.dias_restantes.includes('Cosechado hace')) {
            claseCosecha = 'cosecha-pasada';
        }
        
        // LÓGICA DE ALERTA DE PROXIMIDAD
        const dias = parseInt(cultivo.dias_restantes);
        if (!isNaN(dias) && dias > 0 && dias <= cultivo.dias_alerta) {
            isAlert = true;
        }
        
        const margen = (cultivo.precio_venta - cultivo.precio_compra).toFixed(2);
        
        // Renderizado de celdas
        row.insertCell().textContent = cultivo.nombre;
        row.insertCell().textContent = cultivo.zona;
        row.insertCell().textContent = cultivo.fecha_siembra;
        row.insertCell().textContent = cultivo.fecha_cosecha;
        
        const cellFaltan = row.insertCell();
        cellFaltan.textContent = cultivo.dias_restantes;
        cellFaltan.classList.add(claseCosecha);
        
        row.insertCell().textContent = `€${margen}`;

        // Aplicar clase de alerta a la fila
        if (isAlert) {
            row.classList.add('fila-alerta');
        }

        // Celda de Acciones (Botones)
        const cellAcciones = row.insertCell();
        cellAcciones.classList.add('action-buttons');
        
        const btnEditar = document.createElement('button');
        btnEditar.textContent = 'Editar';
        btnEditar.classList.add('edit-btn');
        // 🚩 CAMBIO: Pasamos el objeto completo (que incluye el ID)
        btnEditar.onclick = () => cargarParaEdicion(cultivo); 
        
        const btnEliminar = document.createElement('button');
        btnEliminar.textContent = 'Eliminar';
        btnEliminar.classList.add('delete-btn');
        // 🚩 CAMBIO: Pasamos el ID del cultivo para la eliminación
        btnEliminar.onclick = () => eliminarCultivo(cultivo.id); 
        
        cellAcciones.appendChild(btnEditar);
        cellAcciones.appendChild(btnEliminar);
    });
}

/**
 * Carga los datos de un cultivo seleccionado al formulario para su edición.
 */
function cargarParaEdicion(cultivo) {
    // 1. Cargar datos al formulario
    document.getElementById('nombre').value = cultivo.nombre;
    document.getElementById('zona').value = cultivo.zona;
    document.getElementById('fecha_siembra').value = cultivo.fecha_siembra;
    document.getElementById('fecha_cosecha').value = cultivo.fecha_cosecha;
    document.getElementById('precio_compra').value = cultivo.precio_compra.toFixed(2);
    document.getElementById('precio_venta').value = cultivo.precio_venta.toFixed(2);
    document.getElementById('dias_alerta').value = cultivo.dias_alerta;
    document.getElementById('notas').value = cultivo.notas;
    
    // 2. Configurar el modo edición
    modoEdicion = true;
    // 🚩 CAMBIO: Guardamos el ID del cultivo para usarlo en la llamada PUT/DELETE
    originalNameInput.value = cultivo.id; 
    submitButton.textContent = `Guardar Cambios de ${cultivo.nombre}`;
    submitButton.classList.add('edit-btn');
    submitButton.classList.remove('delete-btn');
    
    document.getElementById('form-section').scrollIntoView({ behavior: 'smooth' });
}

/**
 * Limpia el formulario y vuelve al modo Añadir.
 */
function resetFormulario() {
    form.reset();
    modoEdicion = false;
    originalNameInput.value = '';
    submitButton.textContent = 'Añadir Cultivo';
    submitButton.classList.remove('edit-btn');
    submitButton.classList.remove('delete-btn');
    
    document.getElementById('precio_compra').value = '0.00';
    document.getElementById('precio_venta').value = '0.00';
    document.getElementById('dias_alerta').value = '7';
}


// --- INICIALIZACIÓN ---

form.addEventListener('submit', manejarEnvioFormulario);
searchInput.addEventListener('input', filtrarCultivos); 

// Botón de Cancelar Edición
const btnCancelar = document.createElement('button');
btnCancelar.textContent = 'Limpiar / Cancelar Edición';
btnCancelar.classList.add('delete-btn');
btnCancelar.type = 'button'; 
btnCancelar.onclick = resetFormulario;
form.appendChild(btnCancelar);

// Carga los cultivos al iniciar la página
document.addEventListener('DOMContentLoaded', cargarCultivos);