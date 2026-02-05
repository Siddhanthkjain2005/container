# 🐳 KernelSight - Educational Container Runtime

> **A hands-on learning project that builds container technology from scratch**  
> Understanding Docker internals through Linux kernel primitives: namespaces, cgroups, and process isolation.

---

## 📖 Table of Contents

- [What is KernelSight?](#-what-is-kernelsight)
- [Why This Project?](#-why-this-project)
- [System Architecture](#-system-architecture)
- [How Containers Work (Simplified)](#-how-containers-work-simplified)
- [Project Structure](#-project-structure)
- [Execution Flow](#-execution-flow)
- [Core Components Explained](#-core-components-explained)
- [Key Concepts with Examples](#-key-concepts-with-examples)
- [Quick Start Guide](#-quick-start-guide)
- [Real-World Example](#-real-world-example)
- [Metrics & Monitoring](#-metrics--monitoring)
- [Technology Stack](#-technology-stack)
- [Learning Outcomes](#-learning-outcomes)

---

## 🎯 What is KernelSight?

**KernelSight is a mini container runtime** - think of it as a simplified, educational version of Docker that shows you exactly how containers work at the Linux kernel level.

### The Analogy

- **Docker/Kubernetes** = A fully-featured smartphone 📱 (powerful but complex)
- **KernelSight** = A basic phone you build yourself 🔧 (simple but teaches you how everything works)

### What It Does

1. **Creates isolated environments** (containers) where applications run
2. **Limits resources** (CPU, memory) so one container can't crash the system
3. **Monitors performance** in real-time with beautiful dashboards
4. **Shows the magic** behind Docker, Kubernetes, and modern cloud platforms

---

## 💡 Why This Project?

### Problem Statement

Everyone uses containers (Docker, Kubernetes), but few understand:
- How does isolation actually work?
- What are namespaces and cgroups?
- How does Docker limit CPU and memory?
- What happens inside the Linux kernel?

### Solution

**Learn by building!** KernelSight implements container technology from scratch using:
- **C programming** for low-level kernel operations
- **Python** for modern API and tooling
- **React** for beautiful visualization

**Result:** You understand containers deeply, not just how to use them.

---

## 🏗️ System Architecture

KernelSight has a **3-tier architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                      KernelSight System                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐   ┌──────────────────┐   ┌─────────────┐│
│  │   1. C Runtime   │──▶│ 2. Python Backend│──▶│ 3. Dashboard││
│  │   (The Engine)   │   │   (The Bridge)   │   │  (The Face) ││
│  └──────────────────┘   └──────────────────┘   └─────────────┘│
│                                                                 │
│  • Namespaces        • REST API             • React UI         │
│  • Cgroups           • WebSocket            • Real-time graphs │
│  • Process isolation • Metrics collection   • Command interface│
│  • System calls      • Python ↔ C bridge    • Responsive design│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Layer Details

| Layer | Technology | Purpose | Files |
|-------|-----------|---------|-------|
| **Frontend** | React + Vite | User interface, visualization | `dashboard/src/App.jsx` |
| **Backend** | Python + FastAPI | API server, WebSocket, metrics | `backend/kernelsight/api.py` |
| **Runtime** | C + Linux Kernel | Container creation, isolation | `runtime/src/*.c` |

---

## 🔍 How Containers Work (Simplified)

Think of your computer as a **big apartment building**:

### Without Containers
```
┌─────────────────────────────────────┐
│         Your Computer (Host)        │
│                                     │
│  App1  App2  App3  App4  App5      │
│    ↓    ↓    ↓    ↓    ↓           │
│  All share everything:              │
│  • Same filesystem                  │
│  • Same processes                   │
│  • Same network                     │
│  • Can interfere with each other    │
│                                     │
│  Problem: App1 can crash App2! ❌   │
└─────────────────────────────────────┘
```

### With Containers (KernelSight)
```
┌─────────────────────────────────────────────────────────────┐
│               Your Computer (Host)                          │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │
│  │Container1│  │Container2│  │Container3│                 │
│  │          │  │          │  │          │                 │
│  │  App1    │  │  App2    │  │  App3    │                 │
│  │          │  │          │  │          │                 │
│  │ Own:     │  │ Own:     │  │ Own:     │                 │
│  │ • Files  │  │ • Files  │  │ • Files  │                 │
│  │ • PIDs   │  │ • PIDs   │  │ • PIDs   │                 │
│  │ • Network│  │ • Network│  │ • Network│                 │
│  │          │  │          │  │          │                 │
│  │ Max:     │  │ Max:     │  │ Max:     │                 │
│  │ 256MB RAM│  │ 512MB RAM│  │ 128MB RAM│                 │
│  │ 50% CPU  │  │ 100% CPU │  │ 25% CPU  │                 │
│  └──────────┘  └──────────┘  └──────────┘                 │
│                                                             │
│  ✅ Isolated    ✅ Resource limits    ✅ Secure             │
└─────────────────────────────────────────────────────────────┘
```

### The Magic: 3 Linux Kernel Features

1. **Namespaces** = Private apartments (isolation)
2. **Cgroups** = Utility limits (resource control)
3. **pivot_root** = Locked doors (filesystem security)

---

## 📁 Project Structure

```
kernelsight/
│
├── 📂 runtime/                    # Part 1: The C Engine
│   ├── src/
│   │   ├── container.c            # Container lifecycle management
│   │   ├── namespace.c            # Isolation (PID, Mount, UTS, Network, IPC)
│   │   ├── cgroup.c               # Resource limits (CPU, Memory, PIDs)
│   │   ├── filesystem.c           # Root filesystem setup
│   │   └── process.c              # Process management
│   ├── include/
│   │   └── container.h            # C header definitions
│   ├── cli/
│   │   └── main.c                 # Command-line interface
│   ├── Makefile                   # Build configuration
│   └── build/
│       └── libcontainer.so        # Compiled shared library
│
├── 📂 backend/                    # Part 2: The Python Bridge
│   ├── requirements.txt           # Python dependencies
│   └── kernelsight/
│       ├── __init__.py            # Package initialization
│       ├── api.py                 # ⭐ FastAPI server + WebSocket
│       ├── wrapper.py             # ⭐ Python ↔ C bridge (ctypes)
│       ├── metrics.py             # ⭐ Metrics collector (reads cgroups)
│       ├── cli.py                 # ⭐ Terminal UI (Rich library)
│       ├── ml.py                  # Machine learning anomaly detection
│       └── storage.py             # Container state storage
│
├── 📂 dashboard/                  # Part 3: The Web Interface
│   ├── package.json               # npm dependencies
│   ├── vite.config.js             # Vite build configuration
│   └── src/
│       ├── main.jsx               # React entry point
│       ├── App.jsx                # ⭐ Main UI component
│       └── App.css                # ⭐ Styling (dark theme)
│
├── 📂 scripts/                    # Helper Scripts
│   ├── setup_rootfs.sh            # Downloads Alpine Linux rootfs
│   ├── cpu_stress.sh              # CPU stress test workload
│   ├── mem_stress.sh              # Memory stress test workload
│   └── restore.sh                 # Cleanup script
│
├── controller.py                  # CLI entry point (root directory)
├── README.md                      # This file
├── REPORT.md                      # Detailed project report
└── SETUP.md                       # Setup instructions

Total: ~9,000 lines of code across 3 languages
```

---

## ⚡ Execution Flow

### How to Run KernelSight

**Terminal 1 - Backend Server:**
```bash
cd backend
sudo PYTHONPATH=. ./venv/bin/python3 -m kernelsight.api
# Starts: http://localhost:8000
```

**Terminal 2 - Frontend Dashboard:**
```bash
cd dashboard
npm run dev
# Starts: http://localhost:5173
```

**Terminal 3 - CLI (Optional):**
```bash
python3 controller.py
# Interactive terminal interface
```

### What Happens Behind the Scenes

```
1. USER ACTION
   ↓
   User clicks "Create Container" in dashboard
   
2. FRONTEND (React)
   ↓
   axios.post('http://localhost:8000/api/containers', {
     name: 'myapp',
     memory_limit: 256,  // MB
     cpu_limit: 50       // percent
   })
   
3. BACKEND (Python FastAPI)
   ↓
   @app.post("/api/containers")
   def create_container(request):
       wrapper.create_container(name, memory, cpu)
   
4. WRAPPER (Python ctypes)
   ↓
   lib.container_create(
       name.encode('utf-8'),
       memory * 1024 * 1024,  // Convert to bytes
       cpu
   )
   
5. C RUNTIME (Kernel Operations)
   ↓
   • mkdir /sys/fs/cgroup/kernelsight/myapp
   • echo "268435456" > memory.max     // 256 MB
   • echo "50000 100000" > cpu.max     // 50% CPU
   • clone() with CLONE_NEWPID | CLONE_NEWNS | ...
   • pivot_root("/tmp/alpine-rootfs", "/tmp/alpine-rootfs/old")
   
6. LINUX KERNEL
   ↓
   • Creates new namespaces
   • Enforces resource limits
   • Isolates processes
   
7. RESPONSE FLOWS BACK
   ↓
   Kernel → C → Python → FastAPI → React
   
8. DASHBOARD UPDATES
   ↓
   • Shows new container in list
   • Status badge: "Running"
   • Starts real-time metrics via WebSocket
```

---

## 🔧 Core Components Explained

### 1️⃣ C Runtime (The Engine)

**Location:** `runtime/src/`

#### `container.c` - Main Container Logic

```c
int container_create(const char *name, size_t memory_limit, int cpu_limit) {
    // STEP 1: Create cgroup directory for this container
    char cgroup_path[256];
    snprintf(cgroup_path, sizeof(cgroup_path), 
             "/sys/fs/cgroup/kernelsight/%s", name);
    mkdir(cgroup_path, 0755);
    
    // STEP 2: Set memory limit
    // Example: 256 MB = 268435456 bytes
    char memory_file[512];
    snprintf(memory_file, sizeof(memory_file), "%s/memory.max", cgroup_path);
    FILE *f = fopen(memory_file, "w");
    fprintf(f, "%zu", memory_limit);
    fclose(f);
    
    // STEP 3: Set CPU limit
    // Example: 50% = "50000 100000" (50ms out of every 100ms)
    char cpu_file[512];
    snprintf(cpu_file, sizeof(cpu_file), "%s/cpu.max", cgroup_path);
    f = fopen(cpu_file, "w");
    fprintf(f, "%d 100000", cpu_limit * 1000);
    fclose(f);
    
    // STEP 4: Set PID limit (prevent fork bombs)
    char pids_file[512];
    snprintf(pids_file, sizeof(pids_file), "%s/pids.max", cgroup_path);
    f = fopen(pids_file, "w");
    fprintf(f, "100");  // Max 100 processes
    fclose(f);
    
    return 0;
}

int container_start(const char *name) {
    // STEP 1: Fork process with namespace isolation
    pid_t pid = clone(
        container_init,           // Function to run
        stack + STACK_SIZE,       // Stack pointer
        CLONE_NEWPID  |           // New PID namespace
        CLONE_NEWNS   |           // New mount namespace
        CLONE_NEWUTS  |           // New hostname namespace
        CLONE_NEWNET  |           // New network namespace
        CLONE_NEWIPC  |           // New IPC namespace
        SIGCHLD,                  // Signal when child exits
        (void *)name              // Pass container name
    );
    
    // STEP 2: Add process to cgroup
    char procs_file[512];
    snprintf(procs_file, sizeof(procs_file), 
             "/sys/fs/cgroup/kernelsight/%s/cgroup.procs", name);
    FILE *f = fopen(procs_file, "w");
    fprintf(f, "%d", pid);
    fclose(f);
    
    return 0;
}
```

**What this does:**
- **Creates cgroups** = Sets up resource limits
- **Clones process** = Creates isolated environment
- **Assigns PID to cgroup** = Kernel now enforces limits

---

#### `namespace.c` - Isolation Magic

```c
int setup_namespaces() {
    // Create 6 types of namespaces for complete isolation
    
    int flags = CLONE_NEWPID  |  // Separate process IDs
                CLONE_NEWNS   |  // Separate filesystem mounts
                CLONE_NEWUTS  |  // Separate hostname
                CLONE_NEWNET  |  // Separate network stack
                CLONE_NEWIPC  |  // Separate IPC (shared memory)
                CLONE_NEWUSER;   // Separate user IDs
    
    if (unshare(flags) < 0) {
        perror("Failed to create namespaces");
        return -1;
    }
    
    return 0;
}
```

**Real-world example:**

| Namespace | What It Isolates | Example |
|-----------|------------------|---------|
| **PID** | Process IDs | Container sees "PID 1" but host sees "PID 12345" |
| **Mount** | Filesystem | Container can't see `/home` on host |
| **UTS** | Hostname | Container thinks hostname is "myapp" |
| **Network** | Network interfaces | Container has own IP address |
| **IPC** | Shared memory | Container can't access host's shared memory |
| **User** | User/Group IDs | Root in container ≠ root on host |

---

#### `cgroup.c` - Resource Limits

```c
int setup_cgroup_limits(const char *container_name, 
                        size_t memory_bytes,
                        int cpu_percent) {
    char path[512];
    
    // Memory limit example: 256 MB
    snprintf(path, sizeof(path), 
             "/sys/fs/cgroup/kernelsight/%s/memory.max", 
             container_name);
    write_to_file(path, "%zu", memory_bytes);
    
    // CPU limit example: 50% of one core
    // Format: "quota period" in microseconds
    // 50000 50% of 100000 (100ms period)
    snprintf(path, sizeof(path), 
             "/sys/fs/cgroup/kernelsight/%s/cpu.max", 
             container_name);
    write_to_file(path, "%d 100000", cpu_percent * 1000);
    
    // PID limit: Prevent fork bombs
    snprintf(path, sizeof(path), 
             "/sys/fs/cgroup/kernelsight/%s/pids.max", 
             container_name);
    write_to_file(path, "100");
    
    return 0;
}
```

**What happens when limits are exceeded:**

```
Container tries to use 300 MB (limit: 256 MB)
       ↓
Kernel detects violation
       ↓
Kernel's OOM (Out-Of-Memory) Killer activates
       ↓
Sends SIGKILL (signal 9) to container
       ↓
Container terminates with exit code 137
       ↓
Exit code 137 = 128 + 9 (SIGKILL)
```

---

#### `filesystem.c` - Root Filesystem Isolation

```c
int setup_rootfs(const char *rootfs_path) {
    // STEP 1: Change root directory to container's filesystem
    // This is like changing the "/" directory
    if (chroot(rootfs_path) < 0) {
        perror("chroot failed");
        return -1;
    }
    
    // STEP 2: Change working directory to new root
    if (chdir("/") < 0) {
        perror("chdir failed");
        return -1;
    }
    
    // STEP 3: Mount /proc filesystem (for ps, top commands)
    if (mount("proc", "/proc", "proc", 0, NULL) < 0) {
        perror("mount /proc failed");
        return -1;
    }
    
    // STEP 4: Mount /sys filesystem (for system info)
    if (mount("sysfs", "/sys", "sysfs", 0, NULL) < 0) {
        perror("mount /sys failed");
        return -1;
    }
    
    return 0;
}
```

**Before vs After:**

```
BEFORE pivot_root:
Container sees:
  /home/student/container/
  /usr/bin/
  /etc/
  → Full access to host filesystem ❌

AFTER pivot_root:
Container sees:
  /tmp/alpine-rootfs/bin/
  /tmp/alpine-rootfs/usr/
  → Only isolated rootfs ✅
```

---

### 2️⃣ Python Backend (The Bridge)

**Location:** `backend/kernelsight/`

#### `api.py` - FastAPI Server

```python
from fastapi import FastAPI, WebSocket
from kernelsight.wrapper import ContainerWrapper
from kernelsight.metrics import MetricsCollector
import uvicorn
import asyncio

app = FastAPI()
wrapper = ContainerWrapper()
metrics = MetricsCollector()

# REST API Endpoints

@app.get("/api/containers")
async def list_containers():
    """Get list of all containers"""
    return wrapper.list_containers()

@app.post("/api/containers")
async def create_container(name: str, memory_limit: int, cpu_limit: int):
    """
    Create a new container
    
    Args:
        name: Container name (e.g., "myapp")
        memory_limit: Memory limit in MB (e.g., 256)
        cpu_limit: CPU limit in percent (e.g., 50)
    
    Returns:
        {"id": "myapp", "status": "created"}
    """
    try:
        wrapper.create_container(name, memory_limit, cpu_limit)
        return {"id": name, "status": "created"}
    except Exception as e:
        return {"error": str(e)}, 500

@app.post("/api/containers/{id}/start")
async def start_container(id: str):
    """Start a stopped container"""
    wrapper.start_container(id)
    return {"status": "started"}

@app.post("/api/containers/{id}/stop")
async def stop_container(id: str):
    """Stop a running container"""
    wrapper.stop_container(id)
    return {"status": "stopped"}

@app.post("/api/containers/{id}/exec")
async def execute_command(id: str, command: str):
    """
    Execute command inside container
    
    Example commands:
    - "echo Hello World"
    - "Memory Stress" (preset workload)
    - "CPU Spike" (preset workload)
    """
    output = wrapper.exec_container(id, command)
    return {"output": output}

@app.get("/api/containers/{id}/metrics")
async def get_metrics(id: str):
    """Get current resource usage metrics"""
    return metrics.get_metrics(id)

# WebSocket for Real-time Updates

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Stream real-time metrics to dashboard
    Sends updates every 1 second
    """
    await websocket.accept()
    
    try:
        while True:
            # Collect metrics for all containers
            all_metrics = {}
            containers = wrapper.list_containers()
            
            for container in containers:
                if container['status'] == 'running':
                    container_id = container['id']
                    all_metrics[container_id] = metrics.get_metrics(container_id)
            
            # Send to frontend
            await websocket.send_json(all_metrics)
            
            # Wait 1 second before next update
            await asyncio.sleep(1)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Start server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

#### `wrapper.py` - Python ↔ C Bridge

```python
import ctypes
import os
from pathlib import Path

class ContainerWrapper:
    """
    Bridge between Python and C library
    Uses ctypes to call C functions
    """
    
    def __init__(self):
        # Load compiled C library
        lib_path = Path(__file__).parent.parent.parent / "runtime" / "build" / "libcontainer.so"
        self.lib = ctypes.CDLL(str(lib_path))
        
        # Define C function signatures
        # container_create(char *name, size_t memory, int cpu) -> int
        self.lib.container_create.argtypes = [
            ctypes.c_char_p,    # name
            ctypes.c_size_t,    # memory_limit
            ctypes.c_int        # cpu_limit
        ]
        self.lib.container_create.restype = ctypes.c_int
        
        # container_start(char *name) -> int
        self.lib.container_start.argtypes = [ctypes.c_char_p]
        self.lib.container_start.restype = ctypes.c_int
        
        # container_exec(char *name, char *command) -> int
        self.lib.container_exec.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        self.lib.container_exec.restype = ctypes.c_int
    
    def create_container(self, name: str, memory_mb: int, cpu_percent: int):
        """
        Create container
        
        Args:
            name: Container name
            memory_mb: Memory limit in megabytes
            cpu_percent: CPU limit (0-100)
        """
        # Convert Python string to C char*
        name_bytes = name.encode('utf-8')
        
        # Convert MB to bytes
        memory_bytes = memory_mb * 1024 * 1024
        
        # Call C function
        result = self.lib.container_create(
            name_bytes,
            memory_bytes,
            cpu_percent
        )
        
        if result != 0:
            raise Exception(f"Container creation failed: {result}")
    
    def start_container(self, name: str):
        """Start container"""
        name_bytes = name.encode('utf-8')
        result = self.lib.container_start(name_bytes)
        
        if result != 0:
            raise Exception(f"Container start failed: {result}")
    
    def exec_container(self, name: str, command: str):
        """Execute command in container"""
        name_bytes = name.encode('utf-8')
        command_bytes = command.encode('utf-8')
        
        result = self.lib.container_exec(name_bytes, command_bytes)
        return result
```

**Magic happening here:**
```python
# Python code
wrapper.create_container("myapp", 256, 50)
       ↓
# ctypes converts to C
lib.container_create(b"myapp", 268435456, 50)
       ↓
# Calls actual C function
int container_create(const char *name, size_t memory, int cpu)
```

---

#### `metrics.py` - Metrics Collector

```python
import os
from pathlib import Path

class MetricsCollector:
    """
    Reads metrics from cgroup v2 files
    """
    
    def __init__(self):
        self.cgroup_base = Path("/sys/fs/cgroup/kernelsight")
        self.previous_cpu = {}  # For CPU percentage calculation
        self.previous_time = {}
    
    def get_metrics(self, container_id: str):
        """
        Get current resource usage for container
        
        Returns:
            {
                "memory_mb": 50.5,
                "memory_limit_mb": 256,
                "memory_percent": 19.7,
                "cpu_percent": 12.3,
                "process_count": 3
            }
        """
        container_path = self.cgroup_base / container_id
        
        if not container_path.exists():
            return None
        
        metrics = {}
        
        # 1. Memory Usage
        memory_current_file = container_path / "memory.current"
        if memory_current_file.exists():
            with open(memory_current_file) as f:
                memory_bytes = int(f.read().strip())
                metrics['memory_mb'] = memory_bytes / (1024 * 1024)
        
        # 2. Memory Limit
        memory_max_file = container_path / "memory.max"
        if memory_max_file.exists():
            with open(memory_max_file) as f:
                limit_str = f.read().strip()
                if limit_str != "max":
                    limit_bytes = int(limit_str)
                    metrics['memory_limit_mb'] = limit_bytes / (1024 * 1024)
                    metrics['memory_percent'] = (metrics['memory_mb'] / 
                                                 metrics['memory_limit_mb']) * 100
        
        # 3. CPU Usage
        cpu_stat_file = container_path / "cpu.stat"
        if cpu_stat_file.exists():
            with open(cpu_stat_file) as f:
                for line in f:
                    if line.startswith("usage_usec"):
                        # CPU time in microseconds
                        cpu_usec = int(line.split()[1])
                        
                        # Calculate CPU percentage
                        if container_id in self.previous_cpu:
                            delta_cpu = cpu_usec - self.previous_cpu[container_id]
                            delta_time = 1000000  # 1 second in microseconds
                            cpu_percent = (delta_cpu / delta_time) * 100
                            metrics['cpu_percent'] = min(cpu_percent, 100)
                        else:
                            metrics['cpu_percent'] = 0
                        
                        self.previous_cpu[container_id] = cpu_usec
        
        # 4. Process Count
        pids_current_file = container_path / "pids.current"
        if pids_current_file.exists():
            with open(pids_current_file) as f:
                metrics['process_count'] = int(f.read().strip())
        
        return metrics
```

**Where data comes from:**

```bash
# Cgroup files on disk:
/sys/fs/cgroup/kernelsight/myapp/
├── memory.current    # 52428800 (50 MB in bytes)
├── memory.max        # 268435456 (256 MB limit)
├── cpu.stat          # usage_usec 1234567890
├── pids.current      # 3 (three processes)
└── cgroup.procs      # List of PIDs in container
```

---

#### `cli.py` - Terminal UI

```python
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress
from kernelsight.wrapper import ContainerWrapper
from kernelsight.metrics import MetricsCollector
import time

console = Console()
wrapper = ContainerWrapper()
metrics = MetricsCollector()

def display_dashboard():
    """
    Beautiful terminal dashboard with live updates
    """
    
    # Create live display
    with Live(generate_table(), refresh_per_second=1) as live:
        while True:
            live.update(generate_table())
            time.sleep(1)

def generate_table():
    """Generate table with container stats"""
    
    table = Table(title="🐳 KernelSight Containers", 
                  show_header=True,
                  header_style="bold cyan")
    
    table.add_column("Name", style="cyan", width=15)
    table.add_column("Status", style="green", width=10)
    table.add_column("Memory", style="yellow", width=20)
    table.add_column("CPU", style="magenta", width=15)
    table.add_column("Processes", style="blue", width=10)
    
    # Get all containers
    containers = wrapper.list_containers()
    
    for container in containers:
        container_id = container['id']
        m = metrics.get_metrics(container_id)
        
        if m:
            # Memory bar
            memory_bar = create_bar(m['memory_percent'])
            memory_text = f"{memory_bar} {m['memory_mb']:.1f}/{m['memory_limit_mb']:.0f} MB"
            
            # CPU bar
            cpu_bar = create_bar(m['cpu_percent'])
            cpu_text = f"{cpu_bar} {m['cpu_percent']:.1f}%"
            
            # Add row
            table.add_row(
                container['name'],
                f"[green]{container['status']}[/green]",
                memory_text,
                cpu_text,
                str(m['process_count'])
            )
    
    return table

def create_bar(percent):
    """Create ASCII progress bar"""
    filled = int(percent / 10)
    return "█" * filled + "░" * (10 - filled)
```

**Output looks like:**

```
╭────────────────── 🐳 KernelSight Containers ──────────────────╮
│ Name      Status   Memory              CPU            Processes│
├─────────────────────────────────────────────────────────────────┤
│ myapp     running  ████░░░░░░ 102/256  ███░░░░░░░ 30%  5       │
│ database  running  ███████░░░ 180/256  ██░░░░░░░░ 20%  12      │
│ cache     stopped  ░░░░░░░░░░ 0/128    ░░░░░░░░░░ 0%   0       │
╰─────────────────────────────────────────────────────────────────╯
```

---

### 3️⃣ React Dashboard (The Face)

**Location:** `dashboard/src/`

#### `App.jsx` - Main UI Component

```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:8000';

function App() {
  // State management
  const [containers, setContainers] = useState([]);
  const [metrics, setMetrics] = useState({});
  const [ws, setWs] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  
  // On component mount
  useEffect(() => {
    // 1. Fetch initial container list
    fetchContainers();
    
    // 2. Connect to WebSocket for live updates
    connectWebSocket();
    
    // Cleanup on unmount
    return () => {
      if (ws) ws.close();
    };
  }, []);
  
  // Fetch containers from API
  const fetchContainers = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/containers`);
      setContainers(response.data);
    } catch (error) {
      console.error('Failed to fetch containers:', error);
    }
  };
  
  // WebSocket for real-time metrics
  const connectWebSocket = () => {
    const websocket = new WebSocket('ws://localhost:8000/ws');
    
    websocket.onopen = () => {
      console.log('WebSocket connected');
    };
    
    websocket.onmessage = (event) => {
      // Receive metrics every second
      const data = JSON.parse(event.data);
      setMetrics(data);  // Update state → triggers re-render
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    websocket.onclose = () => {
      console.log('WebSocket closed, reconnecting...');
      setTimeout(connectWebSocket, 3000);  // Retry after 3 seconds
    };
    
    setWs(websocket);
  };
  
  // Create new container
  const createContainer = async (name, memoryLimit, cpuLimit) => {
    try {
      await axios.post(`${API_URL}/api/containers`, {
        name: name,
        memory_limit: memoryLimit,
        cpu_limit: cpuLimit
      });
      
      fetchContainers();  // Refresh list
      setShowCreateModal(false);  // Close modal
    } catch (error) {
      console.error('Failed to create container:', error);
    }
  };
  
  // Start container
  const startContainer = async (id) => {
    try {
      await axios.post(`${API_URL}/api/containers/${id}/start`);
      fetchContainers();
    } catch (error) {
      console.error('Failed to start container:', error);
    }
  };
  
  // Stop container
  const stopContainer = async (id) => {
    try {
      await axios.post(`${API_URL}/api/containers/${id}/stop`);
      fetchContainers();
    } catch (error) {
      console.error('Failed to stop container:', error);
    }
  };
  
  // Execute command
  const executeCommand = async (id, command) => {
    try {
      const response = await axios.post(
        `${API_URL}/api/containers/${id}/exec`,
        { command: command }
      );
      console.log('Command output:', response.data.output);
    } catch (error) {
      console.error('Command failed:', error);
    }
  };
  
  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <h1>🐳 KernelSight Dashboard</h1>
        <button onClick={() => setShowCreateModal(true)} className="btn-create">
          ➕ Create Container
        </button>
      </header>
      
      {/* Container Grid */}
      <div className="container-grid">
        {containers.map(container => (
          <ContainerCard 
            key={container.id}
            container={container}
            metrics={metrics[container.id]}
            onStart={() => startContainer(container.id)}
            onStop={() => stopContainer(container.id)}
            onExec={(cmd) => executeCommand(container.id, cmd)}
          />
        ))}
      </div>
      
      {/* Create Modal */}
      {showCreateModal && (
        <CreateContainerModal 
          onCreate={createContainer}
          onClose={() => setShowCreateModal(false)}
        />
      )}
    </div>
  );
}

// Container Card Component
function ContainerCard({ container, metrics, onStart, onStop, onExec }) {
  const [showExecModal, setShowExecModal] = useState(false);
  
  // Default metrics if not running
  const m = metrics || {
    memory_mb: 0,
    memory_limit_mb: container.memory_limit || 256,
    memory_percent: 0,
    cpu_percent: 0,
    process_count: 0
  };
  
  return (
    <div className="container-card">
      {/* Header */}
      <div className="card-header">
        <h3>{container.name}</h3>
        <span className={`status-badge ${container.status}`}>
          {container.status}
        </span>
      </div>
      
      {/* Metrics */}
      <div className="metrics">
        {/* Memory Usage */}
        <div className="metric">
          <label>Memory</label>
          <div className="progress-bar">
            <div 
              className="progress-fill memory"
              style={{ width: `${m.memory_percent}%` }}
            />
          </div>
          <span className="metric-value">
            {m.memory_mb.toFixed(1)} / {m.memory_limit_mb} MB 
            ({m.memory_percent.toFixed(1)}%)
          </span>
        </div>
        
        {/* CPU Usage */}
        <div className="metric">
          <label>CPU</label>
          <div className="progress-bar">
            <div 
              className="progress-fill cpu"
              style={{ width: `${m.cpu_percent}%` }}
            />
          </div>
          <span className="metric-value">
            {m.cpu_percent.toFixed(1)}%
          </span>
        </div>
        
        {/* Process Count */}
        <div className="metric">
          <label>Processes</label>
          <span className="metric-value">{m.process_count}</span>
        </div>
      </div>
      
      {/* Action Buttons */}
      <div className="card-actions">
        {container.status === 'running' ? (
          <>
            <button onClick={onStop} className="btn-danger">
              ⏹ Stop
            </button>
            <button onClick={() => setShowExecModal(true)} className="btn-primary">
              ▶ Execute
            </button>
          </>
        ) : (
          <button onClick={onStart} className="btn-success">
            ▶ Start
          </button>
        )}
      </div>
      
      {/* Execute Command Modal */}
      {showExecModal && (
        <ExecuteModal 
          containerName={container.name}
          onExecute={onExec}
          onClose={() => setShowExecModal(false)}
        />
      )}
    </div>
  );
}

// Execute Command Modal
function ExecuteModal({ containerName, onExecute, onClose }) {
  const [selectedWorkload, setSelectedWorkload] = useState('');
  const [customCommand, setCustomCommand] = useState('');
  
  const workloads = [
    { id: 'variable', name: 'Variable CPU Load', icon: '📊' },
    { id: 'memory', name: 'Memory Stress (50MB)', icon: '💾' },
    { id: 'cpu_spike', name: 'CPU Spike Pattern', icon: '⚡' },
    { id: 'gradual', name: 'Gradual Increase', icon: '📈' },
    { id: 'normal', name: 'Normal Workload', icon: '✓' },
    { id: 'custom', name: 'Custom Command', icon: '⌨' }
  ];
  
  const handleExecute = () => {
    if (selectedWorkload === 'custom') {
      onExecute(customCommand);
    } else {
      onExecute(selectedWorkload);
    }
    onClose();
  };
  
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <h2>Execute Command in {containerName}</h2>
        
        <div className="workload-grid">
          {workloads.map(workload => (
            <button
              key={workload.id}
              className={`workload-btn ${selectedWorkload === workload.id ? 'selected' : ''}`}
              onClick={() => setSelectedWorkload(workload.id)}
            >
              <span className="workload-icon">{workload.icon}</span>
              <span className="workload-name">{workload.name}</span>
            </button>
          ))}
        </div>
        
        {selectedWorkload === 'custom' && (
          <input 
            type="text"
            placeholder="Enter command..."
            value={customCommand}
            onChange={e => setCustomCommand(e.target.value)}
            className="custom-input"
          />
        )}
        
        <div className="modal-actions">
          <button onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button onClick={handleExecute} className="btn-primary">
            Execute
          </button>
        </div>
      </div>
    </div>
  );
}

// Create Container Modal
function CreateContainerModal({ onCreate, onClose }) {
  const [name, setName] = useState('');
  const [memory, setMemory] = useState(256);
  const [cpu, setCpu] = useState(50);
  
  const handleCreate = () => {
    if (name.trim()) {
      onCreate(name, memory, cpu);
    }
  };
  
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <h2>Create New Container</h2>
        
        <div className="form-group">
          <label>Container Name</label>
          <input 
            type="text"
            placeholder="myapp"
            value={name}
            onChange={e => setName(e.target.value)}
          />
        </div>
        
        <div className="form-group">
          <label>Memory Limit: {memory} MB</label>
          <input 
            type="range"
            min="64"
            max="1024"
            step="64"
            value={memory}
            onChange={e => setMemory(Number(e.target.value))}
          />
        </div>
        
        <div className="form-group">
          <label>CPU Limit: {cpu}%</label>
          <input 
            type="range"
            min="10"
            max="100"
            step="10"
            value={cpu}
            onChange={e => setCpu(Number(e.target.value))}
          />
        </div>
        
        <div className="modal-actions">
          <button onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button onClick={handleCreate} className="btn-primary">
            Create
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
```

---

#### `App.css` - Styling

```css
/* Dark theme with neon accents */

:root {
  --bg-primary: #0a0e27;
  --bg-secondary: #1a1f3a;
  --bg-card: #252b48;
  --text-primary: #e0e0e0;
  --text-secondary: #a0a0a0;
  --accent-cyan: #00ffff;
  --accent-purple: #a78bfa;
  --accent-green: #10b981;
  --accent-red: #ef4444;
  --accent-yellow: #fbbf24;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
  color: var(--text-primary);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  min-height: 100vh;
}

.app {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

/* Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 3rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(0, 255, 255, 0.2);
}

.header h1 {
  font-size: 2.5rem;
  background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Container Grid */
.container-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

/* Container Card */
.container-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(0, 255, 255, 0.2);
  border-radius: 12px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.container-card:hover {
  border-color: var(--accent-cyan);
  transform: translateY(-4px);
  box-shadow: 0 8px 32px rgba(0, 255, 255, 0.2);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.card-header h3 {
  font-size: 1.25rem;
  color: var(--accent-cyan);
}

/* Status Badge */
.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-badge.running {
  background: rgba(16, 185, 129, 0.2);
  color: var(--accent-green);
  border: 1px solid var(--accent-green);
}

.status-badge.stopped {
  background: rgba(239, 68, 68, 0.2);
  color: var(--accent-red);
  border: 1px solid var(--accent-red);
}

/* Metrics */
.metrics {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.metric {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.metric label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
}

/* Progress Bar */
.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 4px;
  position: relative;
  overflow: hidden;
}

.progress-fill.memory {
  background: linear-gradient(90deg, var(--accent-cyan), var(--accent-purple));
}

.progress-fill.cpu {
  background: linear-gradient(90deg, var(--accent-green), var(--accent-yellow));
}

/* Animated gradient */
.progress-fill::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  animation: shimmer 2s infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.metric-value {
  font-size: 0.875rem;
  color: var(--text-primary);
  font-family: 'JetBrains Mono', monospace;
}

/* Buttons */
button {
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 0.875rem;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-success {
  background: var(--accent-green);
  color: white;
}

.btn-danger {
  background: var(--accent-red);
  color: white;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-primary);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Card Actions */
.card-actions {
  display: flex;
  gap: 0.75rem;
}

.card-actions button {
  flex: 1;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: var(--bg-card);
  border: 1px solid rgba(0, 255, 255, 0.3);
  border-radius: 16px;
  padding: 2rem;
  min-width: 500px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}

.modal h2 {
  margin-bottom: 1.5rem;
  color: var(--accent-cyan);
}

/* Responsive Design */
@media (max-width: 768px) {
  .container-grid {
    grid-template-columns: 1fr;
  }
  
  .modal {
    min-width: auto;
    width: 90vw;
  }
}
```

---

## 🔑 Key Concepts with Examples

### 1. Namespaces - The Isolation Magic

**What are namespaces?**
Namespaces create separate "views" of system resources. Each container sees its own isolated version.

**The 6 Types:**

#### PID Namespace (Process Isolation)
```
HOST VIEW:
  PID 1     → systemd (init)
  PID 1234  → bash
  PID 1235  → python api.py
  PID 12345 → Container process (sees as PID 1)

CONTAINER VIEW:
  PID 1     → /bin/sh (thinks it's init!)
  PID 2     → stress command
  PID 3     → another process
  
Container can't see host processes!
```

#### Mount Namespace (Filesystem Isolation)
```
HOST VIEW:
  / (root)
  ├── /home
  ├── /usr
  ├── /var
  └── /tmp
      └── alpine-rootfs/  ← Container's root

CONTAINER VIEW:
  / (root) = /tmp/alpine-rootfs
  ├── /bin
  ├── /usr
  ├── /lib
  └── /tmp
  
Container thinks /tmp/alpine-rootfs is the entire filesystem!
```

#### Network Namespace (Network Isolation)
```
HOST:
  eth0: 192.168.1.100
  lo: 127.0.0.1

CONTAINER:
  eth0: 172.17.0.2 (separate IP!)
  lo: 127.0.0.1
  
Container has its own network stack, can have own firewall rules!
```

---

### 2. Cgroups - The Resource Police

**What are cgroups?**
Control Groups (cgroups) limit and monitor resource usage. Think of them as "budget limits" enforced by the kernel.

#### Memory Limit Example
```bash
# Set limit
echo "268435456" > /sys/fs/cgroup/kernelsight/myapp/memory.max
# That's 256 MB in bytes

# What happens:
Container uses 100 MB → ✅ OK
Container uses 200 MB → ✅ OK
Container uses 250 MB → ✅ OK, but close to limit
Container tries 300 MB → ❌ KILLED by OOM killer!

# Kernel sends:
SIGKILL (signal 9) → Process exits with code 137
```

#### CPU Limit Example
```bash
# Set limit to 50% of one CPU core
echo "50000 100000" > /sys/fs/cgroup/kernelsight/myapp/cpu.max
#      ^quota  ^period (both in microseconds)
# Means: 50ms out of every 100ms period

# What happens:
Container gets 50ms → Works normally
Container wants more → ⏸ Throttled! Must wait for next period
Container gets 50ms → Works again
```

#### PID Limit Example
```bash
# Set limit
echo "100" > /sys/fs/cgroup/kernelsight/myapp/pids.max

# Prevents fork bombs:
while true; do
  ./malicious_script &  # Tries to create infinite processes
done

# After 100 processes:
❌ fork() fails with error: "Resource temporarily unavailable"
System remains stable! ✅
```

---

### 3. pivot_root - The Security Door

**What is pivot_root?**
Changes what "/" (root directory) means for a process. Like moving to a new house where you can't access your old house's files.

```c
// Before pivot_root
getcwd() → "/home/student/container"
ls /      → Shows entire host filesystem

// Execute pivot_root
pivot_root("/tmp/alpine-rootfs", "/tmp/alpine-rootfs/old");

// After pivot_root
getcwd() → "/"  (but it's actually /tmp/alpine-rootfs)
ls /      → Only shows alpine-rootfs contents
ls /old   → Old root (usually unmounted immediately)

// Container is now jailed! 🔒
```

---

## 🚀 Quick Start Guide

### Prerequisites

```bash
# Check kernel version (need 5.0+)
uname -r
# Output: 5.15.0-91-generic ✅

# Check if cgroup v2 is enabled
mount | grep cgroup
# Should see: cgroup2 on /sys/fs/cgroup type cgroup2

# Install dependencies
sudo apt update
sudo apt install -y build-essential python3 python3-pip nodejs npm
```

### Installation

```bash
# 1. Clone repository
git clone https://github.com/yourusername/kernelsight.git
cd kernelsight

# 2. Build C runtime
cd runtime
make
cd ..

# 3. Setup root filesystem (downloads Alpine Linux mini rootfs)
sudo bash scripts/setup_rootfs.sh
# This creates /tmp/alpine-rootfs/

# 4. Setup Python backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 5. Install dashboard dependencies
cd dashboard
npm install
cd ..
```

### Running

**Terminal 1 - Start Backend:**
```bash
cd backend
sudo PYTHONPATH=. ./venv/bin/python3 -m kernelsight.api

# Output:
# INFO:     Started server process [12345]
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Start Dashboard:**
```bash
cd dashboard
npm run dev

# Output:
# VITE v5.0.0  ready in 300 ms
# ➜  Local:   http://localhost:5173/
```

**Terminal 3 - CLI (Optional):**
```bash
python3 controller.py

# Shows interactive menu
```

### First Container

1. Open http://localhost:5173 in browser
2. Click "➕ Create Container"
3. Enter:
   - Name: `myapp`
   - Memory: `256 MB`
   - CPU: `50%`
4. Click "Create"
5. Click "▶ Start" on the container card
6. Watch real-time metrics update!

---

## 💥 Real-World Example: Memory Stress Test

Let's walk through what happens when you run a memory stress test.

### Step 1: User Clicks "Execute" → "Memory Stress"

**Frontend sends:**
```javascript
axios.post('http://localhost:8000/api/containers/myapp/exec', {
  command: 'Memory Stress'
})
```

### Step 2: Backend Translates Command

```python
# api.py receives "Memory Stress"
# Translates to actual shell script:
command = """
echo '[Memory Stress] Allocating 50MB'
rm -rf /tmp/memstress
mkdir -p /tmp/memstress
i=0
while [ $i -lt 50 ]; do
  yes AAAAAAAAAAAAAAAA | head -c 1048576 > /tmp/memstress/block$i
  i=$((i+1))
  echo "Allocated $i MB"
done
echo '[Done]'
"""
```

### Step 3: C Runtime Executes in Container

```c
// wrapper calls C function
container_exec("myapp", command);

// C code:
1. Finds container's PID
2. Uses setns() to join container's namespaces
3. Executes command via execve("/bin/sh", ...)
```

### Step 4: Inside Container - Script Runs

```bash
# Inside container namespace

# Create directory
mkdir -p /tmp/memstress

# Loop 50 times
for i in 1 2 3 ... 50; do
  # Generate 1 MB of data
  yes AAAAAAAAAAAAAAAA | head -c 1048576 > /tmp/memstress/block$i
  # This creates a 1 MB file, using actual RAM
  
  echo "Allocated $i MB"
done
```

### Step 5: Kernel Tracks Memory Usage

```bash
# Cgroup automatically tracks memory
cat /sys/fs/cgroup/kernelsight/myapp/memory.current
# Output grows:
# 1048576     (1 MB)
# 2097152     (2 MB)
# ...
# 52428800    (50 MB)
```

### Step 6: Metrics Collector Reads Data

```python
# metrics.py reads cgroup file
with open('/sys/fs/cgroup/kernelsight/myapp/memory.current') as f:
    bytes_used = int(f.read())
    mb_used = bytes_used / (1024 * 1024)
    # mb_used = 50.0
```

### Step 7: WebSocket Broadcasts Update

```python
# api.py sends via WebSocket
await websocket.send_json({
    "myapp": {
        "memory_mb": 50.0,
        "memory_limit_mb": 256,
        "memory_percent": 19.5,
        "cpu_percent": 2.3
    }
})
```

### Step 8: Dashboard Updates in Real-time

```javascript
// React receives WebSocket message
websocket.onmessage = (event) => {
  const data = JSON.parse(event.data);
  setMetrics(data);  // State update → re-render
};

// UI updates:
// Progress bar animates to 19.5%
// Text shows "50.0 / 256 MB"
```

### Step 9: What if We Exceed Limit?

```bash
# If container tries to allocate 300 MB (limit: 256 MB)

# Kernel's OOM killer activates:
1. Detects memory.current > memory.max
2. Chooses process to kill (usually the biggest memory user)
3. Sends SIGKILL (signal 9)
4. Process terminates immediately
5. Exit code: 137 (128 + 9)

# Container status changes to "stopped"
# Error logged: "exit code 137 - killed by OOM"
```

---

## 📊 Metrics & Monitoring

### What Gets Monitored?

| Metric | Source | Update Frequency | Purpose |
|--------|--------|-----------------|---------|
| **Memory Usage** | `memory.current` | 1 second | Track RAM consumption |
| **Memory Limit** | `memory.max` | Static | Show maximum allowed |
| **CPU Usage** | `cpu.stat` | 1 second | Track CPU time used |
| **CPU Limit** | `cpu.max` | Static | Show throttle limit |
| **Process Count** | `pids.current` | 1 second | Monitor active processes |
| **Container Status** | Internal state | On change | Running/Stopped/Created |

### Real-time Visualization

**Dashboard features:**
- **Live graphs:** CPU and memory over time
- **Progress bars:** Visual representation of usage vs limits
- **Color coding:**
  - 🟢 Green (0-50%): Healthy
  - 🟡 Yellow (50-80%): Warning
  - 🔴 Red (80-100%): Critical
- **WebSocket updates:** No page refresh needed
- **Historical data:** View trends over time

---

## 🛠️ Technology Stack

### Backend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Runtime** | C (GCC) | Low-level container operations |
| **System Calls** | Linux Kernel API | Namespaces, cgroups, pivot_root |
| **API Server** | Python + FastAPI | REST endpoints + WebSocket |
| **Metrics** | Python + cgroup files | Resource monitoring |
| **CLI** | Python + Rich | Terminal user interface |
| **Interop** | ctypes | Python ↔ C bridge |

### Frontend

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | React 18 | UI components |
| **Build Tool** | Vite | Fast development server |
| **HTTP Client** | Axios | API requests |
| **WebSocket** | Native WebSocket API | Real-time updates |
| **Styling** | CSS3 + Gradients | Dark theme with neon accents |
| **Charts** | Custom CSS animations | Progress bars and graphs |

### System Requirements

- **OS:** Linux (kernel 5.0+)
- **Cgroups:** v2 (unified hierarchy)
- **Permissions:** Root/sudo access
- **Memory:** 2 GB RAM minimum
- **Disk:** 500 MB for rootfs

---

## 🎓 Learning Outcomes

After studying KernelSight, you will understand:

### 1. Linux Kernel Internals
- How namespaces provide isolation
- How cgroups enforce resource limits
- How processes are created and managed
- System call interface (clone, unshare, setns)

### 2. Container Technology
- How Docker actually works under the hood
- Why containers are lighter than VMs
- How resource limits are enforced
- Container security model

### 3. System Programming
- C programming with kernel APIs
- Memory management
- Process lifecycle
- Error handling in system calls

### 4. Backend Development
- REST API design
- WebSocket for real-time communication
- Python-C interoperability
- Metrics collection and aggregation

### 5. Frontend Development
- React state management
- Real-time data visualization
- WebSocket client implementation
- Responsive UI design

### 6. DevOps Concepts
- Container orchestration basics
- Resource monitoring and alerting
- Performance metrics
- System administration

---

## 📚 Additional Resources

### Documentation Files

- [SETUP.md](SETUP.md) - Detailed setup instructions
- [REPORT.md](REPORT.md) - Project report and analysis
- [WORKLOAD_COMMANDS.md](WORKLOAD_COMMANDS.md) - Available workload commands
- [ZSCORE_DOCUMENTATION.md](ZSCORE_DOCUMENTATION.md) - Anomaly detection details

### Learn More

- **Linux Namespaces:** `man namespaces`
- **Cgroups v2:** [kernel.org/doc/cgroups-v2](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html)
- **Container Internals:** [Docker's container architecture](https://docs.docker.com/get-started/overview/)

---

## 🎯 Project Statistics

```
📊 Code Statistics:
├── Total Lines: ~9,000
├── Languages: 3 (C, Python, JavaScript)
├── Components: 3 (Runtime, Backend, Frontend)
├── API Endpoints: 8
├── React Components: 5
└── C Source Files: 6

⚙️ Features:
├── Container Lifecycle: Create, Start, Stop, Delete
├── Resource Limits: Memory, CPU, PID
├── Namespaces: PID, Mount, UTS, Network, IPC, User
├── Monitoring: Real-time metrics via WebSocket
├── CLI: Interactive terminal interface
├── Dashboard: Web-based visual interface
└── Workloads: 6 preset stress tests

🔒 Security:
├── Process Isolation: ✅
├── Filesystem Isolation: ✅
├── Network Isolation: ✅
├── Resource Limits: ✅
└── Root Filesystem Jail: ✅
```

---

## 🤝 Contributing

This is an educational project. Contributions welcome for:
- Additional workload patterns
- UI improvements
- Documentation enhancements
- Bug fixes

---

## 📄 License

MIT License - Free for educational use

---

## 👨‍💻 Author

Built as an educational project to understand container technology from first principles.

---

## 🙏 Acknowledgments

- Linux kernel developers for amazing APIs
- Docker for pioneering container technology
- FastAPI and React communities for excellent frameworks

---

**⭐ Star this repo if you found it helpful for learning!**

**📖 Perfect for presentations, teaching, and understanding container internals**
