"""MiniContainer - Metrics Storage and Process Information

CSV-based storage for historical metrics data and process information retrieval.
"""

import csv
import os
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# Storage directory for CSV files
DATA_DIR = Path("/tmp/minicontainer/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ProcessInfo:
    """Information about a process"""
    pid: int
    ppid: int  # Parent PID
    name: str
    state: str
    cpu_percent: float
    mem_bytes: int
    cmd: str


class MetricsStorage:
    """
    CSV-based storage for container metrics.
    Stores: timestamp, container_id, cpu_percent, memory_bytes, memory_percent, pids
    """
    
    def __init__(self, max_rows_per_file: int = 10000):
        self.max_rows = max_rows_per_file
        self.csv_path = DATA_DIR / "metrics_history.csv"
        self._ensure_csv_exists()
    
    def _ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'datetime', 'container_id', 'container_name',
                    'cpu_percent', 'memory_bytes', 'memory_percent', 
                    'memory_limit', 'pids', 'health_score'
                ])
    
    def store_metrics(self, container_id: str, container_name: str,
                      cpu_percent: float, memory_bytes: int, memory_percent: float,
                      memory_limit: int, pids: int, health_score: float = 100.0):
        """Store a metrics snapshot to CSV"""
        try:
            ts = time.time()
            dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))
            
            with open(self.csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    round(ts, 2), dt, container_id, container_name,
                    round(cpu_percent, 2), memory_bytes, round(memory_percent, 2),
                    memory_limit, pids, round(health_score, 1)
                ])
            
            # Rotate file if too large
            self._rotate_if_needed()
        except Exception as e:
            print(f"Error storing metrics: {e}")
    
    def _rotate_if_needed(self):
        """Rotate CSV if it exceeds max rows"""
        try:
            with open(self.csv_path, 'r') as f:
                row_count = sum(1 for _ in f)
            
            if row_count > self.max_rows:
                # Keep last half of rows
                with open(self.csv_path, 'r') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                
                header = rows[0]
                keep_rows = rows[-(self.max_rows // 2):]
                
                with open(self.csv_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(header)
                    writer.writerows(keep_rows)
        except Exception as e:
            print(f"Error rotating CSV: {e}")
    
    def get_history(self, container_id: str, limit: int = 100) -> List[dict]:
        """Get recent history for a container"""
        history = []
        try:
            with open(self.csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['container_id'] == container_id:
                        history.append({
                            'timestamp': float(row['timestamp']),
                            'datetime': row['datetime'],
                            'cpu_percent': float(row['cpu_percent']),
                            'memory_bytes': int(row['memory_bytes']),
                            'memory_percent': float(row['memory_percent']),
                            'pids': int(row['pids']),
                            'health_score': float(row['health_score'])
                        })
            return history[-limit:]
        except Exception as e:
            print(f"Error reading history: {e}")
            return []
    
    def get_all_history(self, limit: int = 500) -> List[dict]:
        """Get recent history for all containers"""
        history = []
        try:
            with open(self.csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    history.append(dict(row))
            return history[-limit:]
        except Exception as e:
            print(f"Error reading all history: {e}")
            return []
    
    def export_csv_path(self) -> str:
        """Return path to CSV file for download"""
        return str(self.csv_path)
    
    def get_stats_summary(self, container_id: str) -> dict:
        """Get statistical summary for a container"""
        history = self.get_history(container_id, limit=1000)
        
        if not history:
            return {"error": "No data available"}
        
        cpu_values = [h['cpu_percent'] for h in history]
        mem_values = [h['memory_bytes'] for h in history]
        
        return {
            "container_id": container_id,
            "data_points": len(history),
            "time_range_seconds": history[-1]['timestamp'] - history[0]['timestamp'] if len(history) > 1 else 0,
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "max": max(cpu_values),
                "min": min(cpu_values)
            },
            "memory": {
                "avg": sum(mem_values) / len(mem_values),
                "max": max(mem_values),
                "min": min(mem_values)
            }
        }


class ProcessInspector:
    """
    Get information about processes running inside containers.
    
    Explanation:
    - PID (Process ID): A unique number assigned by the OS to each running process
    - In containers, the init process (PID 1 inside container) has a different PID on the host
    - We can see all container processes by looking at /proc on the host
    """
    
    CGROUP_BASE = Path("/sys/fs/cgroup")
    
    def get_container_pids(self, container_id: str) -> List[int]:
        """
        Get all PIDs belonging to a container's cgroup.
        These are the host PIDs of processes running inside the container.
        """
        cgroup_procs = self.CGROUP_BASE / container_id / "cgroup.procs"
        pids = []
        
        try:
            if cgroup_procs.exists():
                content = cgroup_procs.read_text().strip()
                if content:
                    pids = [int(p) for p in content.split('\n') if p.strip()]
        except Exception as e:
            print(f"Error reading container PIDs: {e}")
        
        return pids
    
    def get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """
        Get detailed information about a process.
        
        /proc/<pid>/stat contains process status
        /proc/<pid>/cmdline contains the command line
        /proc/<pid>/status contains human-readable info
        """
        proc_path = Path(f"/proc/{pid}")
        
        if not proc_path.exists():
            return None
        
        try:
            # Read stat file for basic info
            stat_content = (proc_path / "stat").read_text()
            stat_parts = stat_content.split()
            
            # Parse (format: pid (name) state ppid ...)
            name = stat_parts[1].strip('()')
            state = stat_parts[2]
            ppid = int(stat_parts[3])
            
            # Read cmdline
            try:
                cmdline = (proc_path / "cmdline").read_text().replace('\x00', ' ').strip()
                if not cmdline:
                    cmdline = f"[{name}]"
            except:
                cmdline = f"[{name}]"
            
            # Read status for memory info
            mem_bytes = 0
            try:
                for line in (proc_path / "status").read_text().splitlines():
                    if line.startswith("VmRSS:"):
                        # VmRSS is in KB
                        mem_kb = int(line.split()[1])
                        mem_bytes = mem_kb * 1024
                        break
            except:
                pass
            
            return ProcessInfo(
                pid=pid,
                ppid=ppid,
                name=name,
                state=state,
                cpu_percent=0.0,  # Would need /proc/stat comparison over time
                mem_bytes=mem_bytes,
                cmd=cmdline[:200]  # Truncate long commands
            )
        except Exception as e:
            return None
    
    def get_container_processes(self, container_id: str) -> List[dict]:
        """
        Get all processes running inside a container with their info.
        
        Returns a list of process info dictionaries.
        """
        pids = self.get_container_pids(container_id)
        processes = []
        
        for pid in pids:
            info = self.get_process_info(pid)
            if info:
                processes.append({
                    "pid": info.pid,
                    "ppid": info.ppid,
                    "name": info.name,
                    "state": self._state_to_name(info.state),
                    "state_code": info.state,
                    "memory_bytes": info.mem_bytes,
                    "memory_human": self._format_bytes(info.mem_bytes),
                    "command": info.cmd
                })
        
        return processes
    
    def get_init_pid(self, container_id: str) -> Optional[int]:
        """
        Get the init process (PID 1 inside container) host PID.
        This is the first/main process of the container.
        """
        pids = self.get_container_pids(container_id)
        
        # The init process typically has the lowest PID
        if pids:
            return min(pids)
        return None
    
    def _state_to_name(self, state: str) -> str:
        """Convert process state code to human-readable name"""
        states = {
            'R': 'Running',
            'S': 'Sleeping',
            'D': 'Disk Sleep',
            'Z': 'Zombie',
            'T': 'Stopped',
            't': 'Tracing',
            'X': 'Dead',
            'I': 'Idle'
        }
        return states.get(state, 'Unknown')
    
    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024
        return f"{bytes_val:.1f} TB"


# Global instances
metrics_storage = MetricsStorage()
process_inspector = ProcessInspector()
