// scripts.js

// --- CONFIGURACIÓN DE ENDPOINTS ---
// RECUERDA: Reemplaza "nombre-unico-de-tu-api-flask" con tu nombre real de la aplicación Fly.io
const BASE_URL = 'https://nombre-unico-de-tu-api-flask.fly.dev'; // <-- URL BASE ÚNICA

// Endpoints (usados internamente por llamarApi)
const API_CULTIVOS_ENDPOINT = '/api/v1/cultivos';
const API_REGISTRO_ENDPOINT = '/auth/registro';
const API_LOGIN_ENDPOINT = '/auth/login';


// --- VARIABLES GLOBALES DEL DOM ---
const tableBody = document.getElementById('cultivoList');
const form = document.getElementById('cultivoForm');
const submitButton = document.getElementById('submitButton');
const originalNameInput = document.getElementById('cultivoNombreOriginal'); 
const loadingMessage = document.getElementById('loading-message');
const searchInput = document.getElementById('cultivoSearch'); 
const authContainer = document.getElementById('auth-container');
const dashboardContainer = document.getElementById('dashboard-container');
const loginForm = document.getElementById('login-form');
const registroForm = document.getElementById('registro-form');
const logoutButton = document.getElementById('logout-button');
const authMessage = document.getElementById('auth-message');

let modoEdicion = false; 
let cultivosData = []; 
let IS_AUTHENTICATED = false; 


// -----------------------------------------------------
// --- NUEVA FUNCIÓN DE UTILIDAD: LLAMAR A LA API ---
// -----------------------------------------------------

/**
 * Función centralizada para realizar peticiones a la API.
 * CRUCIAL: Añade `credentials: 'include'` para enviar la cookie de sesión.
 */
async function llamarApi(endpoint, method = 'GET', data = null) {
    
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            // ¡Ya NO necesitamos el Authorization Header/Token aquí!
        },
        // 🚨 CAMBIO CLAVE: Permite que el navegador envíe la cookie HttpOnly al Backend.
        credentials: 'include' 
    };

    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(BASE_URL + endpoint, options);
        
        // Manejo de error de autenticación (401)
        if (response.status === 401 && endpoint !== API_LOGIN_ENDPOINT) {
            console.error("Sesión expirada o no autorizado.");
            // Si el error 401 no viene del login (es una ruta CRUD), forzamos el cierre de sesión
            if (IS_AUTHENTICATED) {
                 // Si el usuario estaba logueado y recibe 401, forzamos la vuelta al login
                 cerrarSesion(true); // Pasar 'true' para indicar sesión expirada
            }
        }
        
        return response;
    } catch (error) {
        console.error("❌ Error de conexión con la API:", error);
        // Sugerencia: Alerta solo si no es la carga inicial de login para evitar spam
        if (endpoint !== API_LOGIN_ENDPOINT || IS_AUTHENTICATED) { 
            alert(`Error de conexión con la API (${method} ${endpoint}). Asegúrese de que el Backend está activo en: ${BASE_URL}`);
        }
        throw error;
    }
}


// --- 1. FUNCIONES DE AUTENTICACIÓN ---

/**
 * Muestra u oculta los contenedores de Auth y Dashboard.
 */
function toggleInterface(isAuthenticated) {
    if (isAuthenticated) {
        authContainer.style.display = 'none';
        dashboardContainer.style.display = 'block';
        cargarCultivos(); 
    } else {
        authContainer.style.display = 'block';
        dashboardContainer.style.display = 'none';
        authMessage.textContent = '';
        loginForm.reset();
        registroForm.reset();
    }
}

/**
 * Cierra la sesión y vuelve a la pantalla de login.
 * @param {boolean} [isExpired=false] - Indica si la sesión expiró por 401.
 */
function cerrarSesion(isExpired = false) {
    IS_AUTHENTICATED = false;
    toggleInterface(false);
    tableBody.innerHTML = '';
    cultivosData = [];
    resetFormulario();
    if (!isExpired) {
        alert('Sesión cerrada.');
    } else {
        alert('🚨 Su sesión ha expirado (Error 401). Vuelva a iniciar sesión.');
    }
}


/**
 * Intenta registrar un nuevo usuario.
 * (Usa llamarApi pero sin control de 401, ya que no requiere autenticación)
 */
