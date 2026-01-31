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
from .ml import detector
from .storage import metrics_storage, process_inspector

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
    prev_throttle = {}
    
    while True:
        if ws_manager.active_connections:
            containers = get_running_containers()
            metrics_by_id = {}
            
            for c in containers:
                cid = c["id"]
                current_time = time.time()
                
                # If container is stopped, still read cpu_usec from cgroup (it persists)
                if c.get("state") != "running":
                    cgroup = CGROUP_BASE / cid
                    cpu_usec = 0
                    # Read CPU time even for stopped containers
                    if cgroup.exists():
                        try:
                            for line in (cgroup / "cpu.stat").read_text().splitlines():
                                if line.startswith("usage_usec"):
                                    cpu_usec = int(line.split()[1])
                                    break
                        except:
                            pass
                    metrics_by_id[cid] = {
                        "cpu_percent": 0,
                        "cpu_usec": cpu_usec,  # Include CPU time even when stopped
                        "memory_bytes": 0,
                        "memory_percent": 0,
                        "memory_limit_bytes": 268435456,
                        "pids": 0,
                        "init_pid": 0
                    }
                    continue
                
                # Get real metrics from cgroup only
                cgroup = CGROUP_BASE / cid
                mem = 0
                cpu_usec = 0
                pids = 0
                mem_limit = 268435456
                throttle_count = 0
                
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
                            elif line.startswith("nr_throttled "):
                                throttle_count = int(line.split()[1])
                    except:
                        pass
                
                # Detect if container is being throttled
                is_throttled = False
                if cid in prev_throttle:
                    throttle_delta = throttle_count - prev_throttle[cid]
                    is_throttled = throttle_delta > 0
                prev_throttle[cid] = throttle_count
                
                # Calculate CPU percentage from delta
                cpu_percent = 0
                if cid in prev_cpu and prev_cpu[cid] > 0:
                    cpu_delta = cpu_usec - prev_cpu[cid]
                    time_delta = current_time - prev_time.get(cid, current_time)
                    if time_delta > 0:
                        cpu_percent = (cpu_delta / (time_delta * 1e6)) * 100
                
                prev_cpu[cid] = cpu_usec
                prev_time[cid] = current_time
                
                # Get init PID (main process of container)
                init_pid = process_inspector.get_init_pid(cid)
                
                # Real metrics only - no simulation
                metrics_by_id[cid] = {
                    "cpu_percent": cpu_percent,
                    "cpu_usec": cpu_usec,  # Total CPU time in microseconds
                    "memory_bytes": mem,
                    "memory_percent": (mem / mem_limit * 100) if mem_limit > 0 else 0,
                    "memory_limit_bytes": mem_limit,
                    "pids": pids,
                    "init_pid": init_pid,
                    "is_throttled": is_throttled
                }
                
                # Feed metrics to ML anomaly detector (only for running containers)
                anomalies = detector.add_metrics(cid, cpu_percent, mem, mem_limit, is_throttled)
                
                # Store anomalies to CSV
                for anomaly in anomalies:
                    metrics_storage.store_anomaly(cid, anomaly)
                
                # Get analytics for this container
                analytics = detector.get_container_analytics(cid)
                
                # Store to CSV for history with enhanced data
                container_name = next((c["name"] for c in containers if c["id"] == cid), cid)
                metrics_storage.store_metrics(
                    cid, container_name, cpu_percent, mem,
                    (mem / mem_limit * 100) if mem_limit > 0 else 0,
                    mem_limit, pids, 
                    health_score=analytics.get("health_score", 100),
                    stability_score=analytics.get("stability_score", 100),
                    efficiency_score=analytics.get("efficiency_score", 100),
                    is_stressed=analytics.get("is_stressed", False),
                    cpu_rate=analytics.get("cpu_rate", 0),
                    anomaly_count=analytics.get("anomaly_count_recent", 0)
                )
            
            # Get anomalies for broadcast
            all_analytics = detector.get_all_analytics()
            
            # Build enhanced payload for frontend
            container_analytics = {}
            for cid in metrics_by_id:
                a = detector.get_container_analytics(cid)
                container_analytics[cid] = {
                    "health_score": a.get("health_score", 100),
                    "stability_score": a.get("stability_score", 100),
                    "efficiency_score": a.get("efficiency_score", 100),
                    "is_stressed": a.get("is_stressed", False),
                    "trend": a.get("trend", {}),
                    "prediction": a.get("prediction", {})
                }
            
            payload = {
                "type": "metrics",
                "timestamp": time.time(),
                "containers": containers,
                "metrics": metrics_by_id,
                "anomalies": all_analytics.get("global_anomalies", [])[-5:],
                "health_scores": {cid: container_analytics[cid]["health_score"] for cid in container_analytics},
                "stability_scores": {cid: container_analytics[cid]["stability_score"] for cid in container_analytics},
                "efficiency_scores": {cid: container_analytics[cid]["efficiency_score"] for cid in container_analytics},
                "container_analytics": container_analytics,
                "system_stats": all_analytics.get("system_stats", {})
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
    """Stop a container - kill all processes in cgroup and reset ML stats"""
    # Find container to get PID
    containers = get_running_containers()
    target_container = None
    for c in containers:
        if c["id"] == container_id or c["id"].startswith(container_id) or c["name"] == container_id:
            target_container = c
            break
    
    if target_container:
        # Kill main PID
        if target_container["pid"] > 0:
            os.system(f"sudo kill -9 {target_container['pid']} 2>/dev/null")
        
        # Kill all processes in the cgroup
        cgroup_procs = CGROUP_BASE / container_id / "cgroup.procs"
        if cgroup_procs.exists():
            try:
                pids = cgroup_procs.read_text().strip().split('\n')
                for pid in pids:
                    if pid.strip():
                        os.system(f"sudo kill -9 {pid.strip()} 2>/dev/null")
            except:
                pass
        
        # Update state file to stopped
        state_file = Path(f"/var/lib/minicontainer/containers/{container_id}/state.txt")
        if state_file.exists():
            try:
                content = state_file.read_text()
                new_content = content.replace("state=running", "state=stopped")
                new_content = new_content.replace(f"pid={target_container['pid']}", "pid=0")
                state_file.write_text(new_content)
            except:
                pass
    
    # Reset ML analytics for this container (scores go back to 100)
    detector.reset_container(container_id)
    
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
    """Execute a command in a container with namespace isolation (if running) or cgroup-only (if stopped)"""
    try:
        body = await request.json()
        command = body.get("command", "echo Hello")
    except:
        command = "echo Hello"
    
    # Check if container is running - if so, use C runtime exec with namespace entry
    state_file = Path(f"/var/lib/minicontainer/containers/{container_id}/state.txt")
    is_running = False
    container_pid = 0
    
    if state_file.exists():
        try:
            content = state_file.read_text()
            if "state=running" in content:
                is_running = True
                for line in content.split('\n'):
                    if line.startswith('pid='):
                        container_pid = int(line.split('=')[1])
        except:
            pass
    
    cgroup_path = CGROUP_BASE / container_id
    
    if is_running and container_pid > 0:
        # Use C runtime exec with namespace entry (true container isolation)
        # This uses setns() to enter MNT, UTS, IPC, and cgroup namespaces
        run_script = f'''
{RUNTIME_PATH} exec {container_id} --cmd "{command}"
'''
        import threading
        def run_namespace_exec():
            try:
                subprocess.run(
                    ["sudo", "bash", "-c", run_script],
                    capture_output=True, text=True, timeout=600,
                    env={"LD_LIBRARY_PATH": str(Path(RUNTIME_PATH).parent)}
                )
            except:
                pass
        
        thread = threading.Thread(target=run_namespace_exec, daemon=True)
        thread.start()
        
        return {"status": "started", "message": f"Command started in container {container_id} with namespace isolation (PID {container_pid})"}
    else:
        # Fallback: cgroup-only execution for stopped containers
        if not cgroup_path.exists():
            cgroup_path.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                f"echo '+cpu +memory +pids' | sudo tee /sys/fs/cgroup/minicontainer/cgroup.subtree_control",
                shell=True, capture_output=True
            )
        
        run_script = f'''
echo $$ > {cgroup_path}/cgroup.procs 2>/dev/null
{command}
'''
        import threading
        def run_cgroup_exec():
            try:
                subprocess.run(
                    ["sudo", "bash", "-c", run_script],
                    capture_output=True, text=True, timeout=600
                )
            except:
                pass
        
        thread = threading.Thread(target=run_cgroup_exec, daemon=True)
        thread.start()
        
        return {"status": "started", "message": f"Command started in container {container_id} (cgroup-only mode)"}

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

