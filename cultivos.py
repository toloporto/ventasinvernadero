# --- IMPORTS ---
import datetime
import json
import os
import csv 
# Módulos para la Interfaz Gráfica de Usuario (GUI)
import tkinter as tk
from tkinter import ttk, messagebox, filedialog 
# Módulo para el calendario
from tkcalendar import Calendar 

# --- IMPORTS PARA ANÁLISIS DE DATOS ---
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression 
import numpy as np 

# --- CONFIGURACIÓN DE DATOS PERMANENTES ---
lista_cultivos = []
NOMBRE_ARCHIVO = "cultivos.json"
NOMBRE_ARCHIVO_VENTAS = "ventas_mensuales.csv" # Archivo para análisis externo

# --- CONSTANTES DE COLOR PARA EL TEMA OSCURO ---
COLOR_FONDO_OSCURO = '#2E3436'     
COLOR_FONDO_SEGUNDARIO = '#343A40' 
COLOR_TEXTO_CLARO = '#F0F0F0'      
COLOR_ENFASIS_VERDE = '#5CB85C'    
COLOR_ENFASIS_ROJO = '#DC3545'     
COLOR_PRIMARIO_BOTON = '#007BFF'   
COLOR_TREE_HEADER = '#495057'      
COLOR_ALERTA_CLARA = '#FFC107'     


# --- 1. CLASE MODELO (LA LÓGICA DE NEGOCIO) ---

class Cultivo:
    """Clase base para guardar la información de un cultivo, incluyendo datos financieros, ubicación y alerta."""
    def __init__(self, nombre, fecha_siembra, fecha_cosecha, notas="", zona="", precio_compra=0.0, precio_venta=0.0, dias_alerta=0):
        self.nombre = nombre
        self.fecha_siembra = fecha_siembra
        self.fecha_cosecha = fecha_cosecha
        self.notas = notas
        self.zona = zona 
        self.precio_compra = precio_compra 
        self.precio_venta = precio_venta 
        self.dias_alerta = dias_alerta 

# --- 2. FUNCIONES DE MANEJO DE ARCHIVOS Y DATOS ---

def validar_fecha(fecha_texto):
    """Convierte texto a un objeto de fecha (YYYY-MM-DD)."""
    try:
        return datetime.datetime.strptime(fecha_texto, '%Y-%m-%d').date()
    except ValueError:
        return None

def cargar_cultivos():
    """Carga los cultivos desde el archivo JSON, manejando nuevos campos."""
    global lista_cultivos
    lista_cultivos = []
    
    if not os.path.exists(NOMBRE_ARCHIVO):
        return
    
    try:
        with open(NOMBRE_ARCHIVO, "r") as f:
            datos_cargados = json.load(f)
            for item in datos_cargados:
                siembra = validar_fecha(item["fecha_siembra"])
                cosecha = validar_fecha(item["fecha_cosecha"])
                notas = item.get("notas", "")
                zona = item.get("zona", "") 
                precio_compra = float(item.get("precio_compra", 0.0))
                precio_venta = float(item.get("precio_venta", 0.0))
                dias_alerta = int(item.get("dias_alerta", 0)) 
                
                if siembra and cosecha:
                    nuevo = Cultivo(item["nombre"], siembra, cosecha, notas, zona, precio_compra, precio_venta, dias_alerta)
                    lista_cultivos.append(nuevo)
                    
    except Exception as e:
        messagebox.showerror("Error de Carga", f"Hubo un error al cargar el archivo: {e}")

def guardar_cultivos():
    """Guarda la lista de cultivos en el archivo JSON, incluyendo todos los campos."""
    datos_para_json = []
    for cultivo in lista_cultivos:
        cultivo_dict = {
            "nombre": cultivo.nombre,
            "fecha_siembra": cultivo.fecha_siembra.isoformat(),
            "fecha_cosecha": cultivo.fecha_cosecha.isoformat(),
            "notas": cultivo.notas,
            "zona": cultivo.zona, 
            "precio_compra": cultivo.precio_compra,
            "precio_venta": cultivo.precio_venta,
            "dias_alerta": cultivo.dias_alerta 
        }
        datos_para_json.append(cultivo_dict)
        
    try:
        with open(NOMBRE_ARCHIVO, "w") as f:
            json.dump(datos_para_json, f, indent=4)
    except Exception as e:
        messagebox.showerror("Error de Guardado", f"No se pudo guardar la información: {e}")


# --- 3. LA CLASE DE LA APLICACIÓN (TKINTER) ---

