# How Container Scores Work

## Simple Explanation

Your container dashboard shows 3 scores (0-100) for each container:

| Score | What It Measures | Simple Rule |
|-------|------------------|-------------|
| **Health** | Is the container stable right now? | Drops when things change fast |
| **Stability** | How consistent is the container? | Drops when usage varies a lot |
| **Efficiency** | Is it using resources well? | Drops when idle OR overloaded |

---

## The Z-Score (How We Detect Problems)

**Z-Score** answers: "Is this value normal or unusual?"

```
Z = (Current Value - Average) / Spread

Example:
- Your container normally uses 30% CPU
- Right now it's using 60% CPU
- That's WAY above normal → High Z-Score → PROBLEM DETECTED
```

| Z-Score | Meaning |
|---------|---------|
| 0 | Perfectly normal |
| 1 | Slightly unusual |
| 2 | Very unusual |
| 3+ | Something is wrong! |

**Threshold**: We alert when Z > 1.5 (moderately unusual)

---

## Health Score (0-100)

**Think of it like a traffic light:**
- 🟢 80-100 = Everything is fine
- 🟡 50-79 = Something is changing
- 🔴 0-49 = Major issues

**What makes Health DROP:**
- CPU or Memory changing rapidly
- Container is stressed (high CPU)
- Anomalies detected

**What makes Health GO UP:**
- Everything stays stable
- No rapid changes
- No anomalies

---

## Stability Score (0-100)

**Measures**: How consistent is the resource usage?

```
Stable Container:     CPU: 30%, 31%, 29%, 30%, 32%  → High Stability
Unstable Container:   CPU: 10%, 80%, 20%, 90%, 5%   → Low Stability
```

**Simple formula**: We divide the variation by the average
- Low ratio = Stable (high score)
- High ratio = Unstable (low score)

---

## Efficiency Score (0-100)

**The "Goldilocks" rule:**
- ❌ Too little usage (< 10%) = Wasted resources
- ✅ Just right (10-70%) = Efficient
- ❌ Too much usage (> 90%) = Overloaded

---

## Quick Summary

| Score | High (Good) | Low (Bad) |
|-------|-------------|-----------|
| Health | Container is calm | Container is stressed |
| Stability | Usage is consistent | Usage is all over the place |
| Efficiency | Resources used well | Resources wasted or maxed out |

---

## Example

```
Container: web-server
  CPU: 45% (stable)
  Memory: 60% (stable)
  No anomalies

Scores:
  Health: 95 ✅ (no problems)
  Stability: 90 ✅ (consistent usage)
  Efficiency: 85 ✅ (good utilization)
```

```
Container: cpu-stress
  CPU: jumping 10% → 90% → 20% → 80%
  Memory: 95% (almost full!)
  3 anomalies detected

Scores:
  Health: 45 ⚠️ (rapid changes)
  Stability: 30 ⚠️ (very inconsistent)
  Efficiency: 40 ⚠️ (memory almost full)
```

---

## That's It!

The system automatically:
1. Watches your containers every second
2. Learns what's "normal" for each container
3. Detects when something unusual happens
4. Updates the 3 scores in real-time

No configuration needed - it just works!
