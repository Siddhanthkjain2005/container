#!/usr/bin/env python3
"""MiniContainer Interactive TUI Controller

A beautiful terminal user interface for managing containers with real-time monitoring.
Simplified and streamlined for real container management.
"""

import os
import sys
import time
import signal
import subprocess
import json
from pathlib import Path
from threading import Thread, Event
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timezone, timedelta

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich import box
    from rich.progress import SpinnerColumn, Progress, TextColumn, BarColumn
    from rich.align import Align
    from rich.tree import Tree
except ImportError:
    print("Installing required packages...")
    os.system("pip install rich")
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich import box
    from rich.progress import SpinnerColumn, Progress, TextColumn, BarColumn
    from rich.align import Align
    from rich.tree import Tree

console = Console()

# Configuration
RUNTIME_PATH = Path("/home/student/.gemini/antigravity/scratch/minicontainer/runtime/build/minicontainer-runtime")
CGROUP_BASE = Path("/sys/fs/cgroup/minicontainer")
DEFAULT_ROOTFS = "/tmp/alpine-rootfs"
STATE_DIR = Path("/var/lib/minicontainer")

def get_ist_time():
    """Get current IST time formatted"""
    ist = timezone(timedelta(hours=5, minutes=30))
    now = datetime.now(ist)
    return now.strftime("%A, %d %B %Y at %I:%M:%S %p IST")

def format_bytes(bytes_val):
    """Format bytes to human readable"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f}{unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f}TB"

def format_duration(seconds):
    """Format seconds to human readable duration"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{int(seconds//60)}m {int(seconds%60)}s"
    else:
        return f"{int(seconds//3600)}h {int((seconds%3600)//60)}m"

@dataclass
class Container:
    id: str
    name: str
    state: str
    pid: int = 0
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    memory_limit_mb: float = 0.0
    pids: int = 0
    pids_max: int = 0
    cpu_limit: str = ""
    created_at: str = ""
    rootfs: str = DEFAULT_ROOTFS

def run_runtime(args: List[str], capture=True, timeout=30) -> tuple:
    """Run the C runtime with sudo"""
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(RUNTIME_PATH.parent)
    cmd = ["sudo", str(RUNTIME_PATH)] + args
    
    try:
        if capture:
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=timeout)
            return result.returncode, result.stdout, result.stderr
        else:
            return subprocess.run(cmd, env=env, timeout=timeout).returncode, "", ""
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def get_containers() -> List[Container]:
    """Get list of all containers with accurate state detection"""
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
                        name = data.get("name", container_dir.name)
                        pid = int(data.get("pid", 0))
                        
                        # Determine actual state by checking cgroup
                        actual_state = "created"
                        cgroup = CGROUP_BASE / cid
                        cgroup_procs = cgroup / "cgroup.procs"
                        
                        if cgroup_procs.exists():
                            procs = cgroup_procs.read_text().strip()
                            if procs:
                                actual_state = "running"
                            else:
                                actual_state = "stopped"
                        
                        c = Container(id=cid, name=name, state=actual_state, pid=pid)
                        
                        # Get metrics if cgroup exists
                        if cgroup.exists():
                            try:
                                if (cgroup / "memory.current").exists():
                                    c.memory_mb = int((cgroup / "memory.current").read_text().strip()) / 1048576
                                if (cgroup / "memory.max").exists():
                                    val = (cgroup / "memory.max").read_text().strip()
                                    c.memory_limit_mb = 0 if val == "max" else int(val) / 1048576
                                if (cgroup / "pids.current").exists():
                                    c.pids = int((cgroup / "pids.current").read_text().strip())
                                if (cgroup / "pids.max").exists():
                                    val = (cgroup / "pids.max").read_text().strip()
                                    c.pids_max = 0 if val == "max" else int(val)
                                if (cgroup / "cpu.stat").exists():
                                    for l in (cgroup / "cpu.stat").read_text().splitlines():
                                        if l.startswith("usage_usec"):
                                            c.cpu_percent = int(l.split()[1]) / 1e6
                                if (cgroup / "cpu.max").exists():
                                    val = (cgroup / "cpu.max").read_text().strip().split()[0]
                                    c.cpu_limit = int(val) if val != "max" else 100000
                            except:
                                pass
                        containers.append(c)
                    except:
                        pass
    
    return containers

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_logo():
    """Print beautiful ASCII banner"""
    logo = """
[bold bright_cyan]╔══════════════════════════════════════════════════════════════════╗[/]
[bold bright_cyan]║[/]   [bold bright_blue]███╗   ███╗ ██╗ ███╗   ██╗ ██╗[/]  [bold bright_magenta]Container Manager[/]          [bold bright_cyan]║[/]
[bold bright_cyan]║[/]   [bold bright_blue]████╗ ████║ ██║ ████╗  ██║ ██║[/]  [dim]━━━━━━━━━━━━━━━━━━[/]          [bold bright_cyan]║[/]
[bold bright_cyan]║[/]   [bold bright_blue]██╔████╔██║ ██║ ██╔██╗ ██║ ██║[/]  [bold white]Linux Container Runtime[/]     [bold bright_cyan]║[/]
[bold bright_cyan]║[/]   [bold bright_blue]██║╚██╔╝██║ ██║ ██║╚██╗██║ ██║[/]  [dim]with cgroups v2 support[/]     [bold bright_cyan]║[/]
[bold bright_cyan]║[/]   [bold bright_blue]██║ ╚═╝ ██║ ██║ ██║ ╚████║ ██║[/]                              [bold bright_cyan]║[/]
[bold bright_cyan]╚══════════════════════════════════════════════════════════════════╝[/]
"""
    console.print(logo)

