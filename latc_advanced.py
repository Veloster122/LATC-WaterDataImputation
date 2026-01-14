"""
LATC Scientific Algorithm - True Implementation
Linear Approximation with Temporal Correlation using SVD
"""

import numpy as np
import pandas as pd
from scipy.sparse.linalg import svds
from scipy.signal import savgol_filter
from scipy.interpolate import UnivariateSpline
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from progress_tracker import ProgressTracker


def smooth_imputed_data(imputed_matrix, original_matrix, method='savgol', window_size=11, preserve_monotonicity=True, verbose=False):
    """
    Apply smoothing to imputed values while preserving original data points.
    
    This eliminates the "staircase" effect in imputed consumption profiles.
    
    Args:
        imputed_matrix: Matrix with imputed values (numpy array)
        original_matrix: Original matrix with NaN gaps (numpy array)
        method: Smoothing method - 'moving_avg', 'spline', or 'savgol' (default: 'savgol')
        window_size: Window size for smoothing (must be odd for savgol)
        preserve_monotonicity: Ensure non-decreasing values after smoothing
        verbose: Print progress messages
        
    Returns:
        Smoothed matrix (numpy array)
    """
    if verbose:
        print(f"\n🌊 Aplicando suavização ({method})...")
    
    # Create mask for imputed values (where original was NaN)
    mask_imputed = np.isnan(original_matrix)
    
    # Create output matrix (start with imputed values)
    smoothed_matrix = imputed_matrix.copy()
    
    # Ensure window size is odd for Savitzky-Golay
    if method == 'savgol' and window_size % 2 == 0:
        window_size += 1
    
    # Apply smoothing row-by-row (each meter)
    for i in range(imputed_matrix.shape[0]):
        row = imputed_matrix[i, :].copy()
        original_row = original_matrix[i, :]
        imputed_mask_row = mask_imputed[i, :]
        
        # Skip if no imputed values in this row
        if not imputed_mask_row.any():
            continue
        
        try:
            if method == 'moving_avg':
                # Simple moving average
                df_row = pd.Series(row)
                smoothed_row = df_row.rolling(window=window_size, center=True, min_periods=1).mean().values
                
            elif method == 'spline':
                # Cubic spline interpolation
                x = np.arange(len(row))
                valid_mask = ~np.isnan(row)
                if valid_mask.sum() > 3:  # Need at least 4 points for cubic spline
                    spline = UnivariateSpline(x[valid_mask], row[valid_mask], k=3, s=len(row)*0.1)
                    smoothed_row = spline(x)
                else:
                    smoothed_row = row  # Not enough points, skip smoothing
                    
            elif method == 'savgol':
                # Savitzky-Golay filter (polynomial smoothing)
                # Handle NaN values by temporarily filling them
                row_filled = row.copy()
                if np.isnan(row_filled).any():
                    # Use linear interpolation for NaNs before smoothing
                    row_series = pd.Series(row_filled)
                    row_filled = row_series.interpolate(method='linear').bfill().ffill().values
                
                # Apply filter (requires window_size <= len(row))
                actual_window = min(window_size, len(row_filled))
                if actual_window % 2 == 0:
                    actual_window -= 1
                if actual_window >= 5:  # Minimum window for polynomial order 3
                    smoothed_row = savgol_filter(row_filled, actual_window, polyorder=3)
                else:
                    smoothed_row = row_filled
            else:
                raise ValueError(f"Unknown smoothing method: {method}")
            
            # Only replace imputed values, keep original values intact
            smoothed_matrix[i, imputed_mask_row] = smoothed_row[imputed_mask_row]
            smoothed_matrix[i, ~imputed_mask_row] = original_row[~imputed_mask_row]
            
            # Optional: Preserve monotonicity (horizontal)
            if preserve_monotonicity:
                for j in range(1, smoothed_matrix.shape[1]):
                    if smoothed_matrix[i, j] < smoothed_matrix[i, j-1]:
                        smoothed_matrix[i, j] = smoothed_matrix[i, j-1]
            
        except Exception as e:
            if verbose:
                print(f"   ⚠️ Erro ao suavizar linha {i}: {e}. Mantendo valores originais.")
            # Keep original imputed values if smoothing fails
            continue
    
    if verbose:
        print(f"   ✓ Suavização concluída")
    
    return smoothed_matrix


