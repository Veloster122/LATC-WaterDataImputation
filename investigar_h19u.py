"""
Investigação do Contador H19U
"""

import numpy as np
import pandas as pd

print("="*80)
print("INVESTIGAÇÃO: Contador H19U")
print("="*80)

# Carregar dados
print("\nCarregando dados do contador H19U...")
df_original = pd.read_csv('data/telemetria_consumos_202507281246.csv')
df_imputed = pd.read_csv('data/imputed_consumption_full.csv')

# Filtrar contador H19U
meter_orig = df_original[df_original['id'].str.contains('H19U', na=False)].sort_values('data')
meter_imp = df_imputed[df_imputed['id'].str.contains('H19U', na=False)].sort_values('data')

if len(meter_orig) == 0:
    # Tentar buscar por substring
    print("\nBuscando contadores que contêm 'H19U'...")
    all_meters = df_original['id'].unique()
    matching = [m for m in all_meters if 'H19U' in str(m)]
    print(f"Contadores encontrados: {matching}")
    
    if len(matching) > 0:
        meter_id = matching[0]
        print(f"\nUsando: {meter_id}")
        meter_orig = df_original[df_original['id'] == meter_id].sort_values('data')
        meter_imp = df_imputed[df_imputed['id'] == meter_id].sort_values('data')

print(f"\nEncontrados {len(meter_orig)} dias de leitura")

value_cols = [f'index_{i}' for i in range(24)]

# Analisar cada dia
print("\n" + "="*80)
print("ANÁLISE DIA A DIA")
print("="*80)

for i in range(min(10, len(meter_orig))):  # Primeiros 10 dias
    data = meter_orig.iloc[i]['data']
    vals_orig = meter_orig.iloc[i][value_cols].values.astype(float)
    vals_imp = meter_imp.iloc[i][value_cols].values.astype(float)
    
    n_missing = np.sum(np.isnan(vals_orig))
    n_zeros_imp = np.sum(vals_imp == 0)
    
    print(f"\nData: {data}")
    print(f"  Valores faltantes (original): {n_missing}/24")
    print(f"  Zeros na imputação: {n_zeros_imp}/24")
    
    if n_zeros_imp > 0:
        print(f"  ⚠️ PROBLEMA: Valores imputados como 0!")
        print(f"  Original: {vals_orig[:10]}")  # Primeiros 10
        print(f"  Imputado: {vals_imp[:10]}")
        
        # Verificar se TODOS os valores originais eram NaN
        if n_missing == 24:
            print(f"  💡 CAUSA: Todos os 24 valores eram NaN (dia sem dados)")
            print(f"  → Script preencheu com 0 por padrão")

print("\n" + "="*80)
print("DIAGNÓSTICO")
print("="*80)

# Contar dias problemáticos
dias_sem_dados = 0
dias_parciais = 0

for i in range(len(meter_orig)):
    vals_orig = meter_orig.iloc[i][value_cols].values.astype(float)
    n_missing = np.sum(np.isnan(vals_orig))
    
    if n_missing == 24:
        dias_sem_dados += 1
    elif n_missing > 0:
        dias_parciais += 1

print(f"\nTotal de dias: {len(meter_orig)}")
print(f"Dias SEM nenhum dado (100% NaN): {dias_sem_dados}")
print(f"Dias com dados parciais: {dias_parciais}")
print(f"Dias com dados completos: {len(meter_orig) - dias_sem_dados - dias_parciais}")

print("\n" + "="*80)
print("RECOMENDAÇÃO")
print("="*80)

if dias_sem_dados > 0:
    print(f"""
⚠️ PROBLEMA IDENTIFICADO:

O contador tem {dias_sem_dados} dia(s) onde TODAS as 24 leituras estão faltando.

O script atual (latc_simple.py) preenche esses dias com ZERO, o que NÃO faz
sentido para dados de consumo acumulado!

SOLUÇÕES POSSÍVEIS:

1. **Ignorar dias sem dados**: Remover/filtrar dias com 100% missing
2. **Interpolar entre dias**: Usar o último valor válido do dia anterior
3. **Usar média do mês**: Preencher com padrão típico do contador
4. **Marcar como inválido**: Manter como NaN ao invés de 0

Para dados de consumo acumulado, a melhor opção é (2): interpolar
usando o último valor conhecido e assumir crescimento constante.
""")
else:
    print("✅ Não foram encontrados dias com 100% de dados faltantes.")
    print("   O problema pode ser outro. Verifique os dados manualmente.")
