# 🐳 MiniContainer

A lightweight container management system built from scratch using Linux cgroups v2 and namespaces. Features an interactive CLI and real-time monitoring dashboard.

## Features

- **Container Isolation**: PID, Mount, UTS, IPC, and Cgroup namespaces
- **Resource Limits**: CPU, Memory, and PID limits via cgroups v2
- **Interactive CLI**: Rich terminal interface with live stats
- **Web Dashboard**: Real-time metrics with WebSocket updates
- **Lightweight**: Minimal dependencies, educational codebase

## Quick Start

### Prerequisites

- Linux kernel 5.0+ with cgroup v2
- GCC for C compilation
- Python 3.9+
- Node.js 18+ (for dashboard)
- Root/sudo access for container operations

### Build & Install

```bash
# 1. Build the C runtime
cd runtime && make && cd ..

# 2. Setup the root filesystem (Required for isolation)
sudo bash scripts/setup_rootfs.sh

# 3. Setup Python backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# 4. Install dashboard dependencies
cd dashboard && npm install && cd ..
```

### Usage

#### CLI Commands

```bash
# Create a container
minicontainer create --name myapp --memory 256m --cpus 0.5

# Start/stop containers
minicontainer start myapp
minicontainer stop myapp

# List containers
minicontainer ps

# Live resource monitoring
minicontainer stats

# Run one-shot container
minicontainer run --name test --cmd "echo Hello World"

# Start dashboard
minicontainer dashboard
```

#### Dashboard

```bash
# Start the backend API
cd backend
python -m minicontainer.api

# In another terminal, start the React dashboard
cd dashboard
npm run dev

# Open http://localhost:5173
```

## Architecture

```
minicontainer/
├── runtime/          # C container runtime
│   ├── include/      # Header files
│   ├── src/          # Source files (namespace, cgroup, filesystem)
│   └── cli/          # C CLI for testing
├── backend/          # Python backend
│   └── minicontainer/
│       ├── cli.py    # Rich CLI
│       ├── api.py    # FastAPI + WebSocket
│       ├── wrapper.py # C library bindings
│       └── metrics.py # Cgroup metrics collector
└── dashboard/        # React frontend
    └── src/
        └── App.jsx   # Dashboard UI
```

## How It Works

### Container Creation

1. **Clone with namespaces**: Uses `clone()` syscall with flags like `CLONE_NEWPID`, `CLONE_NEWNS`
2. **Setup cgroup**: Creates a cgroup in `/sys/fs/cgroup/minicontainer/<id>`
3. **Apply limits**: Writes to `memory.max`, `cpu.max`, `pids.max`
4. **Pivot root**: Changes filesystem root to isolated rootfs
5. **Execute command**: Runs the specified command as PID 1 inside container

### Metrics Collection

Reads from cgroup v2 files:
- `memory.current` - Current memory usage
- `cpu.stat` - CPU time consumed  
- `pids.current` - Number of processes

## Requirements

| Component | Requirement |
|-----------|-------------|
| Kernel | Linux 5.0+ |
| Cgroups | v2 (unified hierarchy) |
| Root | Required for namespaces |

## License

MIT License - Educational project for learning container internals.
