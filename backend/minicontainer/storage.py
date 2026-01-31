"""MiniContainer - Metrics Storage and Process Information

CSV-based storage for historical metrics data and process information retrieval.
"""

import csv
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# Storage directory for CSV files
DATA_DIR = Path("/tmp/minicontainer/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


def get_ist_datetime(ts: float = None) -> str:
    """Convert timestamp to IST datetime string"""
    if ts is None:
        ts = time.time()
    dt = datetime.fromtimestamp(ts, tz=IST)
    return dt.strftime('%Y-%m-%d %H:%M:%S IST')


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
        self.anomaly_csv_path = DATA_DIR / "anomalies.csv"
        self.summary_csv_path = DATA_DIR / "container_summary.csv"
        self._ensure_csv_exists()
        self._ensure_anomaly_csv_exists()
        self._ensure_summary_csv_exists()
    
    def _ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp_unix', 'datetime_IST', 'container_id', 'container_name',
                    'cpu_usage_percent', 'memory_used_bytes', 'memory_usage_percent', 
                    'memory_limit_bytes', 'process_count', 'health_score_0_100', 
                    'stability_score_0_100', 'efficiency_score_0_100', 
                    'is_stressed_flag', 'cpu_rate_of_change', 'anomaly_count'
                ])
    
    def _ensure_anomaly_csv_exists(self):
        """Create anomaly CSV file with headers if it doesn't exist"""
        if not self.anomaly_csv_path.exists():
            with open(self.anomaly_csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp_unix', 'datetime_IST', 'container_id', 'anomaly_type',
                    'severity_level', 'actual_value', 'expected_value', 'z_score', 
                    'detection_algorithm', 'description'
                ])
    
    def _ensure_summary_csv_exists(self):
        """Create summary CSV file with headers if it doesn't exist"""
        if not self.summary_csv_path.exists():
            with open(self.summary_csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp_unix', 'datetime_IST', 'container_id', 'container_name',
                    'cpu_average_percent', 'cpu_max_percent', 'cpu_min_percent', 
                    'cpu_std_deviation', 'cpu_95th_percentile',
                    'memory_average_bytes', 'memory_max_bytes', 'memory_min_bytes', 
                    'memory_95th_percentile',
                    'health_score_0_100', 'stability_score_0_100', 'efficiency_score_0_100',
                    'total_anomalies_detected', 'stress_event_count', 
                    'total_stress_duration_sec', 'container_uptime_sec'
                ])
    
    def store_metrics(self, container_id: str, container_name: str,
                      cpu_percent: float, memory_bytes: int, memory_percent: float,
                      memory_limit: int, pids: int, health_score: float = 100.0,
                      stability_score: float = 100.0, efficiency_score: float = 100.0,
                      is_stressed: bool = False, cpu_rate: float = 0.0, anomaly_count: int = 0):
        """Store a metrics snapshot to CSV"""
        try:
            ts = time.time()
            dt = get_ist_datetime(ts)
            
            with open(self.csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    round(ts, 2), dt, container_id, container_name,
                    round(cpu_percent, 2), memory_bytes, round(memory_percent, 2),
                    memory_limit, pids, round(health_score, 1), round(stability_score, 1),
                    round(efficiency_score, 1), 1 if is_stressed else 0, round(cpu_rate, 2), anomaly_count
                ])
            
            # Rotate file if too large
            self._rotate_if_needed()
        except Exception as e:
            print(f"Error storing metrics: {e}")
    
    def store_anomaly(self, container_id: str, anomaly: dict):
        """Store an anomaly to the anomaly CSV"""
        try:
            ts = anomaly.get('timestamp', time.time())
            dt = get_ist_datetime(ts)
            
            with open(self.anomaly_csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    round(ts, 2), dt, container_id, anomaly.get('type', 'unknown'),
                    anomaly.get('severity', 'low'), anomaly.get('value', 0),
                    anomaly.get('expected', 0), anomaly.get('z_score', 0),
                    anomaly.get('algorithm', 'unknown'), anomaly.get('message', '')
                ])
        except Exception as e:
            print(f"Error storing anomaly: {e}")
    
    def store_summary(self, container_id: str, container_name: str, analytics: dict):
        """Store a container analytics summary snapshot"""
        try:
            ts = time.time()
            dt = get_ist_datetime(ts)
            
            with open(self.summary_csv_path, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    round(ts, 2), dt, container_id, container_name,
                    analytics.get('cpu_avg', 0), analytics.get('cpu_max', 0),
                    analytics.get('cpu_min', 0), analytics.get('cpu_std', 0),
                    analytics.get('cpu_p95', 0), analytics.get('memory_avg', 0),
                    analytics.get('memory_max', 0), analytics.get('memory_min', 0),
                    analytics.get('memory_p95', 0), analytics.get('health_score', 100),
                    analytics.get('stability_score', 100), analytics.get('efficiency_score', 100),
                    analytics.get('anomaly_count_total', 0), analytics.get('stress_count', 0),
                    analytics.get('total_stress_time', 0), analytics.get('uptime_seconds', 0)
                ])
        except Exception as e:
            print(f"Error storing summary: {e}")
    
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
                        # Handle both old and new column names for compatibility
                        history.append({
                            'timestamp': float(row.get('timestamp_unix') or row.get('timestamp', 0)),
                            'datetime': row.get('datetime_IST') or row.get('datetime', ''),
                            'cpu_percent': float(row.get('cpu_usage_percent') or row.get('cpu_percent', 0)),
                            'memory_bytes': int(row.get('memory_used_bytes') or row.get('memory_bytes', 0)),
                            'memory_percent': float(row.get('memory_usage_percent') or row.get('memory_percent', 0)),
                            'pids': int(row.get('process_count') or row.get('pids', 0)),
                            'health_score': float(row.get('health_score_0_100') or row.get('health_score', 100)),
                            'stability_score': float(row.get('stability_score_0_100') or row.get('stability_score', 100)),
                            'efficiency_score': float(row.get('efficiency_score_0_100') or row.get('efficiency_score', 100)),
                            'is_stressed': bool(int(row.get('is_stressed_flag') or row.get('is_stressed', 0))),
                            'cpu_rate': float(row.get('cpu_rate_of_change') or row.get('cpu_rate', 0)),
                            'anomaly_count': int(row.get('anomaly_count', 0))
                        })
            return history[-limit:]
        except Exception as e:
            print(f"Error reading history: {e}")
            return []
    
    def get_anomaly_history(self, container_id: str = None, limit: int = 100) -> List[dict]:
        """Get anomaly history, optionally filtered by container"""
        history = []
        try:
            if self.anomaly_csv_path.exists():
                with open(self.anomaly_csv_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if container_id is None or row['container_id'] == container_id:
                            # Handle both old and new column names
                            history.append({
                                'timestamp': float(row.get('timestamp_unix') or row.get('timestamp', 0)),
                                'datetime': row.get('datetime_IST') or row.get('datetime', ''),
                                'container_id': row['container_id'],
                                'anomaly_type': row['anomaly_type'],
                                'severity': row.get('severity_level') or row.get('severity', 'low'),
                                'value': float(row.get('actual_value') or row.get('value', 0) or 0),
                                'expected': float(row.get('expected_value') or row.get('expected', 0) or 0),
                                'z_score': float(row.get('z_score', 0) or 0),
                                'algorithm': row.get('detection_algorithm') or row.get('algorithm', ''),
                                'message': row.get('description') or row.get('message', '')
                            })
            return history[-limit:]
        except Exception as e:
            print(f"Error reading anomaly history: {e}")
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
    
    def export_anomaly_csv_path(self) -> str:
        """Return path to anomaly CSV file for download"""
        return str(self.anomaly_csv_path)
    
    def export_summary_csv_path(self) -> str:
        """Return path to summary CSV file for download"""
        return str(self.summary_csv_path)
    
    def get_stats_summary(self, container_id: str) -> dict:
        """Get statistical summary for a container"""
        history = self.get_history(container_id, limit=1000)
        
        if not history:
            return {"error": "No data available"}
        
        cpu_values = [h['cpu_percent'] for h in history]
        mem_values = [h['memory_bytes'] for h in history]
        health_values = [h.get('health_score', 100) for h in history]
        
        # Calculate percentiles
        sorted_cpu = sorted(cpu_values)
        sorted_mem = sorted(mem_values)
        p50_idx = len(sorted_cpu) // 2
        p95_idx = int(len(sorted_cpu) * 0.95)
        p99_idx = int(len(sorted_cpu) * 0.99)
        
        # Calculate standard deviation
        cpu_avg = sum(cpu_values) / len(cpu_values)
        cpu_variance = sum((x - cpu_avg) ** 2 for x in cpu_values) / len(cpu_values)
        cpu_std = cpu_variance ** 0.5
        
        # Stress analysis
        stressed_count = sum(1 for h in history if h.get('is_stressed', False))
        stress_ratio = stressed_count / len(history) if history else 0
        
        return {
            "container_id": container_id,
            "data_points": len(history),
            "time_range_seconds": history[-1]['timestamp'] - history[0]['timestamp'] if len(history) > 1 else 0,
            "start_time": history[0]['datetime'] if history else None,
            "end_time": history[-1]['datetime'] if history else None,
            "cpu": {
                "avg": round(cpu_avg, 2),
                "max": round(max(cpu_values), 2),
                "min": round(min(cpu_values), 2),
                "std": round(cpu_std, 2),
                "p50": round(sorted_cpu[p50_idx], 2) if sorted_cpu else 0,
                "p95": round(sorted_cpu[p95_idx], 2) if len(sorted_cpu) > p95_idx else 0,
                "p99": round(sorted_cpu[p99_idx], 2) if len(sorted_cpu) > p99_idx else 0,
            },
            "memory": {
                "avg": int(sum(mem_values) / len(mem_values)),
                "avg_mb": round(sum(mem_values) / len(mem_values) / (1024*1024), 2),
                "max": max(mem_values),
                "max_mb": round(max(mem_values) / (1024*1024), 2),
                "min": min(mem_values),
                "min_mb": round(min(mem_values) / (1024*1024), 2),
                "p50": sorted_mem[p50_idx] if sorted_mem else 0,
                "p95": sorted_mem[p95_idx] if len(sorted_mem) > p95_idx else 0,
            },
            "health": {
                "avg": round(sum(health_values) / len(health_values), 1),
                "min": round(min(health_values), 1),
                "current": round(health_values[-1], 1) if health_values else 100,
            },
            "stress": {
                "stress_count": stressed_count,
                "stress_ratio": round(stress_ratio * 100, 1),  # percentage of time stressed
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
    
    # Correct path: /sys/fs/cgroup/minicontainer/{container_id}/
    CGROUP_BASE = Path("/sys/fs/cgroup/minicontainer")
    
    # Process descriptions for common commands
    PROCESS_DESCRIPTIONS = {
        # Shells
        "sh": "Bourne shell - lightweight command interpreter",
        "bash": "GNU Bourne Again Shell - enhanced command interpreter",
        "ash": "Almquist shell - lightweight POSIX shell (Alpine default)",
        "zsh": "Z shell - extended Bourne shell with many improvements",
        
        # Init/System
        "init": "Init process (PID 1) - first process in container",
        "sleep": "Sleep command - pauses for specified duration",
        "cat": "Concatenate and display file contents",
        "tail": "Display the last lines of a file/stream",
        "head": "Display the first lines of a file/stream",
        
        # Stress/Load
        "stress": "Stress test tool - generates CPU/memory/IO load",
        "dd": "Data duplicator - copies/converts data between files",
        "yes": "Repeatedly outputs a string - used for stress testing",
        
        # File operations
        "ls": "List directory contents",
        "cp": "Copy files and directories",
        "mv": "Move/rename files and directories",
        "rm": "Remove files and directories",
        "find": "Search for files in directory hierarchy",
        "grep": "Search for patterns in files",
        
        # Process management
        "ps": "Report process status",
        "top": "Display Linux processes dynamically",
        "htop": "Interactive process viewer",
        "kill": "Send signals to processes",
        
        # Network
        "ping": "Send ICMP echo requests to network hosts",
        "wget": "Download files from the web",
        "curl": "Transfer data to/from servers",
        "nc": "Netcat - networking utility for reading/writing",
        "nginx": "High-performance HTTP server",
        "python": "Python interpreter running a script",
        "python3": "Python 3 interpreter running a script",
        "node": "Node.js JavaScript runtime",
        
        # Package management
        "apk": "Alpine Package Keeper - package manager",
        "apt": "Advanced package tool - Debian package manager",
        "yum": "Yellowdog Updater Modified - RPM package manager",
        
        # Math/scripting
        "awk": "Pattern scanning and processing language",
        "sed": "Stream editor for filtering and transforming text",
        "bc": "Arbitrary precision calculator",
        "expr": "Evaluate expressions",
        
        # Default
        "default": "User process running inside container"
    }
    
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
            print(f"Error reading container PIDs from {cgroup_procs}: {e}")
        
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
    
    def _get_process_description(self, name: str, cmd: str) -> str:
        """Get a description for a process based on its name"""
        # Try exact match
        if name in self.PROCESS_DESCRIPTIONS:
            return self.PROCESS_DESCRIPTIONS[name]
        
        # Try matching first word of command
        first_word = cmd.split()[0].split('/')[-1] if cmd else name
        if first_word in self.PROCESS_DESCRIPTIONS:
            return self.PROCESS_DESCRIPTIONS[first_word]
        
        # Check for common patterns
        if "loop" in cmd.lower() or "while" in cmd.lower():
            return "Loop/stress script generating CPU load"
        if "seq" in cmd.lower():
            return "Sequence generator - often used in counting operations"
        if "for" in cmd.lower():
            return "For loop - iterating over a sequence"
        if "echo" in cmd.lower():
            return "Echo command - prints text to stdout"
        
        return self.PROCESS_DESCRIPTIONS["default"]
    
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
                    "command": info.cmd,
                    "description": self._get_process_description(info.name, info.cmd)
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
