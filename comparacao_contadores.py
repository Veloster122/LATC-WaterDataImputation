
"""
Evolução Temporal de 6 Contadores - Ano Completo 2024
Mostra consumo acumulado de cada contador ao longo dos meses
Refatorado para GUI v3.2 (Modular + Rasterized)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec
from datetime import datetime
import sys

# Configurar estilo visual para prevenir lag
plt.style.use('fast')
sns.set_style("whitegrid")

def get_comparison_data(original_file, imputed_file='data/imputed_consumption_full.csv'):
    """Carrega dados e seleciona os 6 contadores para comparação"""
    
    print(f"[DATA] Carregando datasets...")
    df_original = pd.read_csv(original_file)
    try:
        df_imputed = pd.read_csv(imputed_file)
    except FileNotFoundError:
        print("[ERROR] Arquivo de imputação não encontrado para comparação")
        return None

    value_cols = [f'index_{i}' for i in range(24)]

    # Encontrar contadores
    meter_counts = df_original['id'].value_counts()
    meters_multi = meter_counts[meter_counts >= 10].index.tolist()

    selected_meter_ids = []
    target = 4  # Reduzido de 6 para acelerar

    for meter_id in meters_multi[:150]:
        if len(selected_meter_ids) >= target:
            break
        
        meter_data_orig = df_original[df_original['id'] == meter_id]
        total_missing = 0
        
        # Heurística rápida para missing
        # Validação completa seria lenta, vamos checar NaNs diretos
        # Mas precisamos percorrer
        for idx in range(len(meter_data_orig)):
            vals = meter_data_orig.iloc[idx][value_cols].values.astype(float)
            if np.isnan(vals).any():
                total_missing += np.sum(np.isnan(vals))
        
        if total_missing >= 20:
            selected_meter_ids.append(meter_id)
            if len(selected_meter_ids) >= 4:  # Limita a 4 para performance
                break

    # Preparar payload de dados para plotagem
    # Vamos extrair arrays prontos para não passar DataFrames inteiros
    plot_data = []
    
    for meter_id in selected_meter_ids:
        meter_orig = df_original[df_original['id'] == meter_id].sort_values('data')
        meter_imp = df_imputed[df_imputed['id'] == meter_id].sort_values('data')
        
        timestamps_imp = []
        valores_imp = []
        
        timestamps_orig = []
        valores_orig = []
        
        is_imputed_mask = []

        # Processar série temporal linear
        for i in range(len(meter_orig)):
            date = pd.to_datetime(meter_orig.iloc[i]['data'])
            for h in range(24):
                timestamp = date + pd.Timedelta(hours=h)
                val_orig = meter_orig.iloc[i][f'index_{h}']
                val_imp = meter_imp.iloc[i][f'index_{h}'] # Assumindo alinhamento
                
                timestamps_imp.append(timestamp)
                valores_imp.append(val_imp)
                
                if not np.isnan(val_orig):
                    timestamps_orig.append(timestamp)
                    valores_orig.append(val_orig)
                
                if np.isnan(val_orig):
                    is_imputed_mask.append(True)
                else:
                    is_imputed_mask.append(False)
                    
        plot_data.append({
            'id': meter_id,
            'ts_imp': np.array(timestamps_imp),
            'val_imp': np.array(valores_imp),
            'ts_orig': np.array(timestamps_orig),
            'val_orig': np.array(valores_orig),
            'mask_imp': np.array(is_imputed_mask),
            'n_total': len(timestamps_imp),
            'n_missing': sum(is_imputed_mask),
            'n_dates': len(meter_orig)
        })
        
    return plot_data

def create_figure(plot_data):
    """Gera a figura Matplotlib baseada nos dados pré-processados"""
    if not plot_data:
        return None
        
    # Estilo Eco Light
    plt.style.use('default')
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['grid.alpha'] = 0.3
    
    # Ajuste para 4 gráficos (2x2) para acelerar
    fig = plt.figure(figsize=(12, 10))
    gs = GridSpec(2, 2, figure=fig, hspace=0.5, wspace=0.3)
    
    for plot_idx, data in enumerate(plot_data):
        ax = fig.add_subplot(gs[plot_idx // 2, plot_idx % 2])
        
        # Downsample EXTREMO ::72 (1 ponto a cada 3 dias) para velocidade máxima
        step = 72
        
        # Plotar Imputado PRIMEIRO (Fundo - linha contínua completa)
        ax.plot(data['ts_imp'][::step], data['val_imp'][::step], '-', color='#A23B72', 
                linewidth=2, alpha=1.0, label='Imputado', zorder=1, rasterized=True)
        
        # Plotar Original (já tem gaps porque ts_orig só contém timestamps não-NaN)
        ax.plot(data['ts_orig'][::step], data['val_orig'][::step], 
                '-', color='#2E86AB', linewidth=1.5, alpha=1.0,
                label='Original (Dados Reais)', zorder=2, rasterized=True)
        
        # Destacar imputados (Scatter pesado -> Rasterizar!)
        # Extrair timestamps onde mask é true
        ts_masked = data['ts_imp'][data['mask_imp']]
        val_masked = data['val_imp'][data['mask_imp']]
        
        if len(ts_masked) > 0:
            ax.scatter(ts_masked, val_masked,
                      color='#FF6B6B', s=15, marker='o', alpha=0.8,
                      label='Imputado (Ponto)', zorder=3, rasterized=True)
        
        # Config
        ax.set_title(f"ID: {data['id']} ({data['n_missing']} imputados)", 
                    fontweight='bold', fontsize=10)
        
        if plot_idx == 0:
            ax.legend(fontsize=8, loc='upper left')
            
        ax.grid(True, linestyle=':', alpha=0.5)
        
        # Formatar Eixo X (Meses)
        import matplotlib.dates as mdates
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
        ax.tick_params(axis='x', rotation=45, labelsize=8)

    fig.suptitle('Comparação Multi-Contadores (Integrado)', fontsize=14, fontweight='bold', y=0.98)
    
    return fig

if __name__ == "__main__":
    if len(sys.argv) > 1:
        orig = sys.argv[1]
    else:
        orig = 'data/telemetria_consumos_202507281246.csv'
        
    data = get_comparison_data(orig)
    if data:
        fig = create_figure(data)
        plt.show()
