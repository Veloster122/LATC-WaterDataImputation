"""
Optimized LATC Imputation Script - Handles edge cases better
"""

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
import warnings
import os
warnings.filterwarnings('ignore')

from progress_tracker import ProgressTracker


def simple_latc_imputation(df, value_columns, enforce_monotonicity=True, progress_callback=None):
    """
    LATC-inspired imputation with PER-METER processing to avoid cross-contamination
    
    Args:
        df: DataFrame with consumption data (must include 'id' column)
        value_columns: List of column names with hourly readings
        enforce_monotonicity: Whether to enforce non-decreasing values
        progress_callback: Optional callback for progress updates
        
    Returns:
        DataFrame with imputed values
    """
    print("Starting robust imputation (per-meter mode)...")
    
    # Check if 'id' column exists
    if 'id' not in df.columns:
        print("ERROR: 'id' column not found. Cannot process per-meter.")
        print("Falling back to legacy mode (may cause spikes)...")
        return _legacy_imputation(df, value_columns, enforce_monotonicity)
    
    # Count missing values (overall)
    consumption_matrix = df[value_columns].values.astype(float)
    mask = ~np.isnan(consumption_matrix)
    total_values = consumption_matrix.size
    missing_count = np.sum(~mask)
    
    print(f"Total data shape: {consumption_matrix.shape}")
    print(f"Total missing values: {missing_count:,} ({100 * missing_count / total_values:.2f}%)")
    
    # Process each meter separately
    unique_ids = df['id'].unique()
    print(f"Processing {len(unique_ids):,} unique meters individually...")
    
    processed_batches = []
    
    for idx, meter_id in enumerate(unique_ids):
        if idx % 100 == 0:
            print(f"  Processing meter {idx+1}/{len(unique_ids)}...")
            if progress_callback and idx > 0:
                progress = int(100 * idx / len(unique_ids))
                progress_callback(progress, f"Imputando contador {idx+1}/{len(unique_ids)}")
        
        # Filter data for this specific meter
        meter_data = df[df['id'] == meter_id].copy()
        meter_matrix = meter_data[value_columns].values.astype(float)
        
        # 1. Horizontal interpolation (within day)
        temp_df = pd.DataFrame(meter_matrix, columns=[f'col_{j}' for j in range(meter_matrix.shape[1])])
        
        if np.any(np.isnan(meter_matrix)):
            temp_df = temp_df.interpolate(method='linear', axis=1, limit_direction='both')
        
        temp_df = temp_df.ffill(axis=1).bfill(axis=1)
        
        # 2. Vertical fill (across days) - NOW SAFE because it's only this meter
        if temp_df.isnull().values.any():
            temp_df = temp_df.ffill(axis=0)
            temp_df = temp_df.bfill(axis=0)
        
        # 3. Final cleanup
        temp_df = temp_df.fillna(0)
        
        imputed_matrix = temp_df.values
        
        # 4. Enforce monotonicity (within day only)
        if enforce_monotonicity:
            for i in range(len(imputed_matrix)):
                for j in range(1, imputed_matrix.shape[1]):
                    if imputed_matrix[i, j] < imputed_matrix[i, j-1]:
                        imputed_matrix[i, j] = imputed_matrix[i, j-1]
        
        # Update this meter's data
        meter_data[value_columns] = imputed_matrix
        processed_batches.append(meter_data)
    
    # Combine all meters back
    result_df = pd.concat(processed_batches, ignore_index=True)
    
    # Verify no NaN remaining
    final_matrix = result_df[value_columns].values.astype(float)
    remaining_nan = np.sum(np.isnan(final_matrix))
    print(f"Remaining NaN values: {remaining_nan}")
    
    print("Per-meter imputation complete!")
    return result_df


def _legacy_imputation(df, value_columns, enforce_monotonicity):
    """Legacy imputation method (processes all rows together - may cause spikes)"""
    print("WARNING: Using legacy mode without per-meter grouping")
    
    result_df = df.copy()
    consumption_matrix = df[value_columns].values.astype(float)
    imputed_matrix = consumption_matrix.copy()
    
    temp_df = pd.DataFrame(imputed_matrix, columns=[f'col_{j}' for j in range(imputed_matrix.shape[1])])
    
    if np.any(np.isnan(imputed_matrix)):
        temp_df = temp_df.interpolate(method='linear', axis=1, limit_direction='both')
    
    temp_df = temp_df.ffill(axis=1).bfill(axis=1)
    
    if temp_df.isnull().values.any():
        temp_df = temp_df.ffill(axis=0)
        temp_df = temp_df.bfill(axis=0)
    
    temp_df = temp_df.fillna(0)
    imputed_matrix = temp_df.values
    
    if enforce_monotonicity:
        for i in range(len(imputed_matrix)):
            for j in range(1, imputed_matrix.shape[1]):
                if imputed_matrix[i, j] < imputed_matrix[i, j-1]:
                    imputed_matrix[i, j] = imputed_matrix[i, j-1]
    
    result_df[value_columns] = imputed_matrix
    return result_df


def main():
    """Main execution function"""
    
    print("="*70)
    print("Robust LATC-Inspired Imputation for Telemetry Data")
    print("="*70)
    
    # Load data
    import sys
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        data_file = "data/telemetria_consumos_202507281246.csv"
        
    print(f"\nLoading data from: {data_file}")
    
    if not os.path.exists(data_file):
        print(f"Error: File not found: {data_file}")
        return

    # Initialize progress tracker
    progress = ProgressTracker("Interpolação Linear", 100)
    progress.update("Carregando dados...", 0)

    df = pd.read_csv(data_file)
    progress.update("Dados carregados", 10)
    
    print(f"Loaded {len(df):,} records")
    
    # Identify value columns
    value_columns = [col for col in df.columns if col.startswith('index_')]
    print(f"Value columns: {len(value_columns)} hourly readings")
    
    # Process in batches
    batch_size = 10000
    print(f"\nProcessing in batches of {batch_size:,} meters...")
    
    imputed_batches = []
    
    for i in range(0, len(df), batch_size):
        batch_num = i // batch_size + 1
        total_batches = (len(df) - 1) // batch_size + 1
        
        batch = df.iloc[i:i+batch_size].copy()
        print(f"\n{'='*70}")
        print(f"Batch {batch_num}/{total_batches} (rows {i:,} to {min(i+batch_size, len(df)):,})")
        print(f"{'='*70}")
        
        imputed_batch = simple_latc_imputation(batch, value_columns, enforce_monotonicity=True)
        imputed_batches.append(imputed_batch)
        
        # Update progress (processing batches = 60% of total work)
        batch_progress = 20 + int(60 * (batch_num / total_batches))
        progress.set_progress(batch_progress, f"Processando lote {batch_num}/{total_batches}...")
        if progress_callback:
            progress_callback(batch_progress, f"Processando dados (Lote {batch_num}/{total_batches})")
    
    # Combine all batches
    print(f"\n{'='*70}")
    print("Combining batches...")
    full_imputed_df = pd.concat(imputed_batches, ignore_index=True)
    
    # Save results
    output_file = "data/imputed_consumption_full.csv"
    progress.update("Salvando resultados...", 10)
    if progress_callback:
        progress_callback(90, "Finalizando e salvando...")
    print(f"Saving results to: {output_file}")
    full_imputed_df.to_csv(output_file, index=False)
    
    progress.complete()
    progress.cleanup()
    
    print(f"\n{'='*70}")
    print("SUCCESS!")
    print(f"{'='*70}")
    print(f"Total records processed: {len(full_imputed_df):,}")
    print(f"Output file: {output_file}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
