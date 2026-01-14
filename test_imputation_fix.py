"""
Test script to validate the per-meter imputation fix
Creates synthetic data with known patterns to verify spike elimination
"""

import pandas as pd
import numpy as np
from latc_simple import simple_latc_imputation

print("=" * 70)
print("Testing Per-Meter Imputation Fix")
print("=" * 70)

# Create synthetic test data with 2 meters
np.random.seed(42)

# Meter 1: Values around 100-200
meter1_data = []
for day in range(10):
    row = {'id': 'METER_001', 'data': f'2024-01-{day+1:02d}'}
    for h in range(24):
        # Introduce some missing values (NaN)
        if np.random.random() > 0.3:  # 30% missing
            row[f'index_{h}'] = 100 + day * 10 + h + np.random.random() * 5
        else:
            row[f'index_{h}'] = np.nan
    meter1_data.append(row)

# Meter 2: Values around 500-600 (VERY DIFFERENT from Meter 1)
meter2_data = []
for day in range(10):
    row = {'id': 'METER_002', 'data': f'2024-01-{day+1:02d}'}
    for h in range(24):
        if np.random.random() > 0.3:  # 30% missing
            row[f'index_{h}'] = 500 + day * 10 + h + np.random.random() * 5
        else:
            row[f'index_{h}'] = np.nan
    meter2_data.append(row)

# Combine
df_test = pd.DataFrame(meter1_data + meter2_data)

print(f"\nTest data created:")
print(f"  - {len(df_test)} rows (10 days × 2 meters)")
print(f"  - 2 meters with VERY different value ranges")
print(f"    Meter 1: ~100-200")
print(f"    Meter 2: ~500-600")

value_columns = [f'index_{h}' for h in range(24)]

# Run imputation
print("\nRunning per-meter imputation...")
result = simple_latc_imputation(df_test, value_columns, enforce_monotonicity=True)

# Verify results
print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

meter1_result = result[result['id'] == 'METER_001']
meter2_result = result[result['id'] == 'METER_002']

meter1_values = meter1_result[value_columns].values.flatten()
meter2_values = meter2_result[value_columns].values.flatten()

print(f"\nMeter 1 after imputation:")
print(f"  Min: {meter1_values.min():.2f}")
print(f"  Max: {meter1_values.max():.2f}")
print(f"  Mean: {meter1_values.mean():.2f}")

print(f"\nMeter 2 after imputation:")
print(f"  Min: {meter2_values.min():.2f}")
print(f"  Max: {meter2_values.max():.2f}")
print(f"  Mean: {meter2_values.mean():.2f}")

# Check for cross-contamination
print("\n" + "=" * 70)
print("CROSS-CONTAMINATION CHECK")
print("=" * 70)

# If values from Meter 2 (~500-600) appear in Meter 1 (~100-200), there's contamination
meter1_contaminated = np.any(meter1_values > 400)
meter2_contaminated = np.any(meter2_values < 300)

if meter1_contaminated:
    print("❌ FAIL: Meter 1 has values > 400 (contaminated with Meter 2 data)")
else:
    print("✅ PASS: Meter 1 values stay in expected range (< 400)")

if meter2_contaminated:
    print("❌ FAIL: Meter 2 has values < 300 (contaminated with Meter 1 data)")
else:
    print("✅ PASS: Meter 2 values stay in expected range (> 300)")

# Check for NaN
remaining_nan = np.isnan(result[value_columns].values).sum()
if remaining_nan == 0:
    print(f"✅ PASS: No NaN values remaining")
else:
    print(f"❌ FAIL: {remaining_nan} NaN values remaining")

print("\n" + "=" * 70)
if not meter1_contaminated and not meter2_contaminated and remaining_nan == 0:
    print("🎉 ALL TESTS PASSED - Fix is working correctly!")
else:
    print("⚠️ SOME TESTS FAILED - Review the implementation")
print("=" * 70)
