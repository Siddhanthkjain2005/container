# ML-Based Anomaly Detection - Technical Documentation

## Is a Real ML Model Used?

**No pre-trained .pkl model file is used.** Instead, this system uses **real-time statistical machine learning algorithms** that learn and adapt as they observe container behavior. This approach is known as **online learning** or **streaming ML**.

### Why No .pkl File?

Traditional ML models (like scikit-learn's Random Forest) are trained offline on historical data and saved to `.pkl` files. Our system uses a different approach:

1. **Online Learning**: The model learns in real-time from each container's metrics
2. **Adaptive Thresholds**: Thresholds adjust automatically based on observed behavior
3. **No Training Phase**: Works immediately without requiring historical data
4. **Per-Container Models**: Each container gets its own statistical baseline

This is similar to how production anomaly detection systems work at companies like Netflix and AWS.

---

## What is Z-Score?

**Z-Score** measures how many standard deviations a data point is from the mean.

### Formula:
```
Z = (X - μ) / σ

Where:
  X = Current value (e.g., current CPU usage)
  μ = Mean (average) of historical values
  σ = Standard deviation of historical values
```

### Interpretation:
| Z-Score | Meaning |
|---------|---------|
| Z = 0 | Value equals the average |
| Z = 1 | Value is 1 std dev above average |
| Z = -1 | Value is 1 std dev below average |
| Z = 2 | Value is 2 std dev above (unusual) |
| Z > 2.5 | Highly unusual (potential anomaly) |

### Example:
```
Container normally uses 30% CPU (mean)
Standard deviation is 10%

Current reading: 55% CPU
Z-score = (55 - 30) / 10 = 2.5

This is 2.5 standard deviations above normal → ANOMALY DETECTED
```

### In Our Code (ml.py lines 263-286):
```python
cpu_std = math.sqrt(stats.cpu_ema_variance)  # Standard deviation
cpu_z = (cpu_percent - stats.cpu_ema) / cpu_std  # Z-score calculation

if abs(cpu_z) > threshold:  # Default threshold is 1.5
    # Detected as anomaly!
```

---

## Exponential Moving Average (EMA)

Instead of simple averages, we use EMA which gives more weight to recent values.

### Formula:
```
EMA_new = α × current_value + (1 - α) × EMA_old

Where α (alpha) = smoothing factor (0.3 in our system)
```

### Why EMA?
- **Faster adaptation**: Responds quickly to real changes
- **Noise filtering**: Smooths out random fluctuations
- **Memory efficient**: Only stores one value, not entire history

---

## Score Calculations

### 1. Health Score (0-100)

**Purpose**: Overall container health based on volatility and stress.

**Location**: `ml.py` lines 375-479

**Calculation**:
```
Health = 100 - penalties + recovery_bonus
```

**Penalty Sources**:
| Condition | Penalty |
|-----------|---------|
| CPU changing >30%/sec | -20 |
| CPU changing >15%/sec | -10 |
| Memory changing >50MB/sec | -20 |
| High CPU variance (std > 25) | -15 |
| CPU > 95% | -15 |
| Memory > 95% of limit | -15 |
| Container is throttled | -10 |
| High severity anomaly (recent) | -8 per anomaly |
| Container is stressed | -5 |

**Recovery Bonus**:
| Condition | Bonus |
|-----------|-------|
| Fully stable (no stress, no anomalies) | +15 |
| Mostly stable (≤1 anomaly) | +8 |
| Somewhat stable | +3 |

**Smoothing**: Uses EMA to prevent sudden jumps
```python
new_score = alpha * target_score + (1 - alpha) * old_score
# alpha = 0.4 for recovery (faster), 0.25 for drop (slower)
```

---

### 2. Stability Score (0-100)

**Purpose**: Measures consistency of resource usage patterns.

**Location**: `ml.py` lines 481-535

**Calculation**:
```
Stability = 100 - penalties + recovery_bonus
```

**Key Metric**: Coefficient of Variation (CV)
```
CV = Standard Deviation / Mean
```

| CV Value | Meaning | Penalty |
|----------|---------|---------|
| CV > 0.5 | Very volatile | -30 |
| CV > 0.3 | Moderately volatile | -15 |
| CV > 0.15 | Slightly volatile | -5 |
| CV < 0.1 | Very stable | +5 bonus |

---

### 3. Efficiency Score (0-100)

**Purpose**: Measures how well resources are being utilized.

**Location**: `ml.py` lines 537-595

**Calculation**:
```
Efficiency = 100 - penalties + recovery_bonus
```

**Penalty Sources**:
| Condition | Penalty |
|-----------|---------|
| CPU < 1% (idle/wasted) | -10 |
| CPU > 90% (overloaded) | -(cpu - 90) × 2 |
| Memory < 5% (over-provisioned) | -5 |
| Memory > 90% (under-provisioned) | -(mem% - 90) × 2 |
| High CPU volatility | -15 |

**Recovery Bonus**:
| Condition | Bonus |
|-----------|-------|
| Very stable (CPU std < 5) | +8 |
| Moderately stable | +3 |

---

### 4. Risk Score

**Note**: Risk Score is calculated in the frontend (App.jsx) as:
```javascript
riskScore = 100 - healthScore
```

So if Health = 85, Risk = 15.

---

## Anomaly Detection Algorithms

### 1. Adaptive Z-Score Detection
```python
# Threshold adjusts based on container's historical volatility
if container_is_stable:
    threshold = base_threshold * 0.8  # Stricter
elif container_is_volatile:
    threshold = base_threshold * 1.3  # More lenient
```

### 2. Sudden Change Detection
```python
recent_avg = average of last 3 samples
change_ratio = abs(current - recent_avg) / recent_avg

if change_ratio > 0.5:  # 50% change
    # Sudden change detected!
```

### 3. Resource Exhaustion Prediction
```python
# Linear regression on memory history
slope = calculate_memory_trend()
if slope > 0:  # Memory increasing
    seconds_until_limit = (limit - current) / slope
    if seconds_until_limit < 60:
        # Warning: Will hit limit in <1 minute
```

---

## Data Structures

### Per-Container Statistics (`ContainerStats`):
```python
@dataclass
class ContainerStats:
    cpu_history: deque(maxlen=120)      # Last 2 minutes
    mem_history: deque(maxlen=120)
    cpu_history_long: deque(maxlen=600) # Last 10 minutes
    
    cpu_ema: float          # Exponential Moving Average
    cpu_ema_variance: float # Variance for Z-score
    cpu_ema_slow: float     # Slow EMA for trends
    
    health_score: float     # 0-100
    stability_score: float  # 0-100
    efficiency_score: float # 0-100
    
    anomalies: List[dict]   # Recent anomalies
    stress_count: int       # How many times stressed
    is_throttled: bool      # Currently hitting limits
```

---

## Summary

| Component | Algorithm | Pre-trained? |
|-----------|-----------|--------------|
| Anomaly Detection | Z-Score + EMA | No, learns in real-time |
| Health Score | Rule-based + EMA smoothing | No |
| Stability Score | Coefficient of Variation | No |
| Efficiency Score | Usage thresholds + rules | No |
| Trend Detection | Linear Regression | No |
| Exhaustion Prediction | Linear Regression | No |

**Why this approach?**
1. **No training data required** - Works immediately
2. **Adapts to each container** - Personalized baselines
3. **Low resource usage** - Just statistics, no heavy models
4. **Interpretable** - Easy to understand why an anomaly was detected
5. **Real-time** - Immediate detection, no batch processing

This is exactly how most production monitoring systems (Datadog, New Relic, AWS CloudWatch) work internally.
