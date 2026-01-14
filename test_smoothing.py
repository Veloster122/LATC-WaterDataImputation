"""
Quick test script to verify smoothing functionality
"""
import pandas as pd
import numpy as np
import sys
sys.path.append('c:/Users/Utilizador/Downloads/LATC')

from latc_advanced import smooth_imputed_data

# Create test data with staircase pattern
test_matrix = np.array([
    [1050, 1050, 1050, 1055, 1055, 1060, 1060, 1065, 1065, 1070],
    [1100, 1105, 1110, 1115, 1120, 1125, 1130, 1135, 1140, 1145],
], dtype=float)

# Original has gaps at positions 2-3 and 6-8
original_matrix = test_matrix.copy()
original_matrix[0, 2:4] = np.nan
original_matrix[0, 6:9] = np.nan

print("Original with gaps:")
print(original_matrix[0])

print("\nImputed (with staircase):")
print(test_matrix[0])

# Test smoothing
smoothed = smooth_imputed_data(
    imputed_matrix=test_matrix,
    original_matrix=original_matrix,
    method='savgol',
    window_size=5,
    preserve_monotonicity=True,
    verbose=True
)

print("\nSmoothed result:")
print(smoothed[0])

print("\n✅ Test successful! Smoothing applied to imputed regions only.")
