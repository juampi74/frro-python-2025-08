import pandas as pd
import ast

def expand_array_columns(csv_path = "Archivos/df_con_prod.csv"):
    # Leer CSV
    df = pd.read_csv(csv_path)

    # Detectar columnas con arrays (listas en forma de string)
    array_cols = []
    for col in df.columns:
        if df[col].astype(str).str.startswith("[").any():
            array_cols.append(col)

    print(f"📊 Columnas con arrays detectadas: {array_cols}")

    # Expandir cada columna con arrays
    for col in array_cols:
        # Convertir string a lista real
        df[col] = df[col].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else x)

        # Determinar tamaño máximo de array en esa columna
        max_len = df[col].dropna().map(len).max()

        print(f"  ↳ Expandiendo {col} en {max_len} columnas...")

        # Crear nuevas columnas
        for i in range(max_len):
            df[f"{col}_{i+1}"] = df[col].apply(lambda x: x[i] if isinstance(x, list) and len(x) > i else None)

        # Eliminar columna original
        df.drop(columns=[col], inplace=True)

    output_path = "Archivos/df_prod_expandido.csv"

    cols = [c for c in df.columns if c not in ["superficie_sembrada_ha", "produccion_tn"]]
    cols += ["superficie_sembrada_ha", "produccion_tn"]

    # Reordenar el DataFrame
    df = df[cols]

    df.to_csv(output_path, index=False)

    return df


def create_df_with_differents_outputs():
    df_final = pd.read_csv("Archivos/df_semillas_suelo_clima.csv")

    '''cols_cosecha = [
        "cultivo_nombre", "anio", "organic_carbon", "ph", "clay", "silt", "sand", 
        "temperatura_media_C", "humedad_relativa_%", "velocidad_viento_m_s", 
        "precipitacion_mm_mes", "superficie_sembrada_ha",                               # Entradas
        "superficie_cosechada_ha"                 # Salida esperada
    ]'''

    cols_prod = [
        "cultivo_nombre", "anio", "organic_carbon", "ph", "clay", "silt", "sand", 
        "temperatura_media_C", "humedad_relativa_%", "velocidad_viento_m_s", 
        "precipitacion_mm_mes", "superficie_sembrada_ha",                               # Entradas
        "produccion_tn"                 # Salida esperada
    ]

    '''cols_rend = [
        "cultivo_nombre", "anio", "organic_carbon", "ph", "clay", "silt", "sand", 
        "temperatura_media_C", "humedad_relativa_%", "velocidad_viento_m_s", 
        "precipitacion_mm_mes", "superficie_sembrada_ha",                               # Entradas
        "rendimiento_kgxha"                 # Salida esperada
    ]'''

    #df_con_cosecha = df_final[cols_cosecha].copy()
    df_con_prod = df_final[cols_prod].copy()
    #df_con_rend = df_final[cols_rend].copy()

    #df_con_cosecha["cultivo_nombre"] = df_con_cosecha["cultivo_nombre"].str.lower()
    df_con_prod["cultivo_nombre"] = df_con_prod["cultivo_nombre"].str.lower()
    #df_con_rend["cultivo_nombre"] = df_con_rend["cultivo_nombre"].str.lower()

    #df_con_cosecha.to_csv('Archivos/df_con_cosecha.csv', index=False)
    df_con_prod.to_csv('Archivos/df_con_prod.csv', index=False)
    #df_con_rend.to_csv('Archivos/df_con_rend.csv', index=False)


if __name__ == "__main__":

    create_df_with_differents_outputs()

    df = expand_array_columns("Archivos/df_con_prod.csv")
