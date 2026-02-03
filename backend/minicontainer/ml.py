"""MiniContainer - Enhanced ML-based Anomaly Detection

Implements multiple detection algorithms:
- Z-score detection with adaptive thresholds
- Exponential Moving Average (EMA) for trend detection
- Isolation Forest-inspired outlier detection
- Pattern recognition for periodic anomalies
- Predictive modeling with linear regression
"""

import time
import math
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional


@dataclass
class ContainerStats:
    """Rolling statistics for a container with enhanced metrics"""
    # Core metrics history (last 120 samples = 2 minutes at 1/sec)
    cpu_history: deque = field(default_factory=lambda: deque(maxlen=120))
    mem_history: deque = field(default_factory=lambda: deque(maxlen=120))
    timestamps: deque = field(default_factory=lambda: deque(maxlen=120))
    
    # Extended history for long-term analysis (last 600 samples = 10 minutes)
    cpu_history_long: deque = field(default_factory=lambda: deque(maxlen=600))
    mem_history_long: deque = field(default_factory=lambda: deque(maxlen=600))
    
    # Anomaly tracking
    anomalies: List[dict] = field(default_factory=list)
    
    # Adaptive baseline (EMA)
    cpu_ema: float = 0.0
    mem_ema: float = 0.0
    cpu_ema_variance: float = 0.0
    mem_ema_variance: float = 0.0
    
    # Secondary EMA for trend detection (slower response)
    cpu_ema_slow: float = 0.0
    mem_ema_slow: float = 0.0
    
    # Health metrics
    health_score: float = 100.0
    stability_score: float = 100.0
    efficiency_score: float = 100.0
    
    # Pattern detection
    is_stressed: bool = False
    stress_start_time: Optional[float] = None
    stress_duration: float = 0.0
    total_stress_time: float = 0.0
    stress_count: int = 0
    
    # Peak tracking
    cpu_peak: float = 0.0
    mem_peak: int = 0
    cpu_peak_time: Optional[float] = None
    mem_peak_time: Optional[float] = None
    
    # Learning state
    samples_collected: int = 0
    baseline_learned: bool = False
    
    # Rate of change tracking
    cpu_rate: float = 0.0
    mem_rate: float = 0.0
    prev_cpu: float = 0.0
    prev_mem: int = 0
    
    # Throttling tracking
    is_throttled: bool = False
    throttle_count: int = 0


