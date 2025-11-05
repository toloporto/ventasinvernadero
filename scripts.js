// scripts.js

// --- CONFIGURACIÓN DE ENDPOINTS ---
// RECUERDA: Reemplaza "nombre-unico-de-tu-api-flask" con tu nombre real de la aplicación Fly.io
const API_BASE_URL = 'https://nombre-unico-de-tu-api-flask.fly.dev/api/v1/cultivos';

// ¡NUEVOS ENDPOINTS DE AUTENTICACIÓN!
const API_REGISTRO_URL = 'https://nombre-unico-de-tu-api-flask.fly.dev/auth/registro';
const API_LOGIN_URL = 'https://nombre-unico-de-tu-api-flask.fly.dev/auth/login';


// --- VARIABLES GLOBALES DEL DOM ---

// Elementos del Dashboard (Existentes)
const tableBody = document.getElementById('cultivoList');
const form = document.getElementById('cultivoForm');
const submitButton = document.getElementById('submitButton');
const originalNameInput = document.getElementById('cultivoNombreOriginal'); 
const loadingMessage = document.getElementById('loading-message');
const searchInput = document.getElementById('cultivoSearch'); 

// Elementos de Autenticación (Nuevos, del index.html modificado)
const authContainer = document.getElementById('auth-container');
const dashboardContainer = document.getElementById('dashboard-container');
const loginForm = document.getElementById('login-form');
const registroForm = document.getElementById('registro-form');
const logoutButton = document.getElementById('logout-button');
const authMessage = document.getElementById('auth-message');


let modoEdicion = false; 
let cultivosData = []; 
let IS_AUTHENTICATED = false; // ¡Estado de la sesión!


// --- 1. FUNCIONES DE AUTENTICACIÓN (NUEVAS) ---

/**
 * Muestra u oculta los contenedores de Auth y Dashboard.
 */
function toggleInterface(isAuthenticated) {
    if (isAuthenticated) {
        authContainer.style.display = 'none';
        dashboardContainer.style.display = 'block';
        // Una vez dentro, cargamos los datos
        cargarCultivos(); 
    } else {
        authContainer.style.display = 'block';
        dashboardContainer.style.display = 'none';
        // Limpiar mensajes y formularios al cerrar sesión
        authMessage.textContent = '';
        loginForm.reset();
        registroForm.reset();
    }
}

/**
 * Intenta registrar un nuevo usuario.
 */
async function manejarRegistro(event) {
    event.preventDefault();
    authMessage.textContent = 'Registrando...'; 
    authMessage.style.color = 'blue';

    const usuario = document.getElementById('registro-usuario').value;
    const contraseña = document.getElementById('registro-contraseña').value;

    try {
        const response = await fetch(API_REGISTRO_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuario, contraseña }),
        });

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
        const response = await fetch(API_LOGIN_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usuario, contraseña }),
        });

        const resultado = await response.json();

        if (response.ok) {
            // Éxito en el login
            IS_AUTHENTICATED = true;
            toggleInterface(true);
            authMessage.textContent = ''; // Limpiar mensaje de auth
        } else {
            authMessage.textContent = `❌ Error: ${resultado.error || 'Fallo en la autenticación'}`;
            authMessage.style.color = 'var(--color-danger)';
        }
    } catch (error) {
        authMessage.textContent = '❌ Error de conexión al intentar iniciar sesión.';
        authMessage.style.color = 'var(--color-danger)';
    }
}

/**
 * Cierra la sesión y vuelve a la pantalla de login.
 */
function cerrarSesion() {
    IS_AUTHENTICATED = false;
    toggleInterface(false);
    // Limpiar el formulario de cultivos y datos de la tabla
    tableBody.innerHTML = '';
    cultivosData = [];
    resetFormulario();
    alert('Sesión cerrada.');
}


// --- 2. FUNCIONES DE MANEJO DE LA API (CRUD EXISTENTES, CON CHECK DE AUTH) ---

/**
 * 1. GET (Leer): Carga, procesa y renderiza todos los cultivos.
 */
