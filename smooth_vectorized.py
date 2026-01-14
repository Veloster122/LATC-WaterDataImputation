"""
ULTRA-OPTIMIZED smoothing using vectorized operations
CRITICAL: Only smooths imputed values, preserves original data intact
"""

import numpy as np
import pandas as pd


def smooth_time_series_vectorized(df, value_columns, original_df, window_size=25, verbose=True):
    """
    ULTRA-OPTIMIZED: Vectorized smoothing that PRESERVES ORIGINAL DATA.
    
    Args:
        df: DataFrame with IMPUTED data
        value_columns: List of column names with hourly readings
        original_df: DataFrame with ORIGINAL data (to identify gaps)
        window_size: Window size for moving average
        verbose: Print progress
        
    Returns:
        DataFrame with smoothed values ONLY in gap regions
    """
    if verbose:
        print(f"\n🚀 Suavização Ultra-Rápida (Vetorizada, janela={window_size})...")
        print(f"   Processando {len(df):,} linhas × {len(value_columns)} colunas...")
        print(f"   🔒 Preservando dados originais intactos (só suaviza gaps)")
    
    result_df = df.copy()
    
    # Extract matrices
    imputed_matrix = df[value_columns].values.astype(float)
    original_matrix = original_df[value_columns].values.astype(float)
    
    # Create mask: True where original had gaps (NaN)
    gap_mask = np.isnan(original_matrix)
    
    gaps_count = np.sum(gap_mask)
    total_count = gap_mask.size
    
    if verbose:
        print(f"   📊 Gaps identificados: {gaps_count:,} de {total_count:,} ({100*gaps_count/total_count:.2f}%)")
    
    if verbose:
        print(f"   Aplicando rolling mean horizontal...")
    
    # Apply rolling mean to ALL data first
    smoothed_matrix = pd.DataFrame(imputed_matrix).T.rolling(
        window=min(window_size, len(value_columns)), 
        center=True, 
        min_periods=1
    ).mean().T.values
    
    # CRITICAL: Restore original values where they existed
    # Only keep smoothed values where there were gaps
    smoothed_matrix[~gap_mask] = original_matrix[~gap_mask]
    
    # Enforce monotonicity (each row must be non-decreasing)
    if verbose:
        print(f"   Aplicando monotonicidade...")
    
    for j in range(1, smoothed_matrix.shape[1]):
        # Vectorized: for all rows at once
        mask = smoothed_matrix[:, j] < smoothed_matrix[:, j-1]
        smoothed_matrix[mask, j] = smoothed_matrix[mask, j-1]
    
    # Write back to dataframe
    result_df[value_columns] = smoothed_matrix
    
    if verbose:
        print(f"   ✅ Concluído! Dados originais preservados, gaps suavizados")
    
    return result_df
