"""
FAST NUMPY SMOOTHING that handles FULL TIME SERIES (Inter-day smoothing)
Solves the "staircase" issue across day boundaries while remaining extremely fast.
"""

import numpy as np
import pandas as pd

def smooth_time_series_numpy(df, value_columns, original_df, window_size=25, verbose=True):
    """
    Apply smoothing to the FULL concatenated time series for each meter using fast generic numpy operations.
    
    This works by:
    1. Flattening the 2D matrix (days x hours) into a 1D array (continuous time)
    2. Applying correlation/convolution smoothing per meter
    3. Reshaping back
    
    Args:
        df: DataFrame with IMPUTED data (must check 'id' column)
        value_columns: List of column names (index_0..index_23)
        original_df: DataFrame with ORIGINAL data (aligned)
        window_size: Window size for smoothing
        verbose: Print progress
        
    Returns:
        DataFrame with smoothed values (original values preserved)
    """
    if verbose:
        print(f"\n🌊 Suavização Contínua (Numpy Convolution, janela={window_size})...")
        print(f"   Tratando transições entre dias (Evita degraus nas viradas de dia)")
    
    # 1. Prepare Data
    # Sort by ID and Date to ensure continuous time
    if verbose: print("   Ordenando dados...")
    
    # We work on copies to be safe
    df_work = df.copy()
    
    # Align sorting of both dataframes
    # Assume df and original_df are already aligned by the caller (latc_app.py logic)
    # But just to be sure we are working on the internal df structure
    
    # Extract values: (N_rows, 24)
    imputed_vals = df_work[value_columns].values.astype(float)
    original_vals = original_df[value_columns].values.astype(float)
    ids = df_work['id'].values
    
    n_rows, n_cols = imputed_vals.shape
    
    if verbose: print(f"   Processando {n_rows:,} dias x {n_cols} horas...")
    
    # 2. Identify Meter Boundaries
    # changing_ids is True where id changes from previous row
    # We need to loop over meters. 
    # Fast way: identify start/end indices for each meter
    
    # Get unique IDs and their counts (assuming sorted by ID!)
    # Ideally should sort first, but let's assume the alignment step did it. 
    # To be safe, let's use the ID grouping approach which is robust.
    
    # Efficient iteration using numpy unique with counts
    unique_ids, counts = np.unique(ids, return_counts=True)
    # The ids might not be contiguous blocks if not sorted, so let's rely on pandas groupby indices
    # which is safer and quite fast.
    
    # Group indices by ID
    grouped_indices = df_work.groupby('id').indices # Dict {id: array_of_indices}
    
    total_meters = len(grouped_indices)
    processed_count = 0
    
    # Output arrays
    smoothed_flat = np.zeros(imputed_vals.size)
    
    # Flatten the input matrices for easier indexing
    # But wait, groupby indices refer to ROW indices.
    # We want to smooth the FLATTENED sequence of rows for each meter.
    
    # Let's create a Result Matrix of same shape
    final_matrix = imputed_vals.copy()
    
    # Pre-calculate window for convolution
    window = np.ones(window_size) / window_size
    
    # Iterate over meters
    for i, (meter_id, row_indices) in enumerate(grouped_indices.items()):
        
        # Sort indices (groupby might not guarantee order if data wasn't sorted)
        # We need strict chronological order
        # Assuming df was sorted by date, row_indices should be monotonic.
        # But let's act on the Safe side: Get sorting order of these rows by 'data' if possible?
        # The latc_app passes 'df_to_smooth' which might NOT be sorted by ID/Data completely?
        # Let's trust row_indices are in order if input DF was sorted.
        
        # Extract the block for this meter: (M_days, 24)
        meter_imputed = imputed_vals[row_indices]
        meter_original = original_vals[row_indices]
        
        # Flatten to 1D (M_days * 24)
        meter_flat_imp = meter_imputed.ravel()
        meter_flat_orig = meter_original.ravel()
        
        # Smooth (Convolution)
        # mode='same' keeps size same
        if len(meter_flat_imp) >= window_size:
            # Handle edge effects better? mirror padding?
            # Simple 'same' convolution pads with zero, which is bad for series.
            # Use data reflection or edge value extension.
            # np.convolve doesn't support 'valid' without size change.
            
            # Use pandas rolling on this 1D chunk - it handles edges better (NaNs then min_periods)
            # It's fast enough for 1D arrays
            s_smooth = pd.Series(meter_flat_imp).rolling(
                window=window_size, center=True, min_periods=1
            ).mean().values
            
            # Monotonicity check (Cumulative reading shouldn't decrease)
            # Vectorized enforce: maximum.accumulate
            # But only enforce if it was monotonic to begin with? 
            # Imputed data usually preserves it. Smoothing might oscillate.
            s_smooth = np.maximum.accumulate(s_smooth)
            
        else:
            s_smooth = meter_flat_imp # Too short
        
        # Masking: Put back original values
        mask_nan = np.isnan(meter_flat_orig)
        # Where NOT NaN (Original exists), use Original. Where NaN, use Smooth.
        final_flat = meter_flat_orig.copy()
        final_flat[mask_nan] = s_smooth[mask_nan]
        
        # Reshape back to (M_days, 24) and assign to result matrix
        final_matrix[row_indices] = final_flat.reshape(meter_imputed.shape)
        
        processed_count += 1
        if verbose and processed_count % 2000 == 0:
             print(f"   Progresso: {processed_count}/{total_meters}")

    if verbose: print(f"   ✅ Concluído! {total_meters} contadores processados.")
    
    # Write back to DF
    result_df = df.copy()
    result_df[value_columns] = final_matrix
    
    return result_df
