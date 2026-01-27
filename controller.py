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
from pathlib import Path
from threading import Thread, Event
from dataclasses import dataclass
from typing import List, Dict, Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich import box
    from rich.progress import SpinnerColumn, Progress, TextColumn
    from rich.align import Align
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
    from rich.progress import SpinnerColumn, Progress, TextColumn
    from rich.align import Align

console = Console()

# Configuration
RUNTIME_PATH = Path("/home/student/.gemini/antigravity/scratch/minicontainer/runtime/build/minicontainer-runtime")
CGROUP_BASE = Path("/sys/fs/cgroup/minicontainer")
DEFAULT_ROOTFS = "/tmp/alpine-rootfs"

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

def run_runtime(args: List[str], capture=True) -> tuple:
    """Run the C runtime with sudo"""
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(RUNTIME_PATH.parent)
    cmd = ["sudo", str(RUNTIME_PATH)] + args
    
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True, env=env)
        return result.returncode, result.stdout, result.stderr
    else:
        return subprocess.run(cmd, env=env).returncode, "", ""

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
                                if (cgroup / "cpu.stat").exists():
                                    for l in (cgroup / "cpu.stat").read_text().splitlines():
                                        if l.startswith("usage_usec"):
                                            c.cpu_percent = int(l.split()[1]) / 1e6
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
        ("1", "📋", "List Containers", "View all containers and their status"),
        ("2", "➕", "Create Container", "Create a new container with resource limits"),
        ("3", "⚡", "Execute Command", "Run workloads inside container's cgroup"),
        ("4", "📊", "Live Monitor", "Real-time metrics visualization"),
        ("5", "⏹️", "Stop Container", "Stop a running container"),
        ("6", "🗑️", "Delete Container", "Remove a container permanently"),
        ("7", "ℹ️", "System Info", "View system and runtime information"),
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
    
    table = Table(title="[bold bright_cyan]🐳 Container List[/]", 
                  box=box.DOUBLE_EDGE, show_lines=True, 
                  border_style="bright_blue", header_style="bold bright_magenta")
    table.add_column("#", style="dim", width=3, justify="center")
    table.add_column("Container ID", style="bright_cyan", no_wrap=True, width=14)
    table.add_column("Name", style="bright_magenta")
    table.add_column("Status", justify="center")
    table.add_column("CPU Time", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("Procs", justify="right")
    
    for i, c in enumerate(containers, 1):
        if c.state == "running":
            status = "[bold bright_green]● RUNNING[/]"
        elif c.state == "created":
            status = "[bold bright_yellow]○ CREATED[/]"
        else:
            status = "[bold bright_red]◌ STOPPED[/]"
        
        cpu_str = f"[bright_yellow]{c.cpu_percent:.2f}s[/]" if c.cpu_percent > 0 else "[dim]—[/]"
        mem_str = f"[bright_cyan]{c.memory_mb:.1f}MB[/]" if c.memory_mb > 0 else "[dim]—[/]"
        pids_str = f"[bright_green]{c.pids}[/]" if c.pids > 0 else "[dim]—[/]"
        
        table.add_row(str(i), c.id[:12], c.name, status, cpu_str, mem_str, pids_str)
    
    if not containers:
        console.print(Panel("[dim]No containers found. Create one with option 2![/]", 
                           border_style="yellow"))
    else:
        console.print(table)
    
    return containers

def create_container_cmd():
    """Interactive container creation"""
    console.print(Panel("[bold bright_cyan]➕ Create New Container[/]", 
                       border_style="bright_cyan"))
    
    name = Prompt.ask("[bright_magenta]Container name[/]", 
                     default=f"container-{int(time.time())}")
    rootfs = Prompt.ask("[bright_magenta]Rootfs path[/]", default=DEFAULT_ROOTFS)
    
    if not Path(rootfs).exists():
        console.print(f"[bold red]✗ Error: Rootfs path '{rootfs}' does not exist[/]")
        console.print("[dim]Run: minicontainer setup-rootfs[/]")
        return
    
    memory = IntPrompt.ask("[bright_magenta]Memory limit (MB)[/]", default=256)
    cpus = IntPrompt.ask("[bright_magenta]CPU limit (%)[/]", default=50)
    pids = IntPrompt.ask("[bright_magenta]Max processes[/]", default=100)
    
    console.print()
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
        console.print(f"[bold bright_green]✓ Container '{name}' created successfully![/]")
        console.print(f"[dim]Use option 3 (Execute Command) to run workloads inside the container.[/]")
    else:
        console.print(f"[bold red]✗ Failed to create: {stderr}[/]")

def stop_container_cmd():
    """Stop a running container"""
    containers = [c for c in get_containers() if c.state == "running"]
    if not containers:
        console.print("[yellow]No running containers to stop[/]")
        return
    
    console.print(Panel("[bold bright_red]⏹️ Stop Container[/]", border_style="bright_red"))
    
    for i, c in enumerate(containers, 1):
        console.print(f"  [bright_cyan]{i}[/] - [bright_magenta]{c.name}[/] ({c.id[:12]})")
    
    choice = Prompt.ask("\n[bright_magenta]Select container[/]", default="1")
    try:
        target = containers[int(choice) - 1]
    except:
        console.print("[red]Invalid selection[/]")
        return
    
    # Kill processes in cgroup
    cgroup = CGROUP_BASE / target.id
    if (cgroup / "cgroup.procs").exists():
        procs = (cgroup / "cgroup.procs").read_text().strip().split()
        for pid in procs:
            try:
                os.system(f"sudo kill -9 {pid} 2>/dev/null")
            except:
                pass
    
    console.print(f"[bold bright_green]✓ Container '{target.name}' stopped[/]")

def delete_container_cmd():
    """Delete a container"""
    containers = [c for c in get_containers() if c.state != "running"]
    if not containers:
        console.print("[yellow]No containers to delete (stop running ones first)[/]")
        return
    
    console.print(Panel("[bold bright_red]🗑️ Delete Container[/]", border_style="bright_red"))
    
    for i, c in enumerate(containers, 1):
        status = f"[yellow]{c.state}[/]"
        console.print(f"  [bright_cyan]{i}[/] - [bright_magenta]{c.name}[/] ({c.id[:12]}) {status}")
    
    choice = Prompt.ask("\n[bright_magenta]Select container[/]", default="1")
    try:
        target = containers[int(choice) - 1]
    except:
        console.print("[red]Invalid selection[/]")
        return
    
    if Confirm.ask(f"[bold red]Delete container '{target.name}'?[/]", default=False):
        code, _, stderr = run_runtime(["delete", target.id])
        if code == 0:
            console.print(f"[bold bright_green]✓ Container '{target.name}' deleted[/]")
        else:
            console.print(f"[bold red]✗ Failed: {stderr}[/]")

def monitor_cmd():
    """Real-time monitoring with live updates"""
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
                         border_style="bright_blue")
            table.add_column("Container", style="bright_cyan")
            table.add_column("Status")
            table.add_column("CPU Time", justify="right")
            table.add_column("Memory", justify="right")
            table.add_column("Mem %", justify="right")
            table.add_column("Procs", justify="right")
            
            for c in containers:
                if c.state == "running":
                    status = "[bold bright_green]● RUNNING[/]"
                elif c.state == "created":
                    status = "[bold bright_yellow]○ CREATED[/]"
                else:
                    status = "[bold red]◌ STOPPED[/]"
                
                mem_pct = (c.memory_mb / c.memory_limit_mb * 100) if c.memory_limit_mb > 0 else 0
                
                table.add_row(
                    c.name,
                    status,
                    f"[bright_yellow]{c.cpu_percent:.2f}s[/]",
                    f"[bright_cyan]{c.memory_mb:.1f}MB[/]",
                    f"{mem_pct:.0f}%",
                    str(c.pids) if c.pids > 0 else "—"
                )
            
            clear_screen()
            console.print(Panel("[bold bright_cyan]📊 Live Monitor[/] [dim](Ctrl+C to exit)[/]", 
                               border_style="bright_cyan"))
            console.print()
            
            if containers:
                console.print(table)
            else:
                console.print("[dim]No containers to monitor[/]")
            
            console.print(f"\n[dim]Last updated: {time.strftime('%H:%M:%S')}[/]")
            
            time.sleep(1)
    except:
        pass
    
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    console.print("\n[dim]Monitoring stopped[/]")

