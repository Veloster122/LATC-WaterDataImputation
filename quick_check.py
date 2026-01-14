import pandas as pd
import numpy as np

# Quick check
meter = "C15FA157523"

print("Checando arquivo SUAVIZADO...")
df = pd.read_csv("c:/Users/Utilizador/Downloads/LATC/data/RESULTADO_FINAL_SUAVIZADO.csv")
cols = [c for c in df.columns if c.startswith('index_')]

mask = df['id'].astype(str) == meter
vals = df[mask][cols].values.flatten()

print(f"Min: {np.nanmin(vals)}")
print(f"Max: {np.nanmax(vals)}")
print(f"Mean: {np.nanmean(vals)}")
print(f"Valores > 1000: {np.sum(vals > 1000)}")
print(f"Valores > 10000: {np.sum(vals > 10000)}")

#Sample of high values
high_vals = vals[vals > 1000]
if len(high_vals) > 0:
    print(f"\nAmostra de valores altos:")
    print(high_vals[:20])