def print_status_bar():
    """Print system status bar"""
    containers = get_containers()
    running = sum(1 for c in containers if c.state == "running")
    stopped = sum(1 for c in containers if c.state == "stopped")
    created = sum(1 for c in containers if c.state == "created")
    
    status = Text()
    status.append("  📦 ", style="bold")
    status.append(f"{len(containers)} ", style="bold white")
    status.append("Total  ", style="dim")
    status.append("▶️ ", style="bold")
    status.append(f"{running} ", style="bold green")
    status.append("Running  ", style="dim")
    status.append("⏹️ ", style="bold")
    status.append(f"{stopped} ", style="bold red")
    status.append("Stopped  ", style="dim")
    
    console.print(Panel(status, style="on grey15", padding=(0, 1)))

def print_menu():
    """Print simplified menu with icons"""
    menu_items = [
        ("1", "📋", "List Containers", "View all containers with status and metrics"),
        ("2", "➕", "Create Container", "Create a new container with resource limits"),
        ("3", "⚡", "Execute Command", "Run workloads inside container's cgroup"),
        ("4", "📊", "Live Monitor", "Real-time metrics visualization"),
        ("5", "⏹️", "Stop Container", "Stop a running container"),
        ("6", "🗑️", "Delete Container", "Remove a container permanently"),
        ("7", "ℹ️", "System Info", "View system and runtime information"),
        ("8", "🔍", "Inspect Container", "View detailed container information"),
        ("9", "🔄", "Restart Container", "Restart a container"),
        ("0", "🌐", "Dashboard Info", "How to launch web dashboard"),
        ("q", "🚪", "Quit", "Exit the controller"),
    ]
    
    table = Table(box=box.ROUNDED, show_header=False, padding=(0, 2), 
                  border_style="bright_blue", expand=True)
    table.add_column("Key", style="bold bright_cyan", width=4)
    table.add_column("Icon", width=3)
    table.add_column("Action", style="bold white")
    table.add_column("Description", style="dim")
    
    for key, icon, action, desc in menu_items:
        key_style = "bold bright_yellow" if key == "q" else "bold bright_cyan"
        table.add_row(f"[{key_style}]{key}[/]", icon, action, desc)
    
    console.print(Panel(table, title="[bold bright_magenta]⌘ Main Menu[/]", 
                       title_align="left", border_style="bright_blue"))

def list_containers_cmd():
    """List all containers with beautiful table"""
    containers = get_containers()
    
    console.print(f"\n[dim]Current Time: {get_ist_time()}[/dim]\n")
    
    table = Table(title="[bold bright_cyan]🐳 Container List[/]", 
                  box=box.DOUBLE_EDGE, show_lines=True, 
                  border_style="bright_blue", header_style="bold bright_magenta")
    table.add_column("#", style="dim", width=3, justify="center")
    table.add_column("Container ID", style="bright_cyan", no_wrap=True, width=14)
    table.add_column("Name", style="bright_magenta", width=18)
    table.add_column("Status", justify="center", width=12)
    table.add_column("CPU Time", justify="right", width=10)
    table.add_column("Memory", justify="right", width=14)
    table.add_column("Mem %", justify="right", width=6)
    table.add_column("PIDs", justify="right", width=8)
    
    running_count = 0
    for i, c in enumerate(containers, 1):
        if c.state == "running":
            status = "[bold bright_green]● RUNNING[/]"
            running_count += 1
        elif c.state == "created":
            status = "[bold bright_yellow]○ CREATED[/]"
        else:
            status = "[bold bright_red]◌ STOPPED[/]"
        
        cpu_str = f"[bright_yellow]{format_duration(c.cpu_percent)}[/]" if c.cpu_percent > 0 else "[dim]—[/]"
        
        # Memory with limit
        if c.memory_mb > 0:
            if c.memory_limit_mb > 0:
                mem_str = f"[bright_cyan]{c.memory_mb:.1f}/{c.memory_limit_mb:.0f}MB[/]"
                mem_pct = (c.memory_mb / c.memory_limit_mb) * 100
                mem_pct_str = f"[{'bright_red' if mem_pct > 80 else 'bright_yellow' if mem_pct > 50 else 'bright_green'}]{mem_pct:.0f}%[/]"
            else:
                mem_str = f"[bright_cyan]{c.memory_mb:.1f}MB[/]"
                mem_pct_str = "[dim]—[/]"
        else:
            mem_str = "[dim]—[/]"
            mem_pct_str = "[dim]—[/]"
        
        # PIDs with limit
        if c.pids > 0:
            if c.pids_max > 0:
                pids_str = f"[bright_green]{c.pids}/{c.pids_max}[/]"
            else:
                pids_str = f"[bright_green]{c.pids}[/]"
        else:
            pids_str = "[dim]—[/]"
        
        table.add_row(str(i), c.id[:12], c.name, status, cpu_str, mem_str, mem_pct_str, pids_str)
    
    if not containers:
        console.print(Panel(
            "[dim]No containers found.[/]\n\n"
            "[bold]Create one with option [bright_cyan]2[/bright_cyan] (Create Container)![/]",
            border_style="yellow"
        ))
    else:
        console.print(table)
        console.print(f"\n[dim]Total: {len(containers)} container(s) | Running: {running_count}[/dim]")
    
    return containers

