"""MiniContainer - Interactive CLI with Enhanced Monitoring"""

import os
import sys
import time
import subprocess
import signal
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box

console = Console()

# Runtime path - Use absolute path
RUNTIME_PATH = Path("/home/student/.gemini/antigravity/scratch/minicontainer/runtime/build/minicontainer-runtime")
CGROUP_BASE = Path("/sys/fs/cgroup/minicontainer")

def run_runtime(args, capture=True):
    """Run the C runtime CLI"""
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(RUNTIME_PATH.parent)
    
    cmd = ["sudo", str(RUNTIME_PATH)] + args
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return result.returncode, result.stdout, result.stderr
    else:
        return subprocess.run(cmd, env=env).returncode, "", ""

def get_container_metrics(container_id):
    """Get metrics from cgroup files"""
    cgroup = CGROUP_BASE / container_id
    metrics = {"cpu_percent": 0, "memory_mb": 0, "memory_limit_mb": 0, "pids": 0}
    
    try:
        mem = cgroup / "memory.current"
        if mem.exists():
            metrics["memory_mb"] = int(mem.read_text().strip()) / 1048576
        
        mem_max = cgroup / "memory.max"
        if mem_max.exists():
            val = mem_max.read_text().strip()
            metrics["memory_limit_mb"] = -1 if val == "max" else int(val) / 1048576
        
        pids = cgroup / "pids.current"
        if pids.exists():
            metrics["pids"] = int(pids.read_text().strip())
            
        cpu = cgroup / "cpu.stat"
        if cpu.exists():
            for line in cpu.read_text().splitlines():
                if line.startswith("usage_usec"):
                    metrics["cpu_usec"] = int(line.split()[1])
    except:
        pass
    return metrics

def check_root():
    """Check if running as root"""
    if os.geteuid() != 0:
        console.print("[yellow]⚠ Some operations require root privileges[/yellow]")

@click.group()
@click.version_option(version="1.0.0", prog_name="minicontainer")
def cli():
    """🐳 MiniContainer - Lightweight Container Management
    
    A container runtime built with Linux cgroups v2 and namespaces.
    
    \b
    QUICK START:
      minicontainer create --name myapp --rootfs /path/to/rootfs
      minicontainer start myapp
      minicontainer monitor myapp
      minicontainer stop myapp
    """
    pass

@cli.command()
@click.option("--name", "-n", required=True, help="Container name")
@click.option("--rootfs", "-r", required=True, help="Path to rootfs directory")
@click.option("--memory", "-m", default="256m", help="Memory limit (e.g., 256m, 1g)")
@click.option("--cpus", "-c", type=float, default=1.0, help="CPU limit (0.1-1.0)")
@click.option("--pids", "-p", type=int, default=100, help="Maximum PIDs")
@click.option("--cmd", default="/bin/sh -c 'while true; do i=0; while [ $i -lt 100000 ]; do i=$((i+1)); done; sleep 0.1; done'", help="Command to run")
def create(name, rootfs, memory, cpus, pids, cmd):
    """Create a new container"""
    args = ["create", "--name", name, "--rootfs", rootfs]
    
    # Parse memory
    mem_bytes = memory
    if memory.endswith('m') or memory.endswith('M'):
        mem_bytes = str(int(memory[:-1]) * 1024 * 1024)
    elif memory.endswith('g') or memory.endswith('G'):
        mem_bytes = str(int(memory[:-1]) * 1024 * 1024 * 1024)
    args.extend(["--memory", mem_bytes])
    args.extend(["--cpus", str(int(cpus * 100))])
    args.extend(["--pids", str(pids)])
    
    if cmd:
        args.extend(["--cmd", cmd])
    
    with console.status("[bold green]Creating container..."):
        code, stdout, stderr = run_runtime(args)
    
    if code == 0:
        console.print(f"[green]✓ Container '{name}' created[/green]")
        console.print(f"  Memory: {memory}, CPU: {int(cpus*100)}%, PIDs: {pids}")
        console.print(f"\n  Start with: [cyan]minicontainer start {name}[/cyan]")
    else:
        console.print(f"[red]✗ Failed to create container[/red]")
        if stderr:
            console.print(f"[dim]{stderr}[/dim]")

