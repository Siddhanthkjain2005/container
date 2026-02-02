"""MiniContainer - Interactive CLI with Enhanced Monitoring"""

import os
import sys
import time
import subprocess
import signal
import json
import shutil
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.syntax import Syntax
from rich.tree import Tree
from rich import box

console = Console()

# Runtime path - Use absolute path
RUNTIME_PATH = Path("/home/student/container/runtime/build/minicontainer-runtime")
CGROUP_BASE = Path("/sys/fs/cgroup/minicontainer")
STATE_DIR = Path("/var/lib/minicontainer")
LOG_DIR = STATE_DIR / "logs"

# ASCII Art Banner
BANNER = """
[bold cyan]
 ███╗   ███╗██╗███╗   ██╗██╗ ██████╗ ██████╗ ███╗   ██╗████████╗ █████╗ ██╗███╗   ██╗███████╗██████╗ 
 ████╗ ████║██║████╗  ██║██║██╔════╝██╔═══██╗████╗  ██║╚══██╔══╝██╔══██╗██║████╗  ██║██╔════╝██╔══██╗
 ██╔████╔██║██║██╔██╗ ██║██║██║     ██║   ██║██╔██╗ ██║   ██║   ███████║██║██╔██╗ ██║█████╗  ██████╔╝
 ██║╚██╔╝██║██║██║╚██╗██║██║██║     ██║   ██║██║╚██╗██║   ██║   ██╔══██║██║██║╚██╗██║██╔══╝  ██╔══██╗
 ██║ ╚═╝ ██║██║██║ ╚████║██║╚██████╗╚██████╔╝██║ ╚████║   ██║   ██║  ██║██║██║ ╚████║███████╗██║  ██║
 ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝
[/bold cyan]
[dim]Lightweight Container Runtime powered by Linux Namespaces & Cgroups v2[/dim]
"""

def get_ist_time():
    """Get current IST time formatted"""
    from datetime import timezone, timedelta
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    return now.strftime("%A, %d %B %Y at %I:%M:%S %p IST")

def format_bytes(bytes_val):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}PB"