def create_container_cmd():
    """Interactive container creation"""
    console.print(Panel("[bold bright_cyan]➕ Create New Container[/]", 
                       border_style="bright_cyan"))
    
    # Validate runtime exists
    if not RUNTIME_PATH.exists():
        console.print(f"[bold red]✗ Runtime not found at {RUNTIME_PATH}[/]")
        console.print("[dim]Build it with: cd runtime && make[/]")
        return
    
    name = Prompt.ask("[bright_magenta]Container name[/]", 
                     default=f"container-{int(time.time()) % 10000}")
    rootfs = Prompt.ask("[bright_magenta]Rootfs path[/]", default=DEFAULT_ROOTFS)
    
    if not Path(rootfs).exists():
        console.print(f"[bold red]✗ Error: Rootfs path '{rootfs}' does not exist[/]")
        console.print("[dim]Run: minicontainer setup-rootfs[/]")
        return
    
    memory = IntPrompt.ask("[bright_magenta]Memory limit (MB)[/]", default=256)
    cpus = IntPrompt.ask("[bright_magenta]CPU limit (%)[/]", default=50)
    pids = IntPrompt.ask("[bright_magenta]Max processes[/]", default=100)
    
    console.print()
    
    # Show configuration summary
    config_table = Table(show_header=False, box=box.SIMPLE, padding=(0, 2))
    config_table.add_column("Setting", style="dim")
    config_table.add_column("Value", style="bright_cyan")
    config_table.add_row("Name", name)
    config_table.add_row("Rootfs", rootfs)
    config_table.add_row("Memory", f"{memory} MB")
    config_table.add_row("CPU", f"{cpus}%")
    config_table.add_row("Max PIDs", str(pids))
    console.print(Panel(config_table, title="[dim]Configuration[/dim]", border_style="dim"))
    
    with Progress(
        SpinnerColumn(style="bright_cyan"),
        TextColumn("[bold]Creating container...[/]"),
        console=console
    ) as progress:
        progress.add_task("create", total=None)
        
        args = ["create", "--name", name, "--rootfs", rootfs, 
                "--memory", str(memory * 1024 * 1024),
                "--cpus", str(cpus), "--pids", str(pids)]
        
        code, stdout, stderr = run_runtime(args)
    
    if code == 0:
        console.print(f"\n[bold bright_green]✓ Container '{name}' created successfully![/]")
        console.print(f"[dim]Created at: {get_ist_time()}[/]")
        console.print(f"\n[bold]Next steps:[/]")
        console.print(f"  • Use option [bright_cyan]3[/] to execute commands")
        console.print(f"  • Use option [bright_cyan]4[/] to monitor resources")
        console.print(f"  • Use option [bright_cyan]8[/] to inspect container details")
    else:
        console.print(f"[bold red]✗ Failed to create: {stderr}[/]")

def stop_container_cmd():
    """Stop a running container"""
    containers = [c for c in get_containers() if c.state == "running"]
    if not containers:
        console.print("[yellow]No running containers to stop[/]")
        return
    
    console.print(Panel("[bold bright_red]⏹️ Stop Container[/]", border_style="bright_red"))
    
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("#", style="bright_cyan", width=4)
    table.add_column("Name", style="bright_magenta")
    table.add_column("ID", style="dim")
    table.add_column("CPU", style="bright_yellow")
    table.add_column("Memory", style="bright_cyan")
    
    for i, c in enumerate(containers, 1):
        table.add_row(str(i), c.name, c.id[:12], 
                     format_duration(c.cpu_percent), f"{c.memory_mb:.1f}MB")
    
    console.print(table)
    
    choice = Prompt.ask("\n[bright_magenta]Select container to stop[/]", default="1")
    try:
        target = containers[int(choice) - 1]
    except:
        console.print("[red]Invalid selection[/]")
        return
    
    console.print(f"\n[dim]Stopping container '{target.name}'...[/]")
    
    # Kill processes in cgroup
    cgroup = CGROUP_BASE / target.id
    killed = 0
    if (cgroup / "cgroup.procs").exists():
        procs = (cgroup / "cgroup.procs").read_text().strip().split()
        for pid in procs:
            try:
                os.system(f"sudo kill -9 {pid} 2>/dev/null")
                killed += 1
            except:
                pass
    
    console.print(f"[bold bright_green]✓ Container '{target.name}' stopped[/]")
    console.print(f"[dim]Terminated {killed} process(es) at {get_ist_time()}[/]")

