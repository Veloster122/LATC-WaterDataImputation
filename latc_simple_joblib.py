"""
LATC Simple - Versão com JOBLIB (melhor para Windows + Streamlit)
Joblib tem melhor serialização e funciona bem com NumPy/Pandas
"""

import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

from progress_tracker import ProgressTracker


def _process_meter_joblib(meter_data_tuple):
    """Worker para joblib - recebe tupla (meter_id, meter_matrix, value_columns, enforce_mono)"""
    meter_id, meter_matrix, value_columns, enforce_monotonicity = meter_data_tuple
    
    # 1. Horizontal interpolation
    temp_df = pd.DataFrame(meter_matrix)
    if np.any(np.isnan(meter_matrix)):
        temp_df = temp_df.interpolate(method='linear', axis=1, limit_direction='both')
    temp_df = temp_df.ffill(axis=1).bfill(axis=1)
    
    # 2. Vertical fill
    if temp_df.isnull().values.any():
        temp_df = temp_df.ffill(axis=0).bfill(axis=0)
    temp_df = temp_df.fillna(0)
    
    imputed_matrix = temp_df.values
    
    # 3. Monotonicity
    if enforce_monotonicity:
        for i in range(len(imputed_matrix)):
            for j in range(1, imputed_matrix.shape[1]):
                if imputed_matrix[i, j] < imputed_matrix[i, j-1]:
                    imputed_matrix[i, j] = imputed_matrix[i, j-1]
    
    return (meter_id, imputed_matrix)


def simple_latc_imputation_joblib(df, value_columns, enforce_monotonicity=True, 
                                   progress_callback=None, n_workers=None):
    """
    Versão com JOBLIB para melhor paralelização no Windows
    """
    print("🚀 LATC Imputation (JOBLIB backend - Windows optimized)")
    
    if 'id' not in df.columns:
        print("ERROR: 'id' column required")
        return df
    
    # Stats
    consumption_matrix = df[value_columns].values.astype(float)
    missing_count = np.sum(np.isnan(consumption_matrix))
    print(f"Missing: {missing_count:,} / {consumption_matrix.size:,}")
    
    unique_ids = df['id'].unique()
    print(f"Meters: {len(unique_ids):,}")
    
    # Determine workers
    if n_workers is None:
        from multiprocessing import cpu_count
        n_workers = max(2, cpu_count() - 1)
    
    print(f"Workers: {n_workers}")
    
    # Prepare data tuples (pre-group to avoid repeated filtering)
    print("Preparing batches...")
    grouped = df.groupby('id', sort=False)
    
    tasks = []
    for meter_id, group in grouped:
        meter_matrix = group[value_columns].values.astype(float)
        tasks.append((meter_id, meter_matrix, value_columns, enforce_monotonicity))
    
    print(f"Created {len(tasks)} tasks")
    
    # Process with joblib
    from joblib import Parallel, delayed
    import time
    
    start = time.time()
    
    print(f"\n⚙️ Processing in parallel (joblib)...")
    
    try:
        # Use prefer="processes" for true parallelism (não threads!)
        results = Parallel(n_jobs=n_workers, prefer="processes", verbose=10)(
            delayed(_process_meter_joblib)(task) for task in tasks
        )
        
        elapsed = time.time() - start
        print(f"\n✅ Completed in {elapsed:.1f}s ({len(tasks)/elapsed:.1f} meters/s)")
        
    except Exception as e:
        print(f"❌ Parallel error: {e}")
        print("Falling back to sequential...")
        
        results = []
        for i, task in enumerate(tasks):
            result = _process_meter_joblib(task)
            results.append(result)
            if i % 100 == 0:
                print(f"  {i}/{len(tasks)}")
    
    # Reconstruct DataFrame
    print("Reconstructing DataFrame...")
    
    # Create dict for fast lookup
    imputed_dict = {meter_id: matrix for meter_id, matrix in results}
    
    # Update original df
    result_df = df.copy()
    
    for meter_id in unique_ids:
        mask = result_df['id'] == meter_id
        result_df.loc[mask, value_columns] = imputed_dict[meter_id]
    
    print("✅ Done!")
    return result_df


# Test function
def test_joblib():
    print("Testing JOBLIB parallelization...\n")
    
    # Create dummy data
    n_meters = 1000
    n_days = 100
    
    data = []
    for meter_id in range(n_meters):
        for day in range(n_days):
            row = {'id': meter_id, 'data': f'2024-01-{day+1:02d}'}
            for h in range(24):
                row[f'index_{h}'] = np.random.rand() * 100 if np.random.rand() > 0.2 else np.nan
            data.append(row)
    
    df = pd.DataFrame(data)
    value_cols = [f'index_{i}' for i in range(24)]
    
    print(f"Test data: {len(df)} rows, {n_meters} meters\n")
    
    # Test
    import time
    start = time.time()
    result = simple_latc_imputation_joblib(df, value_cols, n_workers=6)
    elapsed = time.time() - start
    
    print(f"\nTotal time: {elapsed:.2f}s")
    print(f"Throughput: {n_meters/elapsed:.1f} meters/s")


if __name__ == "__main__":
    test_joblib()
