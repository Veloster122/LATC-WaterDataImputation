"""
Script de diagnóstico completo para identificar gargalos
"""
import pandas as pd
import numpy as np
import time
from pathlib import Path

def diagnose_bottleneck():
    print("🔍 Diagnóstico de Performance LATC\n")
    print("="*60)
    
    # 1. Verificar tamanho do dataset
    data_file = Path("data/dataset_exemplo_70mb.csv")
    
    if not data_file.exists():
        print("❌ Arquivo de teste não encontrado")
        return
        
    file_size = data_file.stat().st_size / (1024*1024)
    print(f"1. Tamanho do arquivo: {file_size:.1f} MB")
    
    # 2. Teste de leitura (I/O)
    print("\n2. Teste de I/O (leitura)...")
    start = time.time()
    df = pd.read_csv(data_file)
    io_time = time.time() - start
    print(f"   Tempo de leitura: {io_time:.2f}s")
    print(f"   Linhas: {len(df):,}")
    print(f"   Contadores únicos: {df['id'].nunique():,}")
    
    # 3. Teste de processamento puro (CPU)
    print("\n3. Teste de CPU (uma linha de interpolação)...")
    value_cols = [col for col in df.columns if col.startswith('index_')]
    sample_row = df[value_cols].iloc[0].values.astype(float)
    
    start = time.time()
    for _ in range(1000):
        temp = pd.Series(sample_row).interpolate(method='linear').values
    cpu_time = time.time() - start
    print(f"   1000 interpolações: {cpu_time:.3f}s ({1000/cpu_time:.0f} ops/s)")
    
    # 4. Estimativa de tempo total
    n_meters = df['id'].nunique()
    avg_rows_per_meter = len(df) / n_meters
    
    ops_per_meter = avg_rows_per_meter * 2  # interpolation + monotonicity
    total_ops = ops_per_meter * n_meters
    
    estimated_sequential = total_ops / (1000/cpu_time)  # baseado no benchmark
    
    print(f"\n4. Estimativas:")
    print(f"   Operações totais: ~{total_ops:,.0f}")
    print(f"   Tempo sequencial estimado: ~{estimated_sequential:.1f}s")
    
    # 5. Teste de multiprocessing
    print(f"\n5. Teste de multiprocessing...")
    
    def worker_func(x):
        return sum(range(x))
    
    from multiprocessing import Pool, cpu_count
    n_workers = cpu_count() - 1
    tasks = [1000000] * 20
    
    # Sequential
    start = time.time()
    results_seq = [worker_func(x) for x in tasks]
    seq_time = time.time() - start
    
    # Parallel
    start = time.time()
    try:
        with Pool(n_workers) as pool:
            results_par = pool.map(worker_func, tasks)
        par_time = time.time() - start
        speedup = seq_time / par_time
        
        print(f"   Sequencial: {seq_time:.3f}s")
        print(f"   Paralelo ({n_workers} workers): {par_time:.3f}s")
        print(f"   Speedup: {speedup:.2f}x")
        
        if speedup < 1.5:
            print("   ⚠️  PROBLEMA: Speedup muito baixo!")
            print("   Possível causa: Overhead de serialização ou I/O bound")
        else:
            print("   ✅ Multiprocessing funcionando corretamente")
            
    except Exception as e:
        print(f"   ❌ Erro de multiprocessing: {e}")
        print("   Causa provável: Incompatibilidade Windows + Streamlit")
    
    # 6. Identificar gargalo
    print(f"\n6. Análise de gargalo:")
    io_ratio = io_time / (io_time + estimated_sequential)
    
    if io_ratio > 0.5:
        print(f"   📁 I/O BOUND ({io_ratio*100:.0f}% do tempo em disco)")
        print("   Solução: Processar em memória, evitar re-leitura")
    else:
        print(f"   ⚙️  CPU BOUND ({(1-io_ratio)*100:.0f}% do tempo em processamento)")
        print("   Solução: Paralelização efetiva deve ajudar")
    
    print("\n" + "="*60)
    print("Diagnóstico completo!")

if __name__ == "__main__":
    diagnose_bottleneck()
