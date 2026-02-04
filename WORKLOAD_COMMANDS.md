# Workload Commands Reference

This document explains the 5 workload commands available in both the CLI (`controller.py`) and the Web Dashboard. These commands create different CPU/memory patterns to demonstrate container resource limits and ML-based anomaly detection.

---

## **1. Variable CPU Load** ⚡

```bash
echo '[Variable CPU] Starting alternating load pattern for Xs'
END=$(($(date +%s) + X))
while [ $(date +%s) -lt $END ]; do
    i=0; while [ $i -lt 800000 ]; do i=$((i+1)); done  # HIGH CPU burst
    sleep 1                                              # REST period
done
echo '[Complete]'
```

### CPU Pattern: 📈📉📈📉📈📉 (Sawtooth wave)
- **Burst**: Counts to 800,000 → ~0.5-1 second of HIGH CPU (varies by hardware)
- **Rest**: 1 second sleep → CPU drops to near 0%
- **Result**: Alternating high/low pattern, good for showing ML adaptation to changing loads

---

## **2. Memory Allocation** 💾

```bash
echo '[Memory Test] Allocating XMB'
dd if=/dev/zero of=/tmp/memtest bs=1M count=X  # Allocate memory
echo '[Holding memory for Ys]'
sleep Y                                          # Hold it
rm -f /tmp/memtest                               # Release
echo '[Memory Released]'
```

### CPU Pattern: 📈 (single spike during dd, then flat)
- **Allocate**: `dd` creates brief CPU spike while writing zeros
- **Hold**: Sleep causes ~0% CPU, but MEMORY stays high
- **Result**: Tests memory limits, not CPU. Memory usage goes up and stays steady.

---

## **3. CPU Spike Pattern** 🔥

```bash
echo '[Spike Demo] Running for Xs'
END=$(($(date +%s) + X))
while [ $(date +%s) -lt $END ]; do
    echo 'SPIKE!'
    i=0; while [ $i -lt 1500000 ]; do i=$((i+1)); done  # INTENSE burst (1.5M iterations)
    echo 'idle'
    sleep 2                                              # Long rest (2 seconds)
done
echo '[Complete]'
```

### CPU Pattern: 📈____📈____📈____ (Spikes with long gaps)
- **Burst**: Counts to 1,500,000 → ~1-2 seconds of PEAK CPU
- **Rest**: 2 second sleep → Extended idle period
- **Result**: Dramatic spikes separated by idle. **Best for anomaly detection demos** - the ML should detect the sudden spikes as anomalies.

---

## **4. Gradual Increase** 📈

```bash
echo '[Gradual Increase] Running for Xs'
intensity=100000                                  # Start LOW
END=$(($(date +%s) + X))
while [ $(date +%s) -lt $END ]; do
    echo "Load: $intensity"
    i=0; while [ $i -lt $intensity ]; do i=$((i+1)); done  # Variable work
    intensity=$((intensity + 50000))              # INCREASE each loop
    sleep 0.5
done
echo '[Complete]'
```

### CPU Pattern: 📈📈📈📈📈 (Staircase going UP)
- **Start**: 100,000 iterations (low CPU)
- **Each Loop**: +50,000 more iterations
- **End**: Could reach 500,000+ iterations (high CPU)
- **Result**: Gradually increasing load. **Best for trend detection** - the ML should detect the upward trend and predict overload.

---

## **5. Normal Workload** ⏱️

```bash
echo '[Normal Workload] Running for Xs'
END=$(($(date +%s) + X))
while [ $(date +%s) -lt $END ]; do
    i=0; while [ $i -lt 300000 ]; do i=$((i+1)); done  # Moderate work
    sleep 0.2                                           # Short rest
done
echo '[Complete]'
```

### CPU Pattern: ───────── (Flat, steady line)
- **Work**: 300,000 iterations → Moderate CPU (~30-50%)
- **Rest**: 0.2 second sleep → Keeps it consistent
- **Result**: Stable, predictable load. **Best as a baseline** - establishes what "normal" looks like for the ML health scoring.

---

## **Visual Summary**

```
Command         | CPU Pattern Over Time
----------------|------------------------------------------
Variable CPU    | ▄█▁█▄█▁█▄█▁  (alternating high/low)
Memory          | ▄▁▁▁▁▁▁▁▁▁▁  (spike then flat)
CPU Spike       | █░░░█░░░█░░  (intense spikes, long gaps)
Gradual         | ▁▂▃▄▅▆▇█████  (staircase up)
Normal          | ▄▄▄▄▄▄▄▄▄▄▄  (steady moderate)
```

---

## **Why These Patterns Matter for ML**

The ML anomaly detector in your container monitors:

1. **Rate of Change** - Sudden spikes (like CPU Spike) trigger anomaly alerts
2. **Variance** - Variable CPU shows high variance, Normal shows low variance
3. **Trends** - Gradual Increase demonstrates trend detection
4. **Baseline** - Normal Workload establishes the "healthy" baseline

---

## **Usage**

### CLI (controller.py)
```bash
sudo python3 controller.py
# Select Option 3: Execute Command
# Choose a workload (1-5) or custom command (6)
```

### Web Dashboard
1. Select a container
2. Click "Execute" button
3. Choose workload type and duration
4. Click "Run"

Both interfaces use the **exact same commands** for consistency.
