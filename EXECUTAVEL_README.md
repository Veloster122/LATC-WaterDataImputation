# LATC Tool GUI - Instruções de Uso

## Executável com Interface Gráfica

### Como Gerar o Executável:

```bash
pyinstaller latc_gui.spec
```

O executável será criado em: `dist/LATC_Tool_GUI.exe`

### Como Usar:

1. **Copie o executável** para o diretório `LATC/`
2. **Execute** `LATC_Tool_GUI.exe`
3. A interface gráfica irá abrir automaticamente

## Estrutura de Diretórios Necessária:

```
LATC/
├── LATC_Tool_GUI.exe          # Executável principal
├── data/                      # Diretório de dados (obrigatório)
│   ├── telemetria_consumos_202507281246.csv  # Dados originais
│   └── imputed_consumption_full.csv          # Dados imputados (gerado)
├── latc_simple.py            # Script de imputação
├── serie_horaria_completa.py # Script de visualização
└── comparacao_contadores.py  # Script de comparação
```

## Funcionalidades da Interface:

### 1. ABA PROCESSAMENTO
- **▶ INICIAR PROCESSAMENTO**: Botão único inteligente.
  - Se for a primeira vez: Executa a imputação.
  - Se os dados já existirem: Pergunta se você deseja sobrescrever.
  - *Dica:* Use para gerar dados novos ou re-processar com novos arquivos originais.

### 2. ABA VISUALIZAÇÕES
- **Série Temporal**: Gráfico hora a hora do ano completo
- **Comparação 6 Contadores**: Evolução detalhada com destaque para imputação

### 3. ABA UTILITÁRIOS
- **Resumo dos Dados**: Estatísticas rápidas de arquivo e registros

### 3. Visualizações Interativas (NOVO!)
Agora os gráficos são exibidos **diretamente dentro do aplicativo** na aba "Visualizações".

*   **Série Temporal Integrada**: Gera o gráfico completo sem abrir janelas externas.
*   **Controles Interativos**:
    *   🏠 **Home**: Reseta o zoom.
    *   🔍 **Zoom**: Arraste para ampliar uma área específica.
    *   💾 **Salvar**: Exporta o gráfico atual como PNG.
*   **Comparação de Contadores**: Ainda disponível como janela externa para visualização detalhada multi-janela.

### ✅ Status em Tempo Real
- O aplicativo mostra automaticamente se os arquivos de dados foram encontrados (verde) ou não (vermelho).
- Uma janela de log mostra o progresso da execução dos scripts.

## Notas Importantes:

⚠️ **O executável precisa estar no mesmo diretório que os scripts Python!**
   - Ele funciona como um "lançador" (Launcher) para os scripts.
   - Certifique-se que o Python está instalado no computador.

✅ **Primeira execução**: Vá na aba "Processamento" e clique em "Executar Imputação".

📊 **Visualizações**: Os gráficos serão salvos como imagens PNG na pasta do aplicativo.