# ============== ML Analytics Endpoints ==============

@app.get("/api/analytics")
def get_all_analytics():
    """Get ML analytics for all containers"""
    return detector.get_all_analytics()

@app.get("/api/analytics/{container_id}")
def get_container_analytics(container_id: str):
    """Get ML analytics for a specific container"""
    return detector.get_container_analytics(container_id)

@app.get("/api/analytics/{container_id}/predict")
def predict_container_usage(container_id: str, minutes: int = 5):
    """Predict future resource usage using ML"""
    return detector.predict_usage(container_id, minutes)

@app.get("/api/anomalies")
def get_anomalies():
    """Get all detected anomalies"""
    analytics = detector.get_all_analytics()
    return {
        "anomalies": analytics.get("global_anomalies", []),
        "total": analytics.get("total_anomalies", 0),
        "analysis": analytics.get("anomaly_analysis", {})
    }

@app.get("/api/anomalies/history")
def get_anomaly_history(container_id: str = None, limit: int = 100):
    """Get anomaly history from CSV storage"""
    history = metrics_storage.get_anomaly_history(container_id, limit)
    return {
        "container_id": container_id,
        "data_points": len(history),
        "history": history
    }

@app.get("/api/system/stats")
def get_system_stats():
    """Get system-wide statistics and health metrics"""
    analytics = detector.get_all_analytics()
    return {
        "system_stats": analytics.get("system_stats", {}),
        "anomaly_analysis": analytics.get("anomaly_analysis", {}),
        "active_containers": analytics.get("active_containers", 0),
        "system_uptime": analytics.get("system_uptime", 0),
        "timestamp": analytics.get("timestamp", 0)
    }