async function manejarRegistro(event) {
    event.preventDefault();
    authMessage.textContent = 'Registrando...'; 
    authMessage.style.color = 'blue';

    const usuario = document.getElementById('registro-usuario').value;
    const contraseña = document.getElementById('registro-contraseña').value;

    try {
        // 🚩 CAMBIO: Usar llamarApi
        const response = await llamarApi(API_REGISTRO_ENDPOINT, 'POST', { usuario, contraseña });

        const resultado = await response.json();

        if (response.ok) {
            authMessage.textContent = resultado.mensaje;
            authMessage.style.color = 'var(--color-primary)';
            registroForm.reset();
        } else {
            authMessage.textContent = `❌ Error: ${resultado.error || 'Fallo en el registro'}`;
            authMessage.style.color = 'var(--color-danger)';
        }
    } catch (error) {
        authMessage.textContent = '❌ Error de conexión al registrar.';
        authMessage.style.color = 'var(--color-danger)';
    }
}

/**
 * Intenta iniciar sesión.
 */
async function manejarLogin(event) {
    event.preventDefault();
    authMessage.textContent = 'Iniciando sesión...';
    authMessage.style.color = 'blue';
    
    const usuario = document.getElementById('login-usuario').value;
    const contraseña = document.getElementById('login-contraseña').value;

    try {
        // 🚩 CAMBIO: Usar llamarApi
        const response = await llamarApi(API_LOGIN_ENDPOINT, 'POST', { usuario, contraseña });

        const resultado = await response.json();

        if (response.ok) {
            // 🚨 CAMBIO CLAVE: El navegador guarda la cookie HttpOnly automáticamente.
            // ELIMINAMOS CUALQUIER CÓDIGO QUE GUARDE EL TOKEN MANUALMENTE (ej. localStorage)
            
            IS_AUTHENTICATED = true;
            toggleInterface(true);
            authMessage.textContent = ''; // Limpiar mensaje de auth
            console.log("Login Exitoso: Cookie de sesión recibida.");
        } else {
            authMessage.textContent = `❌ Error: ${resultado.error || 'Fallo en la autenticación'}`;
            authMessage.style.color = 'var(--color-danger)';
        }
    } catch (error) {
        authMessage.textContent = '❌ Error de conexión al intentar iniciar sesión.';
        authMessage.style.color = 'var(--color-danger)';
    }
}


// --- 2. FUNCIONES DE MANEJO DE LA API (CRUD REFRACTORIZADO) ---

/**
 * 1. GET (Leer): Carga, procesa y renderiza todos los cultivos.
 */
async function cargarCultivos() {
    if (!IS_AUTHENTICATED) return; 
    
    loadingMessage.textContent = 'Cargando datos de la API...';
    try {
        // 🚩 CAMBIO: Usar llamarApi (esto enviará la cookie automáticamente)
        const response = await llamarApi(API_CULTIVOS_ENDPOINT, 'GET');
        
        if (!response.ok) {
            // Si el error es 401, llamarApi ya lo manejará, pero si es otro error de API:
             const errorText = await response.text();
             throw new Error(`Error de la API: ${response.status} - ${errorText}`);
        }
        
        const cultivos = await response.json();
        cultivosData = cultivos; 
        
        loadingMessage.style.display = 'none'; 
        renderizarTabla(cultivosData); 
        actualizarKpis(cultivosData); 
        dibujarGraficoGanancias(cultivosData); 

    } catch (error) {
        console.error('Error al cargar cultivos:', error);
        loadingMessage.textContent = `❌ ERROR DE CONEXIÓN o AUTENTICACIÓN: ${error.message}`;
        loadingMessage.style.color = 'var(--color-danger)';
    }
}

/**
 * 2. POST / PUT (Crear / Actualizar): Envía datos del formulario a la API.
 */
