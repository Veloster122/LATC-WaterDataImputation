"""
Diagnostic script to verify if smoothing is actually being applied
"""
import pandas as pd
import numpy as np
from pathlib import Path

# Check files
files = {
    "Original": "c:/Users/Utilizador/Downloads/LATC/data/web_upload.csv",
    "Imputado": "c:/Users/Utilizador/Downloads/LATC/data/RESULTADO_FINAL.csv",
    "Suavizado": "c:/Users/Utilizador/Downloads/LATC/data/RESULTADO_FINAL_SUAVIZADO.csv"
}

print("="*70)
print("DIAGNÓSTICO: Verificando se suavização foi aplicada")
print("="*70)

for name, path in files.items():
    p = Path(path)
    if p.exists():
        print(f"\n✓ {name}: {p.name} ({p.stat().st_size / (1024*1024):.1f} MB)")
    else:
        print(f"\n✗ {name}: NÃO ENCONTRADO")

# Load and compare
meter_id = "C15FA157523"

try:
    df_imp = pd.read_csv(files["Imputado"])
    print(f"\n[IMPUTADO]")
    print(f"  Total linhas: {len(df_imp):,}")
    
    value_cols = [c for c in df_imp.columns if c.startswith('index_')]
    
    # Find meter
    mask = df_imp['id'].astype(str) == meter_id
    if mask.any():
        meter_imp = df_imp[mask][value_cols].values.flatten()
        print(f"  Contador {meter_id}: {len(meter_imp):,} valores")
        print(f"  Min: {np.nanmin(meter_imp):.2f}, Max: {np.nanmax(meter_imp):.2f}, Mean: {np.nanmean(meter_imp):.2f}")
        print(f"  NaN: {np.sum(np.isnan(meter_imp))}")
        
        # Check for extreme values
        extreme = meter_imp > 1000
        if extreme.any():
            print(f"  ⚠️ VALORES EXTREMOS (>1000): {np.sum(extreme)} pontos!")
            print(f"     Máximo extremo: {np.max(meter_imp[extreme]):.2f}")
except Exception as e:
    print(f"Erro ao ler imputado: {e}")

try:
    df_smooth = pd.read_csv(files["Suavizado"])
    print(f"\n[SUAVIZADO]")
    print(f"  Total linhas: {len(df_smooth):,}")
    
    mask = df_smooth['id'].astype(str) == meter_id
    if mask.any():
        meter_smooth = df_smooth[mask][value_cols].values.flatten()
        print(f"  Contador {meter_id}: {len(meter_smooth):,} valores")
        print(f"  Min: {np.nanmin(meter_smooth):.2f}, Max: {np.nanmax(meter_smooth):.2f}, Mean: {np.nanmean(meter_smooth):.2f}")
        
        # Compare with imputed
        if 'meter_imp' in locals():
            diff = np.abs(meter_imp - meter_smooth)
            print(f"\n[COMPARAÇÃO Imputado vs Suavizado]")
            print(f"  Diferença média: {np.nanmean(diff):.6f}")
            print(f"  Diferença máxima: {np.nanmax(diff):.6f}")
            print(f"  Valores que mudaram: {np.sum(diff > 0.01):,}/{len(diff):,}")
            
            if np.nanmax(diff) < 0.001:
                print(f"\n  ❌ PROBLEMA: Suavização NÃO foi aplicada! (valores idênticos)")
            else:
                print(f"\n  ✓ Suavização foi aplicada")
                
        # Check for extreme values
        extreme_smooth = meter_smooth > 1000
        if extreme_smooth.any():
            print(f"\n  ⚠️ VALORES EXTREMOS PERSISTEM: {np.sum(extreme_smooth)} pontos")
except FileNotFoundError:
    print(f"\n✗ Arquivo suavizado não existe - suavização não foi executada")
except Exception as e:
    print(f"\nErro ao ler suavizado: {e}")

print("\n" + "="*70)
