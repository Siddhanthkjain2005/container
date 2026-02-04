"""
Shared workload commands used by both CLI (controller.py) and Website (api.py)
Keep these in sync to ensure consistent behavior.
"""

def get_workload_commands():
    """Return workload command templates used by both CLI and website"""
    return {
        "1": {
            "name": "Variable CPU Load",
            "icon": "⚡",
            "desc": "Alternating high/low CPU patterns",
            "color": "yellow",
            "template": lambda duration: f"echo '[Variable CPU] Starting alternating load pattern for {duration}s'; END=$(($(date +%s) + {duration})); while [ $(date +%s) -lt $END ]; do i=0; while [ $i -lt 800000 ]; do i=$((i+1)); done; sleep 1; done; echo '[Complete]'"
        },
        "2": {
            "name": "Memory Stress",
            "icon": "💾",
            "desc": "Allocate real RAM - shows memory usage",
            "color": "cyan",
            # Use yes|head instead of dd (device files blocked in chroot)
            # Files persist in /tmp and are tracked by cgroups
            "template": lambda duration, size_mb=50: f"echo '[Memory Stress] Allocating {size_mb}MB'; rm -rf /tmp/memstress; mkdir -p /tmp/memstress; i=0; while [ $i -lt {size_mb} ]; do yes AAAAAAAAAAAAAAAA | head -c 1048576 > /tmp/memstress/block$i; i=$((i+1)); echo \"Allocated $i MB\"; done; echo '[Done - memory persists until container restart]'; ls -sh /tmp/memstress | head -1"
        },
        "3": {
            "name": "CPU Spike Pattern",
            "icon": "🔥",
            "desc": "Bursts & idle - best for anomaly demos",
            "color": "pink",
            "template": lambda duration: f"echo '[Spike Demo] Running for {duration}s'; END=$(($(date +%s) + {duration})); while [ $(date +%s) -lt $END ]; do echo 'SPIKE!'; i=0; while [ $i -lt 1500000 ]; do i=$((i+1)); done; echo 'idle'; sleep 2; done; echo '[Complete]'"
        },
        "4": {
            "name": "Gradual Increase",
            "icon": "📈",
            "desc": "Slowly increasing load - shows trend detection",
            "color": "green",
            "template": lambda duration: f"echo '[Gradual Increase] Running for {duration}s'; intensity=100000; END=$(($(date +%s) + {duration})); while [ $(date +%s) -lt $END ]; do echo \"Load: $intensity\"; i=0; while [ $i -lt $intensity ]; do i=$((i+1)); done; intensity=$((intensity + 50000)); sleep 0.5; done; echo '[Complete]'"
        },
        "5": {
            "name": "Normal Workload",
            "icon": "⏱️",
            "desc": "Stable load - baseline for health scores",
            "color": "blue",
            "template": lambda duration: f"echo '[Normal Workload] Running for {duration}s'; END=$(($(date +%s) + {duration})); while [ $(date +%s) -lt $END ]; do i=0; while [ $i -lt 300000 ]; do i=$((i+1)); done; sleep 0.2; done; echo '[Complete]'"
        }
    }
