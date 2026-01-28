"""
Script de diagnóstico para verificar utilização de CPU durante processamento
"""
import psutil
import time
import threading

class CPUMonitor:
    def __init__(self):
        self.running = False
        self.cpu_history = []
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._monitor)
        self.thread.start()
        
    def _monitor(self):
        while self.running:
            cpu_percent = psutil.cpu_percent(interval=0.5, percpu=True)
            total_cpu = psutil.cpu_percent(interval=0.5)
            self.cpu_history.append({
                'time': time.time(),
                'total': total_cpu,
                'per_core': cpu_percent
            })
            
    def stop(self):
        self.running = False
        self.thread.join()
        
    def report(self):
        if not self.cpu_history:
            print("No data collected")
            return
            
        avg_total = sum(d['total'] for d in self.cpu_history) / len(self.cpu_history)
        max_total = max(d['total'] for d in self.cpu_history)
        
        print(f"\n📊 CPU Utilization Report:")
        print(f"   Average: {avg_total:.1f}%")
        print(f"   Peak: {max_total:.1f}%")
        print(f"   Cores available: {psutil.cpu_count()}")
        
        # Per-core stats
        n_cores = len(self.cpu_history[0]['per_core'])
        core_avgs = [0] * n_cores
        
        for record in self.cpu_history:
            for i, val in enumerate(record['per_core']):
                core_avgs[i] += val
                
        core_avgs = [x / len(self.cpu_history) for x in core_avgs]
        
        print(f"\n   Per-core average:")
        for i, avg in enumerate(core_avgs):
            bar = '█' * int(avg / 10)
            print(f"   Core {i}: {avg:5.1f}% {bar}")


# Teste
if __name__ == "__main__":
    print("Iniciando monitor de CPU...")
    print("Execute seu processamento LATC em outra janela")
    print("Pressione Ctrl+C para parar\n")
    
    monitor = CPUMonitor()
    monitor.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\nParando monitor...")
        monitor.stop()
        monitor.report()
