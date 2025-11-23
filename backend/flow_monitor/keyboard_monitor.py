"""
Keyboard Monitoring Module
Tracks typing cadence, inter-key latency, and error rate
"""

import time
from collections import deque
from threading import Lock
from pynput import keyboard


class KeyboardMonitor:
    def __init__(self, window_size=60):
        """
        Initialize keyboard monitor
        
        Args:
            window_size: Time window in seconds for metric calculation
        """
        self.window_size = window_size
        self.key_timestamps = deque(maxlen=1000)
        self.backspace_count = 0
        self.delete_count = 0
        self.total_keys = 0
        self.inter_key_latencies = deque(maxlen=100)
        
        self.lock = Lock()
        self.listener = None
        self.last_key_time = None
        
    def on_press(self, key):
        """Handle key press events"""
        current_time = time.time()
        
        with self.lock:
            # Calculate inter-key latency
            if self.last_key_time is not None:
                latency = current_time - self.last_key_time
                # Only consider reasonable latencies (< 5 seconds)
                if latency < 5.0:
                    self.inter_key_latencies.append(latency)
            
            self.last_key_time = current_time
            self.key_timestamps.append(current_time)
            self.total_keys += 1
            
            # Track backspace/delete for error rate
            try:
                if key == keyboard.Key.backspace:
                    self.backspace_count += 1
                elif key == keyboard.Key.delete:
                    self.delete_count += 1
            except AttributeError:
                pass
    
    def get_metrics(self):
        """
        Calculate current keyboard metrics
        
        Returns:
            dict: Keyboard metrics including typing cadence, latency, and error rate
        """
        current_time = time.time()
        
        with self.lock:
            # Filter timestamps within window
            recent_keys = [ts for ts in self.key_timestamps 
                          if current_time - ts <= self.window_size]
            
            # Calculate typing cadence (keys per minute)
            if recent_keys:
                time_span = max(current_time - recent_keys[0], 1)
                typing_cadence = (len(recent_keys) / time_span) * 60
            else:
                typing_cadence = 0
            
            # Calculate average inter-key latency
            if self.inter_key_latencies:
                avg_latency = sum(self.inter_key_latencies) / len(self.inter_key_latencies)
                latency_variance = sum((x - avg_latency) ** 2 
                                      for x in self.inter_key_latencies) / len(self.inter_key_latencies)
            else:
                avg_latency = 0
                latency_variance = 0
            
            # Calculate error rate
            if self.total_keys > 0:
                error_rate = (self.backspace_count + self.delete_count) / self.total_keys
            else:
                error_rate = 0
            
            return {
                'typing_cadence': typing_cadence,  # keys per minute
                'avg_inter_key_latency': avg_latency,  # seconds
                'latency_variance': latency_variance,
                'error_rate': error_rate,  # ratio
                'backspace_count': self.backspace_count,
                'delete_count': self.delete_count,
                'total_keys': len(recent_keys),
                'timestamp': current_time
            }
    
    def start(self):
        """Start monitoring keyboard events"""
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()
        print("Keyboard monitor started")
    
    def stop(self):
        """Stop monitoring keyboard events"""
        if self.listener:
            self.listener.stop()
            print("Keyboard monitor stopped")
    
    def reset(self):
        """Reset all counters"""
        with self.lock:
            self.key_timestamps.clear()
            self.inter_key_latencies.clear()
            self.backspace_count = 0
            self.delete_count = 0
            self.total_keys = 0
            self.last_key_time = None