class AppCultivos(tk.Tk):
    """Clase principal de la aplicación GUI con Tema Oscuro."""
    def __init__(self):
        super().__init__()
        self.title("Asistente de Cultivos (v18.0 - Alarmas Inteligentes)")
        self.geometry("1050x700") 
        
        self.cultivo_seleccionado_indice = None
        
        self.configurar_estilos() 
        
        cargar_cultivos() 
        self.crear_widgets()
        self.actualizar_lista_cultivos()
        self.revisar_cosechas_al_inicio()
        
    def configurar_estilos(self):
        """Define los temas, estilos, tags y fuentes de la aplicación con un tema oscuro."""
        
        style = ttk.Style(self)
        
        try:
            style.theme_use('clam') 
        except tk.TclError:
            pass 

        # 1. Colores generales
        self.configure(background=COLOR_FONDO_OSCURO)
        
        style.configure('TLabel', background=COLOR_FONDO_OSCURO, foreground=COLOR_TEXTO_CLARO, font=('Helvetica', 10))
        
        # Estilo para los marcos LabelFrame
        style.configure('TLabelframe', background=COLOR_FONDO_SEGUNDARIO)
        style.configure('TLabelframe.Label', 
                        font=('Helvetica', 12, 'bold'), 
                        foreground=COLOR_ENFASIS_VERDE,
                        background=COLOR_FONDO_SEGUNDARIO) 
        
        # Estilo para las cajas de entrada (Entry)
        style.configure('TEntry', fieldbackground=COLOR_FONDO_SEGUNDARIO, foreground=COLOR_TEXTO_CLARO)
        
        # 2. Configurar la Lista (Treeview)
        style.configure('Treeview', 
                        fieldbackground=COLOR_FONDO_SEGUNDARIO, 
                        background=COLOR_FONDO_SEGUNDARIO, 
                        foreground=COLOR_TEXTO_CLARO,
                        rowheight=25) 
        style.configure('Treeview.Heading', 
                        font=('Helvetica', 10, 'bold'), 
                        background=COLOR_TREE_HEADER, 
                        foreground=COLOR_TEXTO_CLARO)
        style.map('Treeview', background=[('selected', '#0056B3')], foreground=[('selected', COLOR_TEXTO_CLARO)]) 
        
        # Tags de color para las filas del Treeview (Reporte)
        self.lista_tree = ttk.Treeview(self) 
        self.lista_tree.tag_configure('cosecha_pasada', background=COLOR_FONDO_OSCURO, foreground='#AAAAAA') 
        self.lista_tree.tag_configure('cosecha_hoy', background=COLOR_ALERTA_CLARA, foreground=COLOR_FONDO_OSCURO, font=('Helvetica', 10, 'bold'))
        self.lista_tree.tag_configure('cosecha_futura', background='#444444', foreground=COLOR_ENFASIS_VERDE)

        # 3. Configurar Alertas de Recordatorio y Botones
        style.configure('Alerta.TLabel', 
                        foreground='#333333', 
                        font=('Helvetica', 12, 'bold'), 
                        background=COLOR_ALERTA_CLARA, 
                        padding=5, 
                        borderwidth=1, 
                        relief="solid")
                        
        style.configure('TButton', font=('Helvetica', 10, 'bold'), foreground=COLOR_TEXTO_CLARO, background=COLOR_TREE_HEADER) 
        style.map('TButton', background=[('active', '#555555')]) 
        
        style.configure('Principal.TButton', font=('Helvetica', 11, 'bold'), background=COLOR_PRIMARIO_BOTON)
        style.map('Principal.TButton', background=[('active', '#0056B3')])

    def limpiar_campos(self):
        """Función auxiliar para limpiar la interfaz y salir del modo edición."""
        self.nombre_var.set("")
        self.siembra_display_var.set("Seleccionar fecha...")
        self.cosecha_display_var.set("Seleccionar fecha...")
        self.notas_var.set("")
        self.zona_var.set("")
        self.compra_var.set("")
        self.venta_var.set("")
        self.dias_alerta_var.set("7") # Restaurar valor por defecto
        self.fecha_siembra_obj = None
        self.fecha_cosecha_obj = None
        
        self.btn_guardar.config(text="Añadir a la Lista", style='Principal.TButton')
        self.cultivo_seleccionado_indice = None
        
    def crear_widgets(self):
        """Define la disposición de todos los elementos."""
        
        self.columnconfigure(0, weight=1) 
        self.columnconfigure(1, weight=3) 
        self.rowconfigure(0, weight=1)
        
        # --- Marco Izquierdo (Añadir/Editar Cultivo) ---
        frame_agregar = ttk.LabelFrame(self, text="🌱 Añadir/Editar Cultivo", padding="10")
        frame_agregar.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        self.nombre_var = tk.StringVar()
        self.siembra_display_var = tk.StringVar(value="Seleccionar fecha...")
        self.cosecha_display_var = tk.StringVar(value="Seleccionar fecha...")
        self.fecha_siembra_obj = None
        self.fecha_cosecha_obj = None
        self.notas_var = tk.StringVar()
        self.zona_var = tk.StringVar()
        self.compra_var = tk.StringVar()
        self.venta_var = tk.StringVar()
        self.dias_alerta_var = tk.StringVar(value="7") # Valor por defecto

        # Nombre, Zona, Fechas, Precios, Notas 
        ttk.Label(frame_agregar, text="Nombre:").pack(fill='x', pady=2)
        ttk.Entry(frame_agregar, textvariable=self.nombre_var).pack(fill='x', pady=1)

        ttk.Label(frame_agregar, text="Zona de Cultivo:").pack(fill='x', pady=2)
        zonas_posibles = ["Zona A", "Zona B", "Zona C", "Zona D", "Invernadero", "Exterior"]
        self.zona_combobox = ttk.Combobox(frame_agregar, textvariable=self.zona_var, values=zonas_posibles, state="readonly")
        self.zona_combobox.pack(fill='x', pady=1)

        ttk.Label(frame_agregar, text="Fecha Siembra:").pack(fill='x', pady=2)
        ttk.Label(frame_agregar, textvariable=self.siembra_display_var, foreground=COLOR_ENFASIS_VERDE).pack(fill='x', pady=1)
        ttk.Button(frame_agregar, text="Elegir Fecha de Siembra", command=lambda: self.mostrar_calendario("siembra")).pack(fill='x', pady=2)
        
        ttk.Label(frame_agregar, text="Fecha Cosecha:").pack(fill='x', pady=2)
        ttk.Label(frame_agregar, textvariable=self.cosecha_display_var, foreground=COLOR_ENFASIS_VERDE).pack(fill='x', pady=1)
        ttk.Button(frame_agregar, text="Elegir Fecha de Cosecha", command=lambda: self.mostrar_calendario("cosecha")).pack(fill='x', pady=2)

        frame_precios = ttk.Frame(frame_agregar, style='TLabelframe') 
        frame_precios.pack(fill='x', pady=5)
        
        frame_precios.columnconfigure(0, weight=1)
        ttk.Label(frame_precios, text="Costo (€):").grid(row=0, column=0, sticky='w', padx=2)
        ttk.Entry(frame_precios, textvariable=self.compra_var, width=15).grid(row=1, column=0, sticky='ew', padx=2)
        
        frame_precios.columnconfigure(1, weight=1)
        ttk.Label(frame_precios, text="Venta Est. (€):").grid(row=0, column=1, sticky='w', padx=2)
        ttk.Entry(frame_precios, textvariable=self.venta_var, width=15).grid(row=1, column=1, sticky='ew', padx=2)

        ttk.Label(frame_agregar, text="Notas (Opcional):").pack(fill='x', pady=2)
        ttk.Entry(frame_agregar, textvariable=self.notas_var).pack(fill='x', pady=1)
        
        # --- NUEVO WIDGET: ALARMA INTELIGENTE ---
        frame_alerta = ttk.LabelFrame(frame_agregar, text="🔔 Alarma Inteligente", padding="5")
        frame_alerta.pack(fill='x', pady=5)
        
        ttk.Label(frame_alerta, text="Días de Alerta Previa a Cosecha:").pack(fill='x', pady=2)
        ttk.Entry(frame_alerta, textvariable=self.dias_alerta_var).pack(fill='x', pady=1)
        
        self.btn_guardar = ttk.Button(frame_agregar, text="Añadir a la Lista", 
                                     command=self.manejar_agregar_o_editar, style='Principal.TButton')
        self.btn_guardar.pack(fill='x', pady=10)
        
        ttk.Button(frame_agregar, text="Limpiar Campos", command=self.limpiar_campos).pack(fill='x', pady=2)


        # --- Marco Derecho (Lista, Reporte y Botones) ---
        frame_mostrar = ttk.LabelFrame(self, text="🗓 Mis Cultivos", padding="10")
        frame_mostrar.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Panel de Resumen Financiero 
        frame_totales = ttk.LabelFrame(frame_mostrar, text="💸 Resumen Financiero Potencial", padding="5")
        frame_totales.pack(fill='x', pady=5)
        
        frame_totales.columnconfigure(0, weight=1)
        frame_totales.columnconfigure(1, weight=1)
        frame_totales.columnconfigure(2, weight=1)
        
        ttk.Label(frame_totales, text="Costo Total:").grid(row=0, column=0, sticky='w')
        self.label_costo_total = ttk.Label(frame_totales, text="€0.00", font=('Helvetica', 10, 'bold'), foreground=COLOR_ENFASIS_ROJO) 
        self.label_costo_total.grid(row=1, column=0, sticky='w')

        ttk.Label(frame_totales, text="Venta Est. Total:").grid(row=0, column=1, sticky='w')
        self.label_venta_total = ttk.Label(frame_totales, text="€0.00", font=('Helvetica', 10, 'bold'), foreground=COLOR_ENFASIS_VERDE)
        self.label_venta_total.grid(row=1, column=1, sticky='w')
        
        ttk.Label(frame_totales, text="Margen Potencial:").grid(row=0, column=2, sticky='w')
        self.label_margen_total = ttk.Label(frame_totales, text="€0.00", font=('Helvetica', 10, 'bold'))
        self.label_margen_total.grid(row=1, column=2, sticky='w')

        # Recordatorio y Treeview 
        self.recordatorio_label = ttk.Label(frame_mostrar, text="Recordatorios aparecerán aquí.", font=('Helvetica', 12, 'bold'), style='Alerta.TLabel')
        self.recordatorio_label.pack(fill='x', pady=5)
        
        frame_mostrar.rowconfigure(2, weight=1) 
        
        self.lista_tree = ttk.Treeview(frame_mostrar, columns=('zona', 'siembra', 'cosecha', 'notas', 'compra', 'venta', 'margen', 'faltan'), show='headings')
        self.lista_tree.heading('#0', text='Cultivo')
        self.lista_tree.heading('zona', text='Zona') 
        self.lista_tree.heading('siembra', text='Siembra')
        self.lista_tree.heading('cosecha', text='Cosecha')
        self.lista_tree.heading('notas', text='Notas')
        self.lista_tree.heading('compra', text='Costo') 
        self.lista_tree.heading('venta', text='Venta') 
        self.lista_tree.heading('margen', text='Margen') 
        self.lista_tree.heading('faltan', text='Faltan')
        self.lista_tree.column('#0', width=120, anchor='w')
        self.lista_tree.column('zona', width=70, anchor='center')
        self.lista_tree.column('siembra', width=70, anchor='center')
        self.lista_tree.column('cosecha', width=70, anchor='center')
        self.lista_tree.column('notas', width=100, anchor='w')
        self.lista_tree.column('compra', width=60, anchor='center')
        self.lista_tree.column('venta', width=60, anchor='center')
        self.lista_tree.column('margen', width=60, anchor='center')
        self.lista_tree.column('faltan', width=100, anchor='center')
        self.lista_tree.pack(fill='both', expand=True, pady=10)

        # Botones de lista (Incluye Exportar y Analizar)
        frame_botones_lista = ttk.Frame(frame_mostrar, style='TLabel') 
        frame_botones_lista.pack(fill='x', pady=5)
        
        # Botón para Lanzar el Análisis Externo
        ttk.Button(frame_botones_lista, text="📈 Analizar Ventas Externas", 
                   command=self.analizar_ventas_externas, style='Principal.TButton').pack(side='left', expand=True, fill='x', padx=5)
        
        # Botón de Exportar 
        ttk.Button(frame_botones_lista, text="📤 Exportar Cultivos CSV", 
                   command=self.exportar_a_csv, style='Principal.TButton').pack(side='left', expand=True, fill='x', padx=5)

        # Botones de gestión
        ttk.Button(frame_botones_lista, text="❌ Eliminar", command=self.manejar_eliminar_cultivo).pack(side='left', expand=True, fill='x', padx=5)
        ttk.Button(frame_botones_lista, text="✏️ Editar Seleccionado", command=self.manejar_editar_cultivo).pack(side='right', expand=True, fill='x', padx=5)


    # --- 4. FUNCIONES CONECTADAS A LA INTERFAZ ---
    
    def calcular_totales_financieros(self):
        total_compra = 0.0
        total_venta = 0.0
        for cultivo in lista_cultivos:
            total_compra += cultivo.precio_compra
            total_venta += cultivo.precio_venta
        return total_compra, total_venta

    def calcular_tiempo_restante(self, fecha_objetivo):
        hoy = datetime.date.today()
        if fecha_objetivo < hoy:
            dias = (hoy - fecha_objetivo).days
            return f"¡COSECHADO HACE {dias} DÍAS!"
        elif fecha_objetivo == hoy:
            return "¡COSECHA HOY!"
        else:
            dias = (fecha_objetivo - hoy).days
            return f"{dias} Días Restantes"

    def mostrar_calendario(self, campo_destino):
        def set_fecha():
            fecha_str = cal.get_date() 
            fecha_obj = datetime.datetime.strptime(fecha_str, '%m/%d/%y').date()
            if campo_destino == "siembra":
                self.fecha_siembra_obj = fecha_obj
                self.siembra_display_var.set(fecha_obj.strftime('%Y-%m-%d'))
            elif campo_destino == "cosecha":
                self.fecha_cosecha_obj = fecha_obj
                self.cosecha_display_var.set(fecha_obj.strftime('%Y-%m-%d'))
            top.destroy()
        top = tk.Toplevel(self)
        top.title(f"Seleccionar Fecha de {campo_destino.capitalize()}")
        cal = Calendar(top, selectmode='day', date_pattern='mm/dd/yy',
                       year=datetime.date.today().year, month=datetime.date.today().month,
                       day=datetime.date.today().day)
        cal.pack(padx=10, pady=10)
        ttk.Button(top, text="Confirmar", command=set_fecha).pack(pady=10)
        
    def manejar_agregar_o_editar(self):
        nombre = self.nombre_var.get().strip()
        fecha_siembra = self.fecha_siembra_obj
        fecha_cosecha = self.fecha_cosecha_obj
        notas = self.notas_var.get().strip()
        zona = self.zona_var.get().strip()
        
        try:
            precio_compra = float(self.compra_var.get().strip() or 0.0)
            precio_venta = float(self.venta_var.get().strip() or 0.0)
            
            dias_alerta = int(self.dias_alerta_var.get().strip() or 0)
            if dias_alerta < 0:
                raise ValueError("La alarma no puede tener días negativos.")
            
        except ValueError as e:
            messagebox.showerror("Error", f"Los campos de Costo, Venta o Días de Alerta deben ser números válidos. {e}")
            return
            
        if not nombre or not fecha_siembra or not fecha_cosecha:
            messagebox.showerror("Error", "Debe completar el nombre y seleccionar ambas fechas.")
            return
            
        if fecha_cosecha < fecha_siembra:
            messagebox.showerror("Error", "La fecha de cosecha no puede ser anterior a la siembra.")
            return
            
        if self.cultivo_seleccionado_indice is None:
            # Modo Añadir
            nuevo_cultivo = Cultivo(nombre, fecha_siembra, fecha_cosecha, notas, zona, precio_compra, precio_venta, dias_alerta)
            lista_cultivos.append(nuevo_cultivo)
            msg = f"'{nombre}' añadido con éxito."
        else:
            # Modo Editar
            indice = self.cultivo_seleccionado_indice
            cultivo_a_editar = lista_cultivos[indice]
            cultivo_a_editar.nombre = nombre
            cultivo_a_editar.fecha_siembra = fecha_siembra
            cultivo_a_editar.fecha_cosecha = fecha_cosecha
            cultivo_a_editar.notas = notas
            cultivo_a_editar.zona = zona
            cultivo_a_editar.precio_compra = precio_compra
            cultivo_a_editar.precio_venta = precio_venta
            cultivo_a_editar.dias_alerta = dias_alerta
            msg = f"'{nombre}' actualizado con éxito."
            
        guardar_cultivos()
        self.actualizar_lista_cultivos()
        self.revisar_cosechas_al_inicio()
        self.limpiar_campos()
        messagebox.showinfo("Éxito", msg)

    def manejar_editar_cultivo(self):
        seleccion_id = self.lista_tree.selection()
        if not seleccion_id:
            messagebox.showwarning("Advertencia", "Selecciona un cultivo para editar.")
            return
        try:
            indice = int(self.lista_tree.focus())
        except ValueError:
            messagebox.showerror("Error", "Error al identificar el cultivo.")
            return
            
        cultivo_a_editar = lista_cultivos[indice]
        self.nombre_var.set(cultivo_a_editar.nombre)
        self.notas_var.set(cultivo_a_editar.notas)
        self.zona_var.set(cultivo_a_editar.zona)
        self.compra_var.set(f"{cultivo_a_editar.precio_compra:.2f}")
        self.venta_var.set(f"{cultivo_a_editar.precio_venta:.2f}")
        self.dias_alerta_var.set(str(cultivo_a_editar.dias_alerta)) 
        
        self.fecha_siembra_obj = cultivo_a_editar.fecha_siembra
        self.siembra_display_var.set(cultivo_a_editar.fecha_siembra.strftime('%Y-%m-%d'))
        self.fecha_cosecha_obj = cultivo_a_editar.fecha_cosecha
        self.cosecha_display_var.set(cultivo_a_editar.fecha_cosecha.strftime('%Y-%m-%d'))
        self.cultivo_seleccionado_indice = indice
        self.btn_guardar.config(text=f"✏️ Guardar Cambios (Editando {cultivo_a_editar.nombre})", style='Principal.TButton')
        messagebox.showinfo("Modo Edición", f"Datos de '{cultivo_a_editar.nombre}' cargados. Haz tus cambios y pulsa 'Guardar Cambios'.")

    def manejar_eliminar_cultivo(self):
        seleccion_id = self.lista_tree.selection()
        if not seleccion_id:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un cultivo de la lista para eliminar.")
            return
        try:
            indice_a_eliminar = int(self.lista_tree.focus()) 
        except ValueError:
            messagebox.showerror("Error", "Error al identificar el cultivo. Intenta seleccionar otra vez.")
            return
        nombre_cultivo = lista_cultivos[indice_a_eliminar].nombre
        confirmar = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de que quieres eliminar '{nombre_cultivo}' de tus cultivos?"
        )
        if confirmar:
            del lista_cultivos[indice_a_eliminar] 
            guardar_cultivos()
            self.actualizar_lista_cultivos()
            self.revisar_cosechas_al_inicio()
            self.limpiar_campos() 
            messagebox.showinfo("Éxito", f"El cultivo '{nombre_cultivo}' ha sido eliminado.")

    def exportar_a_csv(self):
        """Exporta todos los datos de la lista de cultivos a un archivo CSV."""
        if not lista_cultivos:
            messagebox.showwarning("Advertencia", "No hay cultivos para exportar.")
            return
        nombre_archivo_csv = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv")],
            initialfile="reporte_cultivos.csv",
            title="Guardar Reporte CSV"
        )
        if not nombre_archivo_csv:
            return
        encabezados = [
            "Nombre", "Zona", "Fecha_Siembra", "Fecha_Cosecha", 
            "Costo_Compra_(€)", "Venta_Estimada_(€)", "Margen_Potencial_(€)", "Dias_Alerta", "Notas"
        ]
        try:
            with open(nombre_archivo_csv, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';') 
                writer.writerow(encabezados)
                for cultivo in lista_cultivos:
                    margen = cultivo.precio_venta - cultivo.precio_compra
                    writer.writerow([
                        cultivo.nombre, cultivo.zona, cultivo.fecha_siembra.strftime('%Y-%m-%d'),
                        cultivo.fecha_cosecha.strftime('%Y-%m-%d'),
                        f"{cultivo.precio_compra:.2f}", f"{cultivo.precio_venta:.2f}",
                        f"{margen:.2f}", cultivo.dias_alerta, cultivo.notas
                    ])
            messagebox.showinfo("Éxito", f"Datos exportados correctamente a:\n{nombre_archivo_csv}")
        except Exception as e:
            messagebox.showerror("Error de Exportación", f"No se pudo escribir el archivo CSV: {e}")

    def analizar_ventas_externas(self):
        """
        Carga el archivo CSV externo, realiza análisis descriptivo, y genera 
        tres gráficos: Producto, Tendencia Temporal (con Predicción), y Región.
        """
        nombre_archivo = NOMBRE_ARCHIVO_VENTAS
        
        # 1. Carga de Datos y Manejo de Errores
        if not os.path.exists(nombre_archivo):
            messagebox.showwarning("Advertencia", 
                                   f"No se encontró el archivo de ventas externas '{nombre_archivo}'.\n"
                                   f"Asegúrate de que exista y se llame '{NOMBRE_ARCHIVO_VENTAS}'.")
            return

        try:
            df = pd.read_csv(nombre_archivo, sep=',')
        except pd.errors.ParserError:
            messagebox.showerror("Error", "Error de formato en el CSV. ¿Es el delimitador correcto (coma)?")
            return
        except Exception as e:
            messagebox.showerror("Error", f"Error inesperado al cargar los datos: {e}")
            return

        # 2. Preparación de Datos
        df['Venta_Total'] = pd.to_numeric(df['Venta_Total'], errors='coerce')
        df.dropna(subset=['Venta_Total'], inplace=True)
        
        if df.empty:
            messagebox.showwarning("Advertencia", "El archivo de ventas está vacío o solo contiene encabezados válidos.")
            return

        # 3. Análisis Agrupado (Ventas por Producto)
        ventas_por_producto = df.groupby('Producto')['Venta_Total'].sum().sort_values(ascending=False)
        
        # 4. Análisis Temporal (Preparación para Regresión)
        mapa_meses = {'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4, 'May': 5, 'Jun': 6, 
                      'Jul': 7, 'Ago': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12}
        df['Num_Mes'] = df['Mes'].map(mapa_meses)
        ventas_por_mes_df = df.groupby(['Num_Mes', 'Mes'])['Venta_Total'].sum().reset_index()
        ventas_por_mes_df = ventas_por_mes_df.sort_values(by='Num_Mes').reset_index(drop=True)
        
        # 5. Análisis Agrupado por Región
        ventas_por_region = df.groupby('Region')['Venta_Total'].sum().sort_values(ascending=False)
        
        
        # --- 6. PREDICCIÓN DE VENTAS (REGRESIÓN LINEAL) ---
        X = ventas_por_mes_df['Num_Mes'].values.reshape(-1, 1) 
        Y = ventas_por_mes_df['Venta_Total'].values
        
        modelo_regresion = LinearRegression()
        modelo_regresion.fit(X, Y)
        
        ultimo_mes_num = ventas_por_mes_df['Num_Mes'].max()
        mes_futuro_num = ultimo_mes_num + 1
        
        meses_lista = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        mes_futuro_nombre = meses_lista[(mes_futuro_num - 1) % 12] 
        if mes_futuro_num > 12: 
             mes_futuro_nombre = f"Mes {mes_futuro_num}" 

        prediccion_futura = modelo_regresion.predict(np.array([[mes_futuro_num]]))[0]
        
        print("\n--- PREDICCIÓN DE VENTAS ---")
        print(f"Predicción de venta para {mes_futuro_nombre}: €{prediccion_futura:.2f}")

        X_pred = np.append(X, [[mes_futuro_num]], axis=0) 
        Y_tendencia = modelo_regresion.predict(X_pred)     
        
        labels_x = ventas_por_mes_df['Mes'].tolist() + [f"Pred. {mes_futuro_nombre}"]
        
        
        # --- 7. VISUALIZACIÓN DE DATOS con Matplotlib (Tres Subplots) ---
        try:
            plt.style.use('dark_background') 
            fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))
            fig.suptitle(f'Análisis de Ventas (Predicción {mes_futuro_nombre}: €{prediccion_futura:.2f})', color='white', fontsize=16)

            
            # --- Gráfico 1: Ventas por Producto (Barras) ---
            ventas_por_producto.plot(kind='bar', color='#1E8449', ax=ax1) 
            ax1.set_title('1. Ventas por Producto', color='white')
            ax1.set_xlabel('Producto', color='white')
            ax1.set_ylabel('Venta Total (€)', color='white')
            ax1.tick_params(axis='x', rotation=45, colors='white')
            ax1.tick_params(axis='y', colors='white')
            ax1.grid(axis='y', linestyle='--', alpha=0.4) 
            
            # --- Gráfico 2: Ventas por Mes (Líneas con Predicción) ---
            ax2.plot(ventas_por_mes_df['Mes'], ventas_por_mes_df['Venta_Total'], 
                     marker='o', linestyle='-', color='#007BFF', linewidth=3, label='Ventas Históricas')
            ax2.plot(labels_x, Y_tendencia, 
                     linestyle='--', color='#FFC107', linewidth=2, label='Predicción Lineal')
                     
            ax2.set_title('2. Tendencia Temporal y Predicción', color='white')
            ax2.set_xlabel('Mes', color='white')
            ax2.set_ylabel('Venta Total (€)', color='white')
            ax2.tick_params(axis='x', rotation=45, colors='white')
            ax2.tick_params(axis='y', colors='white')
            ax2.grid(axis='both', linestyle='--', alpha=0.4) 
            ax2.legend(loc='upper left', frameon=False) 
            
            # --- Gráfico 3: Ventas por Región (Barras) ---
            ventas_por_region.plot(kind='bar', color='#FFC107', ax=ax3) 
            ax3.set_title('3. Ventas por Región', color='white')
            ax3.set_xlabel('Región', color='white')
            ax3.set_ylabel('Venta Total (€)', color='white')
            ax3.tick_params(axis='x', rotation=45, colors='white')
            ax3.tick_params(axis='y', colors='white')
            ax3.grid(axis='y', linestyle='--', alpha=0.4) 

            
            plt.tight_layout(rect=[0, 0.03, 1, 0.95]) 
            messagebox.showinfo("Análisis Completo", f"Se han generado tres gráficos, incluyendo una predicción para {mes_futuro_nombre}.")
            plt.show() 

