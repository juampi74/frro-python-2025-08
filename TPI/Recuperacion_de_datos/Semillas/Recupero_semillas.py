import pandas as pd
from limpio_caracteres import limpiar_texto
import glob
import os

# ------------------------------------ AVENA ------------------------------------
def recupero_datos_avena():
    # Load the dataset
    avena_data = pd.read_csv('Bases_de_datos/Semillas/avena-serie-1923-2024.csv', encoding='latin1')
    avena_data = avena_data.apply(lambda col: col.map(limpiar_texto))
    avena_collumns = avena_data[['cultivo_nombre', 'anio', 'departamento_nombre', 'superficie_sembrada_ha', 'superficie_cosechada_ha', 
                                 'produccion_tn', 'rendimiento_kgxha']]
    print(avena_collumns.head())
    avena_collumns.to_csv('Recuperacion_de_datos/Semillas/Archivos generados/avena_recuperado.csv', index=False)

# ------------------------------------ CEBADA -----------------------------------
def recupero_datos_cebada():
    # Load the dataset
    cebada_data = pd.read_csv('Bases_de_datos/Semillas/cebada-total-serie-1938-2024.csv', encoding='latin1')
    cebada_data = cebada_data.apply(lambda col: col.map(limpiar_texto))
    cebada_collumns = cebada_data[['cultivo_nombre', 'anio', 'departamento_nombre', 'superficie_sembrada_ha', 'superficie_cosechada_ha', 
                                   'produccion_tn', 'rendimiento_kgxha']]
    print(cebada_collumns.head())
    cebada_collumns.to_csv('Recuperacion_de_datos/Semillas/Archivos generados/cebada_recuperado.csv', index=False)

# ------------------------------------ CENTENO -----------------------------------
def recupero_datos_centeno():
    # Load the dataset
    centeno_data = pd.read_csv('Bases_de_datos/Semillas/centeno-serie-1923-2024.csv', encoding='latin1')
    centeno_data = centeno_data.apply(lambda col: col.map(limpiar_texto))
    centeno_collumns = centeno_data[['cultivo_nombre', 'anio', 'departamento_nombre', 'superficie_sembrada_ha', 'superficie_cosechada_ha', 
                                     'produccion_tn', 'rendimiento_kgxha']]
    print(centeno_collumns.head())
    centeno_collumns.to_csv('Recuperacion_de_datos/Semillas/Archivos generados/centeno_recuperado.csv', index=False)

# ------------------------------------ GIRASOL -----------------------------------
def recupero_datos_girasol():
    # Load the dataset
    girasol_data = pd.read_csv('Bases_de_datos/Semillas/girasol-serie-1969-2023.csv', encoding='latin1')
    girasol_data = girasol_data.apply(lambda col: col.map(limpiar_texto))
    girasol_collumns = girasol_data[['cultivo_nombre', 'anio', 'departamento_nombre', 'superficie_sembrada_ha', 'superficie_cosechada_ha', 
                                     'produccion_tn', 'rendimiento_kgxha']]
    print(girasol_collumns.head())
    girasol_collumns.to_csv('Recuperacion_de_datos/Semillas/Archivos generados/girasol_recuperado.csv', index=False)

# ------------------------------------ MAIZ -----------------------------------
def recupero_datos_maiz():
    # Load the dataset
    maiz_data = pd.read_csv('Bases_de_datos/Semillas/maiz-serie-1923-2023.csv', encoding='latin1')
    maiz_data = maiz_data.apply(lambda col: col.map(limpiar_texto))
    maiz_collumns = maiz_data[['cultivo_nombre', 'anio', 'departamento_nombre', 'superficie_sembrada_ha', 'superficie_cosechada_ha', 
                               'produccion_tn', 'rendimiento_kgxha']]
    print(maiz_collumns.head())
    maiz_collumns.to_csv('Recuperacion_de_datos/Semillas/Archivos generados/maiz_recuperado.csv', index=False)

# ------------------------------------ MANI -----------------------------------
def recupero_datos_mani():
    # Load the dataset
    mani_data = pd.read_csv('Bases_de_datos/Semillas/mani-serie-1927-2023.csv', encoding='latin1')
    mani_data = mani_data.apply(lambda col: col.map(limpiar_texto))
    mani_collumns = mani_data[['cultivo_nombre', 'anio', 'departamento_nombre', 'superficie_sembrada_ha', 'superficie_cosechada_ha', 
                               'produccion_tn', 'rendimiento_kgxha']]
    print(mani_collumns.head())
    mani_collumns.to_csv('Recuperacion_de_datos/Semillas/Archivos generados/mani_recuperado.csv', index=False)

# ------------------------------------ MIJO -----------------------------------
def recupero_datos_mijo():
    # Load the dataset
    mijo_data = pd.read_csv('Bases_de_datos/Semillas/mijo-serie-1935-2023.csv', encoding='latin1')
    mijo_data = mijo_data.apply(lambda col: col.map(limpiar_texto))
    mijo_collumns = mijo_data[['cultivo_nombre', 'anio', 'departamento_nombre', 'superficie_sembrada_ha', 'superficie_cosechada_ha', 
                               'produccion_tn', 'rendimiento_kgxha']]
    print(mijo_collumns.head())
    mijo_collumns.to_csv('Recuperacion_de_datos/Semillas/Archivos generados/mijo_recuperado.csv', index=False)