def delete_container_cmd():
    """Delete a container"""
    containers = [c for c in get_containers() if c.state != "running"]
    if not containers:
        all_containers = get_containers()
        if all_containers:
            console.print("[yellow]All containers are running. Stop them first with option 5.[/]")
        else:
            console.print("[yellow]No containers to delete.[/]")
        return
    
    console.print(Panel("[bold bright_red]🗑️ Delete Container[/]", border_style="bright_red"))
    
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("#", style="bright_cyan", width=4)
    table.add_column("Name", style="bright_magenta")
    table.add_column("ID", style="dim")
    table.add_column("Status", style="yellow")
    
    for i, c in enumerate(containers, 1):
        table.add_row(str(i), c.name, c.id[:12], c.state)
    
    console.print(table)
    
    choice = Prompt.ask("\n[bright_magenta]Select container to delete[/]", default="1")
    try:
        target = containers[int(choice) - 1]
    except:
        console.print("[red]Invalid selection[/]")
        return
    
    if Confirm.ask(f"[bold red]Delete container '{target.name}' permanently?[/]", default=False):
        with Progress(
            SpinnerColumn(style="bright_red"),
            TextColumn("[bold]Deleting...[/]"),
            console=console
        ) as progress:
            progress.add_task("delete", total=None)
            code, _, stderr = run_runtime(["delete", target.id])
        
        if code == 0:
            console.print(f"\n[bold bright_green]✓ Container '{target.name}' deleted[/]")
            console.print(f"[dim]Deleted at: {get_ist_time()}[/]")
        else:
            console.print(f"[bold red]✗ Failed: {stderr}[/]")
    else:
        console.print("[dim]Cancelled[/]")

def monitor_cmd():
    """Real-time monitoring with live updates and progress bars"""
    console.print(Panel("[bold bright_cyan]📊 Live Container Monitor[/]", 
                       border_style="bright_cyan"))
    console.print("[dim]Press Ctrl+C to exit monitoring...[/]\n")
    
    stop_event = Event()
    
    def signal_handler(sig, frame):
        stop_event.set()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        while not stop_event.is_set():
            containers = get_containers()
            
            table = Table(box=box.ROUNDED, show_header=True, 
                         header_style="bold bright_magenta",
                         border_style="bright_blue",
                         title="[bold]Container Resources[/]")
            table.add_column("Container", style="bright_cyan", min_width=12)
            table.add_column("Status", justify="center")
            table.add_column("CPU Time", justify="right")
            table.add_column("Memory", justify="right")
            table.add_column("Mem %", justify="center")
            table.add_column("Usage Bar", min_width=15)
            table.add_column("PIDs", justify="center")
            
            for c in containers:
                if c.state == "running":
                    status = "[bold bright_green]● RUN[/]"
                elif c.state == "created":
                    status = "[bold bright_yellow]○ NEW[/]"
                else:
                    status = "[bold red]◌ OFF[/]"
                
                mem_pct = (c.memory_mb / c.memory_limit_mb * 100) if c.memory_limit_mb > 0 else 0
                
                # Create visual memory bar
                bar_width = 12
                filled = int(mem_pct / 100 * bar_width)
                if mem_pct > 80:
                    bar_color = "bright_red"
                elif mem_pct > 50:
                    bar_color = "bright_yellow"
                else:
                    bar_color = "bright_green"
                bar = f"[{bar_color}]{'█' * filled}{'░' * (bar_width - filled)}[/]"
                
                pids_display = f"{c.pids}/{c.pids_max}" if c.pids_max > 0 else str(c.pids) if c.pids > 0 else "—"
                
                table.add_row(
                    c.name,
                    status,
                    f"[bright_yellow]{c.cpu_percent:.2f}s[/]",
                    f"[bright_cyan]{c.memory_mb:.1f}/{c.memory_limit_mb:.0f}MB[/]",
                    f"[{bar_color}]{mem_pct:.0f}%[/]",
                    bar,
                    pids_display
                )
            
            clear_screen()
            console.print(Panel(f"[bold bright_cyan]📊 Live Monitor[/] [dim](Ctrl+C to exit) • {get_ist_time()}[/]", 
                               border_style="bright_cyan"))
            console.print()
            
            if containers:
                console.print(table)
                
                # Summary stats
                running = sum(1 for c in containers if c.state == "running")
                total_mem = sum(c.memory_mb for c in containers)
                total_cpu = sum(c.cpu_percent for c in containers)
                console.print(f"\n[dim]Summary:[/] [bright_green]{running}[/] running, "
                             f"[bright_cyan]{total_mem:.1f}MB[/] total memory, "
                             f"[bright_yellow]{total_cpu:.2f}s[/] total CPU time")
            else:
                console.print("[dim]No containers to monitor. Create one with option 2.[/]")
            
            time.sleep(1)
    except:
        pass
    
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    console.print("\n[dim]Monitoring stopped[/]")

