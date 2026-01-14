"""
Gap Analysis Module for Telemetry Data
Analyzes missing data patterns and generates comprehensive reports
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json
from datetime import datetime


def analyze_gaps(df, value_columns):
    """
    Analyze gap patterns in the dataset
    
    Returns:
        dict: Comprehensive gap statistics
    """
    print("\n" + "="*70)
    print("ANÁLISE DE GAPS - Dataset de Telemetria")
    print("="*70)
    
    consumption_matrix = df[value_columns].values.astype(float)
    mask = ~np.isnan(consumption_matrix)
    
    # Global statistics
    total_values = consumption_matrix.size
    missing_count = np.sum(~mask)
    missing_pct = 100 * missing_count / total_values
    
    print(f"\n📊 Estatísticas Globais:")
    print(f"   Contadores: {consumption_matrix.shape[0]:,}")
    print(f"   Timestamps: {consumption_matrix.shape[1]:,}")
    print(f"   Total de valores: {total_values:,}")
    print(f"   Valores faltantes: {missing_count:,} ({missing_pct:.2f}%)")
    print(f"   Valores presentes: {np.sum(mask):,} ({100-missing_pct:.2f}%)")
    
    # Per-meter statistics
    meter_stats = []
    
    for i in range(consumption_matrix.shape[0]):
        row = consumption_matrix[i, :]
        row_mask = ~np.isnan(row)
        
        missing_in_row = np.sum(~row_mask)
        pct_missing = 100 * missing_in_row / len(row)
        
        # Find gap sequences
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
                    gaps.append(j - gap_start)
                    in_gap = False
        
        if in_gap:  # Gap extends to end
            gaps.append(len(row) - gap_start)
        
        meter_id = df.iloc[i, 0] if 'id_contador' in df.columns else f"Meter_{i}"
        
        meter_stats.append({
            'meter_id': meter_id,
            'missing_count': missing_in_row,
            'missing_pct': pct_missing,
            'num_gaps': len(gaps),
            'max_gap_size': max(gaps) if gaps else 0,
            'avg_gap_size': np.mean(gaps) if gaps else 0,
            'median_gap_size': np.median(gaps) if gaps else 0
        })
    
    stats_df = pd.DataFrame(meter_stats)
    
    print(f"\n📈 Estatísticas por Contador:")
    print(f"   Contadores com 0% falta: {np.sum(stats_df['missing_pct'] == 0):,}")
    print(f"   Contadores com 1-10% falta: {np.sum((stats_df['missing_pct'] > 0) & (stats_df['missing_pct'] <= 10)):,}")
    print(f"   Contadores com 11-50% falta: {np.sum((stats_df['missing_pct'] > 10) & (stats_df['missing_pct'] <= 50)):,}")
    print(f"   Contadores com >50% falta: {np.sum(stats_df['missing_pct'] > 50):,}")
    print(f"   Contadores 100% vazios: {np.sum(stats_df['missing_pct'] == 100):,}")
    
    print(f"\n🔍 Tamanho dos Gaps:")
    print(f"   Maior gap encontrado: {stats_df['max_gap_size'].max():.0f} horas")
    print(f"   Gap médio: {stats_df['avg_gap_size'].mean():.1f} horas")
    print(f"   Mediana de gap: {stats_df['median_gap_size'].median():.1f} horas")
    
    return {
        'global': {
            'total_meters': consumption_matrix.shape[0],
            'total_timestamps': consumption_matrix.shape[1],
            'total_values': int(total_values),
            'missing_count': int(missing_count),
            'missing_pct': float(missing_pct)
        },
        'meter_stats': stats_df.to_dict('records'),
        'consumption_matrix_shape': consumption_matrix.shape,
        'timestamp': datetime.now().isoformat()
    }


def generate_gap_heatmap(df, value_columns, output_path='data/gap_heatmap.png', sample_size=500):
    """
    Generate heatmap visualization of gaps
    """
    print(f"\n🎨 Gerando heatmap de gaps...")
    
    consumption_matrix = df[value_columns].values.astype(float)
    
    # Sample if too large
    if consumption_matrix.shape[0] > sample_size:
        indices = np.random.choice(consumption_matrix.shape[0], sample_size, replace=False)
        consumption_matrix = consumption_matrix[indices, :]
        print(f"   (Amostrando {sample_size} contadores de {df.shape[0]} para visualização)")
    
    # Create binary mask (1=missing, 0=present)
    gap_mask = np.isnan(consumption_matrix).astype(int)
    
    # Downsample timestamps for visualization
    step = max(1, consumption_matrix.shape[1] // 200)  # ~200 colunas max
    gap_mask_downsampled = gap_mask[:, ::step]
    
    plt.figure(figsize=(14, 8))
    sns.heatmap(gap_mask_downsampled, cmap='RdYlGn_r', cbar_kws={'label': 'Missing Data'},
                yticklabels=False, xticklabels=False)
    plt.title('Padrão de Dados Faltantes (Vermelho = Falta)', fontsize=14)
    plt.xlabel('Tempo (Horas)', fontsize=12)
    plt.ylabel('Contadores', fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"   ✓ Heatmap salvo: {output_path}")


def generate_gap_report(stats, output_path='data/gap_report.md'):
    """
    Generate markdown report
    """
    print(f"\n📝 Gerando relatório markdown...")
    
    report = f"""# Relatório de Análise de Gaps