def system_info_cmd():
    """Display system information"""
    console.print(Panel("[bold bright_cyan]ℹ️ System Information[/]", 
                       border_style="bright_cyan"))
    
    info = Table(box=box.ROUNDED, show_header=False, border_style="bright_blue")
    info.add_column("Property", style="bright_magenta")
    info.add_column("Value", style="white")
    
    cgroup_status = "✓ Available" if CGROUP_BASE.exists() else "✗ Not found"
    cgroup_style = "bright_green" if CGROUP_BASE.exists() else "red"
    
    runtime_status = "✓ Found" if RUNTIME_PATH.exists() else "✗ Not found"
    runtime_style = "bright_green" if RUNTIME_PATH.exists() else "red"
    
    rootfs_status = "✓ Found" if Path(DEFAULT_ROOTFS).exists() else "✗ Not found"
    rootfs_style = "bright_green" if Path(DEFAULT_ROOTFS).exists() else "red"
    
    containers = get_containers()
    running = sum(1 for c in containers if c.state == "running")
    
    info.add_row("Runtime Path", str(RUNTIME_PATH))
    info.add_row("Runtime Status", f"[{runtime_style}]{runtime_status}[/]")
    info.add_row("Cgroup Base", str(CGROUP_BASE))
    info.add_row("Cgroup Status", f"[{cgroup_style}]{cgroup_status}[/]")
    info.add_row("Default Rootfs", DEFAULT_ROOTFS)
    info.add_row("Rootfs Status", f"[{rootfs_style}]{rootfs_status}[/]")
    info.add_row("Total Containers", str(len(containers)))
    info.add_row("Running Containers", f"[bright_green]{running}[/]")
    
    console.print(info)

