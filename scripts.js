// scripts.js

// 🚨 CRÍTICO: Reemplaza con la URL de tu servicio en Render.
// Ejemplo: https://ventas-invernadero-antolin.onrender.com
const BASE_URL = 'https://ventas-invernadero-antolin.onrender.com';

// --- Estado de la Aplicación ---
let cultivosData = []; // Almacenará los datos de cultivos

// --- Función de Utilidad para Peticiones de API ---
/**
 * Envía peticiones a la API del Backend, maneja las credenciales (cookies) y errores.
 * @param {string} endpoint - Ruta de la API (e.g., '/auth/login').
 * @param {object} options - Opciones de fetch.
 * @returns {Promise<object>} Objeto con el estado de la respuesta.
 */
async function apiFetch(endpoint, options = {}) {
    const url = `${BASE_URL}${endpoint}`;
    
    // Configuración para enviar cookies (credenciales)
    options.credentials = 'include';
    
    // Si no se especifica el Content-Type y hay un body, lo configuramos a JSON
    if (!options.headers) {
        options.headers = {};
    }
    if (options.body && typeof options.body !== 'string') {
        options.body = JSON.stringify(options.body);
        options.headers['Content-Type'] = 'application/json';
    }

    try {
        const response = await fetch(url, options);

        if (response.status === 401) {
            // Manejar token expirado o inválido: redirigir a login
            alert("Sesión expirada o inválida. Por favor, inicia sesión de nuevo.");
            logout(); // Ejecutamos la función de logout para limpiar la sesión
            return { success: false, status: 401 };
        }

        // Intentar parsear el JSON solo si hay contenido
        const contentType = response.headers.get("content-type");
        const data = (contentType && contentType.indexOf("application/json") !== -1) ? await response.json() : null;

        return { success: response.ok, data: data, status: response.status };

    } catch (error) {
        console.error("Error de conexión con la API:", error);
        alert("Error de conexión con el servidor. Asegúrate de que el Backend está activo en: " + BASE_URL);
        return { success: false, error: error };
    }
}

// --- Gestión de Vistas (Simulación de SPA) ---

function showView(viewId) {
    // Oculta todas las vistas
    document.querySelectorAll('.view').forEach(view => {
        view.classList.remove('active');
    });
    // Muestra la vista solicitada
    document.getElementById(viewId).classList.add('active');
}

// --- Lógica de Autenticación ---

async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    const result = await apiFetch('/auth/login', {
        method: 'POST',
        body: { username, password }
    });

    if (result.success) {
        alert("Inicio de sesión exitoso.");
        showView('dashboard-view');
        await loadDashboard(); // Cargar datos y gráficos
    } else {
        alert(result.data ? result.data.message : "Error al iniciar sesión.");
    }
}

async function handleRegister(event) {
    event.preventDefault();
    const username = document.getElementById('register-username').value;
    const password = document.getElementById('register-password').value;

    const result = await apiFetch('/auth/register', {
        method: 'POST',
        body: { username, password }
    });

    if (result.success) {
        alert("Registro exitoso. Por favor, inicia sesión.");
        showView('login-view');
        // Limpiar formulario de registro
        document.getElementById('register-form').reset();
    } else {
        alert(result.data ? result.data.message : "Error al registrar usuario.");
    }
}

async function logout() {
    const result = await apiFetch('/auth/logout', { method: 'POST' });

    // La función de logout se encarga de eliminar la cookie
    // independientemente del resultado del fetch, redirigimos.
    showView('login-view');
    window.location.hash = '#login';
    alert("Sesión cerrada.");
}

// --- Lógica del Dashboard y CRUD ---

async function loadDashboard() {
    // 1. Cargar datos de la API
    const result = await apiFetch('/api/v1/cultivos', { method: 'GET' });

    if (result.success) {
        cultivosData = result.data || [];
        renderCultivosTable(cultivosData);
        renderCharts(cultivosData);
    } else if (result.status !== 401) {
        // Mostrar error solo si no es un 401 (ya manejado por apiFetch)
        alert(result.data ? result.data.message : "Error al cargar los datos de cultivos.");
    }
}

function renderCultivosTable(data) {
    const tableBody = document.getElementById('cultivos-table-body');
    tableBody.innerHTML = ''; // Limpiar tabla

    if (data.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="6" class="text-center">No se encontraron cultivos.</td></tr>';
        return;
    }

    data.forEach(cultivo => {
        const row = tableBody.insertRow();
        row.innerHTML = `
            <td>${cultivo.id}</td>
            <td>${cultivo.nombre}</td>
            <td>${cultivo.estado}</td>
            <td>${cultivo.cantidad_sembrada}</td>
            <td>${cultivo.fecha_siembra}</td>
            <td>
                <button class="btn btn-sm btn-info" onclick="editCultivo(${cultivo.id})">Editar</button>
                <button class="btn btn-sm btn-danger" onclick="deleteCultivo(${cultivo.id})">Eliminar</button>
            </td>
        `;
    });
}

