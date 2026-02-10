"""KernelSight - Container metrics collection"""

import time
import threading
from typing import Dict, List, Callable
from pathlib import Path
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

@dataclass 
class MetricPoint:
    timestamp: float
    cpu_percent: float = 0.0
    memory_bytes: int = 0
    memory_percent: float = 0.0
    pids: int = 0
    net_rx_bytes: int = 0
    net_tx_bytes: int = 0

class MetricsCollector:
    """Collects and stores container metrics over time"""
    
    def __init__(self, history_size: int = 60):
        self.history_size = history_size
        self._metrics: Dict[str, deque] = {}
        self._prev_cpu: Dict[str, int] = {}
        self._prev_time: Dict[str, float] = {}
        self._callbacks: List[Callable] = []
        self._running = False
        self._thread = None
    
    def add_callback(self, callback: Callable):
        """Add a callback for new metrics"""
        self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remove a callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _read_cgroup_value(self, path: Path) -> int:
        try:
            content = path.read_text().strip()
            return -1 if content == "max" else int(content)
        except:
            return 0
    
    def _collect_container_metrics(self, container_id: str, cgroup_path: Path) -> MetricPoint:
        """Collect metrics for a single container"""
        point = MetricPoint(timestamp=time.time())
        
        # Memory
        mem_current = cgroup_path / "memory.current"
        mem_max = cgroup_path / "memory.max"
        if mem_current.exists():
            point.memory_bytes = self._read_cgroup_value(mem_current)
            mem_limit = self._read_cgroup_value(mem_max)
            if mem_limit > 0:
                point.memory_percent = (point.memory_bytes / mem_limit) * 100
        
        # CPU
        cpu_stat = cgroup_path / "cpu.stat"
        if cpu_stat.exists():
            for line in cpu_stat.read_text().splitlines():
                if line.startswith("usage_usec"):
                    cpu_ns = int(line.split()[1]) * 1000
                    
                    prev_cpu = self._prev_cpu.get(container_id, 0)
                    prev_time = self._prev_time.get(container_id, point.timestamp)
                    
                    delta_cpu = cpu_ns - prev_cpu
                    delta_time = point.timestamp - prev_time
                    
                    if delta_time > 0 and prev_cpu > 0:
                        # CPU percent (100% = 1 core fully used)
                        point.cpu_percent = (delta_cpu / (delta_time * 1e9)) * 100
                    
                    self._prev_cpu[container_id] = cpu_ns
                    self._prev_time[container_id] = point.timestamp
                    break
        
        # PIDs
        pids_current = cgroup_path / "pids.current"
        if pids_current.exists():
            point.pids = self._read_cgroup_value(pids_current)
        
        return point
    
    def collect_all(self) -> Dict[str, MetricPoint]:
        """Collect metrics for all containers"""
        results = {}
        cgroup_base = Path("/sys/fs/cgroup/kernelsight")
        
        if not cgroup_base.exists():
            return results
        
        for container_dir in cgroup_base.iterdir():
            if not container_dir.is_dir():
                continue
            container_id = container_dir.name
            
            point = self._collect_container_metrics(container_id, container_dir)
            results[container_id] = point
            
            # Store in history
            if container_id not in self._metrics:
                self._metrics[container_id] = deque(maxlen=self.history_size)
            self._metrics[container_id].append(point)
        
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(results)
            except:
                pass
        
        return results
    
    def get_history(self, container_id: str) -> List[MetricPoint]:
        """Get metric history for a container"""
        return list(self._metrics.get(container_id, []))
    
    def _collection_loop(self, interval: float):
        """Background collection loop"""
        while self._running:
            self.collect_all()
            time.sleep(interval)
    
    def start(self, interval: float = 1.0):
        """Start background metric collection"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._collection_loop, args=(interval,), daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop background metric collection"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

# Global collector instance
collector = MetricsCollector()
