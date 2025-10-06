# -*- coding: utf-8 -*-
# Archivo: recupero_anio_nnn.py (PSL only + Nino numérico + CSV trimestral)
import os
import pandas as pd
import numpy as np
import requests

PSL_ONI = "https://psl.noaa.gov/data/correlation/oni.data"

SEASONS = ["DJF","JFM","FMA","MAM","AMJ","MJJ","JJA","JAS","ASO","SON","OND","NDJ"]
SEASON_ORDER = {s:i for i,s in enumerate(SEASONS)}
SEASON_NUM = {s: i+1 for i, s in enumerate(SEASONS)}  # DJF=1, ..., NDJ=12

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
    # Asegurar carpeta de salida
    out_dir = "Recuperacion_de_datos/Clima"
    os.makedirs(out_dir, exist_ok=True)

    # 1) Leer ONI y pasar a formato largo
    df = load_oni_table()
    df_long = df.melt(id_vars="Year", value_vars=SEASONS,
                      var_name="season", value_name="oni").dropna()
    df_long["order_key"] = df_long["Year"]*12 + df_long["season"].map(SEASON_ORDER)
    df_long = df_long.sort_values("order_key", ignore_index=True)

    # 2) Clasificación cruda por umbral y episodio (regla NOAA)
    df_long["phase_raw"] = df_long["oni"].apply(phase_from_oni)
    is_nino_ep = mark_episodes(df_long["phase_raw"], "Nino", min_len=5)
    is_nina_ep = mark_episodes(df_long["phase_raw"], "Nina", min_len=5)
    df_long["phase_episode"] = "Neutral"
    df_long.loc[is_nino_ep, "phase_episode"] = "Nino"
    df_long.loc[is_nina_ep, "phase_episode"] = "Nina"

    # === CSV 1: Anual ===
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

    out_years = pd.DataFrame(rows).sort_values("year")
    out_years["Nino"] = out_years["phase"].map({"Nino":1, "Neutral":0, "Nina":-1}).astype("int8")
    out_years.to_csv(f"{out_dir}/enso_years.csv", index=False, encoding="utf-8")

    # === CSV 2: Trimestral ===
    tri = df_long[["Year","season","phase_episode"]].rename(
        columns={"Year":"year", "phase_episode":"phase"}
    )
    tri["season_ord"] = tri["season"].map(SEASON_ORDER)
    tri = tri.sort_values(["year","season_ord"]).drop(columns="season_ord")
    tri["trimester"] = tri["season"].map(SEASON_NUM).astype("int8")  # <-- nueva columna entera
    tri["Nino"] = tri["phase"].map({"Nino":1, "Neutral":0, "Nina":-1}).astype("int8")
    tri = tri[["year","season","trimester","phase","Nino"]]
    tri.to_csv(f"{out_dir}/phase_trimestral.csv", index=False, encoding="utf-8")

    # Logs de verificación rápida
    print(out_years.head(15))
    print("\nGuardado", f"{out_dir}/enso_years.csv")
    print(tri.head(12))
    print("\nGuardado", f"{out_dir}/phase_trimestral.csv")

if __name__ == "__main__":
    main()