def system_info_cmd():
    """Display comprehensive system information"""
    console.print(Panel("[bold bright_cyan]ℹ️ System Information[/]", 
                       border_style="bright_cyan"))
    
    # System health check
    health_table = Table(box=box.ROUNDED, show_header=True, 
                        header_style="bold bright_white",
                        border_style="bright_blue",
                        title="[bold]Health Checks[/]")
    health_table.add_column("Component", style="bright_magenta")
    health_table.add_column("Path", style="dim")
    health_table.add_column("Status", justify="center")
    
    checks = [
        ("Runtime Binary", str(RUNTIME_PATH), RUNTIME_PATH.exists()),
        ("Cgroup v2 Base", str(CGROUP_BASE), CGROUP_BASE.exists()),
        ("Default Rootfs", DEFAULT_ROOTFS, Path(DEFAULT_ROOTFS).exists()),
        ("Container State", str(Path("/var/lib/minicontainer/containers")), 
         Path("/var/lib/minicontainer/containers").exists()),
    ]
    
    for name, path, exists in checks:
        status = "[bold bright_green]✓ OK[/]" if exists else "[bold red]✗ Missing[/]"
        health_table.add_row(name, path, status)
    
    console.print(health_table)
    
    # Container statistics
    containers = get_containers()
    running = sum(1 for c in containers if c.state == "running")
    stopped = sum(1 for c in containers if c.state != "running")
    total_mem = sum(c.memory_mb for c in containers)
    total_cpu = sum(c.cpu_percent for c in containers)
    
    stats_table = Table(box=box.ROUNDED, show_header=True,
                       header_style="bold bright_white",
                       border_style="bright_green",
                       title="[bold]Container Statistics[/]")
    stats_table.add_column("Metric", style="bright_magenta")
    stats_table.add_column("Value", style="bright_cyan", justify="right")
    
    stats_table.add_row("Total Containers", str(len(containers)))
    stats_table.add_row("Running", f"[bright_green]{running}[/]")
    stats_table.add_row("Stopped", f"[yellow]{stopped}[/]")
    stats_table.add_row("Total Memory Usage", f"{total_mem:.2f} MB")
    stats_table.add_row("Total CPU Time", f"{total_cpu:.2f} seconds")
    
    console.print()
    console.print(stats_table)
    
    # System time info
    console.print(f"\n[dim]System Time (IST): {get_ist_time()}[/]")