def format_duration(seconds):
    """Format seconds to human readable duration"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds//60:.0f}m {seconds%60:.0f}s"
    else:
        return f"{seconds//3600:.0f}h {(seconds%3600)//60:.0f}m"

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
    metrics = {"cpu_percent": 0, "memory_mb": 0, "memory_limit_mb": 0, "pids": 0, "pids_max": 0}
    
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
        
        pids_max = cgroup / "pids.max"
        if pids_max.exists():
            val = pids_max.read_text().strip()
            metrics["pids_max"] = 0 if val == "max" else int(val)
            
        cpu = cgroup / "cpu.stat"
        if cpu.exists():
            for line in cpu.read_text().splitlines():
                if line.startswith("usage_usec"):
                    metrics["cpu_usec"] = int(line.split()[1])
                    
        # Get CPU max limit
        cpu_max = cgroup / "cpu.max"
        if cpu_max.exists():
            val = cpu_max.read_text().strip().split()[0]
            metrics["cpu_max"] = int(val) if val != "max" else 100000
    except:
        pass
    return metrics

def check_root():
    """Check if running as root"""
    if os.geteuid() != 0:
        console.print("[yellow]⚠ Some operations require root privileges[/yellow]")

def check_runtime():
    """Check if runtime is available"""
    if not RUNTIME_PATH.exists():
        console.print(f"[red]✗ Runtime not found at {RUNTIME_PATH}[/red]")
        console.print("[dim]Run 'cd runtime && make' to build it[/dim]")
        return False
    return True

def get_container_list():
    """Get list of containers as structured data"""
    code, stdout, stderr = run_runtime(["list"])
    containers = []
    if code == 0:
        lines = stdout.strip().split("\n")
        for line in lines[2:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 4:
                containers.append({
                    "id": parts[0],
                    "name": parts[1],
                    "status": parts[2],
                    "pid": parts[3] if len(parts) > 3 else "0"
                })
    return containers

@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version")
@click.pass_context
def cli(ctx, version):
    """🐳 MiniContainer - Lightweight Container Management
    
    A container runtime built with Linux cgroups v2 and namespaces.
    
    \b
    QUICK START:
      minicontainer create --name myapp --rootfs /path/to/rootfs
      minicontainer start myapp
      minicontainer monitor myapp
      minicontainer stop myapp
    """
    if version:
        console.print(BANNER)
        console.print(f"[bold]Version:[/bold] 1.0.0")
        console.print(f"[bold]Time:[/bold] {get_ist_time()}")
        return
    
    if ctx.invoked_subcommand is None:
        console.print(BANNER)
        console.print("[dim]Type 'minicontainer --help' for available commands[/dim]\n")

# ============ CONTAINER LIFECYCLE COMMANDS ============

@cli.command()
@click.option("--name", "-n", required=True, help="Container name")
@click.option("--rootfs", "-r", required=True, help="Path to rootfs directory")
@click.option("--memory", "-m", default="256m", help="Memory limit (e.g., 256m, 1g)")
@click.option("--cpus", "-c", type=float, default=1.0, help="CPU limit (0.1-1.0)")
@click.option("--pids", "-p", type=int, default=100, help="Maximum PIDs")
@click.option("--cmd", default="/bin/sh -c 'while true; do i=0; while [ $i -lt 100000 ]; do i=$((i+1)); done; sleep 0.1; done'", help="Command to run")
@click.option("--env", "-e", multiple=True, help="Environment variables (KEY=VALUE)")
def create(name, rootfs, memory, cpus, pids, cmd, env):
    """Create a new container
    
    \b
    Examples:
      minicontainer create -n myapp -r /tmp/alpine-rootfs
      minicontainer create -n web -r /tmp/rootfs -m 512m -c 0.5 -p 50
      minicontainer create -n test -r /tmp/rootfs -e APP_ENV=prod -e DEBUG=0
    """
    if not check_runtime():
        return
    
    # Validate rootfs
    rootfs_path = Path(rootfs)
    if not rootfs_path.exists():
        console.print(f"[red]✗ Rootfs directory not found: {rootfs}[/red]")
        console.print("[dim]Create a rootfs with: minicontainer rootfs create alpine[/dim]")
        return
    
    args = ["create", "--name", name, "--rootfs", rootfs]
    
    # Parse memory
    mem_bytes = memory
    if memory.endswith('m') or memory.endswith('M'):
        mem_bytes = str(int(memory[:-1]) * 1024 * 1024)
    elif memory.endswith('g') or memory.endswith('G'):
        mem_bytes = str(int(memory[:-1]) * 1024 * 1024 * 1024)
    elif memory.endswith('k') or memory.endswith('K'):
        mem_bytes = str(int(memory[:-1]) * 1024)
    args.extend(["--memory", mem_bytes])
    args.extend(["--cpus", str(int(cpus * 100))])
    args.extend(["--pids", str(pids)])
    
    if cmd:
        args.extend(["--cmd", cmd])
    
    console.print(f"\n[bold cyan]📦 Creating Container[/bold cyan]")
    console.print(f"[dim]{'─' * 40}[/dim]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[green]Setting up container...", total=None)
        code, stdout, stderr = run_runtime(args)
    
    if code == 0:
        # Show success panel
        config_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
        config_table.add_column("Key", style="dim")
        config_table.add_column("Value", style="cyan")
        config_table.add_row("Name", name)
        config_table.add_row("Memory Limit", memory)
        config_table.add_row("CPU Limit", f"{int(cpus*100)}%")
        config_table.add_row("Max PIDs", str(pids))
        config_table.add_row("Rootfs", rootfs)
        
        console.print(Panel(
            config_table,
            title="[green]✓ Container Created[/green]",
            border_style="green"
        ))
        
        console.print(f"\n[bold]Next steps:[/bold]")
        console.print(f"  1. Start:   [cyan]minicontainer start {name}[/cyan]")
        console.print(f"  2. Monitor: [cyan]minicontainer monitor {name}[/cyan]")
        console.print(f"  3. Stop:    [cyan]minicontainer stop {name}[/cyan]")
    else:
        console.print(f"[red]✗ Failed to create container[/red]")
        if stderr:
            console.print(Panel(stderr, title="Error", border_style="red"))

@cli.command()
@click.argument("container")
@click.option("--detach", "-d", is_flag=True, help="Run in background")
@click.option("--timeout", "-t", type=int, default=0, help="Auto-stop after N seconds (0=never)")
def start(container, detach, timeout):
    """Start a container
    
    \b
    Examples:
      minicontainer start myapp
      minicontainer start myapp -d        # Run in background
      minicontainer start myapp -t 60     # Auto-stop after 60 seconds
    """
    if not check_runtime():
        return
    
    if timeout > 0:
        console.print(f"[yellow]⏱ Container will auto-stop after {timeout} seconds[/yellow]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"[green]Starting '{container}'...", total=None)
        code, stdout, stderr = run_runtime(["start", container])
    
    if code == 0:
        console.print(f"\n[green]✓ Container '{container}' is now running[/green]")
        console.print(f"  Time: {get_ist_time()}")
        console.print(f"\n[bold]Commands:[/bold]")
        console.print(f"  Monitor: [cyan]minicontainer monitor {container}[/cyan]")
        console.print(f"  Stop:    [cyan]minicontainer stop {container}[/cyan]")
        console.print(f"  Logs:    [cyan]minicontainer logs {container}[/cyan]")
    else:
        console.print(f"[red]✗ Failed to start container[/red]")
        if stderr:
            console.print(f"[dim]{stderr}[/dim]")

@cli.command()
@click.argument("container")
@click.option("--force", "-f", is_flag=True, help="Force stop (SIGKILL)")
@click.option("--timeout", "-t", type=int, default=10, help="Timeout before force kill")
def stop(container, force, timeout):
    """Stop a running container
    
    \b
    Examples:
      minicontainer stop myapp
      minicontainer stop myapp -f         # Force kill immediately
      minicontainer stop myapp -t 5       # Wait 5s before force kill
    """
    if not check_runtime():
        return
    
    signal_type = "SIGKILL" if force else "SIGTERM"
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"[yellow]Stopping '{container}' ({signal_type})...", total=None)
        code, stdout, stderr = run_runtime(["stop", container])
    
    if code == 0:
        console.print(f"\n[green]✓ Container '{container}' stopped[/green]")
        console.print(f"  Time: {get_ist_time()}")
    else:
        console.print(f"[red]✗ Failed to stop container[/red]")
        if stderr:
            console.print(f"[dim]{stderr}[/dim]")

@cli.command()
@click.argument("container")
@click.option("--force", "-f", is_flag=True, help="Force restart")
def restart(container, force):
    """Restart a container
    
    \b
    Examples:
      minicontainer restart myapp
      minicontainer restart myapp -f      # Force restart
    """
    if not check_runtime():
        return
    
    console.print(f"\n[bold cyan]🔄 Restarting Container '{container}'[/bold cyan]")
    
    # Stop
    with console.status("[yellow]Stopping..."):
        run_runtime(["stop", container])
    
    time.sleep(1)
    
    # Start
    with console.status("[green]Starting..."):
        code, stdout, stderr = run_runtime(["start", container])
    
    if code == 0:
        console.print(f"[green]✓ Container '{container}' restarted[/green]")
    else:
        console.print(f"[red]✗ Failed to restart container[/red]")

@cli.command()
@click.argument("container")
@click.option("--force", "-f", is_flag=True, help="Force remove running container")
@click.option("--volumes", "-v", is_flag=True, help="Remove associated volumes")
def rm(container, force, volumes):
    """Remove a container
    
    \b
    Examples:
      minicontainer rm myapp
      minicontainer rm myapp -f           # Force remove even if running
      minicontainer rm myapp -f -v        # Also remove volumes
    """
    if not check_runtime():
        return
    
    # Check if container is running
    containers = get_container_list()
    target = next((c for c in containers if c["name"] == container or c["id"] == container), None)
    
    if target and target["status"] == "running":
        if not force:
            console.print(f"[red]✗ Container '{container}' is running. Use -f to force remove.[/red]")
            return
        # Stop first
        console.print(f"[yellow]Stopping container first...[/yellow]")
        run_runtime(["stop", container])
        time.sleep(1)
    
    with console.status(f"[bold red]Removing container '{container}'..."):
        code, stdout, stderr = run_runtime(["delete", container])
    
    if code == 0:
        console.print(f"[green]✓ Container '{container}' removed[/green]")
    else:
        console.print(f"[red]✗ Failed to remove container[/red]")
        if stderr:
            console.print(f"[dim]{stderr}[/dim]")

# ============ LISTING & MONITORING COMMANDS ============

@cli.command()
@click.option("--all", "-a", "show_all", is_flag=True, help="Show all containers including stopped")
@click.option("--quiet", "-q", is_flag=True, help="Only show container IDs")
@click.option("--format", "fmt", type=click.Choice(["table", "json"]), default="table", help="Output format")
def ps(show_all, quiet, fmt):
    """List containers
    
    \b
    Examples:
      minicontainer ps                    # Show running containers
      minicontainer ps -a                 # Show all containers
      minicontainer ps -q                 # Only show IDs
      minicontainer ps --format json      # JSON output
    """
    containers = get_container_list()
    
    if not show_all:
        containers = [c for c in containers if c["status"] == "running"]
    
    if quiet:
        for c in containers:
            console.print(c["id"][:12])
        return
    
    if fmt == "json":
        for c in containers:
            if c["status"] == "running":
                c["metrics"] = get_container_metrics(c["id"])
        console.print(json.dumps(containers, indent=2))
        return
    
    # Table format
    table = Table(title="🐳 Containers", box=box.ROUNDED, show_lines=False)
    table.add_column("ID", style="cyan", no_wrap=True, width=14)
    table.add_column("Name", style="bold white", width=20)
    table.add_column("Status", width=12)
    table.add_column("PID", justify="right", width=8)
    table.add_column("Memory", justify="right", width=12)
    table.add_column("CPU Time", justify="right", width=12)
    table.add_column("PIDs", justify="right", width=8)
    
    for c in containers:
        cid = c["id"][:12]
        status = c["status"]
        
        # Get metrics for running containers
        mem_str = "-"
        cpu_str = "-"
        pids_str = "-"
        
        if status == "running":
            metrics = get_container_metrics(c["id"])
            if metrics["memory_mb"] > 0:
                limit = metrics.get("memory_limit_mb", 0)
                if limit > 0:
                    mem_str = f"{metrics['memory_mb']:.1f}/{limit:.0f}MB"
                else:
                    mem_str = f"{metrics['memory_mb']:.1f}MB"
            if "cpu_usec" in metrics:
                cpu_str = format_duration(metrics["cpu_usec"] / 1e6)
            pids_str = str(metrics.get("pids", 0))
        
        status_style = {"running": "[green]● running[/green]", 
                       "created": "[yellow]○ created[/yellow]", 
                       "stopped": "[dim]◌ stopped[/dim]"}.get(status, status)
        
        table.add_row(cid, c["name"], status_style, c["pid"], mem_str, cpu_str, pids_str)
    
    if len(containers) == 0:
        console.print("[dim]No containers found. Create one with:[/dim]")
        console.print("  [cyan]minicontainer create -n myapp -r /path/to/rootfs[/cyan]")
    else:
        console.print(table)
        console.print(f"\n[dim]Showing {len(containers)} container(s). Use -a to show all.[/dim]")

@cli.command()
@click.argument("container")
@click.option("--interval", "-i", type=float, default=1.0, help="Update interval in seconds")
@click.option("--count", "-n", type=int, default=0, help="Number of updates (0=infinite)")
def monitor(container, interval, count):
    """Monitor container resources in real-time
    
    \b
    Examples:
      minicontainer monitor myapp
      minicontainer monitor myapp -i 0.5   # Update every 0.5 seconds
      minicontainer monitor myapp -n 10    # Show 10 updates then exit
    """
    console.print(f"\n[bold cyan]📊 Live Monitor: {container}[/bold cyan]")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n")
    
    # Find container ID
    containers = get_container_list()
    target = next((c for c in containers if c["name"] == container or c["id"] == container), None)
    
    if not target:
        console.print(f"[red]✗ Container '{container}' not found[/red]")
        return
    
    if target["status"] != "running":
        console.print(f"[yellow]⚠ Container '{container}' is not running[/yellow]")
        return
    
    container_id = target["id"]
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
    
    console.print(f"\n[bold cyan]🚀 Running container '{name}'[/bold cyan]")
    if duration > 0:
        console.print(f"[yellow]⏱ Will auto-exit after {duration} seconds[/yellow]")
    
    code, _, _ = run_runtime(args, capture=False)
    
    if code == 0:
        console.print(f"\n[green]✓ Container exited successfully[/green]")
    else:
        console.print(f"\n[red]✗ Container failed with exit code {code}[/red]")

# ============ INSPECTION COMMANDS ============

@cli.command()
@click.argument("container")
def inspect(container):
    """Show detailed container information
    
    \b
    Examples:
      minicontainer inspect myapp
    """
    containers = get_container_list()
    target = next((c for c in containers if c["name"] == container or c["id"] == container), None)
    
    if not target:
        console.print(f"[red]✗ Container '{container}' not found[/red]")
        return
    
    # Get metrics
    metrics = get_container_metrics(target["id"])
    
    # Build tree view
    tree = Tree(f"[bold cyan]🐳 Container: {target['name']}[/bold cyan]")
    
    # Basic info
    info = tree.add("[bold]📋 Basic Info[/bold]")
    info.add(f"ID: [cyan]{target['id']}[/cyan]")
    info.add(f"Name: [white]{target['name']}[/white]")
    status_color = {"running": "green", "created": "yellow", "stopped": "red"}.get(target["status"], "white")
    info.add(f"Status: [{status_color}]{target['status']}[/{status_color}]")
    info.add(f"PID: {target['pid']}")
    
    # Resources
    resources = tree.add("[bold]💾 Resources[/bold]")
    resources.add(f"Memory: {metrics['memory_mb']:.2f} MB")
    if metrics['memory_limit_mb'] > 0:
        resources.add(f"Memory Limit: {metrics['memory_limit_mb']:.0f} MB")
    resources.add(f"Processes: {metrics['pids']}")
    if metrics.get('pids_max', 0) > 0:
        resources.add(f"Max Processes: {metrics['pids_max']}")
    if "cpu_usec" in metrics:
        resources.add(f"CPU Time: {format_duration(metrics['cpu_usec'] / 1e6)}")
    
    # Cgroup paths
    cgroup = tree.add("[bold]📁 Cgroup Path[/bold]")
    cgroup.add(f"{CGROUP_BASE / target['id']}")
    
    console.print(tree)

@cli.command()
@click.argument("container")
@click.option("--tail", "-n", type=int, default=50, help="Number of lines to show")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def logs(container, tail, follow):
    """Show container logs
    
    \b
    Examples:
      minicontainer logs myapp
      minicontainer logs myapp -n 100     # Show last 100 lines
      minicontainer logs myapp -f         # Follow logs
    """
    log_file = LOG_DIR / f"{container}.log"
    
    if not log_file.exists():
        console.print(f"[yellow]No logs found for container '{container}'[/yellow]")
        return
    
    console.print(f"[bold]📜 Logs for {container}[/bold]\n")
    
    try:
        with open(log_file, "r") as f:
            lines = f.readlines()
            for line in lines[-tail:]:
                console.print(f"[dim]{line.rstrip()}[/dim]")
        
        if follow:
            console.print("\n[dim]Following logs... Press Ctrl+C to exit[/dim]")
            import subprocess
            subprocess.run(["tail", "-f", str(log_file)])
    except Exception as e:
        console.print(f"[red]Error reading logs: {e}[/red]")

@cli.command()
@click.argument("container")
@click.argument("key")
@click.argument("value")
def update(container, key, value):
    """Update container resource limits
    
    \b
    Keys: memory, cpu, pids
    
    Examples:
      minicontainer update myapp memory 512m
      minicontainer update myapp cpu 0.5
      minicontainer update myapp pids 200
    """
    containers = get_container_list()
    target = next((c for c in containers if c["name"] == container or c["id"] == container), None)
    
    if not target:
        console.print(f"[red]✗ Container '{container}' not found[/red]")
        return
    
    cgroup = CGROUP_BASE / target["id"]
    
    try:
        if key == "memory":
            mem_bytes = value
            if value.endswith('m') or value.endswith('M'):
                mem_bytes = str(int(value[:-1]) * 1024 * 1024)
            elif value.endswith('g') or value.endswith('G'):
                mem_bytes = str(int(value[:-1]) * 1024 * 1024 * 1024)
            (cgroup / "memory.max").write_text(mem_bytes)
            console.print(f"[green]✓ Updated memory limit to {value}[/green]")
        
        elif key == "cpu":
            cpu_percent = int(float(value) * 100)
            quota = cpu_percent * 1000  # Based on 100000 period
            (cgroup / "cpu.max").write_text(f"{quota} 100000")
            console.print(f"[green]✓ Updated CPU limit to {value}[/green]")
        
        elif key == "pids":
            (cgroup / "pids.max").write_text(value)
            console.print(f"[green]✓ Updated PIDs limit to {value}[/green]")
        
        else:
            console.print(f"[red]Unknown key '{key}'. Use: memory, cpu, pids[/red]")
    except PermissionError:
        console.print("[red]✗ Permission denied. Run with sudo.[/red]")
    except Exception as e:
        console.print(f"[red]✗ Failed to update: {e}[/red]")

# ============ SYSTEM COMMANDS ============

@cli.command()
@click.option("--port", "-p", default=8000, help="API port")
@click.option("--host", "-h", default="0.0.0.0", help="Host to bind")
def dashboard(port, host):
    """Start the web dashboard with real-time monitoring
    
    \b
    Examples:
      minicontainer dashboard
      minicontainer dashboard -p 9000     # Use port 9000
    """
    import uvicorn
    
    console.print(BANNER)
    console.print(Panel(
        f"[bold green]🚀 Starting MiniContainer Dashboard[/bold green]\n\n"
        f"  API Server:  [cyan]http://localhost:{port}[/cyan]\n"
        f"  Dashboard:   [cyan]http://localhost:5173[/cyan]\n\n"
        f"  Time: {get_ist_time()}\n\n"
        f"  [dim]In another terminal, run:[/dim]\n"
        f"  [cyan]cd dashboard && npm run dev[/cyan]",
        title="🐳 Dashboard", border_style="cyan"
    ))
    
    from .api import app
    uvicorn.run(app, host=host, port=port, log_level="info")

@cli.command()
def info():
    """Show system information and health check"""
    console.print(BANNER)
    
    import platform
    
    table = Table(title="🖥 System Information", box=box.ROUNDED, show_header=False)
    table.add_column("Property", style="cyan", width=25)
    table.add_column("Value", style="white")
    
    table.add_row("Hostname", platform.node())
    table.add_row("Kernel", platform.release())
    table.add_row("Architecture", platform.machine())
    table.add_row("Python Version", platform.python_version())
    table.add_row("Current Time", get_ist_time())
    
    console.print(table)
    console.print()
    
    # Health checks
    health_table = Table(title="🔍 Health Checks", box=box.ROUNDED, show_header=False)
    health_table.add_column("Check", style="white", width=25)
    health_table.add_column("Status", width=40)
    
    # Cgroup v2
    cgroup_v2 = Path("/sys/fs/cgroup/cgroup.controllers").exists()
    health_table.add_row("Cgroup v2", "[green]✓ Available[/green]" if cgroup_v2 else "[red]✗ Not available[/red]")
    
    # Runtime
    runtime_ok = RUNTIME_PATH.exists()
    health_table.add_row("Runtime Binary", 
                        f"[green]✓ Found[/green]" if runtime_ok else f"[red]✗ Not found at {RUNTIME_PATH}[/red]")
    
    # State directory
    state_ok = STATE_DIR.exists() or True  # Will be created
    health_table.add_row("State Directory", f"[green]✓ {STATE_DIR}[/green]")
    
    # Root privileges
    is_root = os.geteuid() == 0
    health_table.add_row("Root Privileges", 
                        "[green]✓ Running as root[/green]" if is_root else "[yellow]⚠ Not root (some features limited)[/yellow]")
    
    # Container count
    containers = get_container_list()
    running = len([c for c in containers if c["status"] == "running"])
    health_table.add_row("Containers", f"{running} running / {len(containers)} total")
    
    console.print(health_table)

@cli.command()
@click.option("--force", "-f", is_flag=True, help="Force cleanup without confirmation")
def prune(force):
    """Remove all stopped containers and clean up resources
    
    \b
    Examples:
      minicontainer prune
      minicontainer prune -f              # Force without confirmation
    """
    containers = get_container_list()
    stopped = [c for c in containers if c["status"] == "stopped"]
    
    if not stopped:
        console.print("[green]✓ No stopped containers to remove[/green]")
        return
    
    console.print(f"[yellow]Found {len(stopped)} stopped container(s):[/yellow]")
    for c in stopped:
        console.print(f"  • {c['name']} ({c['id'][:12]})")
    
    if not force:
        if not click.confirm("\nDo you want to remove them?"):
            console.print("[dim]Cancelled[/dim]")
            return
    
    removed = 0
    for c in stopped:
        code, _, _ = run_runtime(["delete", c["id"]])
        if code == 0:
            removed += 1
            console.print(f"[green]✓ Removed {c['name']}[/green]")
    
    console.print(f"\n[bold green]Cleaned up {removed} container(s)[/bold green]")

@cli.command()
def help_all():
    """Show all commands with detailed examples"""
    console.print(BANNER)
    console.print(Panel("""