def latc_svd_imputation(df, value_columns, n_components=50, max_iterations=10, 
                        tolerance=1e-4, enforce_monotonicity=True, apply_smoothing=False, 
                        smoothing_method='savgol', smoothing_window=11, verbose=True, progress_callback=None):
    """
    Advanced LATC imputation using SVD-based matrix completion
    NOW WITH PER-METER PROCESSING to prevent cross-contamination
    
    This captures temporal correlations between meters to intelligently fill gaps
    
    Args:
        df: DataFrame with consumption data (must include 'id' column)
        value_columns: List of column names with hourly readings
        n_components: Number of SVD components to use
        max_iterations: Maximum refinement iterations
        tolerance: Convergence tolerance
        enforce_monotonicity: Ensure non-decreasing values
        verbose: Print progress
        
    Returns:
        DataFrame with scientifically imputed values
    """
    if verbose:
        print("\n" + "="*70)
        print("LATC CIENTÍFICO - Matrix Factorization SVD (Per-Meter Mode)")
        print("="*70)
    
    # Check if 'id' column exists
    if 'id' not in df.columns:
        if verbose:
            print("⚠️  WARNING: 'id' column not found. Using legacy mode (may cause spikes).")
        return _legacy_svd_imputation(df, value_columns, n_components, max_iterations, 
                                     tolerance, enforce_monotonicity, apply_smoothing,
                                     smoothing_method, smoothing_window, verbose, progress_callback)
    
    # Process each meter separately to avoid cross-contamination
    unique_ids = df['id'].unique()
    if verbose:
        print(f"\n📊 Processando {len(unique_ids):,} contadores individualmente...")
    
    processed_batches = []
    
    for idx, meter_id in enumerate(unique_ids):
        if verbose and idx % 100 == 0:
            print(f"   Contador {idx+1}/{len(unique_ids)}...")
        
        # Filter this meter's data
        meter_df = df[df['id'] == meter_id].copy()
        
        # Process this meter using legacy SVD (which works fine for single meter)
        meter_imputed = _legacy_svd_imputation(
            meter_df, value_columns, n_components, max_iterations,
            tolerance, enforce_monotonicity, apply_smoothing, smoothing_method, 
            smoothing_window, verbose=False, progress_callback=None
        )
        
        processed_batches.append(meter_imputed)
        
        # Update progress
        if progress_callback and idx % 50 == 0 and idx > 0:
            progress = int(80 * idx / len(unique_ids))
            progress_callback(progress, f"Processando contador {idx+1}/{len(unique_ids)}")
    
    # Combine all meters
    result_df = pd.concat(processed_batches, ignore_index=True)
    
    if verbose:
        final_matrix = result_df[value_columns].values.astype(float)
        remaining_nan = np.sum(np.isnan(final_matrix))
        print(f"\n✅ Imputação Completa (Per-Meter):")
        print(f"   NaN restantes: {remaining_nan}")
    
    return result_df