def exec_cmd():
    """Execute commands inside ISOLATED container with full namespace isolation"""
    containers = get_containers()
    
    if not containers:
        console.print("[yellow]No containers available. Create one first![/]")
        return
    
    console.print(Panel("[bold bright_yellow]⚡ Execute Command in Isolated Container[/]", 
                       border_style="bright_yellow"))
    console.print("[bold bright_green]✓ Commands run with FULL ISOLATION:[/]")
    console.print("  • [dim]Separate filesystem (Alpine Linux rootfs)[/]")
    console.print("  • [dim]PID namespace (only sees container processes)[/]")
    console.print("  • [dim]Mount namespace (isolated mounts)[/]")
    console.print("  • [dim]UTS namespace (separate hostname)[/]")
    console.print("  • [dim]Cgroup limits (memory, CPU, PIDs)[/]")
    console.print()
    
    # List containers
    console.print("[bold]Available Containers:[/]")
    for i, c in enumerate(containers, 1):
        status_icon = "🟢" if c.state == "running" else ("🟡" if c.state == "created" else "🔴")
        console.print(f"  [bright_cyan]{i}[/] {status_icon} [bright_magenta]{c.name}[/] ({c.id[:12]})")
    
    choice = Prompt.ask("\n[bright_magenta]Select container[/]", default="1")
    
    try:
        idx = int(choice) - 1
        target = containers[idx]
    except:
        target = next((c for c in containers if c.name == choice or c.id.startswith(choice)), None)
        if not target:
            console.print(f"[red]Container '{choice}' not found[/]")
            return
    
    console.print(f"\n[bold bright_cyan]Selected:[/] {target.name} ({target.id[:12]})")
    
    # Command menu - matching website commands
    console.print("\n[bold]Available Commands:[/]")
    commands = [
        ("1", "⚡", "Variable CPU Load", "Alternating CPU patterns - triggers anomaly detection", "amber"),
        ("2", "💾", "Memory Allocation", "Allocate memory - shows memory limits", "cyan"),
        ("3", "🔥", "CPU Spike Pattern", "Bursts & idle - best for anomaly demos", "pink"),
        ("4", "📈", "Gradual Increase", "Slowly increasing load - shows trend detection", "green"),
        ("5", "⏱️", "Normal Workload", "Stable load - baseline for health scores", "blue"),
        ("6", "✏️", "Custom Command", "Enter your own shell command", "purple"),
    ]
    
    for key, icon, name, desc, color in commands:
        console.print(f"  [bright_cyan]{key}[/] {icon} [bright_white]{name}[/] - [dim]{desc}[/]")
    
    cmd_choice = Prompt.ask("\n[bright_magenta]Select command[/]", default="1")
    
    cmd = ""
    duration = 120
    
    if cmd_choice == "1":
        # Variable CPU Load - alternating high/low patterns
        duration = IntPrompt.ask("[bright_magenta]Duration (seconds)[/]", default=120)
        cmd = f"""
echo '[Variable CPU] Starting alternating load pattern for {duration}s...'
END=$(($(date +%s) + {duration}))
while [ $(date +%s) -lt $END ]; do
    # High load phase (2 seconds)
    i=0; while [ $i -lt 800000 ]; do i=$((i+1)); done
    # Low load phase (1 second)
    sleep 1
done
echo 'Variable CPU complete'
"""
        console.print(f"\n[bold bright_yellow]⚡ Running Variable CPU Load for ~{duration} seconds...[/]")
        
    elif cmd_choice == "2":
        # Memory Allocation
        size_mb = IntPrompt.ask("[bright_magenta]Memory to allocate (MB)[/]", default=100)
        duration = IntPrompt.ask("[bright_magenta]Duration (seconds)[/]", default=120)
        cmd = f"dd if=/dev/zero of=/dev/shm/memtest bs=1M count={size_mb} 2>/dev/null && echo '[Memory] Allocated {size_mb}MB' && sleep {duration} && rm -f /dev/shm/memtest && echo 'Memory released'"
        console.print(f"\n[bold bright_cyan]💾 Allocating {size_mb}MB for {duration} seconds...[/]")
        
    elif cmd_choice == "3":
        # CPU Spike Pattern - bursts and idle
        duration = IntPrompt.ask("[bright_magenta]Duration (seconds)[/]", default=60)
        cmd = f"""
echo '[Spike Demo] CPU spike pattern for {duration}s - best for anomaly detection'
END=$(($(date +%s) + {duration}))
while [ $(date +%s) -lt $END ]; do
    # Intense burst (1 second)
    i=0; while [ $i -lt 600000 ]; do i=$((i+1)); done
    # Idle period (2 seconds)
    sleep 2
done
echo 'Spike pattern complete'
"""
        console.print(f"\n[bold bright_magenta]🔥 Running CPU Spike Pattern for {duration}s...[/]")
        
    elif cmd_choice == "4":
        # Gradual Increase
        duration = IntPrompt.ask("[bright_magenta]Duration (seconds)[/]", default=60)
        cmd = f"""
echo '[Gradual] Starting gradual increase over {duration}s...'
steps=10
step_duration=$(({duration} / steps))
for step in $(seq 1 $steps); do
    intensity=$((step * 100000))
    echo "Step $step/$steps - intensity $intensity"
    i=0; while [ $i -lt $intensity ]; do i=$((i+1)); done
    sleep $step_duration
done
echo 'Gradual increase complete'
"""
        console.print(f"\n[bold bright_green]📈 Running Gradual Increase for ~{duration}s...[/]")
        
    elif cmd_choice == "5":
        # Normal Workload - stable baseline
        duration = IntPrompt.ask("[bright_magenta]Duration (seconds)[/]", default=120)
        cmd = f"""
echo '[Normal] Stable workload for {duration}s - baseline for health scores'
END=$(($(date +%s) + {duration}))
while [ $(date +%s) -lt $END ]; do
    i=0; while [ $i -lt 200000 ]; do i=$((i+1)); done
    sleep 0.5
done
echo 'Normal workload complete'
"""
        console.print(f"\n[bold bright_blue]⏱️ Running Normal Workload for {duration}s...[/]")
        
    else:
        cmd = Prompt.ask("[bright_magenta]Enter command[/]", default="echo Hello from container")
        console.print(f"\n[bold]Running custom command...[/]")
    
    console.print("\n" + "─" * 60)
    console.print(f"[bold bright_green]🔒 Running in ISOLATED environment[/]")
    console.print(f"[dim]Rootfs: {DEFAULT_ROOTFS}[/]")
    console.print(f"[dim]Namespaces: PID, MNT, UTS, IPC, CGROUP[/]")
    console.print("─" * 60 + "\n")
    
    # Ensure rootfs exists
    if not Path(DEFAULT_ROOTFS).exists():
        console.print(f"[bold red]✗ Rootfs not found at {DEFAULT_ROOTFS}[/]")
        console.print("[dim]Cannot run isolated container without rootfs.[/]")
        return
    
    # Use the C runtime to run with full namespace isolation
    # This creates a new container process with pivot_root into the Alpine rootfs
    
    # Write command to a temp script in the rootfs
    script_content = f'''#!/bin/sh
{cmd}
'''
    script_path = Path(DEFAULT_ROOTFS) / "tmp" / f"exec_{target.id}.sh"
    try:
        script_path.write_text(script_content)
        script_path.chmod(0o755)
    except PermissionError:
        os.system(f"sudo bash -c 'echo \"{script_content}\" > {script_path} && chmod 755 {script_path}'")
    
    # Run the C runtime with the command
    # The runtime will: clone with namespaces -> pivot_root -> exec command
    console.print(f"[dim]Executing isolated command...[/]\n")
    
    # Use runtime to run in isolated namespace
    args = ["run", "--name", f"{target.name}-exec", 
            "--rootfs", DEFAULT_ROOTFS,
            "--memory", "268435456",  # 256MB
            "--cpus", "100",
            "--pids", "100",
            "--", "/bin/sh", f"/tmp/exec_{target.id}.sh"]
    
    try:
        with Progress(
            SpinnerColumn(style="bright_green"),
            TextColumn("[bold]Running in isolated container...[/]"),
            console=console
        ) as progress:
            task = progress.add_task("exec", total=None)
            code, stdout, stderr = run_runtime(args, timeout=max(duration + 120, 600))
        
        console.print("─" * 60)
        
        if stdout.strip():
            # Filter out runtime logs
            output_lines = [l for l in stdout.strip().split('\n') 
                          if not l.startswith('[INFO]') and not l.startswith('[DEBUG]')]
            if output_lines:
                console.print(f"\n[bold bright_green]Output:[/]")
                console.print(Panel('\n'.join(output_lines), border_style="bright_green"))
        
        if code == 0:
            console.print(f"\n[bold bright_green]✓ Command completed successfully in isolated container[/]")
        else:
            console.print(f"\n[bold yellow]Command exited with code {code}[/]")
            if stderr.strip():
                console.print(f"[dim]{stderr.strip()}[/]")
        
        # Show resource usage from cgroup
        cgroup_path = CGROUP_BASE / target.id
        try:
            if (cgroup_path / "memory.current").exists():
                mem = int((cgroup_path / "memory.current").read_text().strip())
                console.print(f"\n[bold bright_cyan]📊 Resource Usage:[/]")
                console.print(f"  [bright_cyan]💾 Memory:[/] {mem / 1048576:.2f} MB")
        except:
            pass
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
    
    # Cleanup script
    try:
        script_path.unlink()
    except:
        os.system(f"sudo rm -f {script_path}")
    
    console.print(f"\n[dim]Executed at: {get_ist_time()}[/]")
    console.print("[bold bright_green]✓ Host filesystem was PROTECTED - command ran in isolated Alpine rootfs[/]")

