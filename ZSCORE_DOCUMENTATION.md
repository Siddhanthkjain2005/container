# Z-Score Analytics - Technical Documentation

## Overview

This system uses **Z-Score based statistical analysis** to monitor container health and detect anomalies. It does NOT use a pre-trained machine learning model (no `.pkl` file) - instead, it learns each container's baseline behavior in real-time and detects deviations using statistical methods.

---

## What is Z-Score?

**Z-Score** (also called Standard Score) measures how many standard deviations a data point is from the mean. It's a fundamental statistical concept used to identify outliers.

### The Formula

```
Z = (X - μ) / σ

Where:
  X = Current value (e.g., current CPU percentage)
  μ = Mean (average) of historical values  
  σ = Standard deviation of historical values
```

### Visual Explanation

```
Normal Distribution:
                    μ (mean)
                       │
      ┌────────────────┼────────────────┐
      │                │                │
   -3σ    -2σ    -1σ   0   +1σ    +2σ   +3σ
      │    │      │    │    │      │    │
      └────┴──────┴────┴────┴──────┴────┘
           │      │         │      │
         Very   Unusual   Unusual  Very
         Rare                      Rare
```

### Interpretation

| Z-Score | Meaning | Probability |
|---------|---------|-------------|
| Z = 0 | Exactly at the average | 50% |
| |Z| < 1 | Within normal range | 68% of data |
| |Z| < 2 | Somewhat unusual | 95% of data |
| |Z| > 2 | Unusual (potential anomaly) | Only 5% of data |
| |Z| > 2.5 | Very unusual | Only 1.2% of data |
| |Z| > 3 | Extreme outlier | Only 0.3% of data |

---

## How It Works in MiniContainer

### Step 1: Data Collection

Every second, the system collects metrics from each container:
- **CPU Usage** (percentage)
- **Memory Usage** (bytes)
- **Process Count** (PIDs)

### Step 2: Baseline Learning (EMA)

Instead of storing all historical values, we use **Exponential Moving Average (EMA)** for efficient memory usage:

```python
# EMA Formula (α = 0.3 in our system)
new_average = α × current_value + (1 - α) × old_average

# For variance (used to calculate standard deviation)
new_variance = α × (value - average)² + (1 - α) × old_variance
```

**Why EMA?**
- Gives more weight to recent values
- Uses constant memory (just 2 numbers per metric)
- Adapts to changing container behavior

### Step 3: Anomaly Detection

When a new metric arrives:

```python
# Calculate standard deviation from variance
std = sqrt(variance)

# Calculate Z-score
z_score = (current_value - average) / std

# Check if it exceeds threshold (default: 1.5)
if abs(z_score) > 1.5:
    # ANOMALY DETECTED!
    if z_score > 0:
        # Value is HIGHER than normal (spike)
    else:
        # Value is LOWER than normal (drop)
```

### Step 4: Severity Classification

| Z-Score Range | Severity |
|---------------|----------|
| 1.5 < |Z| ≤ 1.8 | Low |
| 1.8 < |Z| ≤ 2.25 | Medium |
| |Z| > 2.25 | High |

---

## Container Scores

### 1. Health Score (0-100)

**Purpose**: Overall container health based on stability and current state.

**Calculation**:
```
Health = 100 - penalties + recovery_bonus

Penalties Applied For:
- Rapid CPU changes (>15%/sec): -10 to -20
- Rapid memory changes (>20MB/sec): -10 to -20  
- High variance (std > 15): -8 to -15
- CPU > 95%: -15
- Memory > 95%: -15
- Recent anomalies: -3 to -8 per anomaly

Recovery Bonus (when stable):
- Fully stable conditions: +15
- Mostly stable: +8
- Somewhat stable: +3
```

**Smoothing**: EMA prevents sudden jumps:
```python
new_health = 0.3 × target + 0.7 × previous_health
```

---

### 2. Stability Score (0-100)