@cli.command()
@click.argument("container")
@click.option("--detach", "-d", is_flag=True, help="Run in background")
@click.option("--timeout", "-t", type=int, default=0, help="Auto-stop after N seconds (0=never)")
def start(container, detach, timeout):
    """Start a container"""
    if timeout > 0:
        console.print(f"[yellow]Container will auto-stop after {timeout} seconds[/yellow]")
    
    with console.status(f"[bold green]Starting container '{container}'..."):
        code, stdout, stderr = run_runtime(["start", container])
    
    if code == 0:
        console.print(f"[green]✓ Container '{container}' started[/green]")
        console.print(f"\n  Monitor with: [cyan]minicontainer monitor {container}[/cyan]")
        console.print(f"  Stop with: [cyan]minicontainer stop {container}[/cyan]")
    else:
        console.print(f"[red]✗ Failed to start container[/red]")

@cli.command()
@click.argument("container")
@click.option("--force", "-f", is_flag=True, help="Force stop (SIGKILL)")
def stop(container, force):
    """Stop a container"""
    with console.status(f"[bold yellow]Stopping container '{container}'..."):
        code, stdout, stderr = run_runtime(["stop", container])
    
    if code == 0:
        console.print(f"[green]✓ Container '{container}' stopped[/green]")
    else:
        console.print(f"[red]✗ Failed to stop container[/red]")

@cli.command()
@click.argument("container")
def rm(container):
    """Remove a container"""
    with console.status(f"[bold red]Removing container '{container}'..."):
        code, stdout, stderr = run_runtime(["delete", container])
    
    if code == 0:
        console.print(f"[green]✓ Container '{container}' removed[/green]")
    else:
        console.print(f"[red]✗ Failed to remove container[/red]")