async function saveCultivo(event) {
    event.preventDefault();
    const form = event.target;
    const isEdit = form.dataset.editId;
    
    const cultivo = {
        nombre: form.nombre.value,
        estado: form.estado.value,
        cantidad_sembrada: parseInt(form.cantidad_sembrada.value),
        fecha_siembra: form.fecha_siembra.value,
    };

    let result;
    if (isEdit) {
        cultivo.id = parseInt(isEdit);
        result = await apiFetch(`/api/v1/cultivos/${isEdit}`, {
            method: 'PUT',
            body: cultivo
        });
    } else {
        result = await apiFetch('/api/v1/cultivos', {
            method: 'POST',
            body: cultivo
        });
    }

    if (result.success) {
        alert(`Cultivo ${isEdit ? 'actualizado' : 'creado'} con éxito.`);
        form.reset();
        delete form.dataset.editId; // Limpiar modo edición
        document.getElementById('cultivo-form-title').textContent = 'Añadir Nuevo Cultivo';
        await loadDashboard(); // Recargar datos
    } else {
        alert(result.data ? result.data.message : `Error al ${isEdit ? 'actualizar' : 'crear'} el cultivo.`);
    }
}

function editCultivo(id) {
    const cultivo = cultivosData.find(c => c.id === id);
    if (!cultivo) return;

    const form = document.getElementById('cultivo-form');
    document.getElementById('cultivo-form-title').textContent = 'Editar Cultivo (ID: ' + id + ')';
    form.dataset.editId = id; // Almacenar el ID en el formulario
    
    // Llenar el formulario
    form.nombre.value = cultivo.nombre;
    form.estado.value = cultivo.estado;
    form.cantidad_sembrada.value = cultivo.cantidad_sembrada;
    form.fecha_siembra.value = cultivo.fecha_siembra;
    
    // Opcional: Desplazarse al formulario
    form.scrollIntoView({ behavior: 'smooth' });
}

async function deleteCultivo(id) {
    if (!confirm(`¿Estás seguro de que quieres eliminar el cultivo con ID: ${id}?`)) {
        return;
    }
    
    const result = await apiFetch(`/api/v1/cultivos/${id}`, { method: 'DELETE' });

    if (result.success) {
        alert("Cultivo eliminado con éxito.");
        await loadDashboard(); // Recargar datos
    } else {
        alert(result.data ? result.data.message : "Error al eliminar el cultivo.");
    }
}

// --- Lógica de Gráficos ---

let chartInstance = null; // Para almacenar la instancia del gráfico

function renderCharts(data) {
    const ctx = document.getElementById('cultivos-chart').getContext('2d');
    
    // Destruir la instancia anterior si existe
    if (chartInstance) {
        chartInstance.destroy();
    }

    // 1. Agrupar por estado
    const statusCounts = data.reduce((acc, cultivo) => {
        acc[cultivo.estado] = (acc[cultivo.estado] || 0) + 1;
        return acc;
    }, {});

    const labels = Object.keys(statusCounts);
    const chartData = Object.values(statusCounts);
    
    chartInstance = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: chartData,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.6)', // Crecimiento
                    'rgba(54, 162, 235, 0.6)', // Cosecha
                    'rgba(255, 206, 86, 0.6)', // Semilla
                    'rgba(75, 192, 192, 0.6)'  // Otros estados
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Distribución de Cultivos por Estado'
                }
            }
        }
    });
}

// --- Inicialización y Event Listeners ---

document.addEventListener('DOMContentLoaded', () => {
    
    // Inicializar formularios y botones
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
    }
    
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    const cultivoForm = document.getElementById('cultivo-form');
    if (cultivoForm) {
        cultivoForm.addEventListener('submit', saveCultivo);
    }
    
    const showRegisterBtn = document.getElementById('show-register-btn');
    if (showRegisterBtn) {
        showRegisterBtn.addEventListener('click', () => {
            showView('register-view');
            window.location.hash = '#register';
        });
    }

    const showLoginBtn = document.getElementById('show-login-btn');
    if (showLoginBtn) {
        showLoginBtn.addEventListener('click', () => {
            showView('login-view');
            window.location.hash = '#login';
        });
    }
    
    // --- Lógica de Enrutamiento Básico (Hash) ---
    function handleRoute() {
        const hash = window.location.hash || '#login';
        
        if (hash === '#dashboard') {
            // Intentar cargar el dashboard (si la sesión es válida, cargará datos)
            showView('dashboard-view');
            loadDashboard();
        } else if (hash === '#register') {
            showView('register-view');
        } else {
            // Por defecto, va a login
            showView('login-view');
        }
    }
    
    window.addEventListener('hashchange', handleRoute);
    handleRoute(); // Ejecutar al cargar la página por primera vez
});