class EnhancedAnomalyDetector:
    """
    Advanced ML-based anomaly detection with multiple algorithms:
    
    1. Adaptive Z-Score: Adjusts threshold based on historical variance
    2. EMA-Based Detection: Uses exponential moving averages for smoother detection
    3. Sudden Change Detection: Detects rapid changes in metrics
    4. Resource Exhaustion Warning: Predicts when resources will hit limits
    """
    
    def __init__(self, 
                 base_z_threshold: float = 1.5,
                 ema_alpha: float = 0.3,
                 ema_alpha_slow: float = 0.1,
                 min_samples: int = 5,
                 stress_threshold_cpu: float = 30.0,
                 stress_threshold_mem_percent: float = 60.0):
        """
        Initialize detector with configurable parameters.
        
        Args:
            base_z_threshold: Base Z-score threshold (adjusted adaptively)
            ema_alpha: EMA smoothing factor (0-1, higher = more reactive)
            ema_alpha_slow: Slow EMA for trend detection (lower = smoother)
            min_samples: Minimum samples before detection starts
            stress_threshold_cpu: CPU % to consider as stressed
            stress_threshold_mem_percent: Memory % to consider as stressed
        """
        self.base_z_threshold = base_z_threshold
        self.ema_alpha = ema_alpha
        self.ema_alpha_slow = ema_alpha_slow
        self.min_samples = min_samples
        self.stress_threshold_cpu = stress_threshold_cpu
        self.stress_threshold_mem = stress_threshold_mem_percent
        
        self.container_stats: Dict[str, ContainerStats] = {}
        self.global_anomalies: List[dict] = []
        self.system_start_time: float = time.time()
    
    def _get_stats(self, container_id: str) -> ContainerStats:
        """Get or create stats for a container"""
        if container_id not in self.container_stats:
            self.container_stats[container_id] = ContainerStats()
        return self.container_stats[container_id]
    
    def _update_ema(self, current: float, ema: float, first: bool = False) -> float:
        """Update exponential moving average"""
        if first:
            return current
        return self.ema_alpha * current + (1 - self.ema_alpha) * ema
    
    def _update_ema_variance(self, value: float, ema: float, ema_var: float, first: bool = False) -> float:
        """Update EMA-based variance estimate"""
        if first:
            return 0.0
        diff = value - ema
        return self.ema_alpha * (diff * diff) + (1 - self.ema_alpha) * ema_var
    
    def _calculate_adaptive_threshold(self, stats: ContainerStats) -> float:
        """Calculate adaptive Z-score threshold based on historical variance"""
        if stats.samples_collected < 30:
            # Be more lenient during learning phase
            return self.base_z_threshold * 1.5
        
        # Reduce threshold for stable containers, increase for volatile ones
        cv = math.sqrt(stats.cpu_ema_variance) / max(stats.cpu_ema, 1)
        if cv < 0.2:  # Very stable
            return self.base_z_threshold * 0.8
        elif cv > 0.5:  # Very volatile
            return self.base_z_threshold * 1.3
        return self.base_z_threshold
    
    def _detect_sudden_change(self, current: float, history: deque, window: int = 3) -> Tuple[bool, float]:
        """Detect sudden changes by comparing to very recent history"""
        if len(history) < window + 1:
            return False, 0.0
        
        recent = list(history)[-window:]
        recent_avg = sum(recent) / len(recent)
        
        if recent_avg == 0:
            return False, 0.0
        
        change_ratio = abs(current - recent_avg) / max(recent_avg, 1)
        is_sudden = change_ratio > 0.5  # 50% change = sudden
        
        return is_sudden, change_ratio
    
    def _detect_resource_exhaustion(self, stats: ContainerStats, mem: int, mem_limit: int) -> Optional[dict]:
        """Predict if resources will hit limits soon"""
        if mem_limit <= 0 or len(stats.mem_history) < 10:
            return None
        
        mem_list = list(stats.mem_history)[-20:]
        n = len(mem_list)
        
        # Calculate slope (bytes per sample)
        x_mean = n / 2
        y_mean = sum(mem_list) / n
        
        numerator = sum((i - x_mean) * (mem_list[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        if slope > 0:
            remaining = mem_limit - mem
            if remaining > 0 and slope > 0:
                samples_until_limit = remaining / slope
                seconds_until_limit = samples_until_limit  # Assuming 1 sample/sec
                
                if seconds_until_limit < 60:  # Less than 1 minute
                    return {
                        "type": "resource_exhaustion_warning",
                        "resource": "memory",
                        "current_usage_percent": (mem / mem_limit) * 100,
                        "seconds_until_limit": seconds_until_limit,
                        "message": f"Memory predicted to hit limit in {seconds_until_limit:.0f}s"
                    }
        return None
    
    def add_metrics(self, container_id: str, cpu_percent: float, memory_bytes: int, 
                    memory_limit: int = 268435456, is_throttled: bool = False) -> List[dict]:
        """
        Add new metrics and run all detection algorithms.
        
        Returns list of detected anomalies.
        """
        stats = self._get_stats(container_id)
        current_time = time.time()
        
        # Track throttling
        stats.is_throttled = is_throttled
        if is_throttled:
            stats.throttle_count = getattr(stats, 'throttle_count', 0) + 1
        
        # Update sample count
        stats.samples_collected += 1
        is_first = stats.samples_collected == 1
        
        # Update EMAs (fast and slow)
        stats.cpu_ema = self._update_ema(cpu_percent, stats.cpu_ema, is_first)
        stats.mem_ema = self._update_ema(memory_bytes, stats.mem_ema, is_first)
        stats.cpu_ema_variance = self._update_ema_variance(cpu_percent, stats.cpu_ema, stats.cpu_ema_variance, is_first)
        stats.mem_ema_variance = self._update_ema_variance(memory_bytes, stats.mem_ema, stats.mem_ema_variance, is_first)
        
        # Slow EMAs for trend detection
        if is_first:
            stats.cpu_ema_slow = cpu_percent
            stats.mem_ema_slow = memory_bytes
        else:
            stats.cpu_ema_slow = self.ema_alpha_slow * cpu_percent + (1 - self.ema_alpha_slow) * stats.cpu_ema_slow
            stats.mem_ema_slow = self.ema_alpha_slow * memory_bytes + (1 - self.ema_alpha_slow) * stats.mem_ema_slow
        
        # Rate of change calculation
        if not is_first:
            stats.cpu_rate = cpu_percent - stats.prev_cpu
            stats.mem_rate = memory_bytes - stats.prev_mem
        stats.prev_cpu = cpu_percent
        stats.prev_mem = memory_bytes
        
        # Peak tracking
        if cpu_percent > stats.cpu_peak:
            stats.cpu_peak = cpu_percent
            stats.cpu_peak_time = current_time
        if memory_bytes > stats.mem_peak:
            stats.mem_peak = memory_bytes
            stats.mem_peak_time = current_time
        
        # Add to history (short and long term)
        stats.cpu_history.append(cpu_percent)
        stats.mem_history.append(memory_bytes)
        stats.timestamps.append(current_time)
        stats.cpu_history_long.append(cpu_percent)
        stats.mem_history_long.append(memory_bytes)
        
        # Mark baseline as learned after minimum samples
        if stats.samples_collected >= self.min_samples and not stats.baseline_learned:
            stats.baseline_learned = True
        
        anomalies_detected = []
        
        # Only run detection after baseline is learned
        if stats.baseline_learned:
            # 1. Adaptive Z-Score Detection
            threshold = self._calculate_adaptive_threshold(stats)
            
            # CPU Z-score
            cpu_std = math.sqrt(stats.cpu_ema_variance) if stats.cpu_ema_variance > 0 else 1
            cpu_z = (cpu_percent - stats.cpu_ema) / cpu_std if cpu_std > 0 else 0
            
            if abs(cpu_z) > threshold:
                # Severity based on z-score magnitude - adjusted thresholds for more high severity
                if abs(cpu_z) > threshold * 1.5:
                    severity = "high"
                elif abs(cpu_z) > threshold * 1.2:
                    severity = "medium"
                else:
                    severity = "low"
                anomaly = {
                    "type": "cpu_spike" if cpu_z > 0 else "cpu_drop",
                    "container_id": container_id,
                    "timestamp": current_time,
                    "value": round(cpu_percent, 2),
                    "expected": round(stats.cpu_ema, 2),
                    "z_score": round(cpu_z, 2),
                    "severity": severity,
                    "algorithm": "adaptive_zscore",
                    "message": f"CPU {'spike' if cpu_z > 0 else 'drop'}: {cpu_percent:.1f}% (expected {stats.cpu_ema:.1f}%)"
                }
                anomalies_detected.append(anomaly)
            
            # Memory Z-score
            mem_std = math.sqrt(stats.mem_ema_variance) if stats.mem_ema_variance > 0 else 1
            mem_z = (memory_bytes - stats.mem_ema) / mem_std if mem_std > 0 else 0
            
            if abs(mem_z) > threshold:
                # Severity based on z-score magnitude - adjusted for more high severity
                if abs(mem_z) > threshold * 1.5:
                    severity = "high"
                elif abs(mem_z) > threshold * 1.2:
                    severity = "medium"
                else:
                    severity = "low"
                mem_mb = memory_bytes / (1024 * 1024)
                expected_mb = stats.mem_ema / (1024 * 1024)
                anomaly = {
                    "type": "memory_spike" if mem_z > 0 else "memory_drop",
                    "container_id": container_id,
                    "timestamp": current_time,
                    "value": memory_bytes,
                    "expected": int(stats.mem_ema),
                    "z_score": round(mem_z, 2),
                    "severity": severity,
                    "algorithm": "adaptive_zscore",
                    "message": f"Memory {'spike' if mem_z > 0 else 'drop'}: {mem_mb:.1f}MB (expected {expected_mb:.1f}MB)"
                }
                anomalies_detected.append(anomaly)
            
            # 2. Sudden Change Detection
            is_sudden, change_ratio = self._detect_sudden_change(cpu_percent, stats.cpu_history)
            if is_sudden and change_ratio > 0.4:  # Lower threshold for detection
                # Severity based on change magnitude - adjusted for more high severity
                if change_ratio > 1.0:
                    severity = "high"
                elif change_ratio > 0.7:
                    severity = "medium"
                else:
                    severity = "low"
                anomaly = {
                    "type": "sudden_cpu_change",
                    "container_id": container_id,
                    "timestamp": current_time,
                    "value": round(cpu_percent, 2),
                    "change_ratio": round(change_ratio, 2),
                    "severity": severity,
                    "algorithm": "sudden_change",
                    "message": f"Sudden CPU change detected: {change_ratio*100:.0f}% change"
                }
                anomalies_detected.append(anomaly)
            
            # 3. Resource Exhaustion Warning
            exhaustion_warning = self._detect_resource_exhaustion(stats, memory_bytes, memory_limit)
            if exhaustion_warning:
                exhaustion_warning["container_id"] = container_id
                exhaustion_warning["timestamp"] = current_time
                exhaustion_warning["severity"] = "high"
                exhaustion_warning["algorithm"] = "exhaustion_prediction"
                anomalies_detected.append(exhaustion_warning)
        
        # Stress detection (always run)
        is_stressed = cpu_percent > self.stress_threshold_cpu
        if is_stressed and not stats.is_stressed:
            stats.is_stressed = True
            stats.stress_start_time = current_time
            stats.stress_count += 1
        elif not is_stressed and stats.is_stressed:
            if stats.stress_start_time:
                duration = current_time - stats.stress_start_time
                stats.stress_duration = duration
                stats.total_stress_time += duration
            stats.is_stressed = False
            stats.stress_start_time = None
        
        # Add anomalies to tracking
        for anomaly in anomalies_detected:
            stats.anomalies.append(anomaly)
            self.global_anomalies.append(anomaly)
        
        # Calculate all scores - pass throttling status
        stats.health_score = self._calculate_health_score(stats, cpu_percent, memory_bytes, memory_limit, is_throttled)
        stats.stability_score = self._calculate_stability_score(stats)
        stats.efficiency_score = self._calculate_efficiency_score(stats, cpu_percent, memory_bytes, memory_limit)
        
        # Cleanup old anomalies
        self._cleanup_old_anomalies(stats)
        
        return anomalies_detected
    
    def _calculate_health_score(self, stats: ContainerStats, cpu: float, mem: int, mem_limit: int, throttled: bool = False) -> float:
        """Calculate health score based on VOLATILITY and RATE OF CHANGE, not absolute values.
        
        Health drops when:
        - CPU or memory usage is changing rapidly (high rate of change)
        - System is volatile (high variance)
        - Anomalies are detected
        - Container is throttled
        
        Health recovers when:
        - Usage is stable (low rate of change, low variance)
        """
        # Start from current health score for smoothing, or 100 if first sample
        base_score = getattr(stats, '_prev_health', 100.0)
        
        penalties = 0.0
        recovery_bonus = 0.0
        
        # --- VOLATILITY PENALTIES (react to CHANGES, not absolute values) ---
        
        # CPU rate of change penalty: abs(cpu_rate) is the change per second
        cpu_change = abs(stats.cpu_rate)
        if cpu_change > 30:  # Very rapid change (>30% per second)
            penalties += 20
        elif cpu_change > 15:  # Significant change
            penalties += 10
        elif cpu_change > 8:  # Moderate change
            penalties += 3
        
        # Memory rate of change penalty
        mem_change_mb = abs(stats.mem_rate) / (1024 * 1024)  # MB per second
        if mem_change_mb > 50:  # >50MB/s change
            penalties += 20
        elif mem_change_mb > 20:  # >20MB/s change
            penalties += 10
        elif mem_change_mb > 10:  # >10MB/s change
            penalties += 3
        
        # CPU variance penalty (high variance = unhealthy)
        cpu_std = math.sqrt(stats.cpu_ema_variance) if stats.cpu_ema_variance > 0 else 0
        if cpu_std > 25:
            penalties += 15
        elif cpu_std > 15:
            penalties += 8
        elif cpu_std > 10:
            penalties += 3
        
        # --- CRITICAL STATE PENALTIES (absolute thresholds for danger zones) ---
        
        # Only penalize EXTREME absolute usage (resource exhaustion)
        if cpu > 95:
            penalties += 15
        
        mem_percent = (mem / mem_limit * 100) if mem_limit > 0 else 0
        if mem_percent > 95:
            penalties += 15
        
        # Throttling penalty - container is hitting limits
        if throttled:
            penalties += 10
        
        # --- ANOMALY PENALTIES (shorter window: 30 seconds) ---
        recent = [a for a in stats.anomalies if time.time() - a["timestamp"] < 30]
        high_severity = sum(1 for a in recent if a.get("severity") == "high")
        medium_severity = sum(1 for a in recent if a.get("severity") == "medium")
        penalties += high_severity * 8
        penalties += medium_severity * 3
        
        # Stress penalty (reduced)
        if stats.is_stressed:
            penalties += 5
        
        # --- RECOVERY MECHANISM (more aggressive) ---
        
        # Partial recovery even with some activity - just needs to be relatively stable
        is_mostly_stable = cpu_change < 8 and mem_change_mb < 10
        
        if is_mostly_stable:
            if not stats.is_stressed and not throttled and len(recent) == 0:
                # Fully stable - aggressive recovery
                recovery_bonus = 15
            elif len(recent) <= 1:
                # Mostly stable - moderate recovery
                recovery_bonus = 8
            else:
                # Some instability but not changing rapidly - gentle recovery
                recovery_bonus = 3
        
        # Calculate new score with smoothing
        target_score = 100.0 - penalties + recovery_bonus
        target_score = max(0, min(100, target_score))
        
        # Smooth the transition (EMA for gradual changes)
        # Use faster alpha when recovering (0.4) vs when dropping (0.25)
        if target_score > base_score:
            alpha = 0.4  # Recover faster
        else:
            alpha = 0.25  # Drop slower
        
        new_score = alpha * target_score + (1 - alpha) * base_score
        
        # Store for next iteration
        stats._prev_health = new_score
        
        return max(0, min(100, new_score))
    
    def _calculate_stability_score(self, stats: ContainerStats) -> float:
        """Calculate stability score based on variance and consistency.
        
        Stability improves when usage patterns are consistent.
        Stability drops when there's high variance or rapid changes.
        """
        if stats.samples_collected < 10:
            return 100.0
        
        # Start from current stability score for smoothing
        base_score = getattr(stats, '_prev_stability', 100.0)
        
        penalties = 0.0
        recovery_bonus = 0.0
        
        # CPU stability - coefficient of variation
        cpu_cv = math.sqrt(stats.cpu_ema_variance) / max(stats.cpu_ema, 1)
        if cpu_cv > 0.5:  # Very volatile
            penalties += 30
        elif cpu_cv > 0.3:  # Moderately volatile
            penalties += 15
        elif cpu_cv > 0.15:  # Slightly volatile
            penalties += 5
        
        # Memory stability
        mem_cv = math.sqrt(stats.mem_ema_variance) / max(stats.mem_ema, 1)
        if mem_cv > 0.5:
            penalties += 30
        elif mem_cv > 0.3:
            penalties += 15
        elif mem_cv > 0.15:
            penalties += 5
        
        # Rate of change impact
        if abs(stats.cpu_rate) > 20:
            penalties += 10
        if abs(stats.mem_rate) / (1024 * 1024) > 30:
            penalties += 10
        
        # Recovery: if very stable (low CV and low rate of change)
        if cpu_cv < 0.1 and mem_cv < 0.1 and abs(stats.cpu_rate) < 3:
            recovery_bonus = 5
        
        # Calculate target score
        target_score = 100.0 - penalties + recovery_bonus
        target_score = max(0, min(100, target_score))
        
        # Smooth the transition
        alpha = 0.25
        new_score = alpha * target_score + (1 - alpha) * base_score
        
        # Store for next iteration
        stats._prev_stability = new_score
        
        return max(0, min(100, new_score))
    
    def _calculate_efficiency_score(self, stats: ContainerStats, cpu: float, mem: int, mem_limit: int) -> float:
        """Calculate resource efficiency score (0-100)
        
        Efficiency considers:
        - Resource utilization (using some resources is good, but not too much)
        - Stability of usage patterns
        - Rate of resource consumption
        
        Efficiency improves when resources are used consistently without waste.
        """
        if stats.samples_collected < 5:
            return 100.0
        
        # Start from current efficiency score for smoothing
        base_score = getattr(stats, '_prev_efficiency', 100.0)
        
        penalties = 0.0
        recovery_bonus = 0.0
        
        # Optimal CPU usage is around 10-70%, penalize extremes
        if cpu < 1:  # Idle container (wasted resources)
            penalties += 10
        elif cpu > 90:  # Overloaded (inefficient)
            penalties += (cpu - 90) * 2
        elif cpu > 80:
            penalties += (cpu - 80) * 1
        
        # Memory efficiency
        mem_percent = (mem / mem_limit * 100) if mem_limit > 0 else 0
        if mem_percent < 5:  # Barely using memory (over-provisioned)
            penalties += 5
        elif mem_percent > 90:  # Memory pressure (under-provisioned)
            penalties += (mem_percent - 90) * 2
        
        # Penalize high volatility (rapid changes indicate inefficiency)
        if abs(stats.cpu_rate) > 20:
            penalties += 15
        elif abs(stats.cpu_rate) > 10:
            penalties += 5
        
        # Reward consistent usage patterns
        cpu_std = math.sqrt(stats.cpu_ema_variance) if stats.cpu_ema_variance > 0 else 0
        if cpu_std < 5:  # Very stable = efficient
            recovery_bonus += 8
        elif cpu_std < 10:
            recovery_bonus += 3
        
        # Calculate target score
        target_score = 100.0 - penalties + recovery_bonus
        target_score = max(0, min(100, target_score))
        
        # Smooth the transition
        alpha = 0.25
        new_score = alpha * target_score + (1 - alpha) * base_score
        
        # Store for next iteration
        stats._prev_efficiency = new_score
        
        return max(0, min(100, new_score))
    
    def _cleanup_old_anomalies(self, stats: ContainerStats):
        """Keep only recent anomalies"""
        if len(stats.anomalies) > 100:
            stats.anomalies = stats.anomalies[-100:]
        if len(self.global_anomalies) > 500:
            self.global_anomalies = self.global_anomalies[-500:]
    
    def get_container_analytics(self, container_id: str) -> dict:
        """Get comprehensive analytics for a container"""
        stats = self._get_stats(container_id)
        
        cpu_list = list(stats.cpu_history)
        mem_list = list(stats.mem_history)
        cpu_list_long = list(stats.cpu_history_long)
        mem_list_long = list(stats.mem_history_long)
        
        # Calculate percentiles
        cpu_p50 = sorted(cpu_list)[len(cpu_list)//2] if cpu_list else 0
        cpu_p95 = sorted(cpu_list)[int(len(cpu_list)*0.95)] if len(cpu_list) > 20 else (max(cpu_list) if cpu_list else 0)
        cpu_p99 = sorted(cpu_list)[int(len(cpu_list)*0.99)] if len(cpu_list) > 100 else (max(cpu_list) if cpu_list else 0)
        
        mem_p50 = sorted(mem_list)[len(mem_list)//2] if mem_list else 0
        mem_p95 = sorted(mem_list)[int(len(mem_list)*0.95)] if len(mem_list) > 20 else (max(mem_list) if mem_list else 0)
        
        # Uptime since first sample
        uptime = time.time() - stats.timestamps[0] if stats.timestamps else 0
        
        return {
            "container_id": container_id,
            # Scores
            "health_score": round(stats.health_score, 1),
            "stability_score": round(stats.stability_score, 1),
            "efficiency_score": round(stats.efficiency_score, 1),
            # CPU metrics
            "cpu_current": round(cpu_list[-1], 2) if cpu_list else 0,
            "cpu_avg": round(stats.cpu_ema, 2),
            "cpu_max": round(max(cpu_list), 2) if cpu_list else 0,
            "cpu_min": round(min(cpu_list), 2) if cpu_list else 0,
            "cpu_std": round(math.sqrt(stats.cpu_ema_variance), 2),
            "cpu_peak": round(stats.cpu_peak, 2),
            "cpu_peak_time": stats.cpu_peak_time,
            "cpu_p50": round(cpu_p50, 2),
            "cpu_p95": round(cpu_p95, 2),
            "cpu_p99": round(cpu_p99, 2),
            "cpu_rate": round(stats.cpu_rate, 2),
            "cpu_ema_slow": round(stats.cpu_ema_slow, 2),
            # Memory metrics
            "memory_current": mem_list[-1] if mem_list else 0,
            "memory_avg": int(stats.mem_ema),
            "memory_max": max(mem_list) if mem_list else 0,
            "memory_min": min(mem_list) if mem_list else 0,
            "memory_peak": stats.mem_peak,
            "memory_peak_time": stats.mem_peak_time,
            "memory_p50": mem_p50,
            "memory_p95": mem_p95,
            "memory_rate": stats.mem_rate,
            # Stress metrics
            "is_stressed": stats.is_stressed,
            "stress_count": stats.stress_count,
            "total_stress_time": round(stats.total_stress_time, 1),
            "current_stress_duration": round(time.time() - stats.stress_start_time, 1) if stats.is_stressed and stats.stress_start_time else 0,
            # Learning state
            "baseline_learned": stats.baseline_learned,
            "samples_collected": stats.samples_collected,
            "uptime_seconds": round(uptime, 1),
            # Anomalies
            "anomaly_count_total": len(stats.anomalies),
            "anomaly_count_recent": len([a for a in stats.anomalies if time.time() - a["timestamp"] < 120]),
            "recent_anomalies": stats.anomalies[-10:],
            # Predictions and trends
            "trend": self._get_trend(stats),
            "memory_trend": self._get_memory_trend(stats),
            "prediction": self._predict_cpu(stats),
            "memory_prediction": self._predict_memory(stats),
            # Distribution data for charts
            "cpu_distribution": self._get_distribution(cpu_list_long if cpu_list_long else cpu_list, 10),
            "memory_distribution": self._get_distribution([m / (1024*1024) for m in (mem_list_long if mem_list_long else mem_list)], 10),
        }
    
    def _get_distribution(self, values: list, buckets: int = 10) -> dict:
        """Calculate distribution of values for histogram"""
        if not values:
            return {"buckets": [], "counts": [], "labels": []}
        
        min_val = min(values)
        max_val = max(values)
        if max_val == min_val:
            return {"buckets": [min_val], "counts": [len(values)], "labels": [f"{min_val:.1f}"]}
        
        bucket_size = (max_val - min_val) / buckets
        bucket_counts = [0] * buckets
        bucket_labels = []
        
        for i in range(buckets):
            start = min_val + i * bucket_size
            end = start + bucket_size
            bucket_labels.append(f"{start:.1f}-{end:.1f}")
        
        for v in values:
            idx = min(int((v - min_val) / bucket_size), buckets - 1)
            bucket_counts[idx] += 1
        
        return {
            "buckets": [min_val + (i + 0.5) * bucket_size for i in range(buckets)],
            "counts": bucket_counts,
            "labels": bucket_labels
        }
    
    def _get_memory_trend(self, stats: ContainerStats) -> dict:
        """Determine memory usage trend"""
        if len(stats.mem_history) < 10:
            return {"direction": "stable", "strength": 0, "description": "Insufficient data"}
        
        recent = list(stats.mem_history)[-10:]
        older = list(stats.mem_history)[-20:-10] if len(stats.mem_history) >= 20 else recent
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        if older_avg == 0:
            return {"direction": "stable", "strength": 0, "description": "No baseline"}
        
        diff_percent = ((recent_avg - older_avg) / older_avg) * 100
        
        if diff_percent > 20:
            return {"direction": "increasing", "strength": min(diff_percent / 20, 3), "description": "Rapidly increasing", "change_percent": round(diff_percent, 1)}
        elif diff_percent > 5:
            return {"direction": "increasing", "strength": diff_percent / 20, "description": "Gradually increasing", "change_percent": round(diff_percent, 1)}
        elif diff_percent < -20:
            return {"direction": "decreasing", "strength": min(abs(diff_percent) / 20, 3), "description": "Rapidly decreasing", "change_percent": round(diff_percent, 1)}
        elif diff_percent < -5:
            return {"direction": "decreasing", "strength": abs(diff_percent) / 20, "description": "Gradually decreasing", "change_percent": round(diff_percent, 1)}
        return {"direction": "stable", "strength": 0, "description": "Stable usage", "change_percent": round(diff_percent, 1)}
    
    def _predict_memory(self, stats: ContainerStats) -> dict:
        """Predict future memory usage"""
        if len(stats.mem_history) < 10:
            return {"value": 0, "confidence": 0, "method": "insufficient_data"}
        
        mem_list = list(stats.mem_history)[-30:]
        n = len(mem_list)
        
        # Linear regression
        x_mean = n / 2
        y_mean = sum(mem_list) / n
        
        numerator = sum((i - x_mean) * (mem_list[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        # Predict 30 seconds ahead
        future_x = n + 30
        predicted = intercept + slope * future_x
        predicted = max(0, predicted)
        
        # Confidence
        ss_tot = sum((mem_list[i] - y_mean) ** 2 for i in range(n))
        ss_res = sum((mem_list[i] - (intercept + slope * i)) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        confidence = r_squared * min(n / 30, 1)
        
        return {
            "value": int(predicted),
            "value_mb": round(predicted / (1024*1024), 2),
            "confidence": round(confidence, 2),
            "method": "linear_regression",
            "slope_per_sec": round(slope, 0)
        }
    
    def _get_trend(self, stats: ContainerStats) -> dict:
        """Determine usage trend with details"""
        if len(stats.cpu_history) < 10:
            return {"direction": "stable", "strength": 0, "description": "Insufficient data"}
        
        recent = list(stats.cpu_history)[-10:]
        older = list(stats.cpu_history)[-20:-10] if len(stats.cpu_history) >= 20 else recent
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        diff = recent_avg - older_avg
        
        if diff > 10:
            return {"direction": "increasing", "strength": min(diff / 10, 3), "description": "Rapidly increasing"}
        elif diff > 3:
            return {"direction": "increasing", "strength": diff / 10, "description": "Gradually increasing"}
        elif diff < -10:
            return {"direction": "decreasing", "strength": min(abs(diff) / 10, 3), "description": "Rapidly decreasing"}
        elif diff < -3:
            return {"direction": "decreasing", "strength": abs(diff) / 10, "description": "Gradually decreasing"}
        return {"direction": "stable", "strength": 0, "description": "Stable usage"}
    
    def _predict_cpu(self, stats: ContainerStats) -> dict:
        """Predict future CPU usage"""
        if len(stats.cpu_history) < 10:
            return {"value": 0, "confidence": 0, "method": "insufficient_data"}
        
        cpu_list = list(stats.cpu_history)[-30:]
        n = len(cpu_list)
        
        # Linear regression
        x_mean = n / 2
        y_mean = sum(cpu_list) / n
        
        numerator = sum((i - x_mean) * (cpu_list[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        # Predict 30 seconds ahead
        future_x = n + 30
        predicted = intercept + slope * future_x
        predicted = max(0, min(100, predicted))
        
        # Confidence based on R-squared and sample count
        ss_tot = sum((cpu_list[i] - y_mean) ** 2 for i in range(n))
        ss_res = sum((cpu_list[i] - (intercept + slope * i)) ** 2 for i in range(n))
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        confidence = r_squared * min(n / 30, 1)
        
        return {
            "value": round(predicted, 1),
            "confidence": round(confidence, 2),
            "method": "linear_regression",
            "slope": round(slope, 3)
        }
    
    def get_all_analytics(self) -> dict:
        """Get analytics for all containers with system-wide stats"""
        container_analytics = {
            cid: self.get_container_analytics(cid) 
            for cid in self.container_stats
        }
        
        # Calculate system-wide aggregates
        total_cpu = sum(a.get("cpu_current", 0) for a in container_analytics.values())
        total_memory = sum(a.get("memory_current", 0) for a in container_analytics.values())
        avg_health = sum(a.get("health_score", 100) for a in container_analytics.values()) / max(len(container_analytics), 1)
        avg_stability = sum(a.get("stability_score", 100) for a in container_analytics.values()) / max(len(container_analytics), 1)
        avg_efficiency = sum(a.get("efficiency_score", 100) for a in container_analytics.values()) / max(len(container_analytics), 1)
        
        stressed_count = sum(1 for a in container_analytics.values() if a.get("is_stressed", False))
        unhealthy_count = sum(1 for a in container_analytics.values() if a.get("health_score", 100) < 70)
        
        # Anomaly breakdown by type
        anomaly_types = {}
        for a in self.global_anomalies[-100:]:
            atype = a.get("type", "unknown")
            anomaly_types[atype] = anomaly_types.get(atype, 0) + 1
        
        # Anomaly breakdown by severity
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for a in self.global_anomalies[-100:]:
            sev = a.get("severity", "low")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1
        
        return {
            "containers": container_analytics,
            "global_anomalies": self.global_anomalies[-50:],
            "total_anomalies": len(self.global_anomalies),
            "active_containers": len(self.container_stats),
            "timestamp": time.time(),
            "system_uptime": time.time() - self.system_start_time,
            # System-wide metrics
            "system_stats": {
                "total_cpu_percent": round(total_cpu, 2),
                "total_memory_bytes": total_memory,
                "total_memory_mb": round(total_memory / (1024*1024), 2),
                "average_health_score": round(avg_health, 1),
                "average_stability_score": round(avg_stability, 1),
                "average_efficiency_score": round(avg_efficiency, 1),
                "stressed_containers": stressed_count,
                "unhealthy_containers": unhealthy_count,
                "healthy_containers": len(container_analytics) - unhealthy_count,
            },
            # Anomaly analysis
            "anomaly_analysis": {
                "by_type": anomaly_types,
                "by_severity": severity_counts,
                "recent_rate": len([a for a in self.global_anomalies if time.time() - a.get("timestamp", 0) < 300]) / 5,  # per minute over last 5 min
            }
        }
    
    def predict_usage(self, container_id: str, minutes_ahead: int = 5) -> dict:
        """Predict future resource usage"""
        stats = self._get_stats(container_id)
        
        if len(stats.cpu_history) < 10:
            return {
                "cpu_predicted": 0, 
                "memory_predicted": 0, 
                "confidence": 0,
                "warning": "Insufficient data for prediction"
            }
        
        cpu_pred = self._predict_cpu(stats)
        mem_pred = self._predict_memory(stats)
        
        return {
            "cpu_predicted": cpu_pred["value"],
            "cpu_confidence": cpu_pred["confidence"],
            "cpu_slope": cpu_pred.get("slope", 0),
            "memory_predicted": mem_pred["value"],
            "memory_predicted_mb": mem_pred.get("value_mb", 0),
            "memory_confidence": mem_pred["confidence"],
            "memory_slope_per_sec": mem_pred.get("slope_per_sec", 0),
            "confidence": (cpu_pred["confidence"] + mem_pred["confidence"]) / 2,
            "trend": self._get_trend(stats),
            "memory_trend": self._get_memory_trend(stats),
            "method": "linear_regression",
            "prediction_horizon_seconds": 30
        }
    
    def reset_container(self, container_id: str):
        """Reset stats for a container (e.g., after restart)"""
        if container_id in self.container_stats:
            del self.container_stats[container_id]
    
    def get_container_history_data(self, container_id: str) -> dict:
        """Get raw history data for charts"""
        stats = self._get_stats(container_id)
        return {
            "container_id": container_id,
            "cpu_history": list(stats.cpu_history),
            "mem_history": [m / (1024*1024) for m in stats.mem_history],  # Convert to MB
            "timestamps": list(stats.timestamps),
            "cpu_history_long": list(stats.cpu_history_long),
            "mem_history_long": [m / (1024*1024) for m in stats.mem_history_long],
        }


# Global detector instance with tuned parameters
detector = EnhancedAnomalyDetector(
    base_z_threshold=2.0,      # Base threshold
    ema_alpha=0.3,             # Responsive EMA
    ema_alpha_slow=0.1,        # Slow EMA for trend detection
    min_samples=5,             # Quick baseline learning
    stress_threshold_cpu=70.0  # CPU stress threshold
)
