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


def crear_archivos_entreno():
    """Crea dataframes y archivos de entrenamiento"""
    from creacion_de_archivo_de_entreno_completo import main as creacion_archivo_entreno

    if not os.path.exists("Archivos/df_semillas_suelo_phases.csv"):
        print("Creando df_semillas_suelo_clima...")
        creacion_archivo_entreno()
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

    # Crear archivos de entrenamiento
    crear_archivos_entreno()


    # Entrenar GBM
    if not os.path.exists("model/model_gbr_phase.pkl"):
        entrenar_gbm()


    # Ejecutar algoritmo genético
    respuesta = 's'
    while respuesta == 's':
        ejecutar_ag(departamento, longitud, latitud, metros_cuadrados)
        respuesta = input("\nDesea ejecutar el algoritmo genético con otros parámetros? (si = s, no = n) ").strip().lower()

    print("FIN DEL PROGRAMA")
    sys.exit(0)
