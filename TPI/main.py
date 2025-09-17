# --------------------------------------------------------------------------
# MAIN: estimación de la mejor combinación de semillas para un campo
# --------------------------------------------------------------------------

import os
import pandas as pd
from Mapa.GIS.gis_optimizado import correr_app
from creacion_de_archivo_de_entreno_completo import calcular_centroide
import sys

# --------------------------------------
# FUNCIONES AUXILIARES
# --------------------------------------

def entrenar_lstm_y_gbr(latitud, longitud, departamento):
    """Entrena LSTM y modelos GBR si no existen"""
    import pandas as pd
    from Pred_Clima.pred_temp import train_LSTM_temp
    from Pred_Clima.pred_humedad import train_LSTM_humedad
    from Pred_Clima.pred_precip_GBR import main as train_GBR_precip
    from Pred_Clima.pred_viento_GBR import main as train_GBR_viento_ms

    clima_file = f"Recuperacion_de_datos/Clima/clima_nasa_mensual_44_anios_de_{departamento}.csv"
    
    if not os.path.exists(clima_file):
        from Recuperacion_de_datos.Clima.Recupero_clima_NASA_Mensual import main as creo_archivo_clima
        print("Creando archivo de clima...")
        creo_archivo_clima(latitud, longitud, departamento, True)

    print("Leyendo datos de clima...")
    df_clima = pd.read_csv(clima_file)

    print("Entrenando LSTM de temperatura...")
    train_LSTM_temp(df_clima)
    print("Entrenando LSTM de humedad...")
    train_LSTM_humedad(df_clima)
    print("Entrenando GBR de precipitación...")
    train_GBR_precip(clima_file)
    print("Entrenando GBR de viento...")
    train_GBR_viento_ms(clima_file)
    print("Finalizó entrenamiento LSTM/GBR\n")


def crear_archivos_entreno():
    """Crea dataframes y archivos de entrenamiento"""
    from creacion_de_archivo_de_entreno_completo import main as creacion_archivo_entreno
    from funciones_auxiliares_csv import create_df_with_differents_outputs, expand_array_columns

    if not os.path.exists("Archivos/df_semillas_suelo_clima.csv"):
        print("Creando df_semillas_suelo_clima...")
        creacion_archivo_entreno()
    if not os.path.exists("Archivos/df_con_prod.csv"):
        print("Creando df_prod...")
        create_df_with_differents_outputs()
    if not os.path.exists("Archivos/df_prod_expandido.csv"):
        print("Creando df_prod_expandido.csv...")
        expand_array_columns()
    print("Finalizó creación de archivos\n")


def entrenar_gbm():
    """Entrena el GBM"""
    from Red_neuronal.My_GBM import main as entrenar_GBM
    print("Entrenando GBM...")
    entrenar_GBM()
    print("Finalizó entrenamiento GBM\n")


def ejecutar_ag(departamento, longitud, latitud, metros_cuadrados):
    """Ejecuta algoritmo genético"""
    from Algoritmo_Genetico.ag import main as ejecuto_ag
    print("Ejecutando algoritmo genético...")
    ejecuto_ag(departamento, longitud, latitud, metros_cuadrados)
    print("Finalizó AG\n")


# --------------------------------------
# MAIN
# --------------------------------------
if __name__ == "__main__":

    print("Iniciando selección de campo...")
    app = correr_app() 
    print("App cerrada. Continuando ejecución...\n")

    # Obtenemos coordenadas y datos del campo
    longitud, latitud = calcular_centroide(app.coordenadas)
    departamento = app.departamento
    metros_cuadrados = app.area_ha

    # Entrenamiento LSTM + GBR
    entrenar_lstm_y_gbr(latitud, longitud, departamento)

    # Crear archivos de entrenamiento
    crear_archivos_entreno()


    # Entrenar GBM
    if not os.path.exists("model/modelo_gbm_completo.pkl"):
        entrenar_gbm()


    # Ejecutar algoritmo genético
    respuesta = 's'
    while respuesta == 's':
        ejecutar_ag(departamento, longitud, latitud, metros_cuadrados)
        respuesta = input("\nDesea ejecutar el algoritmo genético con otros parámetros? (si = s, no = n) ").strip().lower()

    print("FIN DEL PROGRAMA")
    sys.exit(0)
