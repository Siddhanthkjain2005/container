#!/bin/sh
# Memory Stress Script for MiniContainer ML Testing
# Usage: mem_stress.sh [duration_seconds] [size_mb]

DURATION=${1:-30}
SIZE_MB=${2:-50}

echo "Starting memory stress test..."
echo "Duration: ${DURATION}s, Target Size: ${SIZE_MB}MB"

# Allocate memory by creating large strings
allocate_memory() {
    local size=$1
    local count=$((size * 100))  # Approximate KB
    
    # Use dd to allocate memory
    dd if=/dev/zero bs=1024 count=$count 2>/dev/null | cat > /dev/null &
    PID=$!
    
    # Also create a large temp file to hold memory
    dd if=/dev/zero of=/tmp/memtest bs=1M count=$size 2>/dev/null
}

# Gradual memory increase (for ML trend detection)
gradual_increase() {
    local target=$1
    local step=$((target / 10))
    
    for i in $(seq 1 10); do
        local current=$((step * i))
        echo "Allocating ${current}MB..."
        dd if=/dev/zero of=/tmp/memtest_$i bs=1M count=$step 2>/dev/null
        sleep 3
    done
}

# Memory spike pattern
spike_pattern() {
    while true; do
        echo "Memory spike..."
        dd if=/dev/zero of=/tmp/memspike bs=1M count=30 2>/dev/null
        sleep 2
        rm -f /tmp/memspike
        sleep 3
    done
}

case $SIZE_MB in
    spike)
        spike_pattern &
        PID=$!
        sleep $DURATION
        kill $PID 2>/dev/null
        ;;
    gradual)
        gradual_increase 50
        sleep $DURATION
        ;;
    *)
        allocate_memory $SIZE_MB
        sleep $DURATION
        ;;
esac

# Cleanup
rm -f /tmp/memtest* /tmp/memspike 2>/dev/null
echo "Memory stress test completed"