def _legacy_svd_imputation(df, value_columns, n_components=50, max_iterations=10,
                          tolerance=1e-4, enforce_monotonicity=True, apply_smoothing=False,
                          smoothing_method='savgol', smoothing_window=11, verbose=True, progress_callback=None):
    """Legacy SVD imputation (processes all rows together - used per-meter in new mode)"""
    
    result_df = df.copy()
    consumption_matrix = df[value_columns].values.astype(float)
    original_matrix = consumption_matrix.copy()
    
    # Track missing values
    mask = ~np.isnan(consumption_matrix)
    total_values = consumption_matrix.size
    missing_count = np.sum(~mask)
    
    if verbose:
        print(f"\n📊 Dados:")
        print(f"   Shape: {consumption_matrix.shape}")
        print(f"   Missing: {missing_count:,} ({100*missing_count/total_values:.2f}%)")
        print(f"   SVD Components: {n_components}")
    
    # PHASE 1: Initial Fill (Smart Interpolation)
    if verbose:
        print(f"\n🔧 Fase 1: Pré-processamento (Inicialização Inteligente)...")
    
    # Use Pandas for robust interpolation (Vertical then Horizontal)
    # This provides a MUCH better starting point for SVD than just means
    temp_df = pd.DataFrame(consumption_matrix)
    
    # 1. Horizontal Interpolation (within day)
    temp_df = temp_df.interpolate(method='linear', axis=1, limit_direction='both')
    
    # 2. Vertical Fill - NOW SAFE within single meter context
    if temp_df.isnull().values.any():
        if verbose:
            print("   Aplicando forward-fill vertical para dias vazios...")
        temp_df = temp_df.ffill(axis=0).bfill(axis=0)
    
    # 3. Final fallback: Horizontal fill then mean
    temp_df = temp_df.ffill(axis=1).bfill(axis=1)
    
    # Fill NaN with row means for initial estimate
    # -------------------------------------------------------------------------
    # CLEANING STEP: Filter Outliers (User Request)
    # 1. Zero values are often sensor errors in accumulated data -> Convert to NaN
    # 2. Drops (Current < Previous) that aren't resets -> Convert to NaN
    # -------------------------------------------------------------------------
    if verbose:
        print("🔧 Limpeza Prévia: Removendo zeros e quedas inválidas...")
    
    # 1. Treat Zeros as False
    consumption_matrix[consumption_matrix == 0] = np.nan
    mask = ~np.isnan(consumption_matrix) # Update mask after cleaning zeros
    
    # 1.5. Filter Spikes (ANTI-RATCHET)
    if verbose:
        print("   Aplicando filtro Anti-Spike (Rolling Median)...")
        
    # Use Pandas for rolling median (horizontal window)
    temp_spike_df = pd.DataFrame(consumption_matrix)
    median_df = temp_spike_df.rolling(window=5, center=True, min_periods=1, axis=1).median()
    
    # Define Spike: Value > 1.25 * Median
    is_spike = (temp_spike_df > median_df * 1.25) & (median_df > 10)
    
    if is_spike.values.any():
        count = is_spike.values.sum()
        if verbose:
            print(f"      -> Removidos {count} spikes detectados.")
        temp_spike_df[is_spike] = np.nan
        consumption_matrix = temp_spike_df.values

    # 2. Filter Drops (STRICT MONOTONICITY FILTER)
    if verbose:
        print("   Aplicando filtro de monotonicidade estrita (removendo quedas)...")
        
    for j in range(consumption_matrix.shape[1]):
        for i in range(1, consumption_matrix.shape[0]):
            curr_val = consumption_matrix[i, j]
            prev_val = consumption_matrix[i-1, j]
            
            if not np.isnan(curr_val) and not np.isnan(prev_val):
                if curr_val < prev_val:
                     ratio = curr_val / prev_val if prev_val > 0 else 0
                     if ratio > 0.1:
                         consumption_matrix[i, j] = np.nan
    
    # Update mask
    mask = ~np.isnan(consumption_matrix)
    
    # 4. Last resort: Global Mean (after cleaning)
    row_means = np.nanmean(consumption_matrix, axis=1, keepdims=True)
    global_mean = np.nanmean(consumption_matrix)
    
    # Smart Init (same as before)
    temp_df = pd.DataFrame(consumption_matrix)
    temp_df = temp_df.interpolate(method='linear', axis=1, limit_direction='both')
    
    if temp_df.isnull().values.any():
        if verbose:
            print("   Aplicando forward-fill vertical para dias vazios...")
        temp_df = temp_df.ffill(axis=0).bfill(axis=0)
        
    initial_filled = temp_df.values
    
    # PHASE 2: Iterative SVD Refinement
    if verbose:
        print(f"\n🔬 Fase 2: Refinamento Iterativo SVD...")
    
    imputed_matrix = initial_filled.copy()
    
    # Determine optimal rank
    rank = min(n_components, min(consumption_matrix.shape) - 1)
   
    if verbose:
        print(f"   Usando rank={rank}")
    
    for iteration in range(max_iterations):
        # SVD decomposition
        try:
            U, s, Vt = svds(imputed_matrix, k=rank)
            # Reconstruct
            reconstructed = U @ np.diag(s) @ Vt
        except:
            if verbose:
                print(f"   ⚠️  SVD falhou, usando valores atuais")
            break
        
        # Update only missing values
        imputed_matrix[~mask] = reconstructed[~mask]
        
        # Calculate convergence
        if iteration > 0:
            diff = np.linalg.norm(imputed_matrix - prev_imputed) / np.linalg.norm(imputed_matrix)
            if verbose and iteration % 2 == 0:
                print(f"   Iteração {iteration+1}/{max_iterations}: convergência = {diff:.6f}")
                
                if progress_callback:
                    iter_prog = 40 + int(40 * (iteration / max_iterations))
                    progress_callback(iter_prog, f"Iteração SVD {iteration+1}/{max_iterations}")
            
            if diff < tolerance:
                if verbose:
                    print(f"   ✓ Convergiu em {iteration+1} iterações")
                break
        
        prev_imputed = imputed_matrix.copy()
    
    # PHASE 3: Post-processing
    if verbose:
        print(f"\n⚙️  Fase 3: Pós-processamento...")
    
    # Restore known values (CRITICAL: don't modify real data)
    imputed_matrix[mask] = original_matrix[mask]
    
    # Enforce monotonicity if requested
    if enforce_monotonicity:
        if verbose:
            print(f"   Aplicando restrição de monotonicidade...")
        
        for i in range(imputed_matrix.shape[0]):
            for j in range(1, imputed_matrix.shape[1]):
                if imputed_matrix[i, j] < imputed_matrix[i, j-1]:
                    imputed_matrix[i, j] = imputed_matrix[i, j-1]
    
    # Apply smoothing if requested (AFTER monotonicity, BEFORE final update)
    if apply_smoothing:
        if verbose:
            print(f"   Ativando suavização ({smoothing_method})...")
        
        # Smooth the data while preserving original values
        imputed_matrix = smooth_imputed_data(
            imputed_matrix=imputed_matrix,
            original_matrix=original_matrix,
            method=smoothing_method,
            window_size=smoothing_window,
            preserve_monotonicity=enforce_monotonicity,
            verbose=verbose
        )
    
    # Ensure non-negative
    imputed_matrix = np.maximum(imputed_matrix, 0)
    
    # Update result
    result_df[value_columns] = imputed_matrix
    
    # Verification
    remaining_nan = np.sum(np.isnan(imputed_matrix))
    
    if verbose:
        print(f"\n✅ Imputação Completa:")
        print(f"   NaN restantes: {remaining_nan}")
        print(f"   Valores imputados: {missing_count - remaining_nan:,}")
    
    return result_df