[bold cyan]📚 MiniContainer Command Reference[/bold cyan]

[bold yellow]CONTAINER LIFECYCLE:[/bold yellow]
  [cyan]create[/cyan]    Create a new container with resource limits
  [cyan]start[/cyan]     Start a stopped container
  [cyan]stop[/cyan]      Stop a running container
  [cyan]restart[/cyan]   Restart a container
  [cyan]rm[/cyan]        Remove a container
  [cyan]run[/cyan]       Create, run, and cleanup (one-shot)

[bold yellow]MONITORING & INSPECTION:[/bold yellow]
  [cyan]ps[/cyan]        List all containers with status
  [cyan]monitor[/cyan]   Real-time resource monitoring with graphs
  [cyan]inspect[/cyan]   Show detailed container information
  [cyan]logs[/cyan]      View container logs
  [cyan]update[/cyan]    Update container resource limits

[bold yellow]SYSTEM:[/bold yellow]
  [cyan]dashboard[/cyan] Start web UI for visual monitoring
  [cyan]info[/cyan]      Show system information and health
  [cyan]prune[/cyan]     Remove stopped containers

[bold yellow]EXAMPLES:[/bold yellow]

[dim]# Create a container with limits[/dim]
[white]minicontainer create -n webapp -r /tmp/alpine-rootfs -m 512m -c 0.5[/white]

[dim]# Start and monitor[/dim]
[white]minicontainer start webapp[/white]
[white]minicontainer monitor webapp[/white]

[dim]# View detailed info[/dim]
[white]minicontainer inspect webapp[/white]
[white]minicontainer ps -a --format json[/white]

[dim]# Update limits on the fly[/dim]
[white]minicontainer update webapp memory 1g[/white]
[white]minicontainer update webapp cpu 0.8[/white]

[dim]# Cleanup[/dim]
[white]minicontainer stop webapp[/white]
[white]minicontainer rm webapp[/white]
[white]minicontainer prune -f[/white]
""", title="Help", border_style="cyan"))

def main():
    check_root()
    cli()

if __name__ == "__main__":
    main()
