
"""
LATC Imputation Tool - GUI v3.0
Interface Gráfica Integrada com Matplotlib
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import sys
import os
import subprocess
import threading
from pathlib import Path
from datetime import datetime

# ==============================================================================
# IMPORTAÇÕES MATPLOTLIB PARA GUI
# ==============================================================================
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

class LATCApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LATC EcoAnalytics v5.0")
        self.root.geometry("1100x800")
        self.root.configure(bg="#F8F9FA")
        
        # Tema Visual "Eco Light" - Paleta
        self.colors = {
            "bg": "#F8F9FA",         # Fundo Geral (Cinza muito claro)
            "card": "#FFFFFF",       # Fundo de Painéis (Branco)
            "primary": "#27AE60",    # Verde Eco (Botões de Ação)
            "secondary": "#16A085",  # Verde Azulado (Teal)
            "accent": "#2980B9",     # Azul (Links/Neutro)
            "text": "#2C3E50",       # Texto Escuro (Quase preto)
            "text_light": "#7F8C8D"  # Texto Secundário (Cinza)
        }
        
        self.setup_styles()
        
        # Variáveis
        self.original_file_path = tk.StringVar(value="data/telemetria_consumos_202507281246.csv")
        self.has_orig = False
        self.has_imp = False
        
        self.current_figure_canvas = None
        
        self.setup_ui()
        self.check_files()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam') # Base limpa
        
        # Configurar Cores Globais
        style.configure(".", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 10))
        
        # TFrame (Cards)
        style.configure("Card.TFrame", background=self.colors["card"], relief="flat")
        
        # TButton (Primary - Eco)
        style.configure("Primary.TButton", 
                        background=self.colors["primary"], foreground="white",
                        font=("Segoe UI", 10, "bold"), borderwidth=0, focuscolor="none")
        style.map("Primary.TButton", background=[("active", "#2ecc71")]) # Hover mais claro
        
        # TButton (Secondary - Blue)
        style.configure("Secondary.TButton", 
                        background=self.colors["accent"], foreground="white",
                        font=("Segoe UI", 10), borderwidth=0, focuscolor="none")
        style.map("Secondary.TButton", background=[("active", "#3498db")])

        # TNotebook (Abas Limpas)
        style.configure("TNotebook", background=self.colors["bg"], tabposition="n", borderwidth=0)
        style.configure("TNotebook.Tab", background=self.colors["bg"], foreground=self.colors["text_light"],
                       font=("Segoe UI", 11), padding=[20, 10], borderwidth=0)
        style.map("TNotebook.Tab", background=[("selected", self.colors["card"])], 
                 foreground=[("selected", self.colors["primary"])])

    def setup_ui(self):
        # Header "Eco Clean"
        header = tk.Frame(self.root, bg="white", height=70)
        header.pack(fill="x", side="top")
        
        # Linha de destaque verde no topo
        tk.Frame(header, bg=self.colors["primary"], height=4).pack(fill="x", side="top")
        
        tk.Label(header, text="💧 LATC Water Analytics", font=("Segoe UI", 22, "bold"), 
                 bg="white", fg=self.colors["primary"]).pack(side="left", padx=25, pady=10)
        
        # Status Badge no Header
        self.header_status = tk.Label(header, text="Sistema Pronto", font=("Segoe UI", 9), 
                                    bg="#e8f8f5", fg=self.colors["secondary"], padx=10, pady=4, relief="flat")
        self.header_status.pack(side="right", padx=25, pady=15)
        
        # Seleção de Arquivo (Estilo Card)
        file_frame = ttk.Frame(self.root, style="Card.TFrame", padding=15)
        file_frame.pack(fill="x", padx=20, pady=15)
        
        tk.Label(file_frame, text="Arquivo de Entrada:", bg="white", font=("Segoe UI", 10, "bold"), fg=self.colors["text"]).pack(side="left")
        self.entry_file = tk.Entry(file_frame, textvariable=self.original_file_path, width=60, 
                                 font=("Consolas", 10), relief="flat", bg="#F0F2F5")
        self.entry_file.pack(side="left", padx=15, ipady=4)
        
        ttk.Button(file_frame, text="📂 Selecionar...", style="Secondary.TButton", 
                  command=self.select_file, cursor="hand2").pack(side="left")
        
        # Status Indicators (Redesigned)
        status_frame = tk.Frame(self.root, bg=self.colors["bg"], padx=20)
        status_frame.pack(fill="x")
        
        self.lbl_orig = tk.Label(status_frame, text="● Original Faltando", fg="#e74c3c", bg=self.colors["bg"], font=("Segoe UI", 9, "bold"))
        self.lbl_orig.pack(side="left", padx=(5, 15))
        
        self.lbl_imp = tk.Label(status_frame, text="● Imputado Pendente", fg="#f39c12", bg=self.colors["bg"], font=("Segoe UI", 9, "bold"))
        self.lbl_imp.pack(side="left")

        # Abas
        # Estilo já configurado em setup_styles
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Frames das Abas (BG igual ao root)
        self.tab_process = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.tab_visual = tk.Frame(self.notebook, bg=self.colors["bg"])
        self.tab_utils = tk.Frame(self.notebook, bg=self.colors["bg"])
        
        self.notebook.add(self.tab_process, text="Processamento")
        self.notebook.add(self.tab_visual, text="Visualizações")
        self.notebook.add(self.tab_utils, text="Utilitários")
        
        self.setup_process_tab()
        self.setup_visual_tab()
        self.setup_utils_tab()
        
        # Log Panel (Cleaner)
        log_frame = tk.Frame(self.root, height=120, bg="#2d3436")
        log_frame.pack(fill="x", side="bottom")
        self.log_text = scrolledtext.ScrolledText(log_frame, bg="#2c3e50", fg="#ecf0f1", 
                                                font=("Consolas", 10), height=6, relief="flat")
        self.log_text.pack(fill="both", expand=True, padx=20, pady=10)
        
    def setup_process_tab(self):
        # Card style frame
        frame = ttk.Frame(self.tab_process, style="Card.TFrame", padding=30)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Título e Descrição
        tk.Label(frame, text="Processamento de Dados", 
                 font=("Segoe UI", 16, "bold"), bg="white", fg=self.colors["text"]).pack(anchor="w", pady=(0, 10))
        
        desc = ("Este processo irá:\n"
                "1. Ler o arquivo original selecionado e analisar falhas\n"
                "2. Preencher valores faltantes usando algoritmo LATC (Híbrido)\n"
                "3. Ignorar dias completamente vazios para evitar ruído\n"
                "4. Gerar relatório de saúde dos contadores")
                
        tk.Label(frame, text=desc, bg="white", justify="left", font=("Segoe UI", 11), fg="#555").pack(anchor="w", pady=10)
        tk.Label(frame, text="🕑 Tempo estimado: 30-60 seg (Otimizado)", fg="#e67e22", bg="white", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=25)
        
        # Gap Analysis Section
        gap_frame = tk.Frame(frame, bg="white")
        gap_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(gap_frame, text="1️⃣ Primeiro, analise os gaps no dataset:", bg="white", 
                 font=("Segoe UI", 11, "bold"), fg=self.colors["text"]).pack(anchor="w", pady=(0, 10))
        
        ttk.Button(gap_frame, text="📊 Analisar Gaps", style="Secondary.TButton",
                  command=self.run_gap_analysis).pack(anchor="w", ipady=5)
        
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=20)
        
        # Mode Selection
        mode_frame = tk.Frame(frame, bg="white")
        mode_frame.pack(fill="x", pady=(0, 20))
        
        tk.Label(mode_frame, text="2️⃣ Escolha o modo de processamento:", bg="white",
                 font=("Segoe UI", 11, "bold"), fg=self.colors["text"]).pack(anchor="w", pady=(0, 10))
        
        self.processing_mode = tk.StringVar(value="fast")
        
        rb_fast = tk.Radiobutton(mode_frame, text="⚡ Rápido (Interpolação Linear) - Segundos",
                                variable=self.processing_mode, value="fast", bg="white",
                                font=("Segoe UI", 10), fg="#2C3E50")
        rb_fast.pack(anchor="w", pady=5)
        
        rb_sci = tk.Radiobutton(mode_frame, text="🔬 Científico (LATC SVD) - Minutos/Horas",
                               variable=self.processing_mode, value="scientific", bg="white",
                               font=("Segoe UI", 10), fg="#2C3E50")
        rb_sci.pack(anchor="w", pady=5)
        
        tk.Label(mode_frame, text="💡 Recomendação: Use Rápido para datasets com poucos gaps grandes.",
                fg="#7F8C8D", bg="white", font=("Segoe UI", 9, "italic")).pack(anchor="w", pady=(5, 0))
        
        ttk.Separator(frame, orient='horizontal').pack(fill='x', pady=20)
        
        tk.Label(frame, text="3️⃣ Inicie o processamento:", bg="white",
                 font=("Segoe UI", 11, "bold"), fg=self.colors["text"]).pack(anchor="w", pady=(0, 15))
        
        self.btn_process = ttk.Button(frame, text="▶ INICIAR PROCESSAMENTO", style="Primary.TButton",
                                      command=self.run_imputation_logic, cursor="hand2")
        self.btn_process.pack(anchor="center", ipadx=20, ipady=10)
        
        # Local status label removed in favor of global one
        self.progress_bar = ttk.Progressbar(frame, mode='determinate', length=400)
        self.progress_bar.pack(anchor="center", pady=(10, 5))
        self.progress_bar['value'] = 0
        
        self.lbl_status_process = tk.Label(frame, text="Sistema pronto para processar.", bg="white", fg="#95a5a6", font=("Segoe UI", 10))
        self.lbl_status_process.pack(anchor="center", pady=(0, 15))


    def run_gap_analysis(self):
        """Run gap analysis on dataset"""
        orig_path = self.original_file_path.get()
        if not os.path.exists(orig_path):
            messagebox.showerror("Erro", "Arquivo original não encontrado!")
            return
        
        self.log("Iniciando análise de gaps...", "GAP")
        self.run_script("gap_analysis.py", "GAP_ANALYSIS")
        
        # After analysis, offer to open report
        def check_report():
            report_path = Path("data/gap_report.md")
            if report_path.exists():
                if messagebox.askyesno("Relatório Gerado", "Deseja visualizar o relatório de gaps?"):
                    os.startfile(str(report_path.absolute()))
        
        self.root.after(5000, check_report)  # Check after 5 seconds
    
    def run_imputation_logic(self):
        orig_path = self.original_file_path.get()
        if not os.path.exists(orig_path):
            messagebox.showerror("Erro", "Arquivo original não encontrado!")
            return

        out_path = Path("data/imputed_consumption_full.csv")
        if out_path.exists():
            if not messagebox.askyesno("Confirmar", "Arquivo já existe. Sobrescrever?"): return
        
        # Get selected mode
        mode = self.processing_mode.get()
        
        if mode == "fast":
            self.lbl_status_process.config(text="Executando (Modo Rápido)...", fg="#27ae60")
            self.log("Processando com Interpolação Linear...", "PROCESS")
            self.run_script("latc_simple.py", "PROCESSAR")
        else:  # scientific
            self.lbl_status_process.config(text="Executando (Modo Científico - Aguarde)...", fg="#e74c3c")
            self.log("Processando com LATC Científico (SVD)...", "PROCESS")
            self.log("⚠️ Isto pode levar vários minutos!", "WARN")
            self.run_script("latc_advanced.py", "PROCESSAR")
        
        # Start progress monitoring
        self.progress_bar['value'] = 0
        self.monitor_progress()
    
    def monitor_progress(self):
        """Monitor progress.json and update progress bar"""
        self.progress_bar['value'] = 0
        
        # Determine shared path (ensure directory exists)
        base = Path(os.getcwd())
        p_path = base / "data" / "progress.json"
        
        # If in temp dir (frozen), try to find where we should write? 
        # Actually simplest is just use CWD/data/progress.json if CWD is correct
        # But if GUI changes CWD...
        # Let's use a temp location for progress that is guaranteed writable and shared
        import tempfile
        self.current_progress_file = Path(tempfile.gettempdir()) / "latc_progress.json"
        
        if self.current_progress_file.exists():
            try: self.current_progress_file.unlink()
            except: pass
            
        self._check_progress()
    
    def _check_progress(self):
        """Check progress file and update GUI"""
        import json
        from pathlib import Path
        
        if not hasattr(self, 'current_progress_file'):
            self.current_progress_file = Path("data/progress.json")
            
        progress_file = self.current_progress_file
        
        if progress_file.exists():
            try:
                with open(progress_file, 'r') as f:
                    data = json.load(f)
                
                # Update progress bar
                self.progress_bar['value'] = data.get('percent', 0)
                
                # Update status label
                message = data.get('message', '')
                self.lbl_status_process.config(text=message, fg="#27ae60")
                
                # Continue monitoring if not complete
                if data.get('percent', 0) < 100:
                    self.root.after(500, self._check_progress)  # Check every 500ms
                else:
                    self.lbl_status_process.config(text="✅ Processamento concluído!", fg="#27ae60")
                    # Clean up is done by tracker or we can leave it
            except:
                # Continue monitoring on error
                self.root.after(500, self._check_progress)
        else:
            # File doesn't exist yet, keep checking
            self.root.after(500, self._check_progress)

    def setup_visual_tab(self):
        # Layout dividido: Menu Esquerdo | Chart Direito
        container = tk.Frame(self.tab_visual, bg=self.colors["bg"])
        container.pack(fill="both", expand=True)
        
        # Menu (Sidebar Card)
        menu_frame = ttk.Frame(container, style="Card.TFrame", padding=15)
        menu_frame.pack(side="left", fill="y", padx=10, pady=10)
        
        tk.Label(menu_frame, text="📊 Visualizações", font=("Segoe UI", 12, "bold"), 
                 bg="white", fg=self.colors["text"]).pack(anchor="w", pady=(0, 15))
        
        
        # Botões de Gráfico (Estilo Clean)
        ttk.Button(menu_frame, text="Série Temporal (Geral)", style="Primary.TButton",
                  command=self.plot_integrated_time_series).pack(fill="x", pady=5, ipady=5)
                  
        ttk.Button(menu_frame, text="Comparação Contadores", style="Secondary.TButton",
                  command=self.plot_integrated_comparison).pack(fill="x", pady=5, ipady=5)

        # Instruções
        info_frame = tk.Frame(menu_frame, bg="#e8f6f3", padx=10, pady=10)
        info_frame.pack(side="bottom", fill="x", pady=10)
        tk.Label(info_frame, text="Dica:", font=("Segoe UI", 8, "bold"), bg="#e8f6f3", fg=self.colors["secondary"]).pack(anchor="w")
        tk.Label(info_frame, text="Use a barra de ferramentas\nabaixo do gráfico para\nZoom e Salvar imagem.", 
                fg="#555", bg="#e8f6f3", font=("Segoe UI", 8), justify="left").pack(anchor="w")

        # Matplotlib Area (Card)
        self.plot_frame = ttk.Frame(container, style="Card.TFrame")
        self.plot_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        self.lbl_plot_placeholder = tk.Label(self.plot_frame, text="Selecione uma visualização ao lado",
                                           font=("Segoe UI", 16), fg="#bdc3c7", bg="white")
        self.lbl_plot_placeholder.pack(expand=True)

    def plot_integrated_time_series(self):
        """Gera gráfico embedded com toolbar de visualização"""
        self._generic_plot_worker(
            "Série Temporal", 
            "serie_horaria_completa", 
            lambda mod, f: mod.get_data_arrays(f),
            lambda mod, d: mod.create_figure(*d, view_mode='dashboard'), # dashboard mode is fast
            has_view_controls=True
        )

    def plot_integrated_comparison(self):
        """Gera gráfico de comparação embedded"""
        self._generic_plot_worker(
            "Comparação Contadores", 
            "comparacao_contadores", 
            lambda mod, f: mod.get_comparison_data(f),
            lambda mod, d: mod.create_figure(d),
            has_view_controls=False
        )

    def _generic_plot_worker(self, label, module_name, data_func, fig_func, has_view_controls=False):
        file_path = self.original_file_path.get()
        if not os.path.exists(file_path):
            messagebox.showwarning("Aviso", "Arquivo original inválido!")
            return
            
        for widget in self.plot_frame.winfo_children(): widget.destroy()
        
        # Frame de Controles (Topo)
        self.view_frame = tk.Frame(self.plot_frame, bg="white")
        self.view_frame.pack(side="top", fill="x", padx=5, pady=2)
        
        # Se for Série Temporal, montar botoes de view
        self.current_plot_module = None
        self.cached_data = None
        
        if has_view_controls:
            self._mk_view_toolbar(self.view_frame)

        # Container do Canvas
        self.canvas_container = tk.Frame(self.plot_frame, bg="white")
        self.canvas_container.pack(side="top", fill="both", expand=True)

        tk.Label(self.canvas_container, text=f"⏳ Gerando {label}...", font=("Segoe UI", 12), bg="white").pack(expand=True)
        self.root.update()
        
        def _worker():
            try:
                self.log(f"Iniciando plot: {label}", "PLOT")
                import importlib
                mod = importlib.import_module(module_name)
                importlib.reload(mod)
                
                # Salvar referencia para callbacks
                self.current_plot_module = mod
                
                data = data_func(mod, file_path)
                if data is None: raise Exception("Dados não retornados")
                
                # CACHE DOS DADOS PARA RE-RENDERIZAR RÁPIDO
                self.cached_data = data
                
                fig = fig_func(mod, data)
                if fig is None: raise Exception("Figura não gerada")
                
                self.root.after(0, lambda: self._display_figure(fig, self.canvas_container))
                self.root.after(0, lambda: self.log(f"[OK] {label} gerado.", "SUCCESS"))
            except Exception as e:
                self.root.after(0, lambda: self._show_plot_error(str(e)))
        
        threading.Thread(target=_worker, daemon=True).start()

    def _mk_view_toolbar(self, parent):
        """Cria botões de troca de visualização"""
        tk.Label(parent, text="Visualização:", bg="white", font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        
        modes = [
            ("📊 Dashboard", "dashboard", "#3498db"),
            ("📈 Série Completa (100%)", "full", "#2ecc71"),
            ("🔍 Zoom Detalhado", "zoom", "#9b59b6"),
            ("📉 Análise Diferença", "diff", "#e74c3c"),
            ("📋 Estatísticas", "stats", "#34495e")
        ]
        
        for text, mode, color in modes:
            tk.Button(parent, text=text, bg=color, fg="white", font=("Segoe UI", 8),
                     command=lambda m=mode: self.update_plot_view(m)).pack(side="left", padx=2)

    def update_plot_view(self, view_mode):
        """Re-renderiza o gráfico usando o cache e o novo modo"""
        if not self.cached_data or not self.current_plot_module:
            return
            
        # Limpar apenas o container do canvas
        for widget in self.canvas_container.winfo_children(): widget.destroy()
        tk.Label(self.canvas_container, text=f"Renderizando: {view_mode}...", bg="white").pack(expand=True)
        self.root.update()
        
        def _redraw():
            try:
                # Chama create_figure com o novo view_mode
                fig = self.current_plot_module.create_figure(*self.cached_data, view_mode=view_mode)
                self.root.after(0, lambda: self._display_figure(fig, self.canvas_container))
                self.root.after(0, lambda: self.log(f"Visualização alterada: {view_mode}", "VIEW"))
            except Exception as e:
                self.root.after(0, lambda: self._show_plot_error(str(e)))
                
        # Thread rápida (renderização MPL ainda pode demorar 1-2s se for FULL)
        threading.Thread(target=_redraw, daemon=True).start()

    def _display_figure(self, fig, container):
        for widget in container.winfo_children(): widget.destroy()
        
        canvas = FigureCanvasTkAgg(fig, master=container)
        canvas.draw()
        
        toolbar = NavigationToolbar2Tk(canvas, container)
        toolbar.update()
        
        canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

    def _show_plot_error(self, error_msg):
        self.log(f"[ERROR] Plot failed: {error_msg}", "ERROR")
        for widget in self.plot_frame.winfo_children(): widget.destroy()
        tk.Label(self.plot_frame, text=f"Erro ao gerar gráfico:\n{error_msg}", fg="red").pack(expand=True)

    def setup_utils_tab(self):
        frame = tk.Frame(self.tab_utils, bg="#ffffff", padx=20, pady=20)
        frame.pack(fill="both", expand=True)
        tk.Label(frame, text="Utilitários", font=("Segoe UI", 14, "bold"), bg="white").pack(anchor="w")
        tk.Button(frame, text="Investigar Contador H19U", bg="#e67e22", fg="white",
                 command=lambda: self.run_script("investigar_h19u.py")).pack(anchor="w", pady=10)

    # Métodos Auxiliares
    def select_file(self):
        f = filedialog.askopenfilename(filetypes=[("CSV", "*.csv"), ("All", "*.*")])
        if f:
            self.original_file_path.set(f)
            self.check_files()

    def check_files(self):
        orig = Path(self.original_file_path.get())
        imp = Path("data/imputed_consumption_full.csv")
        
        if orig.exists(): self.lbl_orig.config(text="[OK] Original OK", fg="green"); self.has_orig=True
        else: self.lbl_orig.config(text="[X] Original Faltando", fg="red"); self.has_orig=False
        
        if imp.exists(): self.lbl_imp.config(text="[OK] Imputado OK", fg="green"); self.has_imp=True
        else: self.lbl_imp.config(text="[!] Imputado Pendente", fg="orange"); self.has_imp=False

    def log(self, msg, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{ts}] [{level}] {msg}\n")
        self.log_text.see(tk.END)

    def get_base_path(self):
        if getattr(sys, 'frozen', False): return Path(sys.executable).parent
        else: return Path(__file__).resolve().parent

    def run_script(self, script_name, label=None):
        label = label or script_name
        base = self.get_base_path()
        script_path = base / script_name
        if not script_path.exists(): script_path = Path(script_name).resolve()
        
        if not script_path.exists():
            messagebox.showerror("Erro", f"Script não encontrado: {script_name}")
            return
            
        file_p = self.original_file_path.get()
        self.log(f"Iniciando: {label}...", "EXEC")
        
        # Setup environment with progress path and unbuffered python
        env = os.environ.copy()
        if hasattr(self, 'current_progress_file'):
            env['LATC_PROGRESS_FILE'] = str(self.current_progress_file.absolute())
            self.log(f"Progress File: {self.current_progress_file.name}", "DEBUG")
        
        # Force unbuffered stdout
        env['PYTHONUNBUFFERED'] = '1'
        
        def task():
            try:
                cmd = sys.executable
                cwd = script_path.parent
                
                # Using -u flag explicit + env var
                proc = subprocess.Popen([cmd, '-u', str(script_path), file_p],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=str(cwd),
                    env=env,
                    bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
                
                for line in iter(proc.stdout.readline, ''):
                    if line: self.root.after(0, lambda l=line.strip(): self.log(l, "OUT"))
                proc.stdout.close()
                if proc.wait() == 0: self.root.after(0, lambda: self.log(f"[OK] {label} done", "SUCCESS"))
                else: self.root.after(0, lambda: self.log(f"[ERROR] Failed", "ERROR"))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"CRITICAL: {e}", "CRITICAL"))
        threading.Thread(target=task, daemon=True).start()

if __name__ == "__main__":
    # Headless runner logic for PyInstaller
    if len(sys.argv) > 1 and not sys.argv[1].startswith('-'):
        script = sys.argv[1]
        if script.endswith('.py'):
            try:
                import runpy
                sys.argv = sys.argv[1:]
                runpy.run_path(script, run_name="__main__")
                sys.exit(0)
            except Exception as e:
                print(f"Error running internal script: {e}")
                sys.exit(1)

    try:
        root = tk.Tk()
        app = LATCApp(root)
        root.mainloop()
    except Exception as e:
        print(f"FATAL: {e}")
