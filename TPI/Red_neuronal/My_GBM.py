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



# Convertir la columna cultivo_nombre en un entero que represente cada cultivo
def conversor_cultivo_a_entero(df, cultivo_a_entero=None):
    cultivos = df['cultivo_nombre'].unique()
    if cultivo_a_entero is None:
        cultivo_a_entero = {cultivo: i for i, cultivo in enumerate(cultivos)}
    df['cultivo_nombre'] = df['cultivo_nombre'].map(cultivo_a_entero)
    return df, cultivo_a_entero

def conversor_depto_a_entero(df, depto_a_entero=None):
    cultivos = df['departamento_nombre'].unique()
    if depto_a_entero is None:
        depto_a_entero = {cultivo: i for i, cultivo in enumerate(cultivos)}
    df['departamento_nombre'] = df['departamento_nombre'].map(depto_a_entero)
    return df, depto_a_entero

def conversor_entero_a_cultivo(df, cultivo_a_entero):
    entero_a_cultivo = {i: cultivo for cultivo, i in cultivo_a_entero.items()}
    df['cultivo_nombre'] = df['cultivo_nombre'].map(entero_a_cultivo)
    return df

def conversor_entero_a_depto(df, depto_a_entero):
    entero_a_depto = {i: cultivo for cultivo, i in depto_a_entero.items()}
    df['departamento_nombre'] = df['departamento_nombre'].map(entero_a_depto)
    return df


def limpiar_df(df: pd.DataFrame) -> pd.DataFrame:
    # Definimos los valores a considerar como "inválidos"
    invalid_values = ["SD", "sin datos", "", " ", "null", "NULL", "NaN", "nan", None]

    # Reemplazamos esos valores por NaN
    df_limpio = df.replace(invalid_values, pd.NA)

    # Eliminamos filas con al menos un NaN
    df_limpio = df_limpio.dropna(how="any")

    return df_limpio

def guardar_modelo(modelo, ruta="model/modelo_gbm_completo.pkl"):
    joblib.dump(modelo, ruta)
    print(f"Modelo guardado en {ruta}")


