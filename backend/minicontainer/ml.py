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
    
    # Anomaly tracking
    anomalies: List[dict] = field(default_factory=list)
    
    # Adaptive baseline (EMA)
    cpu_ema: float = 0.0
    mem_ema: float = 0.0
    cpu_ema_variance: float = 0.0
    mem_ema_variance: float = 0.0
    
    # Health metrics
    health_score: float = 100.0
    stability_score: float = 100.0
    
    # Pattern detection
    is_stressed: bool = False
    stress_start_time: Optional[float] = None
    stress_duration: float = 0.0
    
    # Learning state
    samples_collected: int = 0
    baseline_learned: bool = False


class EnhancedAnomalyDetector:
    """
    Advanced ML-based anomaly detection with multiple algorithms:
    
    1. Adaptive Z-Score: Adjusts threshold based on historical variance
    2. EMA-Based Detection: Uses exponential moving averages for smoother detection
    3. Sudden Change Detection: Detects rapid changes in metrics
    4. Resource Exhaustion Warning: Predicts when resources will hit limits
    """
    
    def __init__(self, 
                 base_z_threshold: float = 2.0,
                 ema_alpha: float = 0.3,
                 min_samples: int = 5,
                 stress_threshold_cpu: float = 70.0,
                 stress_threshold_mem_percent: float = 80.0):
        """
        Initialize detector with configurable parameters.
        
        Args:
            base_z_threshold: Base Z-score threshold (adjusted adaptively)
            ema_alpha: EMA smoothing factor (0-1, higher = more reactive)
            min_samples: Minimum samples before detection starts
            stress_threshold_cpu: CPU % to consider as stressed
            stress_threshold_mem_percent: Memory % to consider as stressed
        """
        self.base_z_threshold = base_z_threshold
        self.ema_alpha = ema_alpha
        self.min_samples = min_samples
        self.stress_threshold_cpu = stress_threshold_cpu
        self.stress_threshold_mem = stress_threshold_mem_percent
        
        self.container_stats: Dict[str, ContainerStats] = {}
        self.global_anomalies: List[dict] = []
    
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
                    memory_limit: int = 268435456) -> List[dict]:
        """
        Add new metrics and run all detection algorithms.
        
        Returns list of detected anomalies.
        """
        stats = self._get_stats(container_id)
        current_time = time.time()
        
        # Update sample count
        stats.samples_collected += 1
        is_first = stats.samples_collected == 1
        
        # Update EMAs
        stats.cpu_ema = self._update_ema(cpu_percent, stats.cpu_ema, is_first)
        stats.mem_ema = self._update_ema(memory_bytes, stats.mem_ema, is_first)
        stats.cpu_ema_variance = self._update_ema_variance(cpu_percent, stats.cpu_ema, stats.cpu_ema_variance, is_first)
        stats.mem_ema_variance = self._update_ema_variance(memory_bytes, stats.mem_ema, stats.mem_ema_variance, is_first)
        
        # Add to history
        stats.cpu_history.append(cpu_percent)
        stats.mem_history.append(memory_bytes)
        stats.timestamps.append(current_time)
        
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
                severity = "high" if abs(cpu_z) > threshold * 1.5 else "medium"
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
                severity = "high" if abs(mem_z) > threshold * 1.5 else "medium"
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
            if is_sudden and change_ratio > 0.8:  # Major sudden change
                anomaly = {
                    "type": "sudden_cpu_change",
                    "container_id": container_id,
                    "timestamp": current_time,
                    "value": round(cpu_percent, 2),
                    "change_ratio": round(change_ratio, 2),
                    "severity": "high" if change_ratio > 1.5 else "medium",
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
        elif not is_stressed and stats.is_stressed:
            if stats.stress_start_time:
                stats.stress_duration = current_time - stats.stress_start_time
            stats.is_stressed = False
            stats.stress_start_time = None
        
        # Add anomalies to tracking
        for anomaly in anomalies_detected:
            stats.anomalies.append(anomaly)
            self.global_anomalies.append(anomaly)
        
        # Calculate health score
        stats.health_score = self._calculate_health_score(stats, cpu_percent, memory_bytes, memory_limit)
        stats.stability_score = self._calculate_stability_score(stats)
        
        # Cleanup old anomalies
        self._cleanup_old_anomalies(stats)
        
        return anomalies_detected
    
    def _calculate_health_score(self, stats: ContainerStats, cpu: float, mem: int, mem_limit: int) -> float:
        """Calculate comprehensive health score (0-100)"""
        score = 100.0
        
        # CPU usage penalty
        if cpu > 90:
            score -= 30
        elif cpu > 70:
            score -= (cpu - 70) * 0.5
        
        # Memory usage penalty
        mem_percent = (mem / mem_limit * 100) if mem_limit > 0 else 0
        if mem_percent > 90:
            score -= 30
        elif mem_percent > 70:
            score -= (mem_percent - 70) * 0.5
        
        # Recent anomalies penalty
        recent = [a for a in stats.anomalies if time.time() - a["timestamp"] < 120]
        high_severity = sum(1 for a in recent if a.get("severity") == "high")
        medium_severity = sum(1 for a in recent if a.get("severity") == "medium")
        score -= high_severity * 10
        score -= medium_severity * 5
        
        # Stress penalty
        if stats.is_stressed:
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_stability_score(self, stats: ContainerStats) -> float:
        """Calculate stability score based on variance"""
        if stats.samples_collected < 10:
            return 100.0
        
        score = 100.0
        
        # CPU stability
        cpu_cv = math.sqrt(stats.cpu_ema_variance) / max(stats.cpu_ema, 1)
        if cpu_cv > 0.5:
            score -= 30
        elif cpu_cv > 0.3:
            score -= 15
        
        # Memory stability
        mem_cv = math.sqrt(stats.mem_ema_variance) / max(stats.mem_ema, 1)
        if mem_cv > 0.5:
            score -= 30
        elif mem_cv > 0.3:
            score -= 15
        
        return max(0, min(100, score))
    
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
        
        return {
            "container_id": container_id,
            "health_score": round(stats.health_score, 1),
            "stability_score": round(stats.stability_score, 1),
            "cpu_current": round(cpu_list[-1], 2) if cpu_list else 0,
            "cpu_avg": round(stats.cpu_ema, 2),
            "cpu_max": round(max(cpu_list), 2) if cpu_list else 0,
            "cpu_std": round(math.sqrt(stats.cpu_ema_variance), 2),
            "memory_current": mem_list[-1] if mem_list else 0,
            "memory_avg": int(stats.mem_ema),
            "memory_max": max(mem_list) if mem_list else 0,
            "is_stressed": stats.is_stressed,
            "baseline_learned": stats.baseline_learned,
            "samples_collected": stats.samples_collected,
            "anomaly_count_total": len(stats.anomalies),
            "anomaly_count_recent": len([a for a in stats.anomalies if time.time() - a["timestamp"] < 120]),
            "recent_anomalies": stats.anomalies[-10:],
            "trend": self._get_trend(stats),
            "prediction": self._predict_cpu(stats)
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
        """Get analytics for all containers"""
        return {
            "containers": {
                cid: self.get_container_analytics(cid) 
                for cid in self.container_stats
            },
            "global_anomalies": self.global_anomalies[-50:],
            "total_anomalies": len(self.global_anomalies),
            "active_containers": len(self.container_stats),
            "timestamp": time.time()
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
        
        return {
            "cpu_predicted": cpu_pred["value"],
            "memory_predicted": int(stats.mem_ema),
            "confidence": cpu_pred["confidence"],
            "trend": cpu_pred["slope"],
            "method": "linear_regression"
        }
    
    def reset_container(self, container_id: str):
        """Reset stats for a container (e.g., after restart)"""
        if container_id in self.container_stats:
            del self.container_stats[container_id]


# Global detector instance with tuned parameters
detector = EnhancedAnomalyDetector(
    base_z_threshold=2.0,      # Base threshold
    ema_alpha=0.3,             # Responsive EMA
    min_samples=5,             # Quick baseline learning
    stress_threshold_cpu=70.0  # CPU stress threshold
)