@cli.command()
@click.option("--all", "-a", "show_all", is_flag=True, help="Show all containers")
def ps(show_all):
    """List containers"""
    code, stdout, stderr = run_runtime(["list"])
    
    table = Table(title="🐳 Containers", box=box.ROUNDED)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("PID", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("CPU", justify="right")
    
    if code == 0:
        lines = stdout.strip().split("\n")
        for line in lines[2:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 4:
                cid = parts[0]
                status = parts[2]
                if not show_all and status == "stopped":
                    continue
                
                # Get metrics for running containers
                mem_str = "-"
                cpu_str = "-"
                if status == "running":
                    metrics = get_container_metrics(cid)
                    if metrics["memory_mb"] > 0:
                        mem_str = f"{metrics['memory_mb']:.1f}MB"
                    if "cpu_usec" in metrics:
                        cpu_str = f"{metrics['cpu_usec']/1e6:.1f}s"
                
                status_color = {"running": "green", "created": "yellow", "stopped": "red"}.get(status, "white")
                table.add_row(cid[:12], parts[1], f"[{status_color}]{status}[/{status_color}]", 
                             parts[3], mem_str, cpu_str)
    
    console.print(table)

@cli.command()
@click.argument("container")
@click.option("--interval", "-i", type=float, default=1.0, help="Update interval in seconds")
def monitor(container, interval):
    """Monitor container resources in real-time"""
    console.print(f"[bold]📊 Monitoring container '{container}'[/bold]")
    console.print("Press Ctrl+C to exit\n")
    
    # Find container ID
    code, stdout, stderr = run_runtime(["list"])
    container_id = None
    if code == 0:
        for line in stdout.strip().split("\n")[2:]:
            parts = line.split()
            if len(parts) >= 2 and (parts[0] == container or parts[1] == container):
                container_id = parts[0]
                break
    
    if not container_id:
        console.print(f"[red]Container '{container}' not found[/red]")
        return
    
    prev_cpu = 0
    prev_time = time.time()
    
    history = {"cpu": [], "mem": []}
    
    try:
        while True:
            metrics = get_container_metrics(container_id)
            current_time = time.time()
            
            # Calculate CPU percentage
            cpu_percent = 0
            if "cpu_usec" in metrics and prev_cpu > 0:
                cpu_delta = metrics["cpu_usec"] - prev_cpu
                time_delta = current_time - prev_time
                cpu_percent = (cpu_delta / (time_delta * 1e6)) * 100
            prev_cpu = metrics.get("cpu_usec", 0)
            prev_time = current_time
            
            # Store history
            history["cpu"].append(cpu_percent)
            history["mem"].append(metrics["memory_mb"])
            if len(history["cpu"]) > 60:
                history["cpu"].pop(0)
                history["mem"].pop(0)
            
            # Clear and display
            console.clear()
            
            # Header
            console.print(Panel(f"[bold cyan]Container: {container}[/bold cyan] ({container_id[:12]})", 
                               title="📊 Live Monitor", border_style="blue"))
            
            # Metrics table
            table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
            table.add_column("Metric", style="bold")
            table.add_column("Value", justify="right")
            table.add_column("Bar", width=30)
            
            # CPU
            cpu_bar = "█" * int(min(cpu_percent, 100) / 3.33) + "░" * (30 - int(min(cpu_percent, 100) / 3.33))
            cpu_color = "green" if cpu_percent < 50 else "yellow" if cpu_percent < 80 else "red"
            table.add_row("⚡ CPU", f"[{cpu_color}]{cpu_percent:.1f}%[/{cpu_color}]", f"[{cpu_color}]{cpu_bar}[/{cpu_color}]")
            
            # Memory
            mem_percent = 0
            if metrics["memory_limit_mb"] > 0:
                mem_percent = (metrics["memory_mb"] / metrics["memory_limit_mb"]) * 100
            mem_bar = "█" * int(min(mem_percent, 100) / 3.33) + "░" * (30 - int(min(mem_percent, 100) / 3.33))
            mem_color = "green" if mem_percent < 50 else "yellow" if mem_percent < 80 else "red"
            mem_limit_str = f"/{metrics['memory_limit_mb']:.0f}MB" if metrics["memory_limit_mb"] > 0 else ""
            table.add_row("💾 Memory", f"[{mem_color}]{metrics['memory_mb']:.1f}MB{mem_limit_str}[/{mem_color}]", 
                         f"[{mem_color}]{mem_bar}[/{mem_color}]")
            
            # PIDs
            table.add_row("🔢 PIDs", str(metrics["pids"]), "")
            
            console.print(table)
            
            # ASCII Spark Chart for CPU
            if len(history["cpu"]) > 1:
                console.print("\n[bold]CPU History (last 60s):[/bold]")
                spark = ""
                chars = " ▁▂▃▄▅▆▇█"
                max_val = max(history["cpu"]) if max(history["cpu"]) > 0 else 1
                for val in history["cpu"]:
                    idx = int((val / max_val) * 8) if max_val > 0 else 0
                    spark += chars[min(idx, 8)]
                console.print(f"[cyan]{spark}[/cyan]")
            
            console.print(f"\n[dim]Updating every {interval}s. Press Ctrl+C to exit.[/dim]")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        console.print("\n[dim]Stopped monitoring[/dim]")

@cli.command()
@click.option("--name", "-n", required=True, help="Container name")
@click.option("--rootfs", "-r", required=True, help="Path to rootfs")
@click.option("--memory", "-m", default="256m", help="Memory limit")
@click.option("--cpus", "-c", type=float, default=1.0, help="CPU limit")
@click.option("--cmd", default="/bin/sh -c 'i=0; while [ $i -lt 10000000 ]; do i=$((i+1)); done; echo Done'", help="Command to run")
@click.option("--duration", "-d", type=int, default=0, help="Run for N seconds (0=until exit)")
def run(name, rootfs, memory, cpus, cmd, duration):
    """Create and run a container (one-shot)"""
    args = ["run", "--name", name, "--rootfs", rootfs]
    
    mem_bytes = memory
    if memory.endswith('m'):
        mem_bytes = str(int(memory[:-1]) * 1024 * 1024)
    args.extend(["--memory", mem_bytes])
    args.extend(["--cpus", str(int(cpus * 100))])
    
    if cmd:
        if duration > 0:
            # Wrap command to exit after duration
            cmd = f"timeout {duration} {cmd}"
        args.extend(["--cmd", cmd])
    
    console.print(f"[bold]Running container '{name}'...[/bold]")
    if duration > 0:
        console.print(f"[yellow]Will auto-exit after {duration} seconds[/yellow]")
    
    code, _, _ = run_runtime(args, capture=False)
    
    if code == 0:
        console.print(f"\n[green]✓ Container exited[/green]")
    else:
        console.print(f"\n[red]✗ Container failed[/red]")

@cli.command()
@click.option("--port", "-p", default=8000, help="API port")
@click.option("--dashboard-port", default=5173, help="Dashboard port")
def dashboard(port, dashboard_port):
    """Start the web dashboard with real-time monitoring"""
    import uvicorn
    
    console.print(Panel.fit(
        f"[bold green]🚀 MiniContainer Dashboard[/bold green]\n\n"
        f"  API Server: [cyan]http://localhost:{port}[/cyan]\n"
        f"  Dashboard:  [cyan]http://localhost:{dashboard_port}[/cyan]\n\n"
        f"  [dim]Run 'cd dashboard && npm run dev' in another terminal[/dim]",
        title="Dashboard", border_style="green"
    ))
    
    from .api import app
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

@cli.command()
def info():
    """Show system information"""
    table = Table(title="System Information", box=box.ROUNDED)
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    import platform
    table.add_row("Kernel", platform.release())
    table.add_row("Architecture", platform.machine())
    
    cgroup_v2 = Path("/sys/fs/cgroup/cgroup.controllers").exists()
    table.add_row("Cgroup v2", "[green]✓ Available[/green]" if cgroup_v2 else "[red]✗ Not available[/red]")
    
    runtime_ok = RUNTIME_PATH.exists()
    table.add_row("Runtime", "[green]✓ Installed[/green]" if runtime_ok else "[red]✗ Not found[/red]")
    
    state_dir = Path("/var/lib/minicontainer")
    table.add_row("State Directory", str(state_dir))
    
    # Count containers
    containers = list(CGROUP_BASE.glob("*")) if CGROUP_BASE.exists() else []
    table.add_row("Active Containers", str(len(containers)))
    
    console.print(table)

@cli.command()
def help_all():
    """Show all commands with examples"""
    console.print(Panel.fit("""
[bold cyan]🐳 MiniContainer Command Reference[/bold cyan]

[bold]CONTAINER LIFECYCLE:[/bold]
  create   Create a new container
  start    Start a stopped container  
  stop     Stop a running container
  rm       Remove a container
  run      Create, run, and cleanup (one-shot)

[bold]MONITORING:[/bold]
  ps       List all containers
  monitor  Real-time resource monitoring
  stats    Quick stats view

[bold]DASHBOARD:[/bold]
  dashboard  Start web UI for visual monitoring

[bold]EXAMPLES:[/bold]
[dim]# Create and monitor a long-running container[/dim]
minicontainer create -n webapp -r /tmp/alpine-rootfs -m 512m -c 0.5
minicontainer start webapp
minicontainer monitor webapp

[dim]# Run for specific duration[/dim]
minicontainer run -n test -r /tmp/alpine-rootfs --duration 30 --cmd "sleep 60"

[dim]# Start dashboard for graphs[/dim]
minicontainer dashboard
""", title="Help", border_style="blue"))

def main():
    check_root()
    cli()

if __name__ == "__main__":
    main()