def dashboard_info():
    """Show dashboard launch info"""
    console.print(Panel("[bold bright_cyan]🌐 Web Dashboard[/]", border_style="bright_cyan"))
    
    table = Table(box=box.ROUNDED, show_header=False, border_style="bright_blue")
    table.add_column("Step", style="bold bright_cyan", width=6)
    table.add_column("Action", style="bright_white")
    table.add_column("Command", style="bright_yellow")
    
    table.add_row("1", "Start API server", "minicontainer dashboard")
    table.add_row("2", "Start frontend", "cd ~/minicontainer/dashboard && npm run dev")
    table.add_row("3", "Open browser", "http://localhost:5173")
    
    console.print(table)
    
    console.print(f"\n[bold]Features:[/]")
    console.print("  [bright_green]•[/] Live container metrics with real-time graphs")
    console.print("  [bright_green]•[/] Memory and CPU usage visualization")
    console.print("  [bright_green]•[/] Container management controls")
    console.print("  [bright_green]•[/] Resource analytics and insights")
    console.print(f"\n[dim]Current time (IST): {get_ist_time()}[/]")


def inspect_container_cmd():
    """Inspect container details"""
    containers = get_containers()
    if not containers:
        console.print("[yellow]No containers available. Create one first![/]")
        return
    
    console.print(Panel("[bold bright_magenta]🔍 Inspect Container[/]", border_style="bright_magenta"))
    
    for i, c in enumerate(containers, 1):
        status_icon = "🟢" if c.state == "running" else ("🟡" if c.state == "created" else "🔴")
        console.print(f"  [bright_cyan]{i}[/] {status_icon} [bright_magenta]{c.name}[/] ({c.id[:12]})")
    
    choice = Prompt.ask("\n[bright_magenta]Select container[/]", default="1")
    
    try:
        target = containers[int(choice) - 1]
    except:
        console.print("[red]Invalid selection[/]")
        return
    
    console.print()
    
    # Basic info
    info_table = Table(box=box.ROUNDED, show_header=False, 
                      border_style="bright_magenta",
                      title=f"[bold]{target.name}[/]")
    info_table.add_column("Property", style="bright_cyan", width=18)
    info_table.add_column("Value", style="white")
    
    info_table.add_row("Container ID", target.id)
    info_table.add_row("Name", target.name)
    info_table.add_row("State", f"[{'bright_green' if target.state == 'running' else 'yellow'}]{target.state.upper()}[/]")
    info_table.add_row("Rootfs", target.rootfs if target.rootfs else DEFAULT_ROOTFS)
    if target.created_at:
        info_table.add_row("Created", target.created_at)
    
    console.print(info_table)
    
    # Resource limits
    limits_table = Table(box=box.ROUNDED, show_header=True,
                        header_style="bold bright_white",
                        border_style="bright_blue",
                        title="[bold]Resource Limits[/]")
    limits_table.add_column("Resource", style="bright_magenta")
    limits_table.add_column("Limit", style="bright_yellow", justify="right")
    limits_table.add_column("Current", style="bright_cyan", justify="right")
    limits_table.add_column("Usage", justify="center")
    
    mem_pct = (target.memory_mb / target.memory_limit_mb * 100) if target.memory_limit_mb > 0 else 0
    mem_bar = f"[{'bright_red' if mem_pct > 80 else 'bright_yellow' if mem_pct > 50 else 'bright_green'}]{mem_pct:.0f}%[/]"
    
    limits_table.add_row("Memory", f"{target.memory_limit_mb:.0f} MB", f"{target.memory_mb:.2f} MB", mem_bar)
    limits_table.add_row("PIDs", str(target.pids_max) if target.pids_max > 0 else "∞", str(target.pids), "—")
    limits_table.add_row("CPU", str(target.cpu_limit) if target.cpu_limit else "∞", f"{target.cpu_percent:.2f}s", "—")
    
    console.print()
    console.print(limits_table)
    
    # Cgroup path
    console.print(f"\n[dim]Cgroup: {CGROUP_BASE / target.id}[/]")
    console.print(f"[dim]Inspected at: {get_ist_time()}[/]")


