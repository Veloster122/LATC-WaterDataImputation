"""
Script de Re-imputação com Correção
Executa novamente a imputação com o algoritmo corrigido
"""

import subprocess
import os

print("="*80)
print("RE-EXECUTANDO IMPUTAÇÃO COM CORREÇÃO")
print("="*80)

print("""
ALTERAÇÃO REALIZADA:

Antes:
  if np.all(np.isnan(row)):
      imputed_matrix[i, :] = 0  ❌ Preenchia com ZEROS

Depois:
  if np.all(np.isnan(row)):
      continue  ✅ Deixa como NaN (dados inválidos)

IMPACTO:
- Dias sem nenhum dado não serão mais preenchidos com 0
- Consumo acumulado manterá consistência física
- Análises podem filtrar/ignorar dias completamente faltantes
""")

resposta = input("\n⚠️  Deseja re-executar a imputação? (s/n): ")

if resposta.lower() == 's':
    print("\n🔄 Executando latc_simple.py...")
    print("Isso pode levar 2-4 horas...")
    
    # Executar script
    result = subprocess.run(['python', 'latc_simple.py'], 
                          capture_output=False, text=True,
                          cwd=os.getcwd())
    
    if result.returncode == 0:
        print("\n✅ Imputação concluída com sucesso!")
        print("Arquivo atualizado: data/imputed_consumption_full.csv")
    else:
        print("\n❌ Erro durante a execução")
else:
    print("\n💡 Cancelado. Para re-imputar, execute: python latc_simple.py")
