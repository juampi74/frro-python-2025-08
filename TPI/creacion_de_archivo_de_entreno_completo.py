import pandas as pd
from pathlib import Path
import sys, os
from shapely.geometry import MultiPoint
import numpy as np
from configuracion_ReglasNegocio import cultivos_inv, cultivos_ver

# Agrego la carpeta raíz del proyecto (TPI) al PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

#from Recuperacion_de_datos.Clima.Recupero_clima_NASA_Mensual import obtener_datos_nasa_power, procesar_datos_mensuales
from Mapa.GIS.departamento import encontrar_departamento as transformo_coord_a_depto


N_TRIMESTRES = 7 # cantidad de trimestres previos a usar como input

# -----------------------------
# Filtro el departamento
# -----------------------------
def solo_departamento(coord):
    depto, _ = transformo_coord_a_depto(coord)
    return depto

# Calculo el centroide
def calcular_centroide(coord_list):
    multipoint = MultiPoint(coord_list)
    centroid = multipoint.centroid
    return (centroid.x, centroid.y)  # devuelve (lon, lat)


def agregar_clima_por_departamento(df_suelo_semillas,
                                   strategy="drop"):  # "drop" o "edge_fill"
    """
    Agrega Nino_lag1..Nino_lag7 con ENSO de los 7 trimestres previos al trimestre ancla:
      - cultivos de VERANO  -> ancla = 5 (AMJ)
      - cultivos de INVIERNO-> ancla = 11 (OND)

    strategy:
      - "drop": elimina filas con algún lag faltante (recomendado para RN).
      - "edge_fill": rellena faltantes de borde con el primer/último valor disponible.
    """
    df = df_suelo_semillas.copy()

    # Leer clima trimestral
    df_clima = pd.read_csv('Recuperacion_de_datos/Clima/phase_trimestral.csv')

    # Filtrar cultivos contemplados
    # Construí el set de cultivos válidos en minúscula
    cultivos_validos = {s.strip().casefold() for s in (cultivos_inv + cultivos_ver)}

    # Filtrá el DF normalizando la columna a minúscula
    mask = (
        df['cultivo_nombre']
        .astype(str)
        .str.strip()
        .str.casefold()
        .isin(cultivos_validos)
    )
    df = df[mask].copy()

    # Ancla por tipo de cultivo
    is_ver = df['cultivo_nombre'].isin(cultivos_ver)
    df['anchor_trim'] = np.where(is_ver, 5, 11).astype('int16')

    # Índice absoluto (1..12 por año) para restar lags
    df['anchor_idx'] = df['anio'].astype('int32') * 12 + df['anchor_trim']

    # Serie climática indexada por (year, trimester)
    clim_s = (
        df_clima[['year', 'trimester', 'Nino']]
        .dropna()
        .astype({'year': int, 'trimester': int})
        .set_index(['year', 'trimester'])
    )['Nino']

    # Agregar lags previos al ancla
    for k in range(1, N_TRIMESTRES + 1):
        idx_k = df['anchor_idx'] - k
        year_k = ((idx_k - 1) // 12).astype(int)
        tri_k  = ((idx_k - 1) % 12 + 1).astype(int)

        mi = pd.MultiIndex.from_arrays([year_k, tri_k], names=['year', 'trimester'])
        vals = clim_s.reindex(mi).to_numpy()

        if strategy == "edge_fill":
            # Relleno de bordes por clamp al primer/último valor disponible
            # (solo aplica si el (año, trimestre) está fuera del rango de clim_s)
            if len(clim_s) > 0:
                first_val = float(clim_s.iloc[0])
                last_val  = float(clim_s.iloc[-1])
                # donde hay NaN, reemplazo por primer/último según esté antes/después del rango
                min_key = clim_s.index.min()
                max_key = clim_s.index.max()
                fixed = []
                for (yk, tk), v in zip(mi, vals):
                    if np.isnan(v):
                        if (yk, tk) <= min_key:
                            fixed.append(first_val)
                        elif (yk, tk) >= max_key:
                            fixed.append(last_val)
                        else:
                            # caso raro: hueco interno (no debería existir)
                            fixed.append(0.0)
                    else:
                        fixed.append(float(v))
                vals = np.asarray(fixed, dtype=float)

        df[f'Nino_lag{k}'] = vals

    # Quitar auxiliares
    df.drop(columns=['anchor_trim', 'anchor_idx'], inplace=True)

    # ENFORCE: sin NaN
    lag_cols = [f'Nino_lag{k}' for k in range(1, N_TRIMESTRES + 1)]
    if strategy == "drop":
        # eliminar filas con algún NaN en lags
        df = df[df[lag_cols].notna().all(axis=1)].copy()

    # cast a entero compacto para RN (−1,0,1)
    df[lag_cols] = df[lag_cols].astype('int8')

    # sanity check final (garantía)
    assert not df[lag_cols].isna().any().any(), "Quedaron NaN en lags"

    return df


def crear_df_suelo_semillas(path_suelo_semillas):
    # Recupero todos los datos de las semillas desde min_year en adelante
    df_semillas = pd.read_csv('Recuperacion_de_datos/Semillas/Archivos generados/semillas_todas_concatenadas.csv')

    # Asegurar que las semillas tengan al menos un año de datos climáticos previos
    df_semillas = df_semillas[df_semillas['anio'] >= 1983] # Aseguramos que las semillas tengan al menos un año de datos climáticos previos.

    df_suelo = pd.read_csv('Recuperacion_de_datos/Suelos/suelo_unido.csv')

    # Debo limpiar las columnas con muchos datos faltantes porque interfieren mucho en el entreno de la RN.
    # Elimino las columnas que tienen 85% o más datos faltantes
    df_suelo_filtrado = df_suelo.dropna(thresh=len(df_suelo) * 0.15, axis=1).copy()
    df_semillas_filtrado = df_semillas.dropna(thresh=len(df_semillas) * 0.15, axis=1).copy()

    path_archivo_suelo = Path("Recuperacion_de_datos/Suelos/suelo_promedio.csv")

    if path_archivo_suelo.exists():
        df_suelo_promedio = pd.read_csv(path_archivo_suelo)
    else:
        # Crear nueva columna 'departamento' indicando a que departamento corresponde cada dato de suelo
        df_suelo_filtrado.loc[:, 'departamento_nombre'] = df_suelo_filtrado.apply(
            lambda row: solo_departamento([(row['longitude'], row['latitude'])]),
            axis=1
        )
        # Reordenar para que 'departamento' quede como primera columna
        cols = ['departamento_nombre'] + [col for col in df_suelo_filtrado.columns if col != 'departamento_nombre']
        df_suelo_filtrado = df_suelo_filtrado[cols]

        df_suelo_filtrado['coords'] = list(zip(df_suelo_filtrado['longitude'], df_suelo_filtrado['latitude']))

        df_suelo_filtrado.to_csv('Recuperacion_de_datos/Suelos/suelo_filtrado.csv', index=False)

        # Calcular el promedio de las columnas numéricas para cada departamento y centroide para las coordenadas
        df_suelo_promedio = df_suelo_filtrado.groupby('departamento_nombre').agg({
            'coords': lambda x: calcular_centroide(list(x)),   # centroide de todas las coords
            **{col: 'mean' for col in df_suelo_filtrado.columns if col not in ['departamento_nombre', 'coords', 'latitude', 'longitude']}
        }).reset_index()

        df_suelo_promedio.to_csv(path_archivo_suelo, index=False)

    df_suelo_semillas = pd.merge(df_semillas_filtrado, df_suelo_promedio, on = 'departamento_nombre', how = 'inner')
    
    df_suelo_semillas.to_csv(path_suelo_semillas)

    return df_suelo_semillas

# -----------------------------
# PROGRAMA PRINCIPAL
# -----------------------------
def main():

    path_suelo_semillas = 'Archivos/df_suelo_Semillas.csv'

    if not os.path.exists(path_suelo_semillas):
        df_suelo_semillas = crear_df_suelo_semillas(path_suelo_semillas)
    else:
        df_suelo_semillas = pd.read_csv(path_suelo_semillas)

    # Recupero clima para cada centroide de suelo_promedio
    n_meses = 14

    df_final = agregar_clima_por_departamento(df_suelo_semillas, n_meses)

    df_final["cultivo_nombre"] = df_final["cultivo_nombre"].str.strip().str.lower()

    # Como ya no hay merges deberia sacar departamento_nombre y coords
    lags = [f"Nino_lag{k}" for k in range(1, N_TRIMESTRES + 1)]
    column_order = [
        "cultivo_nombre", "anio", "departamento_nombre", "coords",
        "organic_carbon", "ph", "clay", "silt", "sand",
        *lags,
        "superficie_sembrada_ha",
        "superficie_cosechada_ha", "produccion_tn", "rendimiento_kgxha"
    ]
    df_final = df_final[column_order]

    # --- Eliminar filas con datos faltantes o infinitos ---
    # 1) Pasar ±inf a NaN (scikit-learn también los rechaza)
    df_final = df_final.replace([np.inf, -np.inf], np.nan)

    # 2) Marcar filas con al menos un NaN
    mask_nan = df_final.isna().any(axis=1)

    # 3) (Opcional) ver cuántas vas a eliminar
    print("Filas eliminadas por NaN/inf:", int(mask_nan.sum()))

    # 4) Filtrar y resetear índice
    df_final = df_final[~mask_nan].reset_index(drop=True)
    # --- fin limpieza ---

    df_final.to_csv('Archivos/df_semillas_suelo_phases.csv', index=False)
    print("Archivo guardado exitosamente!")


if __name__ == "__main__":
    main()