def entrenar_y_devolver_modelo(head_cant = 0):
    # DATA PREPARATION
    df = pd.read_csv("Archivos/df_semillas_suelo_phases.csv")

    if head_cant != 0:
        df = df.head(head_cant)  # Usar solo las primeras head_cant filas para pruebas rápidas

    df_convertido, cultivo_a_entero = conversor_cultivo_a_entero(df)
    df_convertido, depto_a_entero = conversor_depto_a_entero(df_convertido)

    df_convertido = limpiar_df(df_convertido)

    df_train, df_test = np.split(df_convertido, [int(0.8*len(df_convertido))])
    # Incluir el depto con un diccionario
    X_train = df_train[['cultivo_nombre', 'anio', 'departamento_nombre', 'organic_carbon', 'ph', 'clay', 'silt', 'sand', 
                    'Nino_lag1', 'Nino_lag2', 'Nino_lag3', 'Nino_lag4', 'Nino_lag5', 'Nino_lag6', 'Nino_lag7',
                    'superficie_sembrada_ha']]

    X_test = df_test[['cultivo_nombre', 'anio', 'departamento_nombre', 'organic_carbon', 'ph', 'clay', 'silt', 'sand', 
                    'Nino_lag1', 'Nino_lag2', 'Nino_lag3', 'Nino_lag4', 'Nino_lag5', 'Nino_lag6', 'Nino_lag7',
                    'superficie_sembrada_ha']]

    y_train = df_train['produccion_tn']
    y_test = df_test['produccion_tn']

    # BASELINE MODEL
    #crossvalidation = KFold(n_splits = 10, shuffle = True, random_state = 1)
    crossvalidation = KFold(n_splits = 5, shuffle = True, random_state = 1)

    for depth in range(1, 10):
        tree_regressor = tree.DecisionTreeRegressor(max_depth = depth, random_state = 1)
        '''if tree_regressor.fit(X_train, y_train).tree_.max_depth < depth:
            break'''
        score = np.mean(cross_val_score(tree_regressor, X_train, y_train,
                                        scoring='neg_mean_squared_error',
                                        cv=crossvalidation,n_jobs=1))

        print("Depth:", depth, "   -  Score:", score)


    # HYPERPARAMETER TUNING
    # Solo ejecutar si se cambian los parámetros
    decition = input("¿Hacer hyperparameter tuning? (s/n): ")
    if decition.lower() == 's':
        print("Iniciando hyperparameter tuning...") 
        GBR = GradientBoostingRegressor()
        search_grid = {'n_estimators':[500, 1000, 2000], 'learning_rate':[.001, 0.01, .1], 'max_depth':[1, 2, 4], 
                       'subsample':[.5, .75, 1], 'random_state':[1]}
        #search_grid = {'n_estimators':[500, 1000], 'learning_rate':[.001, 0.05], 'max_depth':[1, 3], 'subsample':[.5, 1], 'random_state':[1]}
        search = GridSearchCV(estimator = GBR, param_grid = search_grid,
                            scoring = 'neg_mean_squared_error', n_jobs = 1, cv = crossvalidation)

        search.fit(X_train, y_train)

        print("Best params:", search.best_params_)
        print("Best score:", search.best_score_)

        # Paso los mejores parámetros
        GBR2 = GradientBoostingRegressor(**search.best_params_)
    else:
        # GRADIENT BOOSTING MODEL DEVELOPMENT
        # Cambiar luego del hyperparameter tuning
        GBR2 = GradientBoostingRegressor(n_estimators = 1000, learning_rate = 0.1,
                                        max_depth = 4, subsample = 0.75, random_state = 1)
        score = np.mean(cross_val_score(GBR2, X_train, y_train,
                                        scoring = 'neg_mean_squared_error',
                                        cv = crossvalidation, n_jobs = 1))
        print("Final model score:", score)

    # PREDECIR
    GBR2.fit(X_train, y_train)
    predicciones = GBR2.predict(X_test)
    guardar_modelo(GBR2)
    guardar_modelo(cultivo_a_entero, "model/cultivo_a_entero.pkl") # No es un modelo pero necesito guardarlo
    guardar_modelo(depto_a_entero, "model/depto_a_entero.pkl") # Es un diccionario


    # GRÁFICAS
    plt.figure(figsize=(10, 6))

    # Línea azul: todos los valores reales (train + test)
    plt.plot(df_convertido['produccion_tn'].values, label='Valores Reales', color='blue', alpha=0.6)

    # Línea roja: predicciones, alineadas con el 20% final
    plt.plot(range(len(y_train), len(y_train) + len(y_test)), predicciones, label='Predicciones', color='red', alpha=0.6)


    titulo = 'Producción (tn)'
    plt.title('Producción Real vs Predicha')
    plt.xlabel('Índice de Muestra')
    plt.ylabel(titulo)
    plt.legend()
    #plt.savefig(f"Archivos/Graficas/{titulo.replace(' ', '_')}.png", dpi=600, bbox_inches="tight")
    plt.show()

    #df_convertido = pd.read_csv("Archivos/df_semillas_suelo_clima_convertido.csv")
    df_reconvertido = conversor_entero_a_cultivo(df_convertido, cultivo_a_entero)
    df_reconvertido = conversor_entero_a_depto(df_convertido, depto_a_entero)
    #df_reconvertido.to_csv("Archivos/df_semillas_suelo_clima_reconvertido.csv", index=False)

    return GBR2


# -------------------------------
# MAIN
# -------------------------------
def main(entradas_para_predecir = None):
    if entradas_para_predecir is None:
        head_cant = int(input("¿Cuántas filas usar para entrenar? (0 para todas): "))
        modelo = entrenar_y_devolver_modelo(head_cant)
    else:
        # Cargar modelo guardado
        modelo = joblib.load("model/modelo_gbm_completo.pkl")
        cultivo_a_entero = joblib.load("model/cultivo_a_entero.pkl")
        depto_a_entero = joblib.load("model/depto_a_entero.pkl")
        predicciones = modelo.predict(entradas_para_predecir)

        return predicciones
    

if __name__ == "__main__":
    main()