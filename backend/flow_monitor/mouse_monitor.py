"""
Mouse Monitoring Module
Tracks mouse movement, scroll velocity, and scroll bursts
"""

import time
from collections import deque
from threading import Lock
from pynput import mouse


class MouseMonitor:
    def __init__(self, window_size=60):
        """
        Initialize mouse monitor
        
        Args:
            window_size: Time window in seconds for metric calculation
        """
        self.window_size = window_size
        self.mouse_moves = deque(maxlen=1000)
        self.scroll_events = deque(maxlen=500)
        self.scroll_velocities = deque(maxlen=100)
        
        self.lock = Lock()
        self.listener = None
        self.last_mouse_time = None
        self.last_scroll_time = None
        
        # For tracking scroll bursts
        self.scroll_burst_threshold = 5  # scrolls per second
        self.burst_count = 0
        
    def on_move(self, x, y):
        """Handle mouse move events"""
        current_time = time.time()
        
        with self.lock:
            self.mouse_moves.append({
                'x': x,
                'y': y,
                'timestamp': current_time
            })
            self.last_mouse_time = current_time
    
    def on_scroll(self, x, y, dx, dy):
        """Handle scroll events"""
        current_time = time.time()
        
        with self.lock:
            # Calculate scroll velocity
            if self.last_scroll_time is not None:
                time_diff = current_time - self.last_scroll_time
                if time_diff > 0:
                    scroll_velocity = abs(dy) / time_diff
                    self.scroll_velocities.append(scroll_velocity)
                    
                    # Check for scroll burst (rapid scrolling)
                    if time_diff < 0.2:  # Less than 200ms between scrolls
                        self.burst_count += 1
            
            self.scroll_events.append({
                'dx': dx,
                'dy': dy,
                'timestamp': current_time
            })
            self.last_scroll_time = current_time
    
    def get_metrics(self):
        """
        Calculate current mouse metrics
        
        Returns:
            dict: Mouse metrics including movement rate, scroll velocity, and bursts
        """
        current_time = time.time()
        
        with self.lock:
            # Filter recent mouse moves
            recent_moves = [m for m in self.mouse_moves 
                           if current_time - m['timestamp'] <= self.window_size]
            
            # Calculate mouse move rate (moves per minute)
            if recent_moves:
                time_span = max(current_time - recent_moves[0]['timestamp'], 1)
                mouse_move_rate = (len(recent_moves) / time_span) * 60
                
                # Calculate average distance moved
                total_distance = 0
                for i in range(1, len(recent_moves)):
                    dx = recent_moves[i]['x'] - recent_moves[i-1]['x']
                    dy = recent_moves[i]['y'] - recent_moves[i-1]['y']
                    distance = (dx**2 + dy**2) ** 0.5
                    total_distance += distance
                avg_distance = total_distance / len(recent_moves) if recent_moves else 0
            else:
                mouse_move_rate = 0
                avg_distance = 0
            
            # Filter recent scroll events
            recent_scrolls = [s for s in self.scroll_events 
                            if current_time - s['timestamp'] <= self.window_size]
            
            # Calculate scroll velocity metrics
            if self.scroll_velocities:
                avg_scroll_velocity = sum(self.scroll_velocities) / len(self.scroll_velocities)
                max_scroll_velocity = max(self.scroll_velocities)
            else:
                avg_scroll_velocity = 0
                max_scroll_velocity = 0
            
            # Calculate scroll frequency
            if recent_scrolls:
                time_span = max(current_time - recent_scrolls[0]['timestamp'], 1)
                scroll_frequency = (len(recent_scrolls) / time_span) * 60
            else:
                scroll_frequency = 0
            
            return {
                'mouse_move_rate': mouse_move_rate,  # moves per minute
                'avg_mouse_distance': avg_distance,  # pixels
                'scroll_velocity': avg_scroll_velocity,  # scroll units per second
                'max_scroll_velocity': max_scroll_velocity,
                'scroll_frequency': scroll_frequency,  # scrolls per minute
                'scroll_bursts': self.burst_count,  # number of rapid scroll events
                'total_scrolls': len(recent_scrolls),
                'timestamp': current_time
            }
    
    def start(self):
        """Start monitoring mouse events"""
        self.listener = mouse.Listener(
            on_move=self.on_move,
            on_scroll=self.on_scroll
        )
        self.listener.start()
        print("Mouse monitor started")
    
    def stop(self):
        """Stop monitoring mouse events"""
        if self.listener:
            self.listener.stop()
            print("Mouse monitor stopped")
    
    def reset(self):
        """Reset all counters"""
        with self.lock:
            self.mouse_moves.clear()
            self.scroll_events.clear()
            self.scroll_velocities.clear()
            self.burst_count = 0
            self.last_mouse_time = None
            self.last_scroll_time = None
