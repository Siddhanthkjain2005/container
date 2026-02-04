# How Container Scores Work

A beginner-friendly guide to understanding container monitoring and scoring.

---

## Overview

Your container dashboard monitors each container and shows **3 scores** (0-100):

| Score | Question It Answers | Icon |
|-------|---------------------|------|
| **Health** | "Is the container doing okay right now?" | ❤️ |
| **Stability** | "Is the container behaving consistently?" | 📊 |
| **Efficiency** | "Is it using resources well?" | ⚡ |

**Score Ranges:**
- 🟢 **80-100**: Excellent - No problems
- 🟡 **50-79**: Warning - Something to watch
- 🔴 **0-49**: Critical - Needs attention

---

## Part 1: What is Z-Score?

### The Problem
How do we know if 60% CPU usage is normal or a problem? It depends on the container:
- For a web server that usually uses 20% → 60% is a **problem**
- For a database that usually uses 55% → 60% is **normal**

### The Solution: Z-Score
Z-Score tells us: **"How unusual is this value compared to what's normal?"**

### The Formula (Don't worry, it's simple!)

```
Z-Score = (Current Value - Normal Average) ÷ Typical Variation
```

### Real Example

**Container: web-app**
- Normal CPU average: 30%
- Typical variation: 5%
- Current CPU: 45%

```
Z-Score = (45 - 30) ÷ 5 = 3

This means: 45% is 3 "variations" away from normal
That's very unusual → ANOMALY DETECTED!
```

### Z-Score Meaning Table

| Z-Score | How Unusual? | What Happens |
|---------|--------------|--------------|
| 0 to 1 | Normal range | Nothing |
| 1 to 1.5 | Slightly unusual | Still okay |
| **1.5 to 2** | **Unusual** | **Alert triggered** |
| 2 to 3 | Very unusual | Medium severity |
| 3+ | Extremely unusual | High severity |

**Our threshold is 1.5** - anything more unusual than this triggers an alert.

---

## Part 2: Health Score (0-100)

### What It Measures
**"Is the container calm and stable right now, or is something going on?"**

Think of it like checking someone's stress level:
- Calm and relaxed → High health
- Stressed and reactive → Low health

### What DECREASES Health

| Condition | Why It's Bad | Penalty |
|-----------|--------------|---------|
| CPU changing quickly | Unstable behavior | -10 to -20 |
| Memory changing quickly | Possible memory leak | -10 to -20 |
| Container is maxed out | Resource exhaustion | -15 |
| Anomaly detected | Something unusual happened | -3 to -8 |
| Container is stressed | Working too hard | -5 |

### What INCREASES Health

| Condition | Why It's Good | Bonus |
|-----------|---------------|-------|
| Everything stable | Normal operation | +15 |
| No sudden changes | Predictable behavior | +8 |
| No anomalies | Nothing unusual | +3 |

### Example

**Calm Container:**
```
CPU: 30% → 31% → 29% → 30%  (barely changing)
Memory: Stable at 100MB
No anomalies

Health Score: 95 ✅
```

**Stressed Container:**
```
CPU: 20% → 80% → 10% → 90%  (jumping around!)
Memory: Growing rapidly
3 anomalies detected

Health Score: 35 ⚠️
```

---

## Part 3: Stability Score (0-100)

### What It Measures
**"How consistent is this container's behavior over time?"**

### The Concept: Coefficient of Variation (CV)

We compare how much the values spread out vs. the average:

```
CV = Spread ÷ Average

Low CV (small spread, big average) = STABLE
High CV (big spread, small average) = UNSTABLE
```

### Visual Example

**Stable Container (High Score):**
```
CPU over time: ▄▄▅▄▄▅▄▄▄▅
               (stays around the same level)
```

**Unstable Container (Low Score):**
```
CPU over time: ▁█▂▇▁█▃▇▁█
               (jumping all over the place)
```

### Score Breakdown

| CV Value | Behavior | Stability Score |
|----------|----------|-----------------|
| < 0.1 | Very consistent | 95-100 |
| 0.1 - 0.2 | Mostly consistent | 80-94 |
| 0.2 - 0.3 | Somewhat variable | 60-79 |
| 0.3 - 0.5 | Quite variable | 40-59 |
| > 0.5 | Very erratic | 0-39 |

---

## Part 4: Efficiency Score (0-100)

### What It Measures
**"Is this container using resources in a smart way?"**

### The Goldilocks Principle

| Usage Level | Problem | Score Impact |
|-------------|---------|--------------|
| **Too Low (< 10%)** | Wasted resources! Why allocate memory/CPU if not using it? | -10 |
| **Just Right (10-70%)** | Perfect! Using resources without being overloaded | No penalty |
| **Too High (> 80%)** | Overloaded! Might slow down or crash | -10 to -20 |

### Why This Matters

- **Under-used container**: You're paying for resources you don't need
- **Over-used container**: Performance will suffer, might crash
- **Well-used container**: Getting value from your resources

### Example Scores

| Container | CPU | Memory | Efficiency Score |
|-----------|-----|--------|------------------|
| web-server | 45% | 60% | 95 ✅ (Optimal) |
| idle-db | 2% | 5% | 70 ⚠️ (Under-used) |
| stressed-app | 95% | 92% | 30 ❌ (Overloaded) |

---

## Part 5: How It All Works Together

### The Monitoring Loop

Every **1 second**, the system:

1. **Collects** CPU, memory, and process count from each container
2. **Updates** the running average and variation (learns what's "normal")
3. **Calculates** Z-scores for the new values
4. **Detects** anomalies if Z-score > 1.5
5. **Updates** all three scores
6. **Sends** the data to your dashboard

### Real-World Scenario

**Minute 0-5: Learning Phase**
```
Container just started, system is learning what's normal.
Health: 100 (benefit of the doubt)
Stability: 100 (not enough data yet)
Efficiency: 100 (not enough data yet)
```

**Minute 5-10: Normal Operation**
```
CPU stable around 40%, Memory at 150MB
Health: 95 (everything fine)
Stability: 92 (very consistent)
Efficiency: 90 (good utilization)
```

**Minute 10-12: CPU Spike Workload**
```
CPU jumps to 85%!
Z-Score: 2.5 → ANOMALY DETECTED!
Health: 65 (rapid change detected)
Stability: 75 (variance increased)
Efficiency: 70 (getting overloaded)
```

**Minute 12-15: Recovery**
```
CPU back to 40%
Health: 85 (recovering gradually)
Stability: 80 (stabilizing)
Efficiency: 88 (back to optimal)
```

---

## Summary Table

| Score | Measures | Good When | Bad When |
|-------|----------|-----------|----------|
| **Health** | Current stability | Calm, no sudden changes | Rapid changes, anomalies |
| **Stability** | Consistency over time | Values stay similar | Values jump around |
| **Efficiency** | Resource utilization | 10-70% usage | Idle or maxed out |

---

## FAQ

**Q: Why does my score drop when CPU goes up?**
A: The score doesn't drop just because CPU is high. It drops when CPU *changes rapidly* or exceeds 90%.

**Q: How long until my scores recover?**
A: Scores recover gradually (about 30-60 seconds) once conditions return to normal.

**Q: What's a "good" score?**
A: Anything above 70 is generally fine. Below 50 means something needs attention.

**Q: Can I change the thresholds?**
A: Yes, in `backend/minicontainer/ml.py` you can adjust `base_z_threshold` and other parameters.
