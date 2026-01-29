"""MiniContainer - ML-based Anomaly Detection

Uses statistical methods (Z-score, Moving Average) to detect unusual
container behavior without heavy ML libraries.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import math

@dataclass
class ContainerStats:
    """Rolling statistics for a container"""
    cpu_history: deque = field(default_factory=lambda: deque(maxlen=60))
    mem_history: deque = field(default_factory=lambda: deque(maxlen=60))
    timestamps: deque = field(default_factory=lambda: deque(maxlen=60))
    anomalies: List[dict] = field(default_factory=list)
    health_score: float = 100.0
    
class AnomalyDetector:
    """
    Simple ML-based anomaly detection using:
    - Z-score for spike detection
    - Moving average for trend analysis
    - Health scoring based on resource usage patterns
    """
    
    def __init__(self, z_threshold: float = 2.5, window_size: int = 10):
        self.z_threshold = z_threshold
        self.window_size = window_size
        self.container_stats: Dict[str, ContainerStats] = {}
        self.global_anomalies: List[dict] = []
    
    def _get_stats(self, container_id: str) -> ContainerStats:
        """Get or create stats for a container"""
        if container_id not in self.container_stats:
            self.container_stats[container_id] = ContainerStats()
        return self.container_stats[container_id]
    
    def _calculate_mean(self, data: deque) -> float:
        """Calculate mean of data"""
        if not data:
            return 0.0
        return sum(data) / len(data)
    
    def _calculate_std(self, data: deque, mean: float) -> float:
        """Calculate standard deviation"""
        if len(data) < 2:
            return 0.0
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return math.sqrt(variance)
    
    def _calculate_z_score(self, value: float, mean: float, std: float) -> float:
        """Calculate Z-score for anomaly detection"""
        if std == 0:
            return 0.0
        return (value - mean) / std
    
    def _moving_average(self, data: deque, window: int) -> float:
        """Calculate moving average"""
        if not data:
            return 0.0
        recent = list(data)[-window:]
        return sum(recent) / len(recent)
    
    def add_metrics(self, container_id: str, cpu_percent: float, memory_bytes: int):
        """Add new metrics and check for anomalies"""
        stats = self._get_stats(container_id)
        current_time = time.time()
        
        # Add to history
        stats.cpu_history.append(cpu_percent)
        stats.mem_history.append(memory_bytes)
        stats.timestamps.append(current_time)
        
        anomalies_detected = []
        
        # Only check for anomalies if we have enough data
        if len(stats.cpu_history) >= self.window_size:
            # CPU anomaly detection
            cpu_mean = self._calculate_mean(stats.cpu_history)
            cpu_std = self._calculate_std(stats.cpu_history, cpu_mean)
            cpu_z = self._calculate_z_score(cpu_percent, cpu_mean, cpu_std)
            
            if abs(cpu_z) > self.z_threshold:
                anomaly = {
                    "type": "cpu_spike" if cpu_z > 0 else "cpu_drop",
                    "container_id": container_id,
                    "timestamp": current_time,
                    "value": cpu_percent,
                    "z_score": cpu_z,
                    "severity": "high" if abs(cpu_z) > 3.5 else "medium",
                    "message": f"CPU {'spike' if cpu_z > 0 else 'drop'} detected: {cpu_percent:.1f}% (Z={cpu_z:.2f})"
                }
                anomalies_detected.append(anomaly)
                stats.anomalies.append(anomaly)
                self.global_anomalies.append(anomaly)
            
            # Memory anomaly detection
            mem_mean = self._calculate_mean(stats.mem_history)
            mem_std = self._calculate_std(stats.mem_history, mem_mean)
            mem_z = self._calculate_z_score(memory_bytes, mem_mean, mem_std)
            
            if abs(mem_z) > self.z_threshold:
                anomaly = {
                    "type": "memory_spike" if mem_z > 0 else "memory_drop",
                    "container_id": container_id,
                    "timestamp": current_time,
                    "value": memory_bytes,
                    "z_score": mem_z,
                    "severity": "high" if abs(mem_z) > 3.5 else "medium",
                    "message": f"Memory {'spike' if mem_z > 0 else 'drop'} detected (Z={mem_z:.2f})"
                }
                anomalies_detected.append(anomaly)
                stats.anomalies.append(anomaly)
                self.global_anomalies.append(anomaly)
        
        # Calculate health score
        stats.health_score = self._calculate_health_score(stats, cpu_percent, memory_bytes)
        
        # Keep only recent anomalies (last 100)
        if len(stats.anomalies) > 100:
            stats.anomalies = stats.anomalies[-100:]
        if len(self.global_anomalies) > 500:
            self.global_anomalies = self.global_anomalies[-500:]
        
        return anomalies_detected
    
    def _calculate_health_score(self, stats: ContainerStats, cpu: float, mem: int) -> float:
        """
        Calculate health score (0-100) based on:
        - Current resource usage
        - Recent anomalies
        - Trend stability
        """
        score = 100.0
        
        # Penalize high CPU usage
        if cpu > 80:
            score -= (cpu - 80) * 0.5
        
        # Penalize recent anomalies
        recent_anomalies = [a for a in stats.anomalies 
                          if time.time() - a["timestamp"] < 300]  # Last 5 mins
        score -= len(recent_anomalies) * 5
        
        # Penalize high variance (instability)
        if len(stats.cpu_history) >= 10:
            cpu_mean = self._calculate_mean(stats.cpu_history)
            cpu_std = self._calculate_std(stats.cpu_history, cpu_mean)
            if cpu_mean > 0:
                cv = cpu_std / cpu_mean  # Coefficient of variation
                if cv > 0.5:
                    score -= cv * 10
        
        return max(0, min(100, score))
    
    def get_container_analytics(self, container_id: str) -> dict:
        """Get analytics data for a container"""
        stats = self._get_stats(container_id)
        
        cpu_list = list(stats.cpu_history)
        mem_list = list(stats.mem_history)
        time_list = list(stats.timestamps)
        
        return {
            "container_id": container_id,
            "health_score": stats.health_score,
            "cpu_history": cpu_list,
            "memory_history": mem_list,
            "timestamps": time_list,
            "cpu_avg": self._calculate_mean(stats.cpu_history),
            "cpu_max": max(cpu_list) if cpu_list else 0,
            "cpu_min": min(cpu_list) if cpu_list else 0,
            "memory_avg": self._calculate_mean(stats.mem_history),
            "memory_max": max(mem_list) if mem_list else 0,
            "anomaly_count": len(stats.anomalies),
            "recent_anomalies": stats.anomalies[-10:],
            "trend": self._get_trend(stats)
        }
    
    def _get_trend(self, stats: ContainerStats) -> str:
        """Determine CPU trend: increasing, decreasing, or stable"""
        if len(stats.cpu_history) < 10:
            return "stable"
        
        recent = list(stats.cpu_history)[-10:]
        older = list(stats.cpu_history)[-20:-10] if len(stats.cpu_history) >= 20 else recent
        
        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)
        
        diff = recent_avg - older_avg
        if diff > 5:
            return "increasing"
        elif diff < -5:
            return "decreasing"
        return "stable"
    
    def get_all_analytics(self) -> dict:
        """Get analytics for all containers"""
        return {
            "containers": {
                cid: self.get_container_analytics(cid) 
                for cid in self.container_stats
            },
            "global_anomalies": self.global_anomalies[-50:],
            "total_anomalies": len(self.global_anomalies),
            "timestamp": time.time()
        }
    
    def predict_usage(self, container_id: str, minutes_ahead: int = 5) -> dict:
        """Simple linear prediction of future usage"""
        stats = self._get_stats(container_id)
        
        if len(stats.cpu_history) < 10:
            return {"cpu_predicted": 0, "memory_predicted": 0, "confidence": 0}
        
        # Simple linear regression on recent data
        cpu_list = list(stats.cpu_history)[-20:]
        n = len(cpu_list)
        
        # Calculate slope
        x_mean = n / 2
        y_mean = sum(cpu_list) / n
        
        numerator = sum((i - x_mean) * (cpu_list[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        # Predict
        future_x = n + (minutes_ahead * 60)  # Assuming 1 sample per second
        cpu_predicted = max(0, min(100, intercept + slope * future_x))
        
        return {
            "cpu_predicted": cpu_predicted,
            "memory_predicted": self._moving_average(stats.mem_history, 10),
            "confidence": min(0.9, len(cpu_list) / 20),
            "trend": "up" if slope > 0 else "down" if slope < 0 else "stable"
        }

# Global detector instance - lower threshold for more sensitive detection
detector = AnomalyDetector(z_threshold=1.5, window_size=5)