def exec_cmd():
    """Execute REAL working commands inside container"""
    containers = get_containers()
    
    if not containers:
        console.print("[yellow]No containers available. Create one first![/]")
        return
    
    console.print(Panel("[bold bright_yellow]⚡ Execute Command in Container[/]", 
                       border_style="bright_yellow"))
    console.print("[dim]Commands run inside the container's cgroup for accurate resource tracking.[/]\n")
    
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
    
    # Working command menu
    console.print("\n[bold]Available Commands:[/]")
    commands = [
        ("1", "🔥", "CPU Stress", "Intensive counting loop - generates real CPU load"),
        ("2", "💾", "Memory Stress", "Allocate memory with dd - shows real memory usage"),
        ("3", "🔄", "Combined Stress", "CPU + Memory together - test both limits"),
        ("4", "⏱️", "Sleep Process", "Long sleep - keeps container running for monitoring"),
        ("5", "📊", "Math Calculations", "Heavy math operations - CPU intensive"),
        ("6", "✏️", "Custom Command", "Enter your own shell command"),
    ]
    
    for key, icon, name, desc in commands:
        console.print(f"  [bright_cyan]{key}[/] {icon} [bright_white]{name}[/] - [dim]{desc}[/]")
    
    cmd_choice = Prompt.ask("\n[bright_magenta]Select command[/]", default="1")
    
    cmd = ""
    duration = 120
    
    if cmd_choice == "1":
        duration = IntPrompt.ask("[bright_magenta]Duration (seconds)[/]", default=120)
        # This is a pure shell counting loop - works in any shell
        iterations = duration * 400000
        cmd = f"i=0; while [ $i -lt {iterations} ]; do i=$((i+1)); done; echo 'CPU stress complete'"
        console.print(f"\n[bold bright_yellow]🔥 Running CPU stress for ~{duration} seconds...[/]")
        
    elif cmd_choice == "2":
        size_mb = IntPrompt.ask("[bright_magenta]Memory to allocate (MB)[/]", default=100)
        duration = IntPrompt.ask("[bright_magenta]Duration (seconds)[/]", default=120)
        # dd writes to /dev/shm which is memory-backed
        cmd = f"dd if=/dev/zero of=/dev/shm/memtest bs=1M count={size_mb} 2>/dev/null && echo 'Allocated {size_mb}MB' && sleep {duration} && rm -f /dev/shm/memtest && echo 'Memory released'"
        console.print(f"\n[bold bright_cyan]💾 Allocating {size_mb}MB for {duration} seconds...[/]")
        
    elif cmd_choice == "3":
        duration = IntPrompt.ask("[bright_magenta]Duration (seconds)[/]", default=60)
        size_mb = IntPrompt.ask("[bright_magenta]Memory (MB)[/]", default=50)
        # Use timeout to ensure the command stops - simpler approach
        # First allocate memory, then run CPU-intensive loop that checks time
        cmd = f"""
dd if=/dev/zero of=/dev/shm/memtest bs=1M count={size_mb} 2>/dev/null
echo 'Allocated {size_mb}MB, running CPU stress...'
END=$(($(date +%s) + {duration}))
i=0
while [ $(date +%s) -lt $END ]; do
    i=$((i+1))
done
rm -f /dev/shm/memtest
echo 'Combined test complete after {duration}s'
"""
        console.print(f"\n[bold bright_magenta]🔄 Running combined stress for {duration}s...[/]")
        
    elif cmd_choice == "4":
        duration = IntPrompt.ask("[bright_magenta]Duration (seconds)[/]", default=300)
        cmd = f"echo 'Container will stay running for {duration}s...'; sleep {duration}; echo 'Done'"
        console.print(f"\n[bold bright_green]⏱️ Container will run for {duration} seconds...[/]")
        
    elif cmd_choice == "5":
        duration = IntPrompt.ask("[bright_magenta]Duration (seconds)[/]", default=60)
        # Math-intensive loop
        iterations = duration * 200000
        cmd = f"i=0; j=0; while [ $i -lt {iterations} ]; do j=$((j+i*i)); i=$((i+1)); done; echo 'Math complete: $j'"
        console.print(f"\n[bold bright_cyan]📊 Running math calculations for ~{duration}s...[/]")
        
    else:
        cmd = Prompt.ask("[bright_magenta]Enter command[/]", default="echo Hello from container")
        console.print(f"\n[bold]Running custom command...[/]")
    
    console.print("\n" + "─" * 60)
    
    # Create/prepare cgroup
    cgroup_path = CGROUP_BASE / target.id
    
    setup_cmd = f"""
    sudo mkdir -p {cgroup_path} 2>/dev/null
    echo '+cpu +memory +pids' | sudo tee /sys/fs/cgroup/minicontainer/cgroup.subtree_control >/dev/null 2>&1
    echo 268435456 | sudo tee {cgroup_path}/memory.max >/dev/null 2>&1
    echo 100 | sudo tee {cgroup_path}/pids.max >/dev/null 2>&1
    """
    os.system(f"bash -c \"{setup_cmd}\"")
    
    # Run command inside cgroup
    run_script = f"""
    echo $$ > {cgroup_path}/cgroup.procs 2>/dev/null
    {cmd}
    """
    
    console.print(f"[dim]Executing in cgroup: {cgroup_path}[/]\n")
    
    try:
        result = subprocess.run(
            ["sudo", "bash", "-c", run_script],
            capture_output=True, text=True, timeout=max(duration + 60, 600)
        )
        
        console.print("─" * 60)
        
        if result.stdout.strip():
            console.print(f"\n[bold bright_green]Output:[/]")
            console.print(Panel(result.stdout.strip(), border_style="bright_green"))
        
        # Show resource usage
        try:
            mem = int((cgroup_path / "memory.current").read_text().strip())
            cpu_stat = (cgroup_path / "cpu.stat").read_text()
            cpu_usec = 0
            for line in cpu_stat.splitlines():
                if line.startswith("usage_usec"):
                    cpu_usec = int(line.split()[1])
                    break
            
            console.print(f"\n[bold bright_cyan]📊 Resource Usage:[/]")
            console.print(f"  [bright_yellow]⚡ CPU Time:[/] {cpu_usec / 1e6:.2f} seconds")
            console.print(f"  [bright_cyan]💾 Memory:[/] {mem / 1048576:.2f} MB")
        except:
            pass
        
        console.print(f"\n[bold bright_green]✓ Command completed (exit code: {result.returncode})[/]")
        
    except subprocess.TimeoutExpired:
        console.print(f"[yellow]Command timed out[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
    
    console.print("[dim]Use option 4 (Monitor) or the web dashboard to see live metrics![/]")

def dashboard_info():
    """Show dashboard launch info"""
    console.print(Panel("[bold bright_cyan]🌐 Web Dashboard[/]", border_style="bright_cyan"))
    
    console.print("[bold]To start the web dashboard:[/]\n")
    console.print("  [bold]1.[/] Start the API server:")
    console.print("     [bright_cyan]minicontainer dashboard[/]")
    console.print()
    console.print("  [bold]2.[/] Start the frontend (in another terminal):")
    console.print("     [bright_cyan]cd ~/minicontainer/dashboard && npm run dev[/]")
    console.print()
    console.print("  [bold]3.[/] Open in browser:")
    console.print("     [bright_cyan]http://localhost:5173[/]")
    console.print()
    console.print("[dim]The dashboard shows live metrics with colorful graphs![/]")

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
            elif choice == "0":
                dashboard_info()
            elif choice.lower() == "q":
                console.print("\n[bold bright_cyan]👋 Goodbye![/]\n")
                break
            else:
                console.print("[yellow]Invalid option[/]")
            
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