[Image of a data dashboard with charts]


        except Exception as e:
            messagebox.showerror("Error de Gráfico/Predicción", f"No se pudo generar el gráfico o el modelo: {e}")


    def actualizar_lista_cultivos(self):
        for item in self.lista_tree.get_children():
            self.lista_tree.delete(item)
            
        for i, cultivo in enumerate(lista_cultivos):
            siembra_f = cultivo.fecha_siembra.strftime('%d-%m-%Y')
            cosecha_f = cultivo.fecha_cosecha.strftime('%d-%m-%Y')
            tiempo_restante = self.calcular_tiempo_restante(cultivo.fecha_cosecha) 
            margen = cultivo.precio_venta - cultivo.precio_compra
            hoy = datetime.date.today()
            if cultivo.fecha_cosecha < hoy:
                tag = 'cosecha_pasada'
            elif cultivo.fecha_cosecha == hoy:
                tag = 'cosecha_hoy'
            else:
                tag = 'cosecha_futura'
                
            self.lista_tree.insert('', tk.END, iid=str(i), 
                                   text=cultivo.nombre, 
                                   values=(cultivo.zona, siembra_f, cosecha_f, cultivo.notas, 
                                           f"€{cultivo.precio_compra:.2f}", 
                                           f"€{cultivo.precio_venta:.2f}", 
                                           f"€{margen:.2f}", 
                                           tiempo_restante),
                                   tags=(tag,))

        total_compra, total_venta = self.calcular_totales_financieros()
        total_margen = total_venta - total_compra
        self.label_costo_total.config(text=f"€{total_compra:.2f}")
        self.label_venta_total.config(text=f"€{total_venta:.2f}")
        self.label_margen_total.config(text=f"€{total_margen:.2f}")
        
        if total_margen < 0:
            self.label_margen_total.config(foreground=COLOR_ENFASIS_ROJO) 
        elif total_margen > 0:
            self.label_margen_total.config(foreground=COLOR_ENFASIS_VERDE) 
        else:
            self.label_margen_total.config(foreground=COLOR_TEXTO_CLARO)


    def revisar_cosechas_al_inicio(self):
        """Revisa si hay cultivos listos para cosechar o que necesitan una alerta temprana."""
        hoy = datetime.date.today()
        cosechas_hoy = []
        alertas_tempranas = []
        
        for cultivo in lista_cultivos:
            dias_restantes = (cultivo.fecha_cosecha - hoy).days
            
            if dias_restantes < 0:
                # Cultivo ya cosechado
                continue
            elif dias_restantes == 0:
                # Cosecha hoy
                cosechas_hoy.append(cultivo.nombre)
            elif 0 < dias_restantes <= cultivo.dias_alerta:
                # Alerta temprana: entre 1 día y los 'dias_alerta' configurados
                alertas_tempranas.append(f"{cultivo.nombre} (Cosecha en {dias_restantes} días)")

        
        mensaje = ""
        titulo = ""
        
        if cosechas_hoy:
            mensaje += "⚠️ ¡COSECHA PENDIENTE HOY! ⚠️\n" + ", ".join(cosechas_hoy)
            titulo = "¡ALERTA MÁXIMA!"
        
        if alertas_tempranas:
            if mensaje:
                mensaje += "\n\n"
            mensaje += "🔔 Preparación de Cosecha:\n" + "\n".join(alertas_tempranas)
            if not titulo:
                 titulo = "Alerta Temprana"

        if mensaje:
            self.recordatorio_label.config(text=mensaje, style='Alerta.TLabel')
            messagebox.showwarning(titulo, mensaje)
        else:
            self.recordatorio_label.config(text="Todo al día. Ninguna cosecha ni alerta activa.", style='TLabel', foreground=COLOR_ENFASIS_VERDE)


# --- 5. INICIO DE LA APLICACIÓN ---
if __name__ == "__main__":
    app = AppCultivos()
    app.mainloop()