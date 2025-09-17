import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.dates import MonthLocator, DateFormatter, YearLocator
from keras.models import Sequential, load_model
from keras.losses import MeanSquaredError 
from keras.metrics import RootMeanSquaredError
from keras.layers import Dense, InputLayer, LSTM
from keras.callbacks import ModelCheckpoint
from keras.optimizers import Adam
from matplotlib.dates import AutoDateLocator, ConciseDateFormatter

WINDOW_SIZE = 14

def plot_predictions(pred, y_true, label, period):
    period = pd.to_datetime(period)
    plt.figure(figsize=(10, 6))
    plt.plot(period, y_true, label='True Values', marker='o', color='black')
    plt.plot(period, pred, label='Predictions', marker='o', color='red')
    plt.xlabel('Date')
    plt.ylabel('Humedad relativa %')
    plt.title(label)
    plt.legend()
    if label == "Train Data":
        plt.gca().xaxis.set_major_locator(YearLocator())
        plt.gca().xaxis.set_major_formatter(DateFormatter('%Y'))
    elif label == "Test Data":
        plt.gca().xaxis.set_major_locator(MonthLocator())
        plt.gca().xaxis.set_major_formatter(DateFormatter('%b %Y'))
    plt.gcf().autofmt_xdate()
    plt.show()

def train_neural_network(X, y, epochs=100, learning_rate=0.001):
    model = Sequential([
        InputLayer((WINDOW_SIZE, 1)),
        LSTM(64),
        Dense(8, activation='relu'),
        Dense(1, 'linear')
    ])
    checkpoint = ModelCheckpoint("model/model_hum.keras", save_best_only=True, monitor='val_loss')
    model.compile(loss=MeanSquaredError(), optimizer=Adam(learning_rate=learning_rate), metrics=[RootMeanSquaredError()])
    model.fit(X, y, epochs=epochs, callbacks=[checkpoint])

def data_to_input_and_out(data):
    X, y = [], []
    for i in range(len(data) - WINDOW_SIZE):
        X.append(data['humedad_relativa_%'][i:i + WINDOW_SIZE])
        y.append(data['humedad_relativa_%'][i + WINDOW_SIZE])
    return np.array(X), np.array(y)

def plot_full_timeline(period, y_true_full, train_overlay=None, test_pred_overlay=None, title="Real Graph Data"):
    period = pd.to_datetime(period)

    plt.figure(figsize=(10, 6))

    plt.plot(period, y_true_full, label='True (all)', marker='o', color='black', linewidth=1)

    if train_overlay is not None:
        plt.plot(period, train_overlay, label='Train segment (used to fit)', marker='o')

    if test_pred_overlay is not None:
        plt.plot(period, test_pred_overlay, label='Predictions (test)', marker='o', color='red')

    plt.xlabel('Date')
    plt.ylabel('Relative Humidity (%)')
    plt.title(title)
    plt.legend()

    # Eje X por meses (podés cambiarlo si tu serie es anual)
    plt.gca().xaxis.set_major_locator(MonthLocator())
    plt.gca().xaxis.set_major_formatter(DateFormatter('%b %Y'))

    plt.gcf().autofmt_xdate()
    plt.show()

def plot_full_timeline_clean(period, y_true_full, n_train, test_pred, title="Real Graph Data"):
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

    # Eje X legible
    locator = AutoDateLocator()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(ConciseDateFormatter(locator))

    titulo = 'Humedad relativa (%)'
    ax.set_xlabel('Date')
    ax.set_ylabel(titulo)
    ax.set_title(title)
    ax.legend()
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig(f"Archivos/Graficas/{titulo.replace(' ', '_')}.png", dpi=600, bbox_inches="tight")
    plt.show()

def train_LSTM_humedad(data):
    split_idx = int(len(data) * 0.85)
    train = data.iloc[:split_idx].reset_index(drop=True)
    test = data.iloc[split_idx:].reset_index(drop=True)
    #print("Train shape:", train.shape)
    #print("Test shape:", test.shape)
    full_input, full_output = data_to_input_and_out(data)
    train_input, train_output = data_to_input_and_out(train)
    test_input, test_output = data_to_input_and_out(test)
    train_neural_network(train_input, train_output)
    model = load_model("model/model_hum.keras")
    train_pred = model.predict(train_input)
    test_pred = model.predict(test_input)
    train_period = train[0:len(train) - WINDOW_SIZE]['fecha']
    test_period = test[0:len(test) - WINDOW_SIZE]['fecha']
    full_period = data.iloc[0:len(data) - WINDOW_SIZE]['fecha']
    n_full  = len(full_output)
    n_train = len(train_output)
    n_test  = len(test_output)
    train_overlay = np.full(n_full, np.nan, dtype=float)
    train_overlay[:n_train] = full_output[:n_train]
    test_pred_overlay = np.full(n_full, np.nan, dtype=float)
    test_pred_overlay[n_train:n_train + n_test] = test_pred.reshape(-1)
    #plot_full_timeline(period=full_period, y_true_full=full_output, test_pred_overlay=test_pred_overlay, title="Real Graph Data")
    plot_full_timeline_clean(full_period, full_output, n_train, test_pred, title="Real Graph Data")
    #plot_predictions(train_pred, train_output, "Train Data", train_period)
    #plot_predictions(test_pred, test_output, "Test Data", test_period)

def predecir_proximos_meses(data, WINDOW_SIZE=14, steps=14):
    #data = creo_archivo_clima(latitud, longitud)
    ultimos = data['humedad_relativa_%'].values[-WINDOW_SIZE:]
    predicciones = []
    model = load_model("model/model_hum.keras")
    entrada = ultimos.reshape(1, WINDOW_SIZE, 1)
    for _ in range(steps):
        pred = model.predict(entrada, verbose=0)[0,0]
        predicciones.append(pred)
        ultimos = np.append(ultimos[1:], pred)
        entrada = ultimos.reshape(1, WINDOW_SIZE, 1)
    return np.array(predicciones)

if __name__ == "__main__":
    '''predicciones_futuras = predecir_proximos_meses(-34.6037, -58.3816)
    print("Predicciones próximas 14 meses:", predicciones_futuras)'''

    df_ejemplo = pd.read_csv("Recuperacion_de_datos/Clima/clima_nasa_mensual_44_anios_de_Rosario.csv")
    train_LSTM_humedad(df_ejemplo)
