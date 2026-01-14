"""
Debug script to test smoothing on actual data
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.append('c:/Users/Utilizador/Downloads/LATC')

# Load the data files
resultado_final = Path("c:/Users/Utilizador/Downloads/LATC/data/RESULTADO_FINAL.csv")
resultado_suavizado = Path("c:/Users/Utilizador/Downloads/LATC/data/RESULTADO_FINAL_SUAVIZADO.csv")

if resultado_final.exists():
    df_imputed = pd.read_csv(resultado_final)
    print(f"✓ Loaded RESULTADO_FINAL.csv: {len(df_imputed)} rows")
    
    # Check a specific meter
    test_meter = "C15FA157523"  # From user's screenshot
    
    value_cols = [c for c in df_imputed.columns if c.startswith('index_')]
    print(f"✓ Value columns: {len(value_cols)}")
    
    if test_meter in df_imputed['id'].astype(str).values:
        meter_data = df_imputed[df_imputed['id'].astype(str) == test_meter]
        print(f"\n✓ Found meter {test_meter}: {len(meter_data)} rows")
        
        # Get first row values
        row_values = meter_data.iloc[0][value_cols].values
        print(f"  Sample values: {row_values[:10]}")
        print(f"  Min: {np.min(row_values):.2f}, Max: {np.max(row_values):.2f}")
        print(f"  NaN count: {np.sum(np.isnan(row_values))}")
    else:
        print(f"✗ Meter {test_meter} not found")
        print(f"  Available meters (first 5): {df_imputed['id'].astype(str).unique()[:5]}")
else:
    print("✗ RESULTADO_FINAL.csv not found")

if resultado_suavizado.exists():
    df_smoothed = pd.read_csv(resultado_suavizado)
    print(f"\n✓ Loaded RESULTADO_FINAL_SUAVIZADO.csv: {len(df_smoothed)} rows")
    
    if test_meter in df_smoothed['id'].astype(str).values:
        meter_data_smooth = df_smoothed[df_smoothed['id'].astype(str) == test_meter]
        row_values_smooth = meter_data_smooth.iloc[0][value_cols].values
        
        print(f"  Sample values (smoothed): {row_values_smooth[:10]}")
        print(f"  Min: {np.min(row_values_smooth):.2f}, Max: {np.max(row_values_smooth):.2f}")
        
        # Compare
        if 'row_values' in locals():
            diff = np.abs(row_values - row_values_smooth)
            print(f"\n  Difference after smoothing:")
            print(f"    Mean abs diff: {np.nanmean(diff):.4f}")
            print(f"    Max diff: {np.nanmax(diff):.4f}")
            
            if np.nanmax(diff) < 0.01:
                print("  ⚠️ WARNING: Values barely changed! Smoothing may not have been applied.")
else:
    print("\n✗ RESULTADO_FINAL_SUAVIZADO.csv not found - smoothing was not applied")

print("\n" + "="*60)
print("Analysis complete")
