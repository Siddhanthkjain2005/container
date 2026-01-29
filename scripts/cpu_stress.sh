#!/bin/sh
# CPU Stress Script for MiniContainer ML Testing
# Usage: cpu_stress.sh [duration_seconds] [intensity]
# Intensity: 1=low, 2=medium, 3=high, 4=spike

DURATION=${1:-30}
INTENSITY=${2:-2}

echo "Starting CPU stress test..."
echo "Duration: ${DURATION}s, Intensity: ${INTENSITY}"

stress_low() {
    # Low CPU usage (~20-30%)
    while true; do
        for i in $(seq 1 10000); do
            x=$((i * i))
        done
        sleep 0.1
    done
}

stress_medium() {
    # Medium CPU usage (~50-60%)
    while true; do
        for i in $(seq 1 50000); do
            x=$((i * i))
        done
        sleep 0.05
    done
}

stress_high() {
    # High CPU usage (~80-90%)
    while true; do
        for i in $(seq 1 100000); do
            x=$((i * i))
        done
    done
}

stress_spike() {
    # Alternating spikes (for ML anomaly detection)
    while true; do
        echo "Spike ON"
        for j in $(seq 1 5); do
            for i in $(seq 1 100000); do
                x=$((i * i))
            done
        done
        echo "Spike OFF"
        sleep 3
    done
}

case $INTENSITY in
    1) stress_low &;;
    2) stress_medium &;;
    3) stress_high &;;
    4) stress_spike &;;
    *) stress_medium &;;
esac

PID=$!
sleep $DURATION
kill $PID 2>/dev/null
echo "CPU stress test completed"
