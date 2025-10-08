
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter
from keras.models import Sequential, load_model
from keras.layers import Dense, InputLayer, LSTM
from keras.callbacks import ModelCheckpoint, EarlyStopping
from keras.optimizers import Adam
from keras.losses import SparseCategoricalCrossentropy
from keras.metrics import Accuracy
import os

# ---------------------- Config ----------------------
WINDOW_SIZE = 12              # usa 12 trimestres previos
MODEL_PATH = "model/model_phase_tri_cls.keras"

# ---------------------- Utils -----------------------
def add_cyclical_trimester_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Espera columnas: [year, trimester, phase, Nino]
    Devuelve df con columnas sin_t, cos_t y Nino_class (0,1,2).
    """
    df = df.copy()
    # trimestre en [1..12] -> ángulo [0..2π)
    angle = 2 * np.pi * (df["trimester"].astype(float) - 1) / 12.0
    df["sin_t"] = np.sin(angle)
    df["cos_t"] = np.cos(angle)
    # objetivo como clase 0,1,2 (Nina, Neutral, Nino)
    df["Nino_class"] = (df["Nino"] + 1).astype(int)
    return df

def season_anchor_datetime(df: pd.DataFrame) -> pd.Series:
    # Mes final por trimestre: 1..12  →  [Feb, Mar, ..., Ene]
    months_end = {1:2, 2:3, 3:4, 4:5, 5:6, 6:7, 7:8, 8:9, 9:10, 10:11, 11:12, 12:1}
    m = df["trimester"].map(months_end).astype(int)
    y = df["year"].astype(int) + (df["trimester"] == 12).astype(int)  # NDJ → enero del año siguiente
    return pd.to_datetime({'year': y, 'month': m, 'day': 1})


def build_sequences(df: pd.DataFrame, feature_cols, target_col="Nino_class", window=WINDOW_SIZE):
    X, y = [], []
    for i in range(len(df) - window):
        X.append(df[feature_cols].iloc[i:i+window].values)
        y.append(int(df[target_col].iloc[i+window]))
    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int64)
    return X, y

def split_train_test(X, y, train_ratio=0.85):
    n = len(y)
    n_train = int(n * train_ratio)
    return (X[:n_train], y[:n_train], X[n_train:], y[n_train:])

# ---------------------- Model -----------------------
def build_model(n_features, lr=1e-3):
    model = Sequential([
        InputLayer((WINDOW_SIZE, n_features)),
        LSTM(64),
        Dense(32, activation="relu"),
        Dense(3, activation="softmax")  # 3 clases: Nina, Neutral, Nino
    ])
    model.compile(
        optimizer=Adam(learning_rate=lr),
        loss=SparseCategoricalCrossentropy(),
        metrics=["accuracy"]
    )
    return model

# ---------------------- Training --------------------
def train_phase_model(df: pd.DataFrame, epochs=60, lr=1e-3):
    os.makedirs("model", exist_ok=True)

    df_feat = add_cyclical_trimester_features(df)
    # Elegí features compactos en [-1,1] para no escalar: Nino, sin_t, cos_t
    feature_cols = ["Nino", "sin_t", "cos_t"]
    X, y = build_sequences(df_feat, feature_cols, "Nino_class", window=WINDOW_SIZE)

    X_train, y_train, X_test, y_test = split_train_test(X, y, train_ratio=0.85)
    # validación: 10% del bloque de entrenamiento (último tramo para no "mirar el futuro")
    n_train = len(y_train)
    n_val = max(1, n_train // 10)
    X_tr, y_tr = X_train[:-n_val], y_train[:-n_val]
    X_val, y_val = X_train[-n_val:], y_train[-n_val:]

    model = build_model(n_features=X.shape[2], lr=lr)
    ckpt = ModelCheckpoint(MODEL_PATH, save_best_only=True, monitor="val_loss")
    es = EarlyStopping(monitor="val_loss", patience=10, restore_best_weights=True)

    history = model.fit(
        X_tr, y_tr,
        validation_data=(X_val, y_val),
        epochs=epochs,
        callbacks=[ckpt, es],
        verbose=1
    )
    # Eval simple
    loss, acc = model.evaluate(X_test, y_test, verbose=0)
    print(f"Test accuracy: {acc:.3f}")
    return history

# ---------------------- Forecasting -----------------
def predict_next_steps(steps=12):
    """
    Predice próximos `steps` trimestres usando la última ventana de 12.
    Avanza el calendario de trimestre en trimestre para construir sin/cos futuros.
    Devuelve dos arrays: clases (0,1,2) y valores mapeados (-1,0,1).
    """
    df = pd.read_csv("Recuperacion_de_datos/Clima/phase_trimestral.csv")
    model = load_model(MODEL_PATH)

    df_feat = add_cyclical_trimester_features(df)
    feature_cols = ["Nino", "sin_t", "cos_t"]

    # ventana inicial (12 últimos)
    window_df = df_feat.iloc[-WINDOW_SIZE:].copy()
    X_win = window_df[feature_cols].values.astype(np.float32).reshape(1, WINDOW_SIZE, len(feature_cols))

    # estado de calendario
    last_year = int(df_feat.iloc[-1]["year"])
    last_trim = int(df_feat.iloc[-1]["trimester"])

    preds_class, preds_value = [], []
    for _ in range(steps):
        proba = model.predict(X_win, verbose=0)[0]
        c = int(np.argmax(proba))             # 0,1,2
        preds_class.append(c)
        # mapear clase a -1,0,1
        val = [-1, 0, 1][c]
        preds_value.append(val)

        # shift de ventana: quitar primer fila y agregar "siguiente" con features
        # avanzar calendario
        next_trim = 1 + (last_trim % 12)
        next_year = last_year + 1 if next_trim == 1 else last_year

        # recomputar sin/cos del próximo trimestre
        angle = 2 * np.pi * (next_trim - 1) / 12.0
        next_row = np.array([[val, np.sin(angle), np.cos(angle)]], dtype=np.float32)  # Nino predicho + sin/cos
        X_win = np.concatenate([X_win[:, 1:, :], next_row.reshape(1, 1, -1)], axis=1)

        last_trim, last_year = next_trim, next_year

    #return np.array(preds_class), np.array(preds_value)
    return preds_class, preds_value

# ---------------------- Plot helper -----------------
def plot_full_timeline_clean(period, y_true_full, n_train, test_pred, title="Phase ENSO Trimestral"):
    from matplotlib.dates import AutoDateLocator, ConciseDateFormatter
    import matplotlib.pyplot as plt
    period = pd.to_datetime(period)
    n_full = len(y_true_full)
    n_test = len(test_pred)

    test_pred_overlay = np.full(n_full, np.nan, dtype=float)
    test_pred_overlay[n_train:n_train + n_test] = np.asarray(test_pred).reshape(-1)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(period, y_true_full, label='True (all)', linewidth=1.5, color='black', zorder=1)
    ax.axvspan(period.iloc[0], period.iloc[n_train-1],
               color='tab:blue', alpha=0.10, label='Train window', zorder=0)
    ax.plot(period, test_pred_overlay, label='Predictions (test)',
            linewidth=1.8, marker='o', markersize=3, color='red', zorder=3)

    locator = AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(ConciseDateFormatter(locator))
    ax.set_xlabel('Date')
    ax.set_ylabel("Phase ENSO Trimestral (-1,0,1)")
    ax.set_title(title)
    ax.legend()
    plt.tight_layout()
    plt.show()

def demo_train_and_plot(csv_path="Recuperacion_de_datos/Clima/phase_trimestral.csv"):
    df = pd.read_csv(csv_path)
    # entrenar
    train_phase_model(df, epochs=60, lr=1e-3)

    # construir serie completa para el plot (true y pred en test)
    df_feat = add_cyclical_trimester_features(df)
    feature_cols = ["Nino", "sin_t", "cos_t"]
    X, y = build_sequences(df_feat, feature_cols, "Nino_class", window=WINDOW_SIZE)
    n_full = len(y)
    n_train = int(n_full * 0.85)
    X_train, y_train, X_test, y_test = X[:n_train], y[:n_train], X[n_train:], y[n_train:]

    model = load_model(MODEL_PATH)
    test_pred_class = np.argmax(model.predict(X_test, verbose=0), axis=1)
    # map a -1,0,1 para visualizar
    map_val = np.array([-1,0,1])
    full_output = map_val[y]  # true
    test_pred_vals = map_val[test_pred_class]

    # eje temporal (simple): usamos year (se repite por trimestre, es solo para referencia)
    full_period = season_anchor_datetime(df).iloc[WINDOW_SIZE:]
    plot_full_timeline_clean(full_period, full_output, n_train, test_pred_vals)

if __name__ == "__main__":
    demo_train_and_plot()

    primer, segundo = predict_next_steps(steps=12)

    print("----------------------------------------------------------------------")
    print("Predicción próximos 12 trimestres (clase):", primer)
    print("----------------------------------------------------------------------")
    print("Predicción próximos 12 trimestres (valor):", segundo)
    print("----------------------------------------------------------------------")
