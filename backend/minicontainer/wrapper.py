"""MiniContainer - Python wrapper for libminicontainer.so"""

import ctypes
import os
from ctypes import Structure, c_char, c_int, c_long, c_double, c_uint, POINTER, create_string_buffer
from typing import Optional, List, Dict
from pathlib import Path

# Find the library
LIB_PATH = Path(__file__).parent.parent.parent / "runtime" / "build" / "libminicontainer.so"

class ResourceLimits(Structure):
    _fields_ = [
        ("memory_limit_bytes", c_long),
        ("memory_swap_bytes", c_long),
        ("cpu_shares", c_int),
        ("cpu_quota_us", c_int),
        ("cpu_period_us", c_int),
        ("pids_max", c_int),
    ]

class ContainerConfig(Structure):
    _fields_ = [
        ("id", c_char * 65),
        ("name", c_char * 256),
        ("hostname", c_char * 256),
        ("rootfs", c_char * 4096),
        ("cmd", POINTER(ctypes.c_char_p)),
        ("cmd_count", c_int),
        ("env", POINTER(ctypes.c_char_p)),
        ("env_count", c_int),
        ("limits", ResourceLimits),
        ("enable_network", c_int),
        ("enable_user_ns", c_int),
        ("uid_map_host", c_uint),
        ("uid_map_container", c_uint),
        ("gid_map_host", c_uint),
        ("gid_map_container", c_uint),
    ]

class ContainerMetrics(Structure):
    _fields_ = [
        ("memory_usage_bytes", c_long),
        ("memory_max_usage_bytes", c_long),
        ("memory_limit_bytes", c_long),
        ("cpu_usage_percent", c_double),
        ("cpu_usage_ns", c_long),
        ("pids_current", c_int),
        ("pids_limit", c_int),
        ("net_rx_bytes", c_long),
        ("net_tx_bytes", c_long),
    ]

class Container:
    """Python representation of a container"""
    
    def __init__(self, id: str, name: str, state: str = "created", pid: int = 0,
                 rootfs: str = "", cgroup_path: str = "", state_dir: str = ""):
        self.id = id
        self.name = name
        self.state = state
        self.pid = pid
        self.rootfs = rootfs
        self.cgroup_path = cgroup_path or f"/sys/fs/cgroup/minicontainer/{id}"
        self.state_dir = state_dir or f"/var/lib/minicontainer/containers/{id}"
    
    def get_metrics(self) -> Dict:
        """Get container metrics from cgroup"""
        metrics = {}
        try:
            mem_current = Path(self.cgroup_path) / "memory.current"
            if mem_current.exists():
                metrics["memory_usage_bytes"] = int(mem_current.read_text().strip())
            
            mem_max = Path(self.cgroup_path) / "memory.max"
            if mem_max.exists():
                val = mem_max.read_text().strip()
                metrics["memory_limit_bytes"] = -1 if val == "max" else int(val)
            
            cpu_stat = Path(self.cgroup_path) / "cpu.stat"
            if cpu_stat.exists():
                for line in cpu_stat.read_text().splitlines():
                    if line.startswith("usage_usec"):
                        metrics["cpu_usage_ns"] = int(line.split()[1]) * 1000
            
            pids_current = Path(self.cgroup_path) / "pids.current"
            if pids_current.exists():
                metrics["pids_current"] = int(pids_current.read_text().strip())
                
            pids_max = Path(self.cgroup_path) / "pids.max"
            if pids_max.exists():
                val = pids_max.read_text().strip()
                metrics["pids_limit"] = -1 if val == "max" else int(val)
        except Exception:
            pass
        return metrics
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "state": self.state,
            "pid": self.pid,
            "rootfs": self.rootfs,
        }

class ContainerManager:
    """Manages containers using the C runtime or pure Python fallback"""
    
    STATE_DIR = Path("/var/lib/minicontainer/containers")
    
    def __init__(self):
        self._lib = None
        try:
            if LIB_PATH.exists():
                self._lib = ctypes.CDLL(str(LIB_PATH))
        except Exception:
            pass
    
    def list_containers(self) -> List[Container]:
        """List all containers"""
        containers = []
        if not self.STATE_DIR.exists():
            return containers
        
        for container_dir in self.STATE_DIR.iterdir():
            if not container_dir.is_dir():
                continue
            state_file = container_dir / "state.txt"
            if not state_file.exists():
                continue
            
            data = {}
            for line in state_file.read_text().splitlines():
                if "=" in line:
                    key, val = line.split("=", 1)
                    data[key] = val
            
            containers.append(Container(
                id=data.get("id", container_dir.name),
                name=data.get("name", container_dir.name),
                state=data.get("state", "unknown"),
                pid=int(data.get("pid", 0)),
                state_dir=str(container_dir),
            ))
        return containers
    
    def get_container(self, id_or_name: str) -> Optional[Container]:
        """Get a container by ID or name"""
        for c in self.list_containers():
            if c.id == id_or_name or c.name == id_or_name or c.id.startswith(id_or_name):
                return c
        return None
    
    def get_all_metrics(self) -> List[Dict]:
        """Get metrics for all running containers"""
        result = []
        for c in self.list_containers():
            if c.state == "running":
                result.append({
                    "container": c.to_dict(),
                    "metrics": c.get_metrics()
                })
        return result

manager = ContainerManager()