async function cargarCultivos() {
    // ⚠️ REVISIÓN: Solo carga si está autenticado
    if (!IS_AUTHENTICATED) return; 
    
    loadingMessage.textContent = 'Cargando datos de la API...';
    try {
        const response = await fetch(API_BASE_URL);
        
        if (!response.ok) {
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
        loadingMessage.textContent = `❌ ERROR DE CONEXIÓN: ${error.message}. Verifica que la URL de Fly.io sea correcta.`;
        loadingMessage.style.color = 'var(--color-danger)';
    }
    // Dentro de la función principal de carga/actualización:
    function actualizarDashboard(cultivos) {
    // ... [Tu código existente para actualizar la tabla y los KPIs]

    // ¡NUEVA LLAMADA!
    dibujarGraficoGanancias(); // <-- Asegúrate de que esta línea esté aquí
    }
}

/**
 * 2. POST / PUT (Crear / Actualizar): Envía datos del formulario a la API.
 */
async function manejarEnvioFormulario(event) {
    event.preventDefault(); 
    // ⚠️ REVISIÓN: Bloquear si no está autenticado
    if (!IS_AUTHENTICATED) return alert('Debes iniciar sesión para realizar cambios.');


    const datosCultivo = obtenerDatosFormulario();

    // 🚩 Validación de campos (conservado)
    if (!datosCultivo.nombre || !datosCultivo.fecha_siembra || !datosCultivo.fecha_cosecha) {
        alert('Por favor, rellena el nombre, la fecha de siembra y la fecha de cosecha.');
        return;
    }
    
    // VALIDACIÓN DE FECHAS (conservado)
    if (!validarFechas(datosCultivo.fecha_siembra, datosCultivo.fecha_cosecha)) {
        alert('❌ Error: La fecha de cosecha no puede ser anterior a la fecha de siembra.');
        return; 
    }

    const idOriginal = originalNameInput.value; 
    let url = API_BASE_URL;
    let method = 'POST';
    
    if (modoEdicion) {
        url = `${API_BASE_URL}/${idOriginal}`; 
        method = 'PUT';
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
    // ⚠️ REVISIÓN: Bloquear si no está autenticado
    if (!IS_AUTHENTICATED) return alert('Debes iniciar sesión para eliminar.');

    const cultivo = cultivosData.find(c => c.id === idCultivo);
    const nombreCultivo = cultivo ? cultivo.nombre : 'este cultivo';
    
    if (!confirm(`¿Estás seguro de que deseas eliminar el cultivo: ${nombreCultivo}?`)) {
        return;
    }

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


// --- 3. FUNCIONES DE UTILIDAD Y RENDERIZADO (EXISTENTES) ---

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
        
        const margen = (cultivo.precio_venta - cultivo.precio_compra).toFixed(2);
        
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
    // ⚠️ REVISIÓN: Bloquear si no está autenticado
    if (!IS_AUTHENTICATED) return alert('Debes iniciar sesión para editar.');
    
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

/**
 * Dibuja un gráfico de barras con los 5 cultivos con mayor ganancia potencial.
 */
function dibujarGraficoGanancias() {
    // 1. Obtener y preparar datos (usamos la variable CULTIVOS_CACHE global)
    const datosGanancia = CULTIVOS_CACHE.map(cultivo => {
        // La ganancia potencial es (Precio Venta - Precio Compra)
        const ganancia = (parseFloat(cultivo.precio_venta) - parseFloat(cultivo.precio_compra));
        return {
            nombre: cultivo.nombre,
            ganancia: ganancia
        };
    }).filter(c => c.ganancia > 0) // Solo cultivos con ganancia
      .sort((a, b) => b.ganancia - a.ganancia) // Ordenar de mayor a menor
      .slice(0, 5); // Tomar solo los 5 principales

    // Si no hay datos, limpiamos el canvas
    if (datosGanancia.length === 0) {
        const ctx = document.getElementById('gananciaChart').getContext('2d');
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        return; 
    }

    // 2. Extraer etiquetas y valores para Chart.js
    const etiquetas = datosGanancia.map(d => d.nombre);
    const valores = datosGanancia.map(d => d.ganancia.toFixed(2));

    // 3. Destruir gráfico anterior si existe (para evitar duplicados al recargar)
    const canvasElement = document.getElementById('gananciaChart');
    if (window.gananciaChartInstance) {
        window.gananciaChartInstance.destroy();
    }

    // 4. Configuración y Creación del Gráfico
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
                        color: '#ddd' // Color de texto para tema oscuro
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)' // Líneas de cuadrícula
                    }
                },
                x: {
                    ticks: {
                        color: '#ddd' // Color de texto para tema oscuro
                    },
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)' // Líneas de cuadrícula
                    }
                }
            },
            plugins: {
                legend: {
                    labels: {
                        color: '#ddd' // Color de la leyenda
                    }
                },
                title: {
                    display: true,
                    text: 'Proyección Top 5 (Venta - Compra)',
                    color: '#fff' // Color del título
                }
            }
        }
    });
}


// --- 4. INICIALIZACIÓN DE EVENTOS (MODIFICADA) ---

document.addEventListener('DOMContentLoaded', () => {
    // 1. Mostrar la interfaz de autenticación al inicio
    toggleInterface(false); 
    
    // 2. Event Listeners para Autenticación
    loginForm.addEventListener('submit', manejarLogin);
    registroForm.addEventListener('submit', manejarRegistro);
    logoutButton.addEventListener('click', cerrarSesion);

    // 3. Event Listeners para CRUD (dentro del Dashboard)
    form.addEventListener('submit', manejarEnvioFormulario);
    searchInput.addEventListener('input', filtrarCultivos); 

    // Botón de Cancelar Edición (Se mantiene la lógica de inyección)
    const btnCancelar = document.createElement('button');
    btnCancelar.textContent = 'Limpiar / Cancelar Edición';
    btnCancelar.classList.add('delete-btn');
    btnCancelar.type = 'button'; 
    btnCancelar.onclick = resetFormulario;
    form.appendChild(btnCancelar);

    // NOTA: La función cargarCultivos() se llama ahora SOLO al iniciar sesión con éxito.
});