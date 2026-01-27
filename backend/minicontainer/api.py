"""MiniContainer - FastAPI Backend with Real Metrics Only"""

import asyncio
import os
import subprocess
import json
import time
from typing import List, Optional
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

from .wrapper import manager, Container
from .metrics import collector

# Pydantic models
class ContainerCreate(BaseModel):
    name: str
    rootfs: Optional[str] = "/tmp/alpine-rootfs"
    memory_limit: Optional[int] = 268435456  # 256MB default
    cpu_percent: Optional[int] = 50
    pids_max: Optional[int] = 100

class ContainerResponse(BaseModel):
    id: str
    name: str
    state: str
    pid: int

# WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections[:]:
            try:
                await connection.send_json(message)
            except:
                self.disconnect(connection)

ws_manager = ConnectionManager()

# Runtime path
RUNTIME_PATH = Path("/home/student/.gemini/antigravity/scratch/minicontainer/runtime/build/minicontainer-runtime")
CGROUP_BASE = Path("/sys/fs/cgroup/minicontainer")
DASHBOARD_DIST = Path("/home/student/.gemini/antigravity/scratch/minicontainer/dashboard/dist")

def run_runtime_command(args: List[str]) -> tuple:
    """Run the C runtime CLI and return output"""
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(RUNTIME_PATH.parent)
    
    try:
        result = subprocess.run(
            ["sudo", str(RUNTIME_PATH)] + args,
            capture_output=True, text=True, timeout=30, env=env
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def get_running_containers():
    """Get list of containers from state files with accurate state detection"""
    containers = []
    state_dir = Path("/var/lib/minicontainer/containers")
    
    if state_dir.exists():
        for container_dir in state_dir.iterdir():
            if container_dir.is_dir():
                state_file = container_dir / "state.txt"
                if state_file.exists():
                    data = {}
                    try:
                        for line in state_file.read_text().splitlines():
                            if "=" in line:
                                key, val = line.split("=", 1)
                                data[key] = val
                        
                        cid = data.get("id", container_dir.name)
                        stored_state = data.get("state", "unknown")
                        pid = int(data.get("pid", 0))
                        
                        # Determine actual state by checking cgroup
                        actual_state = "created"
                        cgroup_path = CGROUP_BASE / cid
                        cgroup_procs = cgroup_path / "cgroup.procs"
                        
                        if cgroup_procs.exists():
                            procs = cgroup_procs.read_text().strip()
                            if procs:
                                # Has active processes in cgroup
                                actual_state = "running"
                            else:
                                # Cgroup exists but no processes
                                actual_state = "stopped"
                        elif pid > 0:
                            # Check if PID is still running
                            try:
                                os.kill(pid, 0)
                                actual_state = "running"
                            except (ProcessLookupError, PermissionError):
                                actual_state = "stopped"
                        
                        containers.append({
                            "id": cid,
                            "name": data.get("name", container_dir.name),
                            "state": actual_state,
                            "pid": pid
                        })
                    except:
                        pass
    
    return containers

# Metrics broadcast task - REAL METRICS ONLY
async def metrics_broadcast_task():
    """Periodically broadcast real metrics to WebSocket clients"""
    prev_cpu = {}
    prev_time = {}
    
    while True:
        if ws_manager.active_connections:
            containers = get_running_containers()
            metrics_by_id = {}
            
            for c in containers:
                cid = c["id"]
                current_time = time.time()
                
                # Get real metrics from cgroup only
                cgroup = CGROUP_BASE / cid
                mem = 0
                cpu_usec = 0
                pids = 0
                mem_limit = 268435456
                
                if cgroup.exists():
                    try:
                        mem = int((cgroup / "memory.current").read_text().strip())
                    except:
                        pass
                    try:
                        val = (cgroup / "memory.max").read_text().strip()
                        if val != "max":
                            mem_limit = int(val)
                    except:
                        pass
                    try:
                        pids = int((cgroup / "pids.current").read_text().strip())
                    except:
                        pass
                    try:
                        for line in (cgroup / "cpu.stat").read_text().splitlines():
                            if line.startswith("usage_usec"):
                                cpu_usec = int(line.split()[1])
                                break
                    except:
                        pass
                
                # Calculate CPU percentage from delta
                cpu_percent = 0
                if cid in prev_cpu and prev_cpu[cid] > 0:
                    cpu_delta = cpu_usec - prev_cpu[cid]
                    time_delta = current_time - prev_time.get(cid, current_time)
                    if time_delta > 0:
                        cpu_percent = (cpu_delta / (time_delta * 1e6)) * 100
                
                prev_cpu[cid] = cpu_usec
                prev_time[cid] = current_time
                
                # Real metrics only - no simulation
                metrics_by_id[cid] = {
                    "cpu_percent": cpu_percent,
                    "memory_bytes": mem,
                    "memory_percent": (mem / mem_limit * 100) if mem_limit > 0 else 0,
                    "memory_limit_bytes": mem_limit,
                    "pids": pids
                }
            
            payload = {
                "type": "metrics",
                "timestamp": time.time(),
                "containers": containers,
                "metrics": metrics_by_id
            }
            await ws_manager.broadcast(payload)
        await asyncio.sleep(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    collector.start(interval=1.0)
    task = asyncio.create_task(metrics_broadcast_task())
    yield
    task.cancel()
    collector.stop()

app = FastAPI(title="MiniContainer API", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets from dashboard dist
if DASHBOARD_DIST.exists() and (DASHBOARD_DIST / "assets").exists():
    app.mount("/assets", StaticFiles(directory=DASHBOARD_DIST / "assets"), name="assets")

@app.get("/")
def root():
    """Serve the dashboard"""
    index_file = DASHBOARD_DIST / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"name": "MiniContainer API", "version": "1.0.0", "dashboard": "Run 'npm run build' in dashboard folder"}

@app.get("/api/containers", response_model=List[ContainerResponse])
def list_containers():
    """List all containers"""
    containers = get_running_containers()
    return [ContainerResponse(**c) for c in containers]

@app.get("/api/containers/{container_id}")
def get_container(container_id: str):
    """Get container details"""
    for c in get_running_containers():
        if c["id"] == container_id or c["id"].startswith(container_id):
            return c
    raise HTTPException(status_code=404, detail="Container not found")

@app.post("/api/containers", response_model=ContainerResponse)
def create_container(config: ContainerCreate):
    """Create a new container (without starting a command)"""
    
    create_args = ["create", "--name", config.name]
    
    if config.rootfs:
        create_args.extend(["--rootfs", config.rootfs])
    if config.memory_limit:
        create_args.extend(["--memory", str(config.memory_limit)])
    if config.cpu_percent:
        create_args.extend(["--cpus", str(config.cpu_percent)])
    if config.pids_max:
        create_args.extend(["--pids", str(config.pids_max)])
    
    code, stdout, stderr = run_runtime_command(create_args)
    if code != 0:
        raise HTTPException(status_code=500, detail=f"Failed to create container: {stderr}")
    
    # Parse container ID from output
    container_id = config.name
    for line in stdout.splitlines():
        if "Created container:" in line:
            container_id = line.split(":")[-1].strip()
            break
    
    # Get PID from state file
    pid = 0
    try:
        state_file = Path(f"/var/lib/minicontainer/containers/{container_id}/state.txt")
        if state_file.exists():
            for line in state_file.read_text().splitlines():
                if line.startswith("pid="):
                    pid = int(line.split("=")[1])
                    break
    except:
        pass
    
    return ContainerResponse(id=container_id, name=config.name, state="created", pid=pid)

@app.post("/api/containers/{container_id}/start")
def start_container(container_id: str):
    """Start a container"""
    code, stdout, stderr = run_runtime_command(["start", container_id])
    return {"status": "started" if code == 0 else "failed"}

@app.post("/api/containers/{container_id}/stop")
def stop_container(container_id: str):
    """Stop a container"""
    # Find container to get PID
    containers = get_running_containers()
    for c in containers:
        if c["id"] == container_id or c["id"].startswith(container_id) or c["name"] == container_id:
            if c["pid"] > 0:
                os.system(f"sudo kill -9 {c['pid']} 2>/dev/null")
            break
    
    run_runtime_command(["stop", container_id])
    return {"status": "stopped"}

@app.delete("/api/containers/{container_id}")
def delete_container(container_id: str):
    """Delete a container"""
    try:
        stop_container(container_id)
    except:
        pass
    
    code, stdout, stderr = run_runtime_command(["delete", container_id])
    if code != 0:
        raise HTTPException(status_code=500, detail=f"Failed to delete: {stderr}")
    return {"status": "deleted"}

@app.post("/api/containers/{container_id}/exec")
async def exec_in_container(container_id: str, request: Request):
    """Execute a command in a container's cgroup"""
    try:
        body = await request.json()
        command = body.get("command", "echo Hello")
    except:
        command = "echo Hello"
    
    cgroup_path = CGROUP_BASE / container_id
    
    # Ensure cgroup exists
    if not cgroup_path.exists():
        cgroup_path.mkdir(parents=True, exist_ok=True)
        # Setup cgroup subtree control
        subprocess.run(
            f"echo '+cpu +memory +pids' | sudo tee /sys/fs/cgroup/minicontainer/cgroup.subtree_control",
            shell=True, capture_output=True
        )
    
    # Run command in background in the cgroup
    run_script = f'''
echo $$ > {cgroup_path}/cgroup.procs 2>/dev/null
{command}
'''
    
    # Use Popen to run in background without blocking
    import threading
    def run_command():
        try:
            subprocess.run(
                ["sudo", "bash", "-c", run_script],
                capture_output=True, text=True, timeout=600
            )
        except:
            pass
    
    thread = threading.Thread(target=run_command, daemon=True)
    thread.start()
    
    return {"status": "started", "message": f"Command started in container {container_id}"}

@app.get("/api/containers/{container_id}/metrics")
def get_container_metrics(container_id: str):
    """Get metrics for a container"""
    cgroup = CGROUP_BASE / container_id
    metrics = {"cpu_percent": 0, "memory_bytes": 0, "memory_limit_bytes": 0, "pids": 0}
    
    if cgroup.exists():
        try:
            metrics["memory_bytes"] = int((cgroup / "memory.current").read_text().strip())
            val = (cgroup / "memory.max").read_text().strip()
            metrics["memory_limit_bytes"] = 0 if val == "max" else int(val)
            metrics["pids"] = int((cgroup / "pids.current").read_text().strip())
        except:
            pass
    
    history = collector.get_history(container_id)
    return {
        "current": metrics,
        "history": [{"timestamp": p.timestamp, "cpu_percent": p.cpu_percent, 
                     "memory_bytes": p.memory_bytes} for p in history[-30:]]
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics"""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
