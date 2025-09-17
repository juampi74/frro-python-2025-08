import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn import tree
from sklearn.model_selection import GridSearchCV
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import KFold
import matplotlib.pyplot as plt
from tqdm import tqdm
import numpy as np
import joblib

def limpiar_df(df: pd.DataFrame) -> pd.DataFrame:
    # Definimos los valores a considerar como "inválidos"
    invalid_values = ["SD", "sin datos", "", " ", "null", "NULL", "NaN", "nan", None]

    # Reemplazamos esos valores por NaN
    df_limpio = df.replace(invalid_values, pd.NA)

    # Eliminamos filas con al menos un NaN
    df_limpio = df_limpio.dropna(how="any")

    return df_limpio

def guardar_modelo(modelo, ruta="model/modelo_gbm_viento_m_s.pkl"):
    joblib.dump(modelo, ruta)
    print(f"Modelo guardado en {ruta}")

def separar_fecha(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reemplaza la columna 'fecha' (formato YYYY-MM-DD)
    por dos columnas: 'anio' y 'mes'.
    """
    # Convertir a datetime
    df['fecha'] = pd.to_datetime(df['fecha'], format='%Y-%m-%d')

    # Crear nuevas columnas
    df['anio'] = df['fecha'].dt.year
    df['mes'] = df['fecha'].dt.month

    # Eliminar la columna original
    df = df.drop(columns=['fecha'])

    return df


def entrenar_y_devolver_modelo(clima_file, head_cant=None):
    # DATA PREPARATION
    df = pd.read_csv(clima_file)

    if head_cant is not None:
        df = df.head(head_cant)  # Usar solo las primeras head_cant filas para pruebas rápidas

    df_convertido = limpiar_df(df)
    df_convertido = separar_fecha(df_convertido)

    # Crear columna lag: viento del mes anterior
    df_convertido['viento_lag1'] = df_convertido['velocidad_viento_m_s'].shift(1)

    # Eliminar la primera fila (porque lag1 queda NaN en el inicio)
    df_convertido = df_convertido.dropna()

    # Dividir train / test
    df_train, df_test = np.split(df_convertido, [int(0.8*len(df_convertido))])

    # Features incluyen año, mes y viento del mes anterior
    X_train = df_train[['anio', 'mes', 'viento_lag1']]
    X_test = df_test[['anio', 'mes', 'viento_lag1']]

    y_train = df_train['velocidad_viento_m_s']
    y_test = df_test['velocidad_viento_m_s']

    # CROSSVALIDATION
    crossvalidation = KFold(n_splits=5, shuffle=True, random_state=1)

    GBR2 = GradientBoostingRegressor(
        n_estimators=1000, learning_rate=0.05,
        max_depth=3, subsample=1, random_state=1
    )

    score = np.mean(cross_val_score(
        GBR2, X_train, y_train,
        scoring='neg_mean_squared_error',
        cv=crossvalidation, n_jobs=1
    ))
    print("Final model score:", score)

    # Entrenar
    GBR2.fit(X_train, y_train)
    predicciones = GBR2.predict(X_test)
    #predicciones = GBR2.predict(X_train)
    guardar_modelo(GBR2)

    # GRÁFICAS
    plt.figure(figsize=(10, 6))
    plt.plot(df_convertido['velocidad_viento_m_s'].values, label='Valores Reales', color='blue', alpha=0.6)

    plt.plot(
        range(len(y_train), len(y_train) + len(y_test)),
        y_test,
        label='Reales (test)',
        color='black',
        alpha=0.6
    )

    plt.plot(range(len(y_train), len(y_train) + len(y_test)), predicciones, label='Predicciones', color='red', alpha=0.6)
    #plt.plot(predicciones, label='Predicciones', color='red', alpha=0.6)

    titulo = 'Viento Real vs Predicho'
    plt.title(titulo)
    plt.xlabel('Índice de Muestra')
    plt.ylabel('Velocidad Viento (m/s)')
    plt.legend()
    plt.savefig(f"Archivos/Graficas/{titulo.replace(' ', '_')}.png", dpi=600, bbox_inches="tight")
    plt.show()

    return GBR2



# -------------------------------
# MAIN
# -------------------------------
def main(clima_file, entradas_para_predecir = None, modelo = None):
    if entradas_para_predecir is None:
        head_cant = int(input("¿Cuántas filas usar para entrenar? (0 para todas): "))
        if head_cant == 0:
            head_cant = None
        modelo = entrenar_y_devolver_modelo(clima_file, head_cant)
    else:
        # Cargar modelo guardado
        modelo = joblib.load("model/modelo_gbm_viento_m_s.pkl")

        df = limpiar_df(entradas_para_predecir)
        df = separar_fecha(df)
        df['viento_lag1'] = df['velocidad_viento_m_s'].shift(1)
        df = df.dropna()
        ultima_tupla = df.tail(1)

        predicciones = []

        for i in range(14):
            prediccion = modelo.predict(ultima_tupla[['anio', 'mes', 'viento_lag1']])
            nueva_fila = {
                'anio': ultima_tupla['anio'].values[0] + (ultima_tupla['mes'].values[0] // 12),
                'mes': (ultima_tupla['mes'].values[0] % 12) + 1,
                'velocidad_viento_m_s': prediccion[0],
                'viento_lag1': ultima_tupla['velocidad_viento_m_s'].values[0]
            }
            nueva_fila_df = pd.DataFrame([nueva_fila])
            predicciones.append(prediccion[0])
            ultima_tupla = nueva_fila_df

        return predicciones
    


if __name__ == "__main__":
    clima_file = f"Recuperacion_de_datos/Clima/clima_nasa_mensual_44_anios_de_Rosario.csv"
    main(clima_file)
