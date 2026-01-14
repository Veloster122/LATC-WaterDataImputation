import streamlit as st
import pandas as pd
import numpy as np
import os
from pathlib import Path

# ==============================================================================
# CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="LATC",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# ESTILO (Eco Light Theme)
# ==============================================================================
st.markdown("""
<style>
    /* Cores Principais */
    :root {
        --primary-color: #27AE60;
        --secondary-color: #2ECC71;
        --background-color: #F8F9FA;
        --text-color: #2C3E50;
    }
    
    /* Global Background */
    .stApp {
        background-color: var(--background-color);
        color: var(--text-color);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: var(--text-color);
        font-family: 'Segoe UI', sans-serif;
    }
    
    h1 {
        color: var(--primary-color);
        font-weight: 700;
        border-bottom: 2px solid var(--primary-color);
        padding-bottom: 10px;
    }
    
    /* Cards (Container) */
    .css-1r6slb0, .stDataFrame, .stPlotlyChart {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Botões */
    .stButton > button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: var(--secondary-color);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/water-element.png", width=80)
    st.title("LATC")
    st.caption("v7.0 (Web Edition)")
    
    st.markdown("---")
    
    st.header("📂 Arquivos")
    uploaded_file = st.file_uploader("Carregar CSV Original", type=["csv"], help="Selecione o arquivo de telemetria bruto.")
    
    if uploaded_file:
        st.success(f"Arquivo carregado: {uploaded_file.name}")
        # Save to temporary location to work with existing scripts
        save_path = Path("data/web_upload.csv")
        save_path.parent.mkdir(exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.session_state['current_file'] = str(save_path.absolute())
    else:
        # Default fallback
        st.info("Usando arquivo padrão (Demo)")
        st.session_state['current_file'] = str(Path("data/telemetria_consumos_202507281246.csv").absolute())

    st.markdown("---")
    
    page = st.radio("Navegação", ["Dashboard", "Análise de Gaps", "Processamento", "Visualização"])
    
    st.markdown("---")
    st.markdown("© 2026 EcoAnalytics")

# ==============================================================================
# PÁGINAS (TABS)
# ==============================================================================

if page == "Dashboard":
    st.title("📊 Visão Geral do Sistema")
    
    # Load basic stats if file exists
    current_file = st.session_state.get('current_file')
    if current_file and os.path.exists(current_file):
        try:
            df = pd.read_csv(current_file)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Contadores", len(df['id'].unique()))
            with col2:
                rows = len(df)
                st.metric("Total de Registros", f"{rows:,}")
            with col3:
                cols = len(df.columns)
                st.metric("Colunas", cols)
                
            st.subheader("Prévia dos Dados")
            st.dataframe(df.head(50), use_container_width=True)
            
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")
    else:
        st.warning("Nenhum arquivo de dados encontrado. Por favor, faça upload na barra lateral.")

elif page == "Análise de Gaps":
    st.title("🔍 Análise de Falhas (Gaps)")
    
    current_file = st.session_state.get('current_file')
    if not current_file or not os.path.exists(current_file):
        st.warning("⚠️ Nenhum arquivo carregado. Por favor, carregue um CSV na barra lateral.")
    else:
        if st.button("▶ Executar Análise de Gaps", type="primary"):
            with st.spinner("Analisando padrões de falha..."):
                try:
                    import gap_analysis
                    
                    df = pd.read_csv(current_file)
                    value_columns = [col for col in df.columns if col.startswith('index_')]
                    
                    if not value_columns:
                        st.error("Erro: Colunas 'index_*' não encontradas no arquivo.")
                    else:
                        # 1. Analyze
                        stats = gap_analysis.analyze_gaps(df, value_columns)
                        
                        # 2. Generate Heatmap
                        heatmap_path = "data/web_heatmap.png"
                        Path("data").mkdir(exist_ok=True)
                        gap_analysis.generate_gap_heatmap(df, value_columns, output_path=heatmap_path)
                        
                        # Display Results
                        st.success("Análise concluída!")
                        
                        # Heatmap
                        st.subheader("Mapa de Calor de Disponibilidade")
                        st.image(heatmap_path, caption="Vermelho=Falta, Verde=Presente", use_container_width=True)
                        
                        # Metrics Card
                        g_stats = stats['global']
                        kpi1, kpi2, kpi3 = st.columns(3)
                        kpi1.metric("Total de Contadores", g_stats['total_meters'])
                        kpi2.metric("Dados Faltantes (%)", f"{g_stats['missing_pct']:.2f}%")
                        kpi3.metric("Total de Gaps", g_stats['missing_count'])
                        
                        # Detailed Table (limit to avoid 200MB error)
                        # Only convert top meters to avoid huge dataframe
                        meter_stats_list = stats['meter_stats']
                        
                        if len(meter_stats_list) > 1000:
                            # Sort in Python before creating DataFrame
                            sorted_stats = sorted(meter_stats_list, key=lambda x: x['missing_pct'], reverse=True)
                            top_1000 = sorted_stats[:1000]
                            
                            st.subheader("Top 1000 Contadores com Mais Faltas")
                            st.dataframe(pd.DataFrame(top_1000))
                            
                            # Summary stats without creating huge DF
                            with st.expander("📊 Estatísticas Resumidas de Todos os Contadores"):
                                st.write(f"Total de contadores: {len(meter_stats_list):,}")
                                avg_pct = sum(m['missing_pct'] for m in meter_stats_list) / len(meter_stats_list)
                                st.write(f"Média de faltas: {avg_pct:.2f}%")
                        else:
                            meter_df = pd.DataFrame(meter_stats_list)
                            st.subheader("Detalhes por Contador")
                            st.dataframe(meter_df)
                        
                except Exception as e:
                    st.error(f"Erro na análise: {str(e)}")

elif page == "Processamento":
    st.title("⚙️ Processamento de Imputação")
    
    current_file = st.session_state.get('current_file')
    if not current_file or not os.path.exists(current_file):
        st.warning("⚠️ Nenhum arquivo carregado.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.info("### ⚡ Modo Rápido\nInterpolação Linear\n\n*Ideal para pequenos gaps.*")
        with col2:
            st.warning("### 🔬 Modo Científico\nLATC (SVD Matrix Completion)\n\n*Ideal para gaps complexos.*")
            
        mode = st.radio("Selecione o Algoritmo:", ["Rápido", "Científico"], horizontal=True)
        
        # Smoothing Options (Collapsible)
        with st.expander("🌊 Opções de Suavização (Recomendado)", expanded=True):
            st.markdown("**Elimina o efeito 'escada' nos dados imputados**")
            enable_smoothing = st.checkbox("✅ Ativar Suavização", value=False, 
                                          help="Suaviza as transições entre dados reais e imputados para um perfil mais natural")
            
            if enable_smoothing:
                smoothing_method = st.selectbox(
                    "Método de Suavização:",
                    ["savgol", "spline", "moving_avg"],
                    format_func=lambda x: {
                        "savgol": "🔬 Savitzky-Golay (Melhor qualidade)",
                        "spline": "📈 Spline Cúbica (Suave)",
                        "moving_avg": "⚡ Média Móvel (Rápido)"
                    }[x],
                    help="Savitzky-Golay: Filtro polinomial que preserva características. Spline: Interpolação suave. Média Móvel: Simples e rápido."
                )
                
                smoothing_window = st.slider(
                    "Tamanho da Janela de Suavização:",
                    min_value=5, max_value=25, value=11, step=2,
                    help="Janelas maiores = mais suave (mas pode perder detalhes). Recomendado: 9-13"
                )
            else:
                smoothing_method = 'savgol'
                smoothing_window = 11
        
        if st.button("▶ Iniciar Imputação", type="primary"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Callback definition
            def streamlit_progress(pct, msg):
                safe_pct = min(100, max(0, pct))
                progress_bar.progress(safe_pct / 100)
                status_text.text(f"⏳ {msg}")
            
            try:
                status_text.text("📂 Lendo arquivo CSV do disco (isso pode demorar para arquivos grandes)...")
                df = pd.read_csv(current_file)
                
                status_text.text("⚡ Preparando dados...")
                value_columns = [col for col in df.columns if col.startswith('index_')]
                
                if mode == "Rápido":
                    import latc_simple
                    import importlib
                    importlib.reload(latc_simple)
                    imputed = latc_simple.simple_latc_imputation(df, value_columns, progress_callback=streamlit_progress)
                else:
                    import latc_advanced
                    import importlib
                    importlib.reload(latc_advanced)
                    
                    # Normal production mode (verbose=False)
                    imputed = latc_advanced.latc_hybrid_imputation(
                        df, value_columns, 
                        progress_callback=streamlit_progress,
                        apply_smoothing=enable_smoothing,
                        smoothing_method=smoothing_method,
                        smoothing_window=smoothing_window,
                        verbose=False 
                    )
                
                # FORCE SAVE LOCAL COPY FOR USER
                local_backup = Path("data/RESULTADO_FINAL.csv")
                imputed.to_csv(local_backup, index=False)
                status_text.text(f"✅ Salvo na pasta data: {local_backup.name}")
                
                st.success(f"Arquivo salvo também em: {local_backup.absolute()}")
                
                # Save temp for download
                from io import BytesIO
                buffer = BytesIO()
                imputed.to_csv(buffer, index=False)
                
                st.success("Imputação finalizada! Baixe o resultado abaixo:")
                st.download_button(
                    label="⬇️ Baixar CSV Processado",
                    data=buffer.getvalue(),
                    file_name="latc_imputed_web.csv",
                    mime="text/csv"
                )
                
                # Store in session state for viz tab
                st.session_state['imputed_df'] = imputed
                
            except Exception as e:
                st.error(f"Erro no processamento: {str(e)}")
                st.exception(e)
        
        # POST-PROCESSING: Smoothing on Already Imputed Data
        st.markdown("---")
        st.subheader("🌊 Suavização Pós-Processamento")
        st.markdown("Aplique suavização aos dados **já imputados** sem reprocessar tudo. Ideal para testar diferentes parâmetros.")
        
        # Check if we have imputed data
        resultado_final = Path("data/RESULTADO_FINAL.csv")
        if resultado_final.exists() or 'imputed_df' in st.session_state:
            
            col_smooth_1, col_smooth_2 = st.columns([2, 1])
            
            with col_smooth_1:
                st.info("**Dados disponíveis para suavização.** Configure os parâmetros abaixo e clique em 'Aplicar Suavização'.")
            
            with col_smooth_2:
                if resultado_final.exists():
                    file_size = resultado_final.stat().st_size / (1024*1024)
                    st.metric("Arquivo", f"{file_size:.1f} MB")
            
            # Smoothing parameters
            st.markdown("**⚡ Moving Average (único método - otimizado para velocidade)**")
            st.caption("Savitzky-Golay e Spline são muito lentos para 18k+ contadores")
            
            post_smooth_window = st.slider(
                "🪟 Tamanho da Janela:",
                min_value=11, max_value=99, value=25, step=2,
                help="Janela maior = mais suave. Recomendado: 25-49",
                key="post_smooth_window"
            )
            
            post_smooth_method = 'moving_avg'  # Force moving average only
            
            if st.button("🌊 Aplicar Suavização Agora", type="secondary", key="apply_smoothing_btn"):
                with st.spinner("Aplicando suavização..."):
                    try:
                        # Load data
                        if 'imputed_df' in st.session_state:
                            df_to_smooth = st.session_state['imputed_df'].copy()
                        else:
                            df_to_smooth = pd.read_csv(resultado_final)
                        
                        # Get value columns
                        value_columns = [col for col in df_to_smooth.columns if col.startswith('index_')]
                        
                        # CRITICAL: Load original dataset to identify gaps
                        original_file = Path("data/web_upload.csv")
                        if not original_file.exists():
                            original_file = Path("data/telemetria_consumos_202507281246.csv")
                        
                        if not original_file.exists():
                            st.error("❌ Arquivo original não encontrado. Necessário para identificar gaps.")
                            st.stop()
                        
                        st.write("📂 Carregando dataset original para identificar gaps...")
                        df_original = pd.read_csv(original_file)
                        
                        # CRITICAL: Align original data to imputed data
                        # Imputation process might sort or filter rows, so we MUST align by id/data
                        st.write("🔄 Alinhando datasets (ID + Data)...")
                        
                        # Ensure date columns are datetime
                        if 'data' in df_to_smooth.columns:
                            df_to_smooth['data'] = pd.to_datetime(df_to_smooth['data'])
                        if 'data' in df_original.columns:
                            df_original['data'] = pd.to_datetime(df_original['data'])
                            
                        # Prepare original DF - drop duplicates to prevent row explosion
                        # Critical fix for "boolean index did not match indexed array" error
                        if 'id' in df_original.columns and 'data' in df_original.columns:
                            df_original_clean = df_original.drop_duplicates(subset=['id', 'data'])
                        else:
                            df_original_clean = df_original
                            
                        # Create a merged version solely to get the aligned original values
                        # Left join essentially keeps imputed structure and attaches original values
                        df_aligned = pd.merge(
                            df_to_smooth[['id', 'data']], 
                            df_original_clean, 
                            on=['id', 'data'], 
                            how='left',
                            suffixes=('', '_orig')
                        )
                        
                        # Now df_aligned has the same rows/order as df_to_smooth
                        # Use THIS as the original_df source
                        
                        # Sort by ID and Data is CRITICAL for inter-day smoothing
                        st.write("🔄 Ordenando cronologicamente por contador...")
                        df_to_smooth = df_to_smooth.sort_values(by=['id', 'data'])
                        
                        # Re-align original after sorting (simple merge left again or just re-sort aligned)
                        # Let's re-merge to be absolutely safe and correctly ordered
                        df_aligned = pd.merge(
                            df_to_smooth[['id', 'data']], 
                            df_original_clean, 
                            on=['id', 'data'], 
                            how='left',
                            suffixes=('', '_orig')
                        )
                        
                        # Import FAST NUMPY smoothing (Inter-day capable)
                        import sys
                        sys.path.insert(0, str(Path(__file__).parent))
                        from smooth_fast_numpy import smooth_time_series_numpy
                        
                        # Apply CONTINUOUS smoothing
                        st.write(f"🚀 Aplicando suavização contínua (Numpy)...")
                        st.info("💡 Suaviza transições entre dias e gaps, preservando originais.")
                        
                        df_smoothed = smooth_time_series_numpy(
                            df=df_to_smooth,
                            value_columns=value_columns,
                            original_df=df_aligned,
                            window_size=post_smooth_window,
                            verbose=True
                        )
                        
                        # Save
                        output_path = Path("data/RESULTADO_FINAL_SUAVIZADO.csv")
                        df_smoothed.to_csv(output_path, index=False)
                        
                        # Update session
                        st.session_state['imputed_df'] = df_smoothed
                        
                        st.success(f"✅ Suavização aplicada com sucesso!")
                        st.info(f"📁 Salvo em: `{output_path.absolute()}`")
                        
                        # Download button
                        from io import BytesIO
                        buffer = BytesIO()
                        df_smoothed.to_csv(buffer, index=False)
                        
                        st.download_button(
                            label="⬇️ Baixar Dados Suavizados",
                            data=buffer.getvalue(),
                            file_name="latc_suavizado.csv",
                            mime="text/csv",
                            key="download_smoothed"
                        )
                            
                    except Exception as e:
                        st.error(f"❌ Erro ao aplicar suavização: {str(e)}")
                        st.exception(e)
        else:
            st.warning("⚠️ Nenhum dado imputado encontrado. Execute a imputação primeiro.")


elif page == "Visualização":
    st.title("📈 Visualização Interativa")
    
    # FILE SELECTOR: Choose which dataset to visualize
    st.markdown("### 📁 Selecione o Dataset")
    
    # Check available files
    file_options = []
    file_paths = {}
    
    resultado_suavizado = Path("data/RESULTADO_FINAL_SUAVIZADO.csv")
    resultado_final = Path("data/RESULTADO_FINAL.csv")
    resultado_antigo = Path("data/imputed_consumption_full.csv")
    
    if resultado_suavizado.exists():
        file_options.append("🌊 Dados Suavizados (Recomendado)")
        file_paths["🌊 Dados Suavizados (Recomendado)"] = resultado_suavizado
    
    if resultado_final.exists():
        file_options.append("⚙️ Dados Imputados (Original)")
        file_paths["⚙️ Dados Imputados (Original)"] = resultado_final
    
    if resultado_antigo.exists():
        file_options.append("📦 Processamento Antigo")
        file_paths["📦 Processamento Antigo"] = resultado_antigo
    
    # Add session state option if available
    if 'imputed_df' in st.session_state:
        file_options.insert(0, "💾 Dados em Memória (Última Execução)")
    
    df = None
    
    if file_options:
        # Default to smoothed if available, otherwise most recent
        default_idx = 0
        
        selected_file = st.selectbox(
            "Escolha qual versão visualizar:",
            file_options,
            index=default_idx,
            help="Dados Suavizados = resultado da suavização pós-processamento. Dados Imputados = resultado direto da imputação."
        )
        
        # Load selected file
        if selected_file == "💾 Dados em Memória (Última Execução)":
            df = st.session_state['imputed_df']
            st.success("✅ Visualizando dados em memória (última execução).")
        else:
            file_path = file_paths[selected_file]
            with st.spinner(f"Carregando {file_path.name}..."):
                df = pd.read_csv(file_path)
                st.success(f"✅ Carregado: `{file_path.name}` ({file_path.stat().st_size / (1024*1024):.1f} MB)")
    else:
        # No files available
        st.warning("⚠️ Nenhum arquivo de dados encontrado. Execute o processamento primeiro na aba 'Processamento'.")
        
    if df is not None:
        import plotly.graph_objects as go
        import plotly.express as px
        
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Série Temporal", "🔥 Heatmap Global", "🔀 Comparação vs Original", "📈 Perfil Consumo Ano Todo"])
        
        # Identify columns
        value_cols = [c for c in df.columns if c.startswith('index_')]
        id_col = 'id' if 'id' in df.columns else df.columns[0]
        
        with tab1:
            st.markdown("### Perfil de Carga Individual")
            
            # Selector
            meter_ids = df[id_col].astype(str).unique()
            selected_id = st.selectbox("Selecione o Contador:", meter_ids)
            
            # Get data - ALL rows for this meter, not just one day
            mask = df[id_col].astype(str) == selected_id
            if mask.any():
                meter_rows = df[mask].copy()
                
                # Sort by date if available
                if 'data' in meter_rows.columns:
                    meter_rows = meter_rows.sort_values('data')
                
                # Concatenate all hourly values across all days
                all_values = []
                all_timestamps = []
                
                for idx, row in meter_rows.iterrows():
                    daily_values = row[value_cols].values
                    all_values.extend(daily_values)
                    
                    # Generate timestamps for this day
                    if 'data' in row:
                        base_date = pd.to_datetime(row['data'])
                        daily_timestamps = [base_date + pd.Timedelta(hours=h) for h in range(len(value_cols))]
                        all_timestamps.extend(daily_timestamps)
                
                # Use timestamps if available, otherwise just indices
                x_axis = all_timestamps if all_timestamps else list(range(len(all_values)))
                
                # Plot cumulative readings (as requested by user)
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=x_axis,
                    y=all_values, 
                    mode='lines', 
                    name='Leitura Acumulada (m³)',
                    line=dict(color='#27AE60', width=1.5),
                    fill='tozeroy',
                    fillcolor='rgba(39, 174, 96, 0.1)'
                ))
                
                fig.update_layout(
                    title=f"Série Temporal - Contador: {selected_id} ({len(all_values):,} pontos)",
                    xaxis_title="Data e Hora",
                    yaxis_title="Leitura Acumulada (m³)",
                    template="plotly_white",
                    height=600,
                    hovermode="x unified"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Stats
                st.markdown("#### Estatísticas da Série")
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Média", f"{np.mean(all_values):.2f} m³")
                c2.metric("Máximo", f"{np.max(all_values):.2f} m³")
                c3.metric("Mínimo", f"{np.min(all_values):.2f} m³")
                c4.metric("Desvio Padrão", f"{np.std(all_values):.2f} m³")
                
        with tab2:
            st.markdown("### Visão Geral da Rede (Heatmap)")
            st.markdown("*Eixo Y: Contadores | Eixo X: Tempo | Cor: Volume (m³)*")
            
            if len(df) > 100:
                st.info(f"Visualizando os primeiros 100 contadores (de {len(df)}) para performance.")
                plot_matrix = df[value_cols].iloc[:100].values
            else:
                plot_matrix = df[value_cols].values
                
            fig = px.imshow(
                plot_matrix,
                labels=dict(x="Tempo", y="Contador Index", color="m³"),
                aspect="auto",
                color_continuous_scale="Viridis"
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            st.markdown("### 🔀 Comparação: Original (com gaps) vs Imputado")
            
            # Try to load original file
            original_file = Path("data/web_upload.csv")
            if not original_file.exists():
                original_file = Path("data/telemetria_consumos_202507281246.csv")
            
            if original_file.exists():
                with st.spinner("Carregando dados originais..."):
                    df_original = pd.read_csv(original_file)
                
                # Selector
                meter_ids_comp = df[id_col].astype(str).unique()
                selected_id_comp = st.selectbox("Selecione o Contador para Comparar:", meter_ids_comp, key="comp_selector")
                
                # Get both versions - ALL rows
                mask_imp = df[id_col].astype(str) == selected_id_comp
                mask_orig = df_original[id_col].astype(str) == selected_id_comp
                
                if mask_imp.any() and mask_orig.any():
                    # Prepare Imputed Data (Full Year)
                    rows_imp = df[mask_imp].copy()
                    if 'data' in rows_imp.columns:
                        rows_imp = rows_imp.sort_values('data')
                    
                    all_imputed = []
                    all_timestamps = []
                    
                    for _, row in rows_imp.iterrows():
                        all_imputed.extend(row[value_cols].values)
                        if 'data' in row:
                            base = pd.to_datetime(row['data'])
                            # Fixed: use list comprehension correctly
                            ts = [base + pd.Timedelta(hours=h) for h in range(len(value_cols))]
                            all_timestamps.extend(ts)
                    
                    # Prepare Original Data (Full Year)
                    rows_orig = df_original[mask_orig].copy()
                    if 'data' in rows_orig.columns:
                        rows_orig = rows_orig.sort_values('data')
                        
                    all_original = []
                    for _, row in rows_orig.iterrows():
                        all_original.extend(row[value_cols].values)
                    
                    # X Axis
                    x_axis = all_timestamps if all_timestamps else list(range(len(all_imputed)))
                    
                    # Create comparison plot
                    fig_comp = go.Figure()
                    
                    # Convert to numpy for easier masking
                    arr_imputed = np.array(all_imputed)
                    arr_original = np.array(all_original)
                    arr_x = np.array(x_axis)
                    
                    # 1. Imputed Line (Background - Green)
                    fig_comp.add_trace(go.Scatter(
                        x=x_axis,
                        y=all_imputed,
                        mode='lines',
                        name='Imputado (Linha)',
                        line=dict(color='#27AE60', width=2, dash='solid'),
                        opacity=0.5
                    ))
                    
                    # 2. Imputed Points (Green Dots) - Where Original is NaN
                    # Find indices where original is NaN but inputed has value
                    # Note: all_original might have fewer rows if gaps were dropped, but here we iterated same logic.
                    # Wait, logic above constructs all_original by iterating rows. If rows are missing, lists are different lengths?
                    # No, logic in lines 417-437 iterates rows. If timestamps align, we can compare.
                    # Assuming strict alignment based on 'data' sort.
                    
                    if len(all_original) == len(all_imputed):
                         mask_imputed = np.isnan(arr_original) & ~np.isnan(arr_imputed)
                         if mask_imputed.any():
                             fig_comp.add_trace(go.Scatter(
                                 x=arr_x[mask_imputed],
                                 y=arr_imputed[mask_imputed],
                                 mode='markers',
                                 name='Pontos Imputados',
                                 marker=dict(color='#27AE60', size=6, symbol='circle'),
                                 opacity=1.0
                             ))
                    
                    # 3. Original Line (Foreground - Blue) - ON TOP
                    fig_comp.add_trace(go.Scatter(
                        x=x_axis,
                        y=all_original,
                        mode='lines',
                        name='Original (Real)',
                        line=dict(color='#3498DB', width=2),
                        opacity=1.0
                    ))
                    
                    fig_comp.update_layout(
                        title=f"Comparação - Contador: {selected_id_comp}",
                        xaxis_title="Data e Hora",
                        yaxis_title="Leitura (m³)",
                        template="plotly_white",
                        height=600,
                        hovermode="x unified",
                        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
                    )
                    
                    st.plotly_chart(fig_comp, use_container_width=True)
                    

                    
                    # Gap Statistics for this meter (Full Year)
                    st.markdown("#### 📊 Estatísticas de Imputação (Período Completo)")
                    
                    # Convert to numeric array to safely use np.isnan
                    try:
                        original_numeric = pd.to_numeric(all_original, errors='coerce')
                        gaps_filled = int(np.sum(np.isnan(original_numeric)))
                        total_points = len(all_original)
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Pontos Imputados", gaps_filled)
                        col2.metric("% Imputado", f"{100*gaps_filled/total_points:.2f}%")
                        col3.metric("Total de Pontos", total_points)
                    except Exception as e:
                        st.warning(f"Não foi possível calcular estatísticas: {e}")
                    
                else:
                    st.warning("Contador não encontrado em ambos os datasets.")
            else:
                st.warning("⚠️ Arquivo original não encontrado. Certifique-se de que o arquivo está em `data/web_upload.csv` ou `data/telemetria_consumos_202507281246.csv`.")
        
        with tab4:
            st.markdown("### 📈 Perfil de Consumo Horário (Ano Completo)")
            st.markdown("Visualização do **Consumo Horário (Diferenças)** ao longo de todo o período (Janeiro a Dezembro).")
            # st.markdown("_Consumo[t] = Leitura[t] - Leitura[t-1]_")
            
            # Single Selector for Comparison
            all_ids_str = df[id_col].astype(str).unique()
            
            # Default to current selected in tab1
            default_index = 0
            if 'selected_id' in locals() and selected_id in all_ids_str:
                default_index = list(all_ids_str).index(selected_id)
            
            selected_profile_id = st.selectbox(
                "Selecione um Contador para Comparar Consumo (Imputado vs Original):",
                all_ids_str,
                index=default_index,
                key="select_tab4"
            )
            
            if selected_profile_id:
                fig_avg = go.Figure()
                
                # 1. Get Imputed Series
                meter_rows = df[df[id_col].astype(str) == selected_profile_id]
                
                if not meter_rows.empty:
                    # Construct full time series (Imputed)
                    if 'data' in meter_rows.columns:
                        meter_rows = meter_rows.sort_values('data')
                        
                    vals_imp = []
                    ts_imp = []
                    for _, row in meter_rows.iterrows():
                        vals_imp.extend(row[value_cols].values)
                        if 'data' in row:
                            base = pd.to_datetime(row['data'])
                            ts_imp.extend([base + pd.Timedelta(hours=h) for h in range(len(value_cols))])
                    
                    # Calculate Consumption (Diff) - Imputed
                    vals_arr_imp = np.array(vals_imp, dtype=float)
                    consumption_imp = np.diff(vals_arr_imp, prepend=vals_arr_imp[0])
                    consumption_imp[consumption_imp < 0] = 0 # Clean resets
                    
                    # 2. Get Original Series (if available)
                    consumption_orig = None
                    ts_orig = None
                    
                    # Try to load original file (reuse logic from tab3 if loaded globally, but let's be safe)
                    original_file_path = Path("data/web_upload.csv")
                    if not original_file_path.exists():
                        original_file_path = Path("data/telemetria_consumos_202507281246.csv")
                    
                    if original_file_path.exists():
                         # We need to read it efficiently. 
                         # Assuming it's already read in tab3 context? 
                         # Actually, st.session_state is best, but let's re-read or use df_original if available in scope
                         # df_original is defined inside tab3 block... scope issue?
                         # Let's re-read to be safe (cached by st.cache_data if we used it, but we didn't). 
                         # For performance, we should have loaded it once.
                         # Quick fix: Re-read (Streamlit caches file IO a bit)
                         try:
                             df_orig_temp = pd.read_csv(original_file_path)
                             mask_orig = df_orig_temp[id_col].astype(str) == selected_profile_id
                             rows_orig = df_orig_temp[mask_orig].copy()
                             
                             if not rows_orig.empty:
                                 if 'data' in rows_orig.columns:
                                     rows_orig = rows_orig.sort_values('data')
                                 
                                 vals_orig = []
                                 ts_orig = []
                                 for _, row in rows_orig.iterrows():
                                     vals_orig.extend(row[value_cols].values) # Contains NaNs
                                     if 'data' in row:
                                        base = pd.to_datetime(row['data'])
                                        ts_orig.extend([base + pd.Timedelta(hours=h) for h in range(len(value_cols))])
                                        
                                 # Calculate Consumption (Diff) - Original
                                 vals_arr_orig = np.array(vals_orig, dtype=float)
                                 # Diff propagates NaNs. If t-1 is NaN, t is NaN.
                                 consumption_orig = np.diff(vals_arr_orig, prepend=vals_arr_orig[0])
                                 consumption_orig[consumption_orig < 0] = 0
                                 
                         except:
                             pass

                    # Plot Imputed (Active line)
                    fig_avg.add_trace(go.Scatter(
                        x=ts_imp if ts_imp else list(range(len(consumption_imp))),
                        y=consumption_imp,
                        mode='lines',
                        name='Imputado (Calculado)',
                        line=dict(color='#27AE60', width=1.5),
                        opacity=0.8
                    ))
                    
                    # Plot Original (Comparison)
                    if consumption_orig is not None:
                         fig_avg.add_trace(go.Scatter(
                            x=ts_orig if ts_orig else list(range(len(consumption_orig))),
                            y=consumption_orig,
                            mode='lines',
                            name='Original (Calculado)',
                            line=dict(color='#3498DB', width=1.5),
                            opacity=0.8
                        ))
                
                fig_avg.update_layout(
                    title="Consumo Horário Calculado (Diferenças)",
                    xaxis_title="Data e Hora",
                    yaxis_title="Consumo (m³/h)",
                    template="plotly_white",
                    height=500,
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig_avg, use_container_width=True)
                
                st.info("💡 Este gráfico calcula o consumo real (Diferença entre leituras consecutivas) para cada hora do ano. Ideal para visualizar picos de uso e padrões sazonais.")
            
    else:
        st.info("ℹ️ Para visualizar, processe os dados na aba 'Processamento' ou carregue um arquivo existente.")