def latc_hybrid_imputation(df, value_columns, gap_threshold_hours=72,
                           n_components=50, max_iterations=10, apply_smoothing=False,
                           smoothing_method='savgol', smoothing_window=11, verbose=True, progress_callback=None):
    """
    Hybrid approach: Use linear interpolation for small gaps, SVD for large gaps
    
    This balances speed and quality
    """
    if verbose:
        print("\n" + "="*70)
        print("LATC HÍBRIDO - Inteligente")
        print("="*70)
    
    consumption_matrix = df[value_columns].values.astype(float)
    mask = ~np.isnan(consumption_matrix)
    
    # Identify gap sizes
    small_gaps = []
    large_gaps = []
    
    for i in range(consumption_matrix.shape[0]):
        row = consumption_matrix[i, :]
        gaps = []
        in_gap = False
        gap_start = 0
        
        for j in range(len(row)):
            if np.isnan(row[j]):
                if not in_gap:
                    gap_start = j
                    in_gap = True
            else:
                if in_gap:
                    gap_size = j - gap_start
                    if gap_size <= gap_threshold_hours:
                        small_gaps.append((i, gap_start, j))
                    else:
                        large_gaps.append((i, gap_start, j))
                    in_gap = False
    
    total_gaps = len(small_gaps) + len(large_gaps)
    
    if verbose:
        print(f"\n📊 Classificação de Gaps:")
        print(f"   Gaps pequenos (≤{gap_threshold_hours}h): {len(small_gaps)} ({100*len(small_gaps)/total_gaps:.1f}%)" if total_gaps > 0 else "   Sem gaps")
        print(f"   Gaps grandes (>{gap_threshold_hours}h): {len(large_gaps)} ({100*len(large_gaps)/total_gaps:.1f}%)" if total_gaps > 0 else "")
    
    # Strategy decision
    # Strategy decision
    # FORCE SVD FOR TESTING USER HYPOTHESIS
    # (Commented out optimization to valid SVD impact)
    # if len(large_gaps) == 0:
    #     if verbose:
    #         print("\n💡 Decisão: Usar interpolação linear (sem gaps grandes)")
    #     from latc_simple import simple_latc_imputation
    #     return simple_latc_imputation(df, value_columns, enforce_monotonicity=True, progress_callback=progress_callback)
    # else:
    
    if verbose:
        print(f"\n🔬 Decisão: Forçando SVD (Modo Científico Completo)")
    return latc_svd_imputation(df, value_columns, n_components=n_components,
                                max_iterations=max_iterations, apply_smoothing=apply_smoothing,
                                smoothing_method=smoothing_method, smoothing_window=smoothing_window,
                                verbose=verbose, progress_callback=progress_callback)


def main():
    """Main execution"""
    import sys
    import os
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        data_file = "data/telemetria_consumos_202507281246.csv"
    
    mode = sys.argv[2] if len(sys.argv) > 2 else "hybrid"
    
    if not os.path.exists(data_file):
        print(f"❌ Erro: Arquivo não encontrado: {data_file}")
        return
    
    print(f"📂 Carregando: {data_file}")
    df = pd.read_csv(data_file)
    
    value_columns = [col for col in df.columns if col.startswith('index_')]
    
    print(f"Colunas de valores: {len(value_columns)}")
    
    # Choose mode
    if mode == "svd":
        print("\n🔬 Modo: SVD Puro")
        imputed_df = latc_svd_imputation(df, value_columns, n_components=50, max_iterations=10)
    elif mode == "hybrid":
        print("\n⚡ Modo: Híbrido Inteligente")
        imputed_df = latc_hybrid_imputation(df, value_columns, gap_threshold_hours=72)
    else:
        print(f"❌ Modo desconhecido: {mode}")
        return
    
    # Save
    output_file = "data/imputed_consumption_full.csv"
    print(f"\n💾 Salvando: {output_file}")
    imputed_df.to_csv(output_file, index=False)
    
    print("\n" + "="*70)
    print("✅ SUCESSO - LATC Científico")
    print("="*70)


if __name__ == "__main__":
    main()