async function manejarEnvioFormulario(event) {
    event.preventDefault(); 
    if (!IS_AUTHENTICATED) return alert('Debes iniciar sesión para realizar cambios.');

    const datosCultivo = obtenerDatosFormulario();

    if (!datosCultivo.nombre || !datosCultivo.fecha_siembra || !datosCultivo.fecha_cosecha) {
        alert('Por favor, rellena el nombre, la fecha de siembra y la fecha de cosecha.');
        return;
    }
    
    if (!validarFechas(datosCultivo.fecha_siembra, datosCultivo.fecha_cosecha)) {
        alert('❌ Error: La fecha de cosecha no puede ser anterior a la fecha de siembra.');
        return; 
    }

    const idOriginal = originalNameInput.value; 
    let endpoint = API_CULTIVOS_ENDPOINT;
    let method = 'POST';
    
    if (modoEdicion) {
        endpoint = `${API_CULTIVOS_ENDPOINT}/${idOriginal}`; 
        method = 'PUT';
        datosCultivo.id = idOriginal; 
    }

    try {
        // 🚩 CAMBIO: Usar llamarApi
        const response = await llamarApi(endpoint, method, datosCultivo);

        const resultado = await response.json();

        if (response.ok) {
            alert(resultado.mensaje || (modoEdicion ? 'Cultivo actualizado.' : 'Cultivo añadido.'));
            resetFormulario();
            cargarCultivos(); 
        } else {
            alert(`Error ${response.status}: ${resultado.error || 'Algo salió mal en el servidor.'}`);
        }
    } catch (error) {
        console.error('Error al enviar el formulario:', error);
        // El error de conexión ya lo maneja llamarApi
    }
}

/**
 * 3. DELETE (Eliminar): Elimina un cultivo por su ID.
 */
async function eliminarCultivo(idCultivo) {
    if (!IS_AUTHENTICATED) return alert('Debes iniciar sesión para eliminar.');

    const cultivo = cultivosData.find(c => c.id === idCultivo);
    const nombreCultivo = cultivo ? cultivo.nombre : 'este cultivo';
    
    if (!confirm(`¿Estás seguro de que deseas eliminar el cultivo: ${nombreCultivo}?`)) {
        return;
    }

    try {
        // 🚩 CAMBIO: Usar llamarApi
        const endpoint = `${API_CULTIVOS_ENDPOINT}/${idCultivo}`;
        const response = await llamarApi(endpoint, 'DELETE');

        const resultado = await response.json();

        if (response.ok) {
            alert(resultado.mensaje || 'Cultivo eliminado.');
            cargarCultivos(); 
        } else {
            alert(`Error ${response.status}: ${resultado.error || 'No se pudo eliminar el cultivo.'}`);
        }
    } catch (error) {
        console.error('Error al eliminar:', error);
        // El error de conexión ya lo maneja llamarApi
    }
}


// --- 3. FUNCIONES DE UTILIDAD Y RENDERIZADO (EXISTENTES) ---
// (Las funciones de soporte no requieren cambios, se mantienen igual)

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

function actualizarKpis(cultivos) {
    let costoTotal = 0;
    let ventaTotal = 0;

    cultivos.forEach(cultivo => {
        costoTotal += parseFloat(cultivo.precio_compra) || 0;
        ventaTotal += parseFloat(cultivo.precio_venta) || 0;
    });
    
    const gananciaPotencial = ventaTotal - costoTotal;

    document.getElementById('kpiCosto').textContent = `€${costoTotal.toFixed(2)}`;
    document.getElementById('kpiVenta').textContent = `€${ventaTotal.toFixed(2)}`;
    document.getElementById('kpiGanancia').textContent = `€${gananciaPotencial.toFixed(2)}`;
    
    const gananciaElement = document.getElementById('kpiGanancia');
    gananciaElement.style.color = gananciaPotencial >= 0 ? 'var(--color-primary)' : 'var(--color-danger)';
}

function validarFechas(siembraStr, cosechaStr) {
    const siembra = Date.parse(siembraStr);
    const cosecha = Date.parse(cosechaStr);

    if (siembra > cosecha) {
        return false;
    }
    return true;
}

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
        
        if (cultivo.dias_restantes && cultivo.dias_restantes.includes('COSECHA HOY')) {
            claseCosecha = 'cosecha-hoy';
        } else if (cultivo.dias_restantes && cultivo.dias_restantes.includes('Cosechado hace')) {
            claseCosecha = 'cosecha-pasada';
        }
        
        const dias = parseInt(cultivo.dias_restantes);
        if (!isNaN(dias) && dias > 0 && dias <= cultivo.dias_alerta) {
            isAlert = true;
        }
        
        const margen = ((cultivo.precio_venta || 0) - (cultivo.precio_compra || 0)).toFixed(2);
        
        row.insertCell().textContent = cultivo.nombre;
        row.insertCell().textContent = cultivo.zona;
        row.insertCell().textContent = cultivo.fecha_siembra;
        row.insertCell().textContent = cultivo.fecha_cosecha;
        
        const cellFaltan = row.insertCell();
        cellFaltan.textContent = cultivo.dias_restantes;
        cellFaltan.classList.add(claseCosecha);
        
        row.insertCell().textContent = `€${margen}`;

        if (isAlert) {
            row.classList.add('fila-alerta');
        }

        const cellAcciones = row.insertCell();
        cellAcciones.classList.add('action-buttons');
        
        const btnEditar = document.createElement('button');
        btnEditar.textContent = 'Editar';
        btnEditar.classList.add('edit-btn');
        btnEditar.onclick = () => cargarParaEdicion(cultivo); 
        
        const btnEliminar = document.createElement('button');
        btnEliminar.textContent = 'Eliminar';
        btnEliminar.classList.add('delete-btn');
        btnEliminar.onclick = () => eliminarCultivo(cultivo.id); 
        
        cellAcciones.appendChild(btnEditar);
        cellAcciones.appendChild(btnEliminar);
    });
}

