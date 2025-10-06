
import os
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import KFold, cross_val_score

MODEL_PATH = "model/model_gbr_phase.pkl"

# ---------------- Helpers ----------------
def season_anchor_datetime(df: pd.DataFrame) -> pd.Series:
    """
    Construye una fecha representativa por fila usando (year, trimester).
    Ancla en el mes FINAL del trimestre (DJF→feb, ..., NDJ→ene del año sig.).
    """
    months_end = {1:2, 2:3, 3:4, 4:5, 5:6, 6:7, 7:8, 8:9, 9:10, 10:11, 11:12, 12:1}
    m = df["trimester"].astype(int).map(months_end)
    y = df["year"].astype(int) + (df["trimester"].astype(int) == 12).astype(int)
    return pd.to_datetime({'year': y, 'month': m, 'day': 1})

def discretize_nino(x: np.ndarray) -> np.ndarray:
    """Redondea y satura las predicciones continuas a {-1,0,1}."""
    x = np.round(x).astype(int)
    x = np.clip(x, -1, 1)
    return x

def avanzar_trimestre(year: int, trimester: int):
    """Devuelve (year_next, trimester_next) al avanzar un trimestre."""
    t2 = 1 + (trimester % 12)
    y2 = year + (1 if t2 == 1 else 0)
    return y2, t2

# ---------------- Core ----------------
def preparar_datos(path_csv: str):
    df = pd.read_csv(path_csv)
    # Orden por año y trimestre por las dudas
    df = df.sort_values(["year", "trimester"]).reset_index(drop=True)

    # Objetivo: predecir Nino del próximo trimestre
    df["Nino_next"] = df["Nino"].shift(-1)
    df_model = df.dropna(subset=["Nino_next"]).copy()

    # Conjunto de entrada (como pediste): year, trimester, Nino (del trimestre actual)
    X = df_model[["year", "trimester", "Nino"]].astype(float).values
    y = df_model["Nino_next"].astype(float).values

    return df_model, X, y

def entrenar_modelo_phase(path_csv: str, n_splits=5):
    os.makedirs("model", exist_ok=True)

    df, X, y = preparar_datos(path_csv)

    # Split simple temporal (80/20) respetando orden
    split = int(0.8 * len(df))
    X_train, y_train = X[:split], y[:split]
    X_test,  y_test  = X[split:], y[split:]

    # Cross-validation (embarajado=False para no romper la temporalidad en cv)
    cv = KFold(n_splits=n_splits, shuffle=False)
    gbr = GradientBoostingRegressor(
        n_estimators=600, learning_rate=0.05, max_depth=3,
        subsample=0.8, random_state=1
    )
    score = np.mean(cross_val_score(
        gbr, X_train, y_train, scoring='neg_mean_squared_error', cv=cv
    ))
    print("CV (neg MSE) media:", score)

    # Entrenamiento final
    gbr.fit(X_train, y_train)
    joblib.dump(gbr, MODEL_PATH)
    print(f"Modelo guardado en {MODEL_PATH}")

    # Evaluación y gráfico simple
    y_pred_test = gbr.predict(X_test)
    y_pred_test_disc = discretize_nino(y_pred_test)

    # Serie completa para ploteo: y_true (desde 12 en adelante) y overlay de test preds
    t_full = season_anchor_datetime(df)        # eje X
    y_true_full = df["Nino_next"].values      # -1,0,1 reales (shift -1)

    overlay = np.full_like(y_true_full, fill_value=np.nan, dtype='float64')
    overlay[split:] = y_pred_test_disc

    fig, ax = plt.subplots(figsize=(10,6))
    ax.plot(t_full, y_true_full, color='black', label='True (all)', linewidth=1.2)
    ax.axvspan(t_full.iloc[0], t_full.iloc[split-1], color='tab:blue', alpha=0.1, label='Train window')
    ax.plot(t_full, overlay, color='red', marker='o', linewidth=1.8, label='Predictions (test)')
    ax.set_title("ENSO Phase (Nino -1/0/1) – GBR")
    ax.set_ylabel("Nino (-1, 0, 1)")
    ax.set_xlabel("Fecha (trimestral)")
    ax.legend()
    plt.tight_layout()
    plt.show()

    return gbr

def predecir_futuro(path_csv: str, steps: int = 12):
    """
    Predice 'steps' trimestres hacia adelante recursivamente.
    Features de entrada en cada paso: year, trimester y Nino del paso anterior (como pediste).
    """
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError("No se encontró el modelo entrenado. Ejecutá entrenar_modelo_phase primero.")

    gbr = joblib.load(MODEL_PATH)
    df = pd.read_csv(path_csv).sort_values(["year","trimester"]).reset_index(drop=True)

    # Partimos del último registro conocido
    last_year     = int(df.iloc[-1]["year"])
    last_trim     = int(df.iloc[-1]["trimester"])
    last_nino     = float(df.iloc[-1]["Nino"])

    preds = []
    for _ in range(steps):
        # features: (year, trimester, Nino actual)
        X = np.array([[last_year, last_trim, last_nino]], dtype=float)
        y_hat = gbr.predict(X)[0]
        y_hat_disc = float(np.clip(np.round(y_hat), -1, 1))  # discretizar a -1/0/1 para retroalimentar

        preds.append((last_year, last_trim, y_hat_disc))

        # avanzar calendario y actualizar "estado"
        next_year, next_trim = avanzar_trimestre(last_year, last_trim)
        last_year, last_trim, last_nino = next_year, next_trim, y_hat_disc

    # Devolvemos como DataFrame
    return pd.DataFrame(preds, columns=["year", "trimester", "Nino_pred"])

# ---------------- Main ----------------
if __name__ == "__main__":
    csv_path = "Recuperacion_de_datos/Clima/phase_trimestral.csv"  # cámbialo si lo tenés en otra carpeta
    # Entrenar y graficar
    entrenar_modelo_phase(csv_path)

    # Predecir próximos 12 trimestres (opcional)
    fut = predecir_futuro(csv_path, steps=52)
    print(fut)