**Purpose**: Measures consistency of resource usage.

**Key Metric**: Coefficient of Variation (CV)
```
CV = Standard Deviation / Mean
```

**Interpretation**:
| CV Value | Meaning | Penalty |
|----------|---------|---------|
| CV < 0.1 | Very stable | +5 bonus |
| 0.1 ≤ CV < 0.15 | Stable | 0 |
| 0.15 ≤ CV < 0.3 | Slightly volatile | -5 |
| 0.3 ≤ CV < 0.5 | Moderately volatile | -15 |
| CV ≥ 0.5 | Very volatile | -30 |

---

### 3. Efficiency Score (0-100)

**Purpose**: How well are resources being utilized?

**Optimal Range**: 10-70% utilization

| Condition | Impact |
|-----------|--------|
| CPU < 1% | -10 (resource waste) |
| CPU 10-70% | No penalty (optimal) |
| CPU > 80% | -(cpu - 80) × 1 |
| CPU > 90% | -(cpu - 90) × 2 |
| Memory < 5% | -5 (over-provisioned) |
| Memory > 90% | -(mem% - 90) × 2 |
| Low volatility | +3 to +8 bonus |

---

## Example Walkthrough

### Scenario: CPU Spike Detection

```
Container "web-server" baseline:
  - Average CPU: 25%
  - Standard Deviation: 8%

Current reading: 55% CPU

Step 1: Calculate Z-score
  Z = (55 - 25) / 8 = 3.75

Step 2: Check threshold
  |3.75| > 1.5 ✓ → ANOMALY

Step 3: Classify severity
  |3.75| > 2.25 → HIGH SEVERITY

Step 4: Log anomaly
  {
    "type": "cpu_spike",
    "value": 55,
    "expected": 25,
    "z_score": 3.75,
    "severity": "high",
    "message": "CPU spike: 55% (expected 25%)"
  }
```

---

## Why Z-Score Instead of ML?

| Aspect | Z-Score Approach | Traditional ML |
|--------|------------------|----------------|
| Training Data | Not needed | Requires historical data |
| Setup Time | Instant | Hours/days to train |
| Memory Usage | Minimal (few numbers) | Large model file |
| Interpretability | Easy to explain | Black box |
| Adaptation | Real-time | Needs retraining |
| False Positives | Tunable threshold | Model-dependent |

---

## Configuration

The Z-score detector is configured in `backend/minicontainer/ml.py`:

```python
detector = EnhancedAnomalyDetector(
    base_z_threshold=1.5,      # Z-score threshold for anomaly
    ema_alpha=0.3,             # EMA smoothing (0-1, higher = more reactive)
    min_samples=5,             # Samples before detection starts
    stress_threshold_cpu=30.0  # CPU % to consider stressed
)
```

---

## Data Flow

```
Container Metrics (every 1 sec)
        │
        ▼
┌──────────────────────┐
│  Update EMA Average  │ ← μ (mean)
│  Update EMA Variance │ ← σ² (variance)
└──────────────────────┘
        │
        ▼
┌──────────────────────┐
│  Calculate Z-Score   │ ← Z = (X - μ) / σ
└──────────────────────┘
        │
        ▼
┌──────────────────────┐
│  Check Threshold     │ ← |Z| > 1.5 ?
└──────────────────────┘
        │
    ┌───┴───┐
    │       │
 Normal  Anomaly → Log + Update Scores
    │       │
    ▼       ▼
┌──────────────────────┐
│  Calculate Scores    │
│  - Health            │
│  - Stability         │
│  - Efficiency        │
└──────────────────────┘
        │
        ▼
   WebSocket → Dashboard
```

---

## Summary

- **No pre-trained model** - learns baselines in real-time
- **Z-Score based** - simple, interpretable statistical method
- **Adaptive thresholds** - adjusts based on container volatility
- **Three scores** - Health, Stability, Efficiency (0-100)
- **EMA smoothing** - prevents noisy fluctuations