# ------------------------------------ SOJA -----------------------------------
def recupero_datos_soja():
    # Load the dataset
    soja_data = pd.read_csv('Bases_de_datos/Semillas/soja-serie-1941-2023.csv', encoding='latin1')
    soja_data = soja_data.apply(lambda col: col.map(limpiar_texto))
    soja_collumns = soja_data[['cultivo_nombre', 'anio', 'departamento_nombre', 'superficie_sembrada_ha', 'superficie_cosechada_ha', 
                               'produccion_tn', 'rendimiento_kgxha']]
    print(soja_collumns.head())
    soja_collumns.to_csv('Recuperacion_de_datos/Semillas/Archivos generados/soja_recuperado.csv', index=False)

# ------------------------------------ TRIGO -----------------------------------
def recupero_datos_trigo():
   # Leer el archivo en latin1
    trigo_data = pd.read_csv('Bases_de_datos/Semillas/trigo-serie-1927-2024.csv', encoding='latin1')
    trigo_data = trigo_data.apply(lambda col: col.map(limpiar_texto))
    trigo_columnas = trigo_data[['cultivo_nombre', 'anio', 'departamento_nombre', 'superficie_sembrada_ha',
                                'superficie_cosechada_ha', 'produccion_tn', 'rendimiento_kgxha']]
    print(trigo_columnas.head())
    trigo_columnas.to_csv('Recuperacion_de_datos/Semillas/Archivos generados/trigo_recuperado.csv', 
                          index=False, encoding='utf-8')

# ------------------------------------ COMPLETO -----------------------------------
def recupero_datos_completo():
    # Diccionario para estandarizar nombres
    rename_dict = {
        'cultivo': 'cultivo_nombre',
        'ciclo': 'anio',
        'departamento_nombre': 'departamento_nombre',
        'sup_sembrada': 'superficie_sembrada_ha',
        'sup_cosechada': 'superficie_cosechada_ha',
        'produccion': 'produccion_tn',
        'rendimiento': 'rendimiento_kgxha'
    }

    semillas_data = pd.read_csv(
        'Bases_de_datos/Semillas/1_Historico_Semillas.csv',
        encoding='latin1',
        low_memory=False
    )

    # Limpieza de datos
    semillas_data = semillas_data.apply(lambda col: col.map(limpiar_texto))

    # Renombrar columnas según el diccionario (solo si existen en el DataFrame)
    semillas_data.rename(columns={k: v for k, v in rename_dict.items() if k in semillas_data.columns},
                         inplace=True)

    # Si 'anio' viene como 'ciclo', extraer solo el año inicial
    if 'anio' in semillas_data.columns:
        semillas_data['anio'] = semillas_data['anio'].str.split('/').str[0]

    # Reordenar las columnas en el orden estandar
    columnas_finales = [
        'cultivo_nombre', 'anio', 'departamento_nombre',
        'superficie_sembrada_ha', 'superficie_cosechada_ha',
        'produccion_tn', 'rendimiento_kgxha'
    ]
    semillas_columnas = semillas_data[columnas_finales].copy()

    print(semillas_columnas.head())

    semillas_columnas.to_csv(
        'Recuperacion_de_datos/Semillas/Archivos generados/semillas_historico_recuperado.csv',
        index=False,
        encoding='utf-8'
    )

def concatenar_archivos_semillas():
    carpeta = 'Recuperacion_de_datos/Semillas/Archivos generados/'
    
    # Buscar todos los CSV generados por las funciones anteriores
    archivos_csv = glob.glob(os.path.join(carpeta, '*_recuperado.csv'))
    
    # Leer y concatenar todos en un solo DataFrame
    dfs = []
    for archivo in archivos_csv:
        df = pd.read_csv(archivo, encoding='utf-8')
        dfs.append(df)
    
    if not dfs:
        print("No se encontraron archivos para concatenar.")
        return
    
    combinado = pd.concat(dfs, ignore_index=True)
    
    # Ordenar por jerarquía: anio, departamento_nombre, cultivo_nombre
    combinado['anio'] = combinado['anio'].astype(int)  # asegurar tipo numérico para ordenar
    combinado.sort_values(by=['anio', 'departamento_nombre', 'cultivo_nombre'],
                          ascending=[True, True, True], inplace=True)
    
    # Guardar resultado final
    salida = os.path.join(carpeta, 'semillas_todas_concatenadas.csv')
    combinado.to_csv(salida, index=False, encoding='utf-8')
    
    print(f"Archivos combinados guardados en: {salida}")
    print(combinado.head())
    

# ------------------------------------ MAIN -----------------------------------
if __name__ == "__main__":
    recupero_datos_avena()
    recupero_datos_cebada()
    recupero_datos_centeno()
    recupero_datos_girasol()
    recupero_datos_maiz()
    recupero_datos_mani()
    recupero_datos_mijo()
    recupero_datos_soja()
    recupero_datos_trigo()
    recupero_datos_completo()

    # Combino todos los archivos recuperados en uno solo
    concatenar_archivos_semillas()