@app.get("/api/containers/{container_id}/distribution")
def get_container_distribution(container_id: str):
    """Get CPU and memory distribution data for histograms"""
    analytics = detector.get_container_analytics(container_id)
    return {
        "container_id": container_id,
        "cpu_distribution": analytics.get("cpu_distribution", {}),
        "memory_distribution": analytics.get("memory_distribution", {})
    }

@app.get("/api/containers/{container_id}/trends")
def get_container_trends(container_id: str):
    """Get trend and prediction data for a container"""
    analytics = detector.get_container_analytics(container_id)
    return {
        "container_id": container_id,
        "cpu_trend": analytics.get("trend", {}),
        "memory_trend": analytics.get("memory_trend", {}),
        "cpu_prediction": analytics.get("prediction", {}),
        "memory_prediction": analytics.get("memory_prediction", {}),
        "cpu_rate": analytics.get("cpu_rate", 0),
        "memory_rate": analytics.get("memory_rate", 0)
    }

# ============== Process & Stats Endpoints ==============

@app.get("/api/containers/{container_id}/processes")
def get_container_processes(container_id: str):
    """
    Get all processes running inside a container.
    
    Returns:
        List of processes with PID, name, state, memory, and command.
        
    Explanation:
        - PID: Process ID - unique identifier for each running process on the host
        - PPID: Parent Process ID - the PID of the process that spawned this one
        - State: Running (R), Sleeping (S), Stopped (T), Zombie (Z), etc.
        - The init process (with lowest PID) is the main container process
    """
    processes = process_inspector.get_container_processes(container_id)
    init_pid = process_inspector.get_init_pid(container_id)
    
    return {
        "container_id": container_id,
        "init_pid": init_pid,
        "process_count": len(processes),
        "processes": processes
    }

@app.get("/api/containers/{container_id}/history")
def get_container_history(container_id: str, limit: int = 100):
    """Get historical metrics from CSV storage"""
    history = metrics_storage.get_history(container_id, limit)
    return {
        "container_id": container_id,
        "data_points": len(history),
        "history": history
    }

@app.get("/api/containers/{container_id}/stats")
def get_container_stats(container_id: str):
    """Get statistical summary for a container"""
    return metrics_storage.get_stats_summary(container_id)

@app.get("/api/history")
def get_all_history(limit: int = 500):
    """Get historical metrics for all containers"""
    return {
        "data_points": len(metrics_storage.get_all_history(limit)),
        "history": metrics_storage.get_all_history(limit)
    }

@app.get("/api/export/csv")
def export_csv():
    """Export metrics CSV file for download"""
    csv_path = metrics_storage.export_csv_path()
    if Path(csv_path).exists():
        return FileResponse(
            csv_path, 
            media_type="text/csv",
            filename="minicontainer_metrics.csv"
        )
    raise HTTPException(status_code=404, detail="No data available yet")

@app.get("/api/export/anomalies")
def export_anomalies_csv():
    """Export anomalies CSV file for download"""
    csv_path = metrics_storage.export_anomaly_csv_path()
    if Path(csv_path).exists():
        return FileResponse(
            csv_path, 
            media_type="text/csv",
            filename="minicontainer_anomalies.csv"
        )
    raise HTTPException(status_code=404, detail="No anomaly data available yet")

@app.get("/api/export/summary")
def export_summary_csv():
    """Export container summary CSV file for download"""
    csv_path = metrics_storage.export_summary_csv_path()
    if Path(csv_path).exists():
        return FileResponse(
            csv_path, 
            media_type="text/csv",
            filename="minicontainer_summary.csv"
        )
    raise HTTPException(status_code=404, detail="No summary data available yet")
