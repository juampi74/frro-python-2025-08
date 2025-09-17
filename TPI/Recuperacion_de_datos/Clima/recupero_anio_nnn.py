# -*- coding: utf-8 -*-
# Archivo: recupero_anio_nnn.py (versión simplificada: PSL only)
import pandas as pd
import numpy as np
import requests

'''
Este script genera un archivo enso_years.csv con la clasificación histórica de cada año calendario como Niño, Niña o Neutral, a partir del índice ONI 
(Oceanic Niño Index) publicado por NOAA, calculado en el Pacífico ecuatorial central (región Niño 3.4). La fase ENSO es un fenómeno global (no cambia entre países) y este 
archivo no refleja directamente lo ocurrido en Argentina, sino que sirve como variable de referencia para cruzar con datos climáticos o agrícolas locales y analizar cómo 
cada fase afectó a distintas provincias o departamentos. EL SNM se basa en ENOS para elaborar sus informes.
'''

PSL_ONI = "https://psl.noaa.gov/data/correlation/oni.data"

SEASONS = ["DJF","JFM","FMA","MAM","AMJ","MJJ","JJA","JAS","ASO","SON","OND","NDJ"]
SEASON_ORDER = {s:i for i,s in enumerate(SEASONS)}

def _try_float(x):
    try:
        return float(x)
    except:
        return np.nan

def parse_oni_text_loose(txt: str) -> pd.DataFrame:
    rows = []
    for line in txt.splitlines():
        line = line.strip()
        if not line or len(line) < 6 or not line[:4].isdigit():
            continue
        parts = line.split()
        if not parts[0].isdigit():
            continue
        year = int(parts[0])
        vals = [_try_float(v) for v in parts[1:1+12]]
        if len(vals) == 12:
            rows.append([year] + vals)
    if not rows:
        raise ValueError("No se detectaron filas <Year + 12 valores> en el texto ONI (PSL).")
    return pd.DataFrame(rows, columns=["Year"] + SEASONS)

def load_oni_table() -> pd.DataFrame:
    txt = requests.get(PSL_ONI, timeout=30).text
    return parse_oni_text_loose(txt)

def phase_from_oni(x, thr=0.5):
    if x >= thr: return "Nino"
    if x <= -thr: return "Nina"
    return "Neutral"

def mark_episodes(series: pd.Series, label: str, min_len: int = 5) -> np.ndarray:
    mask = (series == label).to_numpy()
    out = np.zeros(len(mask), dtype=bool)
    i = 0
    while i < len(mask):
        if mask[i]:
            j = i
            while j < len(mask) and mask[j]:
                j += 1
            if (j - i) >= min_len:
                out[i:j] = True
            i = j
        else:
            i += 1
    return out

def main():
    df = load_oni_table()
    df_long = df.melt(id_vars="Year", value_vars=SEASONS,
                      var_name="season", value_name="oni").dropna()
    df_long["order_key"] = df_long["Year"]*12 + df_long["season"].map(SEASON_ORDER)
    df_long = df_long.sort_values("order_key", ignore_index=True)

    df_long["phase_raw"] = df_long["oni"].apply(phase_from_oni)
    is_nino_ep = mark_episodes(df_long["phase_raw"], "Nino", min_len=5)
    is_nina_ep = mark_episodes(df_long["phase_raw"], "Nina", min_len=5)
    df_long["phase_episode"] = "Neutral"
    df_long.loc[is_nino_ep, "phase_episode"] = "Nino"
    df_long.loc[is_nina_ep, "phase_episode"] = "Nina"

    rows = []
    for y, g in df_long.groupby("Year"):
        phases = set(g["phase_episode"])
        if "Nino" in phases and "Nina" not in phases:
            year_phase = "Nino"
        elif "Nina" in phases and "Nino" not in phases:
            year_phase = "Nina"
        elif "Nino" in phases and "Nina" in phases:
            max_nino = g.loc[g["phase_episode"]=="Nino","oni"].abs().max()
            max_nina = g.loc[g["phase_episode"]=="Nina","oni"].abs().max()
            year_phase = "Nino" if max_nino >= max_nina else "Nina"
        else:
            year_phase = "Neutral"
        rows.append({"year": int(y), "phase": year_phase})

    out = pd.DataFrame(rows).sort_values("year")
    out.to_csv("Recuperacion_de_datos/Clima/enso_years.csv", index=False)
    print(out.head(15))
    print("\nGuardado Recuperacion_de_datos/Clima/enso_years.csv")

if __name__ == "__main__":
    main()
