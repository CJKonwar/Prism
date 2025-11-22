"""
Flow State Detection Algorithm
AI-driven analysis to detect and classify flow state from behavioral metrics
"""

import time
import numpy as np
from collections import deque
from threading import Lock


class FlowStateDetector:
    """
    Analyzes behavioral patterns to detect flow state
    
    Flow State Indicators:
    - Consistent typing cadence (steady rhythm)
    - Low inter-key latency variance (smooth typing)
    - Low error rate (fewer corrections)
    - Minimal task switching
    - Focused mouse movement (less erratic)
    - Moderate scroll velocity (engaged reading)
    - Few app switches
    """
    
    # Flow state thresholds (can be tuned based on user data)
    THRESHOLDS = {
        'typing_cadence_min': 30,  # minimum keys/min
        'typing_cadence_max': 200,  # maximum keys/min
        'latency_variance_max': 0.05,  # low variance = consistent
        'error_rate_max': 0.15,  # max 15% errors
        'task_switch_max': 5,  # switches per minute
        'app_count_max': 3,  # max apps in use
        'scroll_burst_max': 10,  # max scroll bursts
    }
    
    # Flow state levels
    FLOW_LEVELS = {
        'DEEP_FLOW': 4,      # Optimal flow state
        'FLOW': 3,            # Good flow state
        'FOCUSED': 2,         # Focused but not in flow
        'WORKING': 1,         # Active but distracted
        'DISTRACTED': 0       # Not focused
    }
    
    def __init__(self, history_size=10):
        """
        Initialize flow state detector
        
        Args:
            history_size: Number of past readings to consider
        """
        self.history_size = history_size
        self.flow_history = deque(maxlen=history_size)
        self.metrics_history = deque(maxlen=100)
        
        self.lock = Lock()
        self.current_flow_state = 'WORKING'
        self.flow_score = 0.0
        self.flow_duration = 0.0
        self.flow_start_time = None
        
    def calculate_flow_score(self, metrics):
        """
        Calculate a flow score (0-100) based on all metrics
        
        Args:
            metrics: dict containing all behavioral metrics
            
        Returns:
            float: Flow score (0-100)
        """
        scores = []
        weights = []
        
        # 1. Typing consistency score (25% weight)
        if metrics.get('typing_cadence', 0) > 0:
            typing_score = 0
            cadence = metrics['typing_cadence']
            
            # Optimal cadence range
            if self.THRESHOLDS['typing_cadence_min'] <= cadence <= self.THRESHOLDS['typing_cadence_max']:
                typing_score += 50
            
            # Low latency variance (consistent rhythm)
            latency_var = metrics.get('latency_variance', 1.0)
            if latency_var < self.THRESHOLDS['latency_variance_max']:
                typing_score += 30
            
            # Low error rate
            error_rate = metrics.get('error_rate', 1.0)
            if error_rate < self.THRESHOLDS['error_rate_max']:
                typing_score += 20
            
            scores.append(typing_score)
            weights.append(0.25)
        
        # 2. Task focus score (30% weight)
        focus_score = 0
        
        # Low task switching
        task_switches = metrics.get('task_switch_frequency', 100)
        if task_switches < self.THRESHOLDS['task_switch_max']:
            focus_score += 40
        elif task_switches < self.THRESHOLDS['task_switch_max'] * 2:
            focus_score += 20
        
        # Few active apps
        app_count = metrics.get('active_app_count', 10)
        if app_count <= self.THRESHOLDS['app_count_max']:
            focus_score += 40
        elif app_count <= self.THRESHOLDS['app_count_max'] * 2:
            focus_score += 20
        
        # Time spent per app
        avg_time_per_app = metrics.get('avg_time_per_app', 0)
        if avg_time_per_app > 30:  # 30+ seconds per app
            focus_score += 20
        
        scores.append(focus_score)
        weights.append(0.30)
        
        # 3. Mouse behavior score (20% weight)
        mouse_score = 0
        
        # Moderate mouse movement (not too erratic, not idle)
        mouse_rate = metrics.get('mouse_move_rate', 0)
        if 10 <= mouse_rate <= 100:  # moves per minute
            mouse_score += 50
        
        # Low scroll bursts (not frantically scrolling)
        scroll_bursts = metrics.get('scroll_bursts', 100)
        if scroll_bursts < self.THRESHOLDS['scroll_burst_max']:
            mouse_score += 50
        
        scores.append(mouse_score)
        weights.append(0.20)
        
        # 4. Engagement score (25% weight)
        engagement_score = 0
        
        # Active typing
        if metrics.get('total_keys', 0) > 10:
            engagement_score += 30
        
        # Active scrolling (reading/reviewing)
        scroll_freq = metrics.get('scroll_frequency', 0)
        if 5 <= scroll_freq <= 50:  # scrolls per minute
            engagement_score += 35
        
        # Moderate scroll velocity (engaged, not frantic)
        scroll_vel = metrics.get('scroll_velocity', 0)
        if 0 < scroll_vel < 100:
            engagement_score += 35
        
        scores.append(engagement_score)
        weights.append(0.25)
        
        # Calculate weighted average
        if scores:
            total_weight = sum(weights)
            flow_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        else:
            flow_score = 0
        
        return flow_score
    
    def classify_flow_state(self, flow_score):
        """
        Classify the flow state based on score
        
        Args:
            flow_score: Current flow score (0-100)
            
        Returns:
            str: Flow state classification
        """
        if flow_score >= 80:
            return 'DEEP_FLOW'
        elif flow_score >= 65:
            return 'FLOW'
        elif flow_score >= 45:
            return 'FOCUSED'
        elif flow_score >= 25:
            return 'WORKING'
        else:
            return 'DISTRACTED'
    
    def analyze(self, keyboard_metrics, mouse_metrics, window_metrics):
        """
        Analyze all metrics and determine flow state
        
        Args:
            keyboard_metrics: dict from KeyboardMonitor
            mouse_metrics: dict from MouseMonitor
            window_metrics: dict from WindowMonitor
            
        Returns:
            dict: Flow state analysis results
        """
        current_time = time.time()
        
        # Combine all metrics
        combined_metrics = {
            **keyboard_metrics,
            **mouse_metrics,
            **window_metrics
        }
        
        with self.lock:
            # Calculate flow score
            flow_score = self.calculate_flow_score(combined_metrics)
            
            # Classify flow state
            flow_state = self.classify_flow_state(flow_score)
            
            # Track flow duration
            if flow_state in ['FLOW', 'DEEP_FLOW']:
                if self.flow_start_time is None:
                    self.flow_start_time = current_time
                self.flow_duration = current_time - self.flow_start_time
            else:
                self.flow_start_time = None
                self.flow_duration = 0.0
            
            # Update history
            self.flow_history.append({
                'state': flow_state,
                'score': flow_score,
                'timestamp': current_time
            })
            
            self.metrics_history.append(combined_metrics)
            
            # Calculate flow stability (how consistent is the flow state)
            if len(self.flow_history) >= 3:
                recent_states = [h['state'] for h in list(self.flow_history)[-5:]]
                flow_stability = recent_states.count(flow_state) / len(recent_states)
            else:
                flow_stability = 0.0
            
            # Store current state
            self.current_flow_state = flow_state
            self.flow_score = flow_score
            
            # Generate analysis report
            return {
                'flow_state': flow_state,
                'flow_level': self.FLOW_LEVELS[flow_state],
                'flow_score': round(flow_score, 2),
                'flow_duration': round(self.flow_duration, 2),
                'flow_stability': round(flow_stability, 2),
                'in_flow': flow_state in ['FLOW', 'DEEP_FLOW'],
                'metrics_summary': {
                    'typing_cadence': round(combined_metrics.get('typing_cadence', 0), 2),
                    'error_rate': round(combined_metrics.get('error_rate', 0), 3),
                    'task_switches': combined_metrics.get('total_switches', 0),
                    'active_apps': combined_metrics.get('active_app_count', 0),
                    'current_app': combined_metrics.get('current_app', 'Unknown')
                },
                'timestamp': current_time
            }
    
    def get_flow_trends(self, window_minutes=10):
        """
        Get flow state trends over time
        
        Args:
            window_minutes: Time window to analyze
            
        Returns:
            dict: Trend analysis
        """
        current_time = time.time()
        window_seconds = window_minutes * 60
        
        with self.lock:
            recent_history = [h for h in self.flow_history 
                            if current_time - h['timestamp'] <= window_seconds]
            
            if not recent_history:
                return {
                    'avg_flow_score': 0,
                    'flow_percentage': 0,
                    'deep_flow_percentage': 0,
                    'trend': 'STABLE'
                }
            
            # Calculate average flow score
            avg_score = sum(h['score'] for h in recent_history) / len(recent_history)
            
            # Calculate time in flow states
            flow_count = sum(1 for h in recent_history if h['state'] in ['FLOW', 'DEEP_FLOW'])
            deep_flow_count = sum(1 for h in recent_history if h['state'] == 'DEEP_FLOW')
            
            flow_percentage = (flow_count / len(recent_history)) * 100
            deep_flow_percentage = (deep_flow_count / len(recent_history)) * 100
            
            # Determine trend
            if len(recent_history) >= 5:
                first_half = recent_history[:len(recent_history)//2]
                second_half = recent_history[len(recent_history)//2:]
                
                avg_first = sum(h['score'] for h in first_half) / len(first_half)
                avg_second = sum(h['score'] for h in second_half) / len(second_half)
                
                if avg_second > avg_first + 10:
                    trend = 'IMPROVING'
                elif avg_second < avg_first - 10:
                    trend = 'DECLINING'
                else:
                    trend = 'STABLE'
            else:
                trend = 'STABLE'
            
            return {
                'avg_flow_score': round(avg_score, 2),
                'flow_percentage': round(flow_percentage, 2),
                'deep_flow_percentage': round(deep_flow_percentage, 2),
                'trend': trend,
                'samples': len(recent_history)
            }