function cargarParaEdicion(cultivo) {
    if (!IS_AUTHENTICATED) return alert('Debes iniciar sesión para editar.');
    
    document.getElementById('nombre').value = cultivo.nombre;
    document.getElementById('zona').value = cultivo.zona;
    document.getElementById('fecha_siembra').value = cultivo.fecha_siembra;
    document.getElementById('fecha_cosecha').value = cultivo.fecha_cosecha;
    
    document.getElementById('precio_compra').value = (cultivo.precio_compra || 0).toFixed(2); 
    document.getElementById('precio_venta').value = (cultivo.precio_venta || 0).toFixed(2);
    
    document.getElementById('dias_alerta').value = cultivo.dias_alerta;
    document.getElementById('notas').value = cultivo.notas;
    
    modoEdicion = true;
    originalNameInput.value = cultivo.id; 
    submitButton.textContent = `Guardar Cambios de ${cultivo.nombre}`;
    submitButton.classList.add('edit-btn');
    submitButton.classList.remove('delete-btn');
    
    document.getElementById('form-section').scrollIntoView({ behavior: 'smooth' });
}

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

function dibujarGraficoGanancias(cultivos) {
    const datosGanancia = cultivos.map(cultivo => {
        const compra = parseFloat(cultivo.precio_compra) || 0;
        const venta = parseFloat(cultivo.precio_venta) || 0;
        
        const ganancia = venta - compra;
        
        return {
            nombre: cultivo.nombre,
            ganancia: ganancia
        };
    }).filter(c => c.ganancia > 0) 
      .sort((a, b) => b.ganancia - a.ganancia) 
      .slice(0, 5); 

    const canvasElement = document.getElementById('gananciaChart');
    if (!canvasElement) return;

    if (datosGanancia.length === 0) {
        if (window.gananciaChartInstance) {
            window.gananciaChartInstance.destroy();
            window.gananciaChartInstance = null;
        }
        return; 
    }

    const etiquetas = datosGanancia.map(d => d.nombre);
    const valores = datosGanancia.map(d => d.ganancia.toFixed(2));

    if (window.gananciaChartInstance) {
        window.gananciaChartInstance.destroy();
    }

    const ctx = canvasElement.getContext('2d');
    
    window.gananciaChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: etiquetas,
            datasets: [{
                label: 'Ganancia Potencial (€)',
                data: valores,
                backgroundColor: 'rgba(75, 192, 192, 0.7)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Ganancia (€)'
                    },
                    ticks: {
                        color: '#ddd' 
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)' 
                    }
                },
                x: {
                    ticks: {
                        color: '#ddd' 
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)' 
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#ddd'
                    }
                },
                title: {
                    display: true,
                    text: 'Proyección Top 5 (Venta - Compra)',
                    color: '#fff'
                }
            }
        }
    });
}


// --- 4. INICIALIZACIÓN DE EVENTOS (MODIFICADA) ---

document.addEventListener('DOMContentLoaded', () => {
    toggleInterface(false); 
    
    // 2. Event Listeners para Autenticación
    loginForm.addEventListener('submit', manejarLogin);
    registroForm.addEventListener('submit', manejarRegistro);
    logoutButton.addEventListener('click', cerrarSesion);

    // 3. Event Listeners para CRUD (dentro del Dashboard)
    form.addEventListener('submit', manejarEnvioFormulario);
    searchInput.addEventListener('input', filtrarCultivos); 

    // Botón de Cancelar Edición
    const btnCancelar = document.createElement('button');
    btnCancelar.textContent = 'Limpiar / Cancelar Edición';
    btnCancelar.classList.add('delete-btn');
    btnCancelar.type = 'button'; 
    btnCancelar.onclick = resetFormulario;
    form.appendChild(btnCancelar);
});