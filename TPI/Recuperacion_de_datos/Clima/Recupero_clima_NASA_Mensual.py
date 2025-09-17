import requests
import pandas as pd
from datetime import datetime, timedelta
#import time

def obtener_datos_nasa_power(lat, lon, años_atras=44):
    """
    Obtiene datos climáticos de NASA POWER para agricultura.
    
    Args:
        lat (float): Latitud (-90 a 90)
        lon (float): Longitud (-180 a 180)
        años_atras (int): Número de años hacia atrás para obtener datos
    
    Returns:
        pandas.DataFrame: DataFrame con los datos climáticos
    """
    
    # Validar coordenadas
    if not (-90 <= lat <= 90):
        raise ValueError("La latitud debe estar entre -90 y 90")
    if not (-180 <= lon <= 180):
        raise ValueError("La longitud debe estar entre -180 y 180")
    
    # Configuración de fechas
    fecha_actual = datetime.now()
    fecha_inicio = fecha_actual - timedelta(days=años_atras * 365)
    
    # Formatear fechas para la API (YYYYMMDD)
    start_date = fecha_inicio.strftime('%Y%m%d')
    end_date = fecha_actual.strftime('%Y%m%d')
    
    # Variables climáticas importantes para agricultura
    # T2M: Temperatura a 2m (°C)
    # RH2M: Humedad relativa a 2m (%)
    # WS2M: Velocidad del viento a 2m (m/s)
    # PRECTOTCORR: Precipitación total corregida (mm/día)
    variables = "T2M,RH2M,WS2M,PRECTOTCORR"
    
    # Construir URL de la API NASA POWER
    # Usando datos diarios en lugar de mensuales para más precisión
    base_url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    params = {
        'parameters': variables,
        'community': 'AG',  # Agricultural community
        'longitude': lon,
        'latitude': lat,
        'start': start_date,
        'end': end_date,
        'format': 'JSON'
    }
    
    print(f"Consultando datos NASA POWER para coordenadas ({lat}, {lon})...")
    #print(f"Período: {fecha_inicio.strftime('%Y-%m-%d')} a {fecha_actual.strftime('%Y-%m-%d')}")
    #print(f"URL: {base_url}")
    #print(f"Parámetros: {params}")
    
    try:
        # Realizar solicitud a la API
        response = requests.get(base_url, params=params, timeout=60)
        
        #print(f"Código de respuesta: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar que los datos estén presentes
            if 'properties' not in data or 'parameter' not in data['properties']:
                print("Error: Estructura de datos inesperada en la respuesta")
                return crear_dataframe_vacio()
            
            parametros = data['properties']['parameter']
            
            # Obtener las fechas (claves de cualquier parámetro)
            fechas = list(parametros['T2M'].keys()) if 'T2M' in parametros else []
            
            if not fechas:
                print("Error: No se encontraron datos en la respuesta")
                return crear_dataframe_vacio()
            
            # Crear listas para cada variable
            temperaturas = []
            humedades = []
            vientos = []
            precipitaciones = []
            fechas_formateadas = []
            
            for fecha in fechas:
                try:
                    # Convertir fecha de YYYYMMDD a datetime
                    fecha_dt = datetime.strptime(fecha, '%Y%m%d')
                    fechas_formateadas.append(fecha_dt)
                    
                    # Obtener valores (manejar valores faltantes)
                    temp = parametros.get('T2M', {}).get(fecha, None)
                    hum = parametros.get('RH2M', {}).get(fecha, None)
                    viento = parametros.get('WS2M', {}).get(fecha, None)
                    precip = parametros.get('PRECTOTCORR', {}).get(fecha, None)
                    
                    # Convertir valores -999 (missing data) a None
                    temp = None if temp == -999 else temp
                    hum = None if hum == -999 else hum
                    viento = None if viento == -999 else viento
                    precip = None if precip == -999 else precip
                    
                    temperaturas.append(temp)
                    humedades.append(hum)
                    vientos.append(viento)
                    precipitaciones.append(precip)
                    
                except ValueError as e:
                    print(f"Error procesando fecha {fecha}: {e}")
                    continue
            
            # Crear DataFrame
            df = pd.DataFrame({
                'fecha': fechas_formateadas,
                'temperatura_media_C': temperaturas,
                'humedad_relativa_%': humedades,
                'velocidad_viento_m_s': vientos,
                'precipitacion_mm_dia': precipitaciones
            })
            
            # Convertir velocidad de viento de m/s a km/h
            df['velocidad_viento_km_h'] = df['velocidad_viento_m_s'] * 3.6
            
            #print(f"✅ Datos obtenidos exitosamente: {len(df)} registros")
            return df
            
        elif response.status_code == 422:
            print("Error 422: Parámetros inválidos")
            print("Posibles causas:")
            print("- Coordenadas fuera de rango")
            print("- Fechas inválidas")
            print("- Parámetros no disponibles para la región")
            print(f"Respuesta del servidor: {response.text}")
            return crear_dataframe_vacio()
            
        else:
            print(f"Error HTTP {response.status_code}: {response.text}")
            return crear_dataframe_vacio()
            
    except requests.exceptions.Timeout:
        print("Error: Timeout en la solicitud. La API de NASA puede estar lenta.")
        return crear_dataframe_vacio()
        
    except requests.exceptions.RequestException as e:
        print(f"Error en la solicitud: {e}")
        return crear_dataframe_vacio()
        
    except Exception as e:
        print(f"Error inesperado: {e}")
        return crear_dataframe_vacio()

def crear_dataframe_vacio():
    """Crea un DataFrame vacío con las columnas esperadas"""
    return pd.DataFrame(columns=[
        'fecha', 'temperatura_media_C', 'humedad_relativa_%', 
        'velocidad_viento_m_s', 'precipitacion_mm_dia', 'velocidad_viento_km_h'
    ])

def procesar_datos_mensuales(df):
    """
    Convierte datos diarios a promedios/sumas mensuales
    """
    if df.empty:
        return df
    
    # Asegurar que la fecha sea datetime
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    # Crear columnas año-mes para agrupación
    df['año_mes'] = df['fecha'].dt.to_period('M')
    
    # Agrupar por mes y calcular estadísticas apropiadas
    datos_mensuales = df.groupby('año_mes').agg({
        'temperatura_media_C': 'mean',
        'humedad_relativa_%': 'mean',
        'velocidad_viento_m_s': 'mean',
        'precipitacion_mm_dia': 'sum',  # Suma para obtener precipitación mensual total
        'velocidad_viento_km_h': 'mean'
    }).round(2)
    
    # Renombrar columna de precipitación
    datos_mensuales = datos_mensuales.rename(columns={'precipitacion_mm_dia': 'precipitacion_mm_mes'})
    
    # Resetear índice y convertir período a fecha
    datos_mensuales = datos_mensuales.reset_index()
    datos_mensuales['fecha'] = datos_mensuales['año_mes'].dt.start_time
    datos_mensuales = datos_mensuales.drop('año_mes', axis=1)
    
    # Reordenar columnas
    columnas_orden = ['fecha', 'temperatura_media_C', 'humedad_relativa_%', 
                     'velocidad_viento_m_s', 'velocidad_viento_km_h', 'precipitacion_mm_mes']
    datos_mensuales = datos_mensuales[columnas_orden]
    
    return datos_mensuales


def main(latitud, longitud, departamento, crear_archivo_bool = False, años_atras=44):
    #print("=== OBTENIENDO DATOS DIARIOS Y PROCESANDO MENSUALMENTE ===")
    # Obtener datos diarios
    df_clima_diario = obtener_datos_nasa_power(latitud, longitud, años_atras)
    
    if not df_clima_diario.empty:
        # Procesar a datos mensuales
        df_clima = procesar_datos_mensuales(df_clima_diario)
        #print(f"✅ Datos diarios procesados a {len(df_clima)} registros mensuales")
    
    if not df_clima.empty:
        # Guardar en CSV
        output_path = f"Recuperacion_de_datos/Clima/clima_nasa_mensual_44_anios_de_{departamento}.csv"
        if crear_archivo_bool:
            df_clima.to_csv(output_path, index=False)
        
        # Verificar datos faltantes
        #print("\nDatos faltantes por columna:")
        #print(df_clima.isnull().sum())
  
    else:
        print("\n❌ No se pudieron obtener datos de NASA POWER")
        print("Verifica las coordenadas y la conexión a internet")
    
    return df_clima

# Ejemplo de uso
if __name__ == "__main__":
    # Coordenadas de ejemplo (Córdoba, Argentina)
    latitud = -31.4
    longitud = -64.2
    años_atras = 44

    main(latitud, longitud, años_atras)
    
    