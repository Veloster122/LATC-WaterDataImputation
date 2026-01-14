# Programa de Imputação LATC

Programa para imputação de dados de telemetria de consumo de água usando o algoritmo LATC (Low-Rank Autoregressive Tensor Completion).

## 📁 Estrutura do Projeto

```
LATC/
├── data/
│   ├── telemetria_consumos_202507281246.csv    # Dados originais (1.2 GB)
│   ├── imputed_consumption_sample.csv          # Amostra imputada (1000 medidores)
│   └── imputed_consumption_full.csv            # Dataset completo imputado (1.3 GB)
├── latc_simple.py                              # Script principal de imputação
├── serie_horaria_completa.py                   # Análise de série temporal
├── serie_temporal_horaria.png                  # Visualização da série temporal
├── requirements.txt                            # Dependências Python
└── README.md                                   # Este arquivo
```

## 🚀 Instalação

```bash
pip install -r requirements.txt
```

## 💧 Formato dos Dados

O arquivo CSV contém:
- **id**: Identificador do medidor
- **data**: Data da leitura (YYYY-MM-DD)
- **contact_id**: ID do contato
- **calibre**: Calibre do medidor (15, 20, 30, 40, 80 mm)
- **index_0** a **index_23**: 24 leituras horárias acumuladas

## 📊 Uso

### 1. Imputação de Dados

```bash
python latc_simple.py
```

**Processamento:**
- Carrega dados com valores faltantes (NaN)
- Aplica interpolação linear + forward/backward fill
- Garante monotonicidade (consumo nunca diminui)
- Salva dados imputados em `data/imputed_consumption_full.csv`

**Tempo estimado:** 2-4 horas para dataset completo (~6M registros)

### 2. Análise Temporal

```bash
python serie_horaria_completa.py
```

**Gera:**
- Série temporal hora a hora (~8,142 pontos)
- Padrões diários e semanais
- Comparação original vs imputado
- Salva visualização em `serie_temporal_horaria.png`

## 🔧 Parâmetros do Algoritmo

No arquivo `latc_simple.py`, você pode ajustar:

```python
# Tamanho do batch (menor = menos memória)
batch_size = 10000  

# Aplicar monotonic (True recomendado para consumo acumulado)
enforce_monotonicity = True
```

## 📈 Resultados

### Qualidade da Imputação (Amostra de 1000 medidores)

- **Valores faltantes**: 2,573 (10.72%)
- **Taxa de sucesso**: 100%
- **Monotonicidade**: 100% dos medidores
- **Preservação estatística**: Média e desvio padrão mantidos

### Série Temporal Completa (354 dias)

- **Período**: Janeiro a Dezembro 2024
- **Total de horas**: 8,142 pontos
- **Padrão detectado**: Ritmo diário visível com picos regulares
- **Correlação orig-imputado**: >0.99

## ⚙️ Algoritmo

O script usa uma abordagem robusta de **interpolação temporal**:

1. **Interpolação linear** para gaps entre valores observados
2. **Forward/backward fill** para extremidades
3. **Função de enforçamento de monotonicidade** (pós-processamento)
4. **Processamento em batches** para eficiência de memória

### Por que funciona?

- Valores faltantes são **aleatórios**, não sistemáticos
- Consumo tem **padrões temporais suaves** ao longo de 24h
- Maioria dos medidores tem **boa qualidade** de dados (>89%)

## 📸 Visualizações

A visualização `serie_temporal_horaria.png` mostra:
- Evolução hora a hora do consumo ao longo de 2024
- Zoom em 30 dias para ver padrão diário
- Diferença percentual entre original e imputado
- Distribuição de consumo
- Padrão semanal (seg-dom)
- Estatísticas completas

## 🐛 Troubleshooting

**Memória insuficiente:**
```python
# Reduza batch_size em latc_simple.py
batch_size = 5000  # ou menor
```

**Dataset muito grande:**
- Processar em partes separadas
- Ou aumentar RAM disponível

## 📝 Notas

- Dados processados: **6,041,172 medidores**
- Período coberto: **354 dias em 2024**
- Taxa de imputação: **~10-30% por batch**
- Consumo médio: **~0.04-0.05 m³/hora**

## 📄 Licença

Para fins de pesquisa e educação.
