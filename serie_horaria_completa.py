"""
Série Temporal Hora a Hora - Ano Completo 2024
Cada ponto = uma hora específica (354 dias × 24 horas = ~8,500 pontos)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.gridspec import GridSpec
from datetime import datetime, timedelta
from progress_tracker import ProgressTracker

# Configuração
sns.set_style("whitegrid")

print("="*80)
print("SÉRIE TEMPORAL HORA A HORA - ANO COMPLETO 2024")
print("="*80)

# Arquivos
import sys
import os

if len(sys.argv) > 1:
    original_file = sys.argv[1]
else:
    original_file = "data/telemetria_consumos_202507281246.csv"

imputed_file = "data/imputed_consumption_full.csv"

if not os.path.exists(original_file):
    print(f"Erro: Arquivo original não encontrado: {original_file}")
    sys.exit(1)

print("\nCarregando e processando dados hora a hora...")
print("(Isso criará uma série temporal de ~8,500 pontos...)")


# ==============================================================================
# FUNÇÕES DE API (Para uso na GUI)
# ==============================================================================

def get_data_arrays(original_file, imputed_file="data/imputed_consumption_full.csv"):
    """
    Carrega os dados e retorna os arrays numéricos para plotagem.
    Retorna: (timestamps, consumo_orig_serie, consumo_imp_serie, diff_percent, datas_comuns)
    """
    import pandas as pd
    import numpy as np
    from datetime import timedelta
    
    value_cols = [f'index_{i}' for i in range(24)]
    
    # 1. Carregar Original
    dados_horarios_orig = {}
    chunk_size = 100000
    
    for chunk in pd.read_csv(original_file, chunksize=chunk_size):
        for data in chunk['data'].unique():
            if data not in dados_horarios_orig:
                dados_horarios_orig[data] = np.zeros(23)
            data_chunk = chunk[chunk['data'] == data]
            matrix = data_chunk[value_cols].values.astype(float)
            for i in range(23):
                hourly = matrix[:, i+1] - matrix[:, i]
                valid = (hourly >= 0) & (~np.isnan(hourly))
                if np.any(valid):
                    dados_horarios_orig[data][i] = np.mean(hourly[valid])

    # 2. Carregar Imputado
    dados_horarios_imp = {}
    for chunk in pd.read_csv(imputed_file, chunksize=chunk_size):
        for data in chunk['data'].unique():
            if data not in dados_horarios_imp:
                dados_horarios_imp[data] = np.zeros(23)
            data_chunk = chunk[chunk['data'] == data]
            matrix = data_chunk[value_cols].values.astype(float)
            for i in range(23):
                hourly = matrix[:, i+1] - matrix[:, i]
                valid = (hourly >= 0) & (~np.isnan(hourly))
                if np.any(valid):
                    dados_horarios_imp[data][i] = np.mean(hourly[valid])

    # 3. Construir Série
    datas_comuns = sorted(set(dados_horarios_orig.keys()) & set(dados_horarios_imp.keys()))
    timestamps = []
    consumo_orig_serie = []
    consumo_imp_serie = []
    
    for data in datas_comuns:
        data_dt = pd.to_datetime(data)
        for hora in range(23):
            timestamp = data_dt + timedelta(hours=hora)
            timestamps.append(timestamp)
            consumo_orig_serie.append(dados_horarios_orig[data][hora])
            consumo_imp_serie.append(dados_horarios_imp[data][hora])

    timestamps = np.array(timestamps)
    consumo_orig_serie = np.array(consumo_orig_serie)
    consumo_imp_serie = np.array(consumo_imp_serie)
    
    diff_horaria = consumo_imp_serie - consumo_orig_serie
    diff_percent = (diff_horaria / (consumo_orig_serie + 1e-10)) * 100
    
    return timestamps, consumo_orig_serie, consumo_imp_serie, diff_percent, datas_comuns

def create_figure(timestamps, consumo_orig_serie, consumo_imp_serie, diff_percent, datas_comuns, view_mode='dashboard'):
    """
    Cria e retorna o objeto Figure do Matplotlib.
    Modes: dashboard (default), full, zoom, diff, stats
    """
    # Estilo Eco Light (Clean)
    plt.style.use('default') 
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['grid.alpha'] = 0.3
    
    fig = plt.figure(figsize=(12, 9))
    
    # === MODOS DE VISUALIZAÇÃO ===
    
    if view_mode == 'full':
        # SÉRIE COMPLETA (100% dos pontos)
        ax = fig.add_subplot(111)
        ax.plot(timestamps, consumo_orig_serie, '-', color='#2E86AB', linewidth=1.0, label='Original (Total)', rasterized=True)
        ax.plot(timestamps, consumo_imp_serie, '-', color='#A23B72', linewidth=1.0, alpha=0.8, label='Imputado', rasterized=True)
        ax.set_title(f'Série Temporal Completa - Todos os Detalhes ({len(timestamps):,} pontos)', fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, linestyle=':', alpha=0.5)
        
    elif view_mode == 'zoom':
        # APENAS ZOOM (Primeiros 45 dias com mais detalhes)
        ax = fig.add_subplot(111)
        n_zoom = min(45 * 24, len(timestamps))
        ax.plot(timestamps[:n_zoom], consumo_orig_serie[:n_zoom], '-o', color='#2E86AB', lw=1.5, ms=3, label='Original', rasterized=True)
        ax.plot(timestamps[:n_zoom], consumo_imp_serie[:n_zoom], '-s', color='#A23B72', lw=1.5, ms=3, alpha=0.8, label='Imputado', rasterized=True)
        ax.set_title('Zoom Detalhado: Primeiros 45 Dias', fontweight='bold')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3)
        
    elif view_mode == 'diff':
        # ANÁLISE DE DIFERENÇA
        gs = GridSpec(2, 1, figure=fig, hspace=0.3)
        
        ax1 = fig.add_subplot(gs[0])
        ax1.plot(range(len(diff_percent)), diff_percent, '-', color='#E74C3C', lw=0.5, rasterized=True)
        ax1.axhline(0, color='k'), ax1.axhline(5, color='orange', ls='--'), ax1.axhline(-5, color='orange', ls='--')
        ax1.set_title('Diferença Percentual (%)', fontweight='bold')
        ax1.set_ylabel('% Erro')
        
        ax2 = fig.add_subplot(gs[1])
        ax2.hist(diff_percent, bins=50, color='#E74C3C', alpha=0.7, range=(-20, 20), rasterized=True)
        ax2.set_title('Distribuição do Erro ( Histograma )', fontweight='bold')
        ax2.set_xlabel('% Diferença')

    elif view_mode == 'stats':
        # ESTATÍSTICAS E SEMANAL
        gs = GridSpec(2, 2, figure=fig, hspace=0.3)
        
        # Histograma
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.hist(consumo_orig_serie, bins=30, color='#2E86AB', alpha=0.6, label='Orig', density=True, rasterized=True)
        ax1.hist(consumo_imp_serie, bins=30, color='#A23B72', alpha=0.6, label='Imp', density=True, rasterized=True)
        ax1.set_title('Distribuição de Valores', fontweight='bold')
        ax1.legend()
        
        # Semanal
        ax2 = fig.add_subplot(gs[0, 1])
        df_temp = pd.DataFrame({'ts': timestamps, 'orig': consumo_orig_serie, 'imp': consumo_imp_serie})
        df_temp['sem'] = df_temp['ts'].dt.dayofweek
        sem_orig = df_temp.groupby('sem')['orig'].mean()
        sem_imp = df_temp.groupby('sem')['imp'].mean()
        ax2.plot(range(7), sem_orig, 'o-', label='Orig')
        ax2.plot(range(7), sem_imp, 's-', label='Imp')
        ax2.set_xticks(range(7))
        ax2.set_xticklabels(['S','T','Q','Q','S','S','D'])
        ax2.set_title('Padrão Médio Semanal', fontweight='bold')
        
        # Texto Stats
        ax3 = fig.add_subplot(gs[1, :])
        ax3.axis('off')
        txt = (f"ESTATÍSTICAS GERAIS\n"
               f"{'-'*40}\n"
               f"Original Médio: {np.mean(consumo_orig_serie):.4f} m3/h\n"
               f"Imputado Médio: {np.mean(consumo_imp_serie):.4f} m3/h\n"
               f"Correlação:     {np.corrcoef(consumo_orig_serie, consumo_imp_serie)[0,1]:.4f}\n"
               f"Erro Médio Abs: {np.mean(np.abs(diff_percent)):.2f} %\n"
               f"Pontos Totais:  {len(timestamps):,}")
        ax3.text(0.5, 0.5, txt, fontsize=12, family='monospace', ha='center', va='center',
                 bbox=dict(facecolor='#f0f0f0', edgecolor='#ccc', pad=20))

    else:
        # DASHBOARD PADRÃO (Otimizado)
        gs = GridSpec(4, 2, figure=fig, hspace=0.4, wspace=0.3)
        
        # 1. Série (Downsample)
        ax1 = fig.add_subplot(gs[0, :])
        step = 6
        ax1.plot(timestamps[::step], consumo_orig_serie[::step], '-', color='#2E86AB', linewidth=1.0, label='Original', rasterized=True)
        ax1.plot(timestamps[::step], consumo_imp_serie[::step], '-', color='#A23B72', linewidth=1.0, label='Imputado', rasterized=True)
        ax1.set_title(f'Visão Geral (Otimizada ~{len(timestamps)//step} pts) - Use botões para detalhe', fontweight='bold', color='#555')
        ax1.legend(loc='upper left', fontsize=8)
        ax1.grid(True, linestyle=':', alpha=0.5)

        # 2. Zoom Preview
        ax2 = fig.add_subplot(gs[1, :])
        n_zoom = min(30 * 24, len(timestamps))
        ax2.plot(timestamps[:n_zoom], consumo_orig_serie[:n_zoom], '-o', color='#2E86AB', lw=1, ms=2, label='Original', rasterized=True)
        ax2.plot(timestamps[:n_zoom], consumo_imp_serie[:n_zoom], '-s', color='#A23B72', lw=1, ms=2, label='Imputado', rasterized=True)
        ax2.set_title('Zoom Preview (30 dias)', fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # 3. Diferença
        ax3 = fig.add_subplot(gs[2, 0])
        ax3.plot(range(len(diff_percent)), diff_percent, '-', color='#E74C3C', lw=0.3, alpha=0.5, rasterized=True)
        ax3.set_title('Diferença (%)', fontweight='bold')
        
        # 4. Histograma
        ax4 = fig.add_subplot(gs[2, 1])
        ax4.hist(consumo_orig_serie, bins=30, color='#2E86AB', alpha=0.5, label='Orig', density=True, rasterized=True)
        ax4.hist(consumo_imp_serie, bins=30, color='#A23B72', alpha=0.5, label='Imp', density=True, rasterized=True)
        ax4.set_title('Distribuição', fontweight='bold')
        
        # 5. Stats Mini
        ax5 = fig.add_subplot(gs[3, :])
        ax5.axis('off')
        ax5.text(0.5, 0.5, "Clique em [Estatísticas] na barra superior para ver mais detalhes.", ha='center', color='gray')

    plt.tight_layout()
    return fig

# ==============================================================================
# EXECUÇÃO CLI STANDALONE
# ==============================================================================
if __name__ == "__main__":
    if len(sys.argv) > 1:
        original_file = sys.argv[1]
    else:
        original_file = "data/telemetria_consumos_202507281246.csv"
        
    imputed_file = "data/imputed_consumption_full.csv"
    
    if not os.path.exists(original_file):
        print(f"Erro: Arquivo não encontrado: {original_file}")
        sys.exit(1)

    print("[INFO] Carregando dados...")
    data = get_data_arrays(original_file, imputed_file)
    
    print("[INFO] Gerando gráfico...")
    fig = create_figure(*data)
    
    print("[OK] Gráfico gerado. Abrindo janela...")
    plt.show()