**Data:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 Resumo Global

- **Total de Contadores:** {stats['global']['total_meters']:,}
- **Total de Timestamps:** {stats['global']['total_timestamps']:,}
- **Taxa de Dados Faltantes:** {stats['global']['missing_pct']:.2f}%
- **Valores Presentes:** {stats['global']['total_values'] - stats['global']['missing_count']:,}
- **Valores Faltantes:** {stats['global']['missing_count']:,}

## 🔍 Distribuição de Gaps por Contador

"""
    
    meter_stats_df = pd.DataFrame(stats['meter_stats'])
    
    # Top 10 contadores com mais faltas
    top_missing = meter_stats_df.nlargest(10, 'missing_pct')
    
    report += "### Top 10 Contadores com Mais Faltas\n\n"
    report += "| Contador | % Faltante | Num Gaps | Max Gap (h) |\n"
    report += "|----------|------------|----------|-------------|\n"
    
    for _, row in top_missing.iterrows():
        report += f"| {row['meter_id']} | {row['missing_pct']:.1f}% | {row['num_gaps']:.0f} | {row['max_gap_size']:.0f} |\n"
    
    report += "\n## 💡 Recomendações\n\n"
    
    avg_missing = stats['global']['missing_pct']
    
    if avg_missing < 5:
        report += "- **Qualidade Excelente:** Dataset com poucos gaps. Interpolação linear é suficiente.\n"
    elif avg_missing < 20:
        report += "- **Qualidade Boa:** Considere LATC Científico para melhor precisão em gaps grandes.\n"
    else:
        report += "- **Qualidade Moderada:** LATC Científico recomendado para capturar padrões temporais.\n"
    
    max_gap = meter_stats_df['max_gap_size'].max()
    if max_gap > 168:  # >1 semana
        report += f"- **Atenção:** Gaps muito grandes detectados ({max_gap:.0f}h). LATC pode ajudar.\n"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"   ✓ Relatório salvo: {output_path}")


def main():
    """Run gap analysis on dataset"""
    import sys
    import os
    
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
    else:
        data_file = "data/telemetria_consumos_202507281246.csv"
    
    if not os.path.exists(data_file):
        print(f"❌ Erro: Arquivo não encontrado: {data_file}")
        return
    
    print(f"📂 Carregando: {data_file}")
    df = pd.read_csv(data_file)
    
    value_columns = [col for col in df.columns if col.startswith('index_')]
    
    if not value_columns:
        print("❌ Erro: Nenhuma coluna de valores encontrada (esperado 'index_*')")
        return
    
    # Run analysis
    stats = analyze_gaps(df, value_columns)
    
    # Generate outputs
    Path("data").mkdir(exist_ok=True)
    
    generate_gap_heatmap(df, value_columns)
    generate_gap_report(stats)
    
    # Save JSON metrics
    with open('data/gap_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*70)
    print("✅ ANÁLISE COMPLETA")
    print("="*70)
    print("\nArquivos gerados:")
    print("  • data/gap_report.md")
    print("  • data/gap_heatmap.png")
    print("  • data/gap_metrics.json")


if __name__ == "__main__":
    main()
