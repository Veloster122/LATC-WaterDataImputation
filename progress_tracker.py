"""
Progress tracking utility for LATC processing scripts
Writes progress to a JSON file that GUI can read
"""
import json
from pathlib import Path
from datetime import datetime


class ProgressTracker:
    def __init__(self, task_name, total_steps):
        self.task_name = task_name
        self.total_steps = total_steps
        self.current_step = 0
        
        # Check for env var override
        import os
        env_path = os.environ.get('LATC_PROGRESS_FILE')
        if env_path:
            self.progress_file = Path(env_path)
        else:
            self.progress_file = Path("data/progress.json")
            
        self.progress_file.parent.mkdir(exist_ok=True)
        self._update()
    
    def update(self, step_name, increment=1):
        """Update progress with step name"""
        self.current_step += increment
        self._write_progress(step_name)
    
    def set_progress(self, current, message):
        """Set absolute progress"""
        self.current_step = current
        self._write_progress(message)
    
    def _write_progress(self, message):
        """Write progress to file"""
        progress_data = {
            "task": self.task_name,
            "current": self.current_step,
            "total": self.total_steps,
            "percent": min(100, int(100 * self.current_step / self.total_steps)),
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress_data, f)
    
    def complete(self):
        """Mark as complete"""
        self.current_step = self.total_steps
        self._write_progress("Concluído!")
    
    def cleanup(self):
        """Remove progress file"""
        if self.progress_file.exists():
            self.progress_file.unlink()
