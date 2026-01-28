"""
Versão otimizada do LATC Simple com paralelização eficiente 
Corrige problemas de CPU underutilization
"""

import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor
import warnings
import os
warnings.filterwarnings('ignore')

from progress_tracker import ProgressTracker


def _process_meter_chunk_optimized(args):
    """Worker otimizado - recebe apenas IDs e carrega dados internamente"""
    meter_ids, df_path, value_columns, enforce_monotonicity = args
    
    # Cada worker carrega apenas seus dados (evita serialização pesada)
    df = pd.read_csv(df_path)
    
    results = []
    for meter_id in meter_ids:
        meter_data = df[df['id'] == meter_id].copy()
        meter_matrix = meter_data[value_columns].values.astype(float)
        
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
        
        meter_data[value_columns] = imputed_matrix
        results.append(meter_data)
    
    return pd.concat(results, ignore_index=True)


def simple_latc_imputation_optimized(df, value_columns, enforce_monotonicity=True, 
                                      progress_callback=None, n_workers=None):
    """
    Versão ULTRA-OTIMIZADA com paralelização real
    """
    print("🚀 Starting OPTIMIZED imputation (real parallelization)...")
    
    if 'id' not in df.columns:
        print("ERROR: 'id' column required")
        return df
    
    # Stats
    consumption_matrix = df[value_columns].values.astype(float)
    missing_count = np.sum(np.isnan(consumption_matrix))
    total = consumption_matrix.size
    print(f"Missing: {missing_count:,} ({100*missing_count/total:.2f}%)")
    
    unique_ids = df['id'].unique()
    print(f"Total meters: {len(unique_ids):,}")
    
    # Determine workers
    if n_workers is None:
        import multiprocessing
        n_workers = max(2, multiprocessing.cpu_count() - 1)
    
    print(f"Using {n_workers} parallel workers")
    
    # Save temp file for workers to load
    import tempfile
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='w')
    temp_path = temp_file.name
    temp_file.close()
    df.to_csv(temp_path, index=False)
    
    print(f"Temp file: {temp_path}")
    
    # Split IDs into chunks
    chunk_size = max(1, len(unique_ids) // (n_workers * 4))  # 4 chunks per worker
    id_chunks = [unique_ids[i:i+chunk_size] for i in range(0, len(unique_ids), chunk_size)]
    
    print(f"Created {len(id_chunks)} chunks ({chunk_size} meters/chunk)")
    
    # Prepare args
    args_list = [
        (chunk, temp_path, value_columns, enforce_monotonicity)
        for chunk in id_chunks
    ]
    
    # Process in parallel
    import time
    start = time.time()
    results = []
    
    print(f"\n⚙️ Processing chunks in parallel...")
    
    if n_workers > 1:
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            futures = [executor.submit(_process_meter_chunk_optimized, args) for args in args_list]
            
            for idx, future in enumerate(futures):
                result = future.result()
                results.append(result)
                
                elapsed = time.time() - start
                progress = (idx + 1) / len(futures) * 100
                
                print(f"  [{idx+1}/{len(futures)}] {progress:.1f}% | {elapsed:.1f}s elapsed")
                
                if progress_callback:
                    progress_callback(int(progress), f"Chunk {idx+1}/{len(futures)}")
    else:
        for idx, args in enumerate(args_list):
            result = _process_meter_chunk_optimized(args)
            results.append(result)
    
    # Cleanup
    try:
        os.remove(temp_path)
    except:
        pass
    
    # Combine
    final_df = pd.concat(results, ignore_index=True)
    
    elapsed = time.time() - start
    throughput = len(unique_ids) / elapsed
    
    print(f"\n✅ COMPLETE!")
    print(f"   Time: {elapsed:.1f}s")
    print(f"   Throughput: {throughput:.1f} meters/s")
    
    return final_df
