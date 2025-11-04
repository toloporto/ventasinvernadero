# --- 1. IMPORTS NECESARIOS ---
import pandas as pd # Para manejo de datos (DataFrames)
import matplotlib.pyplot as plt # Para la visualización de datos
import os # Para verificar si el archivo existe

# --- 2. CONFIGURACIÓN ---
NOMBRE_ARCHIVO = 'ventas_mensuales.csv'

# --- 3. FUNCIÓN PRINCIPAL DE ANÁLISIS ---
def analizar_ventas(nombre_archivo):
    """
    Carga el archivo CSV, calcula métricas financieras clave y genera un gráfico.
    """
    print(f"Iniciando análisis del archivo: {nombre_archivo}...")

    # 3.1. Carga de Datos y Manejo de Errores
    if not os.path.exists(nombre_archivo):
        print(f"\n❌ ERROR: No se encontró el archivo '{nombre_archivo}'.")
        print("Asegúrate de que el archivo esté en la misma carpeta que este script.")
        return

    try:
        # Cargar el CSV en un DataFrame de pandas
        df = pd.read_csv(nombre_archivo, sep=',')
        print("✅ Datos cargados con éxito.")
    except pd.errors.ParserError as e:
        print(f"\n❌ ERROR de formato al leer el CSV: {e}")
        print("Asegúrate de que el delimitador sea la coma (,) y el archivo esté limpio.")
        return
    except Exception as e:
        print(f"\n❌ ERROR inesperado al cargar los datos: {e}")
        return

    # 3.2. Limpieza y Preparación de Datos
    # Aseguramos que la columna clave 'Venta_Total' sea numérica
    df['Venta_Total'] = pd.to_numeric(df['Venta_Total'], errors='coerce')
    
    # Eliminamos filas que pudieran haber fallado en la conversión
    df.dropna(subset=['Venta_Total'], inplace=True)
    
    print("✅ Datos preparados y columna 'Venta_Total' verificada.")


    # --- 4. CÁLCULO DE MÉTRICAS CLAVE ---

    print("\n==================================")
    print("      📊 REPORTE DE VENTAS GLOBAL")
    print("==================================")
    
    # Venta Total (Suma)
    venta_total_global = df['Venta_Total'].sum()
    print(f"💰 Venta Total Global: €{venta_total_global:,.2f}")

    # Venta Promedio (Media)
    venta_media = df['Venta_Total'].mean()
    print(f"📈 Venta Media por Transacción: €{venta_media:,.2f}")
    
    # Venta Máxima y Mínima
    venta_maxima = df['Venta_Total'].max()
    venta_minima = df['Venta_Total'].min()
    print(f"🔝 Venta Máxima en una Transacción: €{venta_maxima:,.2f}")
    print(f"⬇️ Venta Mínima en una Transacción: €{venta_minima:,.2f}")
    
    # --- 5. ANÁLISIS AGRUPADO (Ventas por Producto) ---
    
    # Agrupar las ventas por la columna 'Producto'
    ventas_por_producto = df.groupby('Producto')['Venta_Total'].sum().sort_values(ascending=False)
    
    print("\n==================================")
    print("    🔍 VENTAS TOTALES POR PRODUCTO")
    print("==================================")
    print(ventas_por_producto.to_string())


    # --- 6. VISUALIZACIÓN DE DATOS con Matplotlib ---
    
    plt.figure(figsize=(10, 6)) # Define el tamaño del gráfico
    
    # Crear el gráfico de barras
    ventas_por_producto.plot(kind='bar', color='#1E8449') 
    
    # Personalización del gráfico
    plt.title('Ventas Totales por Tipo de Producto', fontsize=14, fontweight='bold')
    plt.xlabel('Producto', fontsize=12)
    plt.ylabel('Venta Total (€)', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.7) 
    plt.tight_layout()
    
    print("\n✅ Generando gráfico de visualización. Una ventana se abrirá...")
    plt.show() # Muestra la ventana del gráfico


# --- 7. EJECUCIÓN DEL SCRIPT ---
if __name__ == "__main__":
    analizar_ventas(NOMBRE_ARCHIVO)