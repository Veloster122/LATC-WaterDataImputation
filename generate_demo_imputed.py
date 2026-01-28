"""
Script to generate the imputed version of the 70MB demo dataset.
This allows the user to have a "complete package" (Original + Imputed) for demo purposes.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import latc_simple
import os

def generate_demo_imputed():
    print("🚀 Iniciando geração de dados imputados para Demo...")
    
    input_file = Path("data/dataset_exemplo_70mb.csv")
    output_file = Path("data/dataset_exemplo_70mb_imputado.csv")
    
    if not input_file.exists():
        print(f"❌ Arquivo de entrada não encontrado: {input_file}")
        return
        
    print(f"📂 Lendo: {input_file}")
    df = pd.read_csv(input_file)
    
    value_columns = [col for col in df.columns if col.startswith('index_')]
    print(f"   Colunas de valor: {len(value_columns)} (index_0..index_23)")
    
    # Simple callback
    def progress(pct, msg):
        print(f"   ⏳ {pct:.0f}% - {msg}", end='\r')
        
    print("⚡ Executando Imputação (Modo Rápido/Linear)...")
    # Using simple for speed and robustness for demo data
    # (The user can run advanced later if they want, but this is enough for viz demo)
    imputed_df = latc_simple.simple_latc_imputation(
        df=df,
        value_columns=value_columns,
        progress_callback=progress
    )
    
    print("\n✅ Imputação concluída!")
    
    print(f"💾 Salvando: {output_file}")
    imputed_df.to_csv(output_file, index=False)
    
    print(f"✨ Arquivo de imputação demo criado com sucesso! ({output_file.stat().st_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    generate_demo_imputed()
