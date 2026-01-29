#!/bin/sh
# Combined Stress Test for ML Anomaly Detection
# This script generates patterns that will trigger different ML alerts
# Usage: ml_test.sh [test_type]
# test_types: baseline, spike, gradual, random, all

TEST_TYPE=${1:-all}

echo "========================================"
echo "MiniContainer ML Anomaly Detection Test"
echo "========================================"
echo "Test Type: $TEST_TYPE"
echo ""

# Baseline test - stable workload for learning
test_baseline() {
    echo "[1/5] BASELINE TEST - Stable workload (30s)"
    echo "  Purpose: Allow ML to learn normal behavior"
    for i in $(seq 1 30); do
        for j in $(seq 1 10000); do
            x=$((j * j))
        done
        sleep 0.5
    done
    echo "  Baseline complete!"
}

# Spike test - sudden CPU spike
test_spike() {
    echo "[2/5] SPIKE TEST - Sudden CPU spike (10s)"
    echo "  Purpose: Trigger sudden_change and cpu_spike alerts"
    for i in $(seq 1 10); do
        for j in $(seq 1 200000); do
            x=$((j * j))
        done
    done
    echo "  Spike complete!"
}

# Gradual increase test
test_gradual() {
    echo "[3/5] GRADUAL TEST - Increasing load (30s)"
    echo "  Purpose: Trigger trend detection"
    for level in 1 2 3 4 5; do
        echo "    Level $level..."
        iterations=$((level * 20000))
        for i in $(seq 1 6); do
            for j in $(seq 1 $iterations); do
                x=$((j * j))
            done
        done
    done
    echo "  Gradual test complete!"
}

# Random pattern test
test_random() {
    echo "[4/5] RANDOM TEST - Variable load (20s)"
    echo "  Purpose: Test variance detection"
    for i in $(seq 1 20); do
        # Random intensity
        rand=$((i % 4 + 1))
        iterations=$((rand * 30000))
        for j in $(seq 1 $iterations); do
            x=$((j * j))
        done
        sleep 0.3
    done
    echo "  Random test complete!"
}

# Memory test
test_memory() {
    echo "[5/5] MEMORY TEST - Allocating memory (10s)"
    echo "  Purpose: Trigger memory anomaly alerts"
    dd if=/dev/zero of=/tmp/mltest bs=1M count=40 2>/dev/null
    sleep 10
    rm -f /tmp/mltest
    echo "  Memory test complete!"
}

# Run tests based on type
case $TEST_TYPE in
    baseline)
        test_baseline
        ;;
    spike)
        test_spike
        ;;
    gradual)
        test_gradual
        ;;
    random)
        test_random
        ;;
    memory)
        test_memory
        ;;
    all)
        echo "Running complete ML test suite..."
        echo ""
        test_baseline
        echo ""
        sleep 2
        test_spike
        echo ""
        sleep 2
        test_gradual
        echo ""
        sleep 2
        test_random
        echo ""
        sleep 2
        test_memory
        ;;
    *)
        echo "Unknown test type: $TEST_TYPE"
        echo "Options: baseline, spike, gradual, random, memory, all"
        exit 1
        ;;
esac

echo ""
echo "========================================"
echo "ML Test Complete!"
echo "Check the Analytics page for detected anomalies"
echo "========================================"
