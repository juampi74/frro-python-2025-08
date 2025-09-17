from Pred_Clima.pred_temp import predecir_proximos_meses as pred_temp
from Pred_Clima.pred_humedad import predecir_proximos_meses as pred_hum
from Pred_Clima.pred_viento_GBR import main as prediccion_viento_GBR
from Pred_Clima.pred_precip_GBR import main as prediccion_precip_GBR
import pandas as pd



def main(depto):
    path = f"Recuperacion_de_datos/Clima/clima_nasa_mensual_44_anios_de_{depto}.csv"

    df_clima = pd.read_csv(path)

    array_14_meses_precip = prediccion_precip_GBR(path, df_clima)
    array_14_meses_viento = prediccion_viento_GBR(path, df_clima)
    array_14_meses_hum = pred_hum(df_clima)
    array_14_meses_temp = pred_temp(df_clima)

    # Crear dataframe con las predicciones
    data = {}

    for i in range(14):
        data[f"temperatura_media_C_{i+1}"] = [array_14_meses_temp[i]]
        data[f"humedad_relativa_%_{i+1}"] = [array_14_meses_hum[i]]
        data[f"velocidad_viento_m_s_{i+1}"] = [array_14_meses_viento[i]]
        data[f"precipitacion_mm_mes_{i+1}"] = [array_14_meses_precip[i]]

    # Crear DataFrame con una sola fila
    df_pred = pd.DataFrame(data)

    return df_pred