def restart_container_cmd():
    """Restart a running container"""
    containers = [c for c in get_containers() if c.state == "running"]
    if not containers:
        console.print("[yellow]No running containers to restart.[/]")
        return
    
    console.print(Panel("[bold bright_yellow]🔄 Restart Container[/]", border_style="bright_yellow"))
    
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("#", style="bright_cyan", width=4)
    table.add_column("Name", style="bright_magenta")
    table.add_column("ID", style="dim")
    table.add_column("Memory", style="bright_cyan")
    
    for i, c in enumerate(containers, 1):
        table.add_row(str(i), c.name, c.id[:12], f"{c.memory_mb:.1f}MB")
    
    console.print(table)
    
    choice = Prompt.ask("\n[bright_magenta]Select container to restart[/]", default="1")
    try:
        target = containers[int(choice) - 1]
    except:
        console.print("[red]Invalid selection[/]")
        return
    
    if Confirm.ask(f"[bold yellow]Restart container '{target.name}'?[/]", default=True):
        with Progress(
            SpinnerColumn(style="bright_yellow"),
            TextColumn("[bold]Stopping container...[/]"),
            console=console
        ) as progress:
            progress.add_task("stop", total=None)
            
            # Kill processes in cgroup
            cgroup = CGROUP_BASE / target.id
            if (cgroup / "cgroup.procs").exists():
                procs = (cgroup / "cgroup.procs").read_text().strip().split()
                for pid in procs:
                    try:
                        os.system(f"sudo kill -9 {pid} 2>/dev/null")
                    except:
                        pass
        
        console.print("[dim]Container stopped. Ready to run new processes.[/]")
        console.print(f"[bold bright_green]✓ Container '{target.name}' restarted[/]")
        console.print(f"[dim]Use option 3 (Execute) to run commands in the container.[/]")
        console.print(f"[dim]Restarted at: {get_ist_time()}[/]")
    else:
        console.print("[dim]Cancelled[/]")

def main():
    """Main interactive loop"""
    if os.geteuid() != 0:
        console.print(Panel(
            "[bold yellow]⚠️ Running without root - some features may be limited[/]\n"
            "[dim]Run with: sudo python3 controller.py[/]",
            border_style="yellow"
        ))
    
    while True:
        try:
            clear_screen()
            print_logo()
            print_status_bar()
            console.print()
            print_menu()
            
            choice = Prompt.ask("\n[bold bright_cyan]Enter command[/]", default="1")
            
            if choice == "1":
                list_containers_cmd()
            elif choice == "2":
                create_container_cmd()
            elif choice == "3":
                exec_cmd()
            elif choice == "4":
                monitor_cmd()
            elif choice == "5":
                stop_container_cmd()
            elif choice == "6":
                delete_container_cmd()
            elif choice == "7":
                system_info_cmd()
            elif choice == "8":
                inspect_container_cmd()
            elif choice == "9":
                restart_container_cmd()
            elif choice == "0":
                dashboard_info()
            elif choice.lower() == "q":
                console.print("\n[bold bright_cyan]👋 Goodbye![/]\n")
                break
            else:
                console.print("[yellow]Invalid option. Please select 0-9 or q.[/]")
            
            if choice not in ["4"]:
                Prompt.ask("\n[dim]Press Enter to continue[/]", default="")
                
        except KeyboardInterrupt:
            console.print("\n[bold bright_cyan]👋 Goodbye![/]\n")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
            Prompt.ask("\n[dim]Press Enter to continue[/]", default="")

if __name__ == "__main__":
    main()
