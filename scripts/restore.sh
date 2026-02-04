#!/bin/bash
# Restoration script for MiniContainer environment
PROJECT_ROOT="/home/student/container"
ROOTFS="/tmp/alpine-rootfs"

echo "==== MiniContainer Restoration ===="

# 1. Setup Rootfs
if [ ! -f "$ROOTFS/bin/busybox" ]; then
    echo "[1/5] Setting up minimal rootfs..."
    bash "$PROJECT_ROOT/scripts/setup_rootfs.sh"
else
    echo "[1/5] Rootfs already exists at $ROOTFS"
fi

# 2. Initialize Cgroups
echo "[2/5] Initializing cgroups..."
sudo mkdir -p /sys/fs/cgroup/minicontainer
sudo chmod -R 777 /sys/fs/cgroup/minicontainer

# Enable controllers in the subtree so child containers inherit them
# This is crucial for resource accounting (CPU/Memory metrics)
if [ -f /sys/fs/cgroup/cgroup.subtree_control ]; then
    # Enable at root level if not already enabled
    for ctrl in cpu memory pids; do
        if ! grep -q "$ctrl" /sys/fs/cgroup/cgroup.subtree_control; then
            sudo bash -c "echo +$ctrl > /sys/fs/cgroup/cgroup.subtree_control" 2>/dev/null
        fi
    done
fi

if [ -f /sys/fs/cgroup/minicontainer/cgroup.subtree_control ]; then
    echo "Enabling controllers in minicontainer subtree..."
    sudo bash -c "echo '+cpu' > /sys/fs/cgroup/minicontainer/cgroup.subtree_control" 2>/dev/null
    sudo bash -c "echo '+memory' > /sys/fs/cgroup/minicontainer/cgroup.subtree_control" 2>/dev/null
    sudo bash -c "echo '+pids' > /sys/fs/cgroup/minicontainer/cgroup.subtree_control" 2>/dev/null
fi

# 3. Build Runtime
echo "[3/5] Re-compiling runtime..."
cd "$PROJECT_ROOT/runtime" && make > /dev/null

# 4. Start Backend
if ! ss -tulpn | grep -q ":8000 "; then
    echo "[4/5] Starting Backend API..."
    cd "$PROJECT_ROOT/backend"
    sudo nohup ./venv/bin/python3 -m minicontainer.api > "$PROJECT_ROOT/backend.log" 2>&1 &
    sleep 2
else
    echo "[4/5] Backend already running on port 8000"
fi

# 5. Start Frontend
if ! ss -tulpn | grep -q ":5173 "; then
    echo "[5/5] Starting Frontend Dashboard..."
    cd "$PROJECT_ROOT/dashboard"
    nohup npm run dev > "$PROJECT_ROOT/frontend.log" 2>&1 &
    sleep 2
else
    echo "[5/5] Frontend already running on port 5173"
fi

echo "==================================="
echo "Restoration Complete!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "==================================="
