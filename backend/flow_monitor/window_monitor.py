"""
Window/App Monitoring Module
Tracks task switching, active apps, and window changes
"""

import time
from collections import deque, defaultdict
from threading import Lock, Thread
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID
)
from AppKit import NSWorkspace


class WindowMonitor:
    def __init__(self, window_size=60, poll_interval=1.0, allowed_apps=None):
        """
        Initialize window monitor
        
        Args:
            window_size: Time window in seconds for metric calculation
            poll_interval: How often to check active window (seconds)
            allowed_apps: List of apps to track (None = track all)
        """
        self.window_size = window_size
        self.poll_interval = poll_interval
        self.allowed_apps = set(allowed_apps) if allowed_apps else None
        
        self.active_window_history = deque(maxlen=1000)
        self.app_usage = defaultdict(float)  # app_name -> total time
        self.window_switches = deque(maxlen=500)
        
        self.lock = Lock()
        self.running = False
        self.monitor_thread = None
        
        self.current_app = None
        self.current_window = None
        self.last_check_time = None
    
    def set_allowed_apps(self, apps):
        """Set the list of apps to track"""
        with self.lock:
            self.allowed_apps = set(apps) if apps else None
    
    def is_app_tracked(self, app_name):
        """Check if an app should be tracked"""
        if self.allowed_apps is None:
            return True  # Track all apps if no whitelist
        return app_name in self.allowed_apps
        
    def get_active_window(self):
        """
        Get the currently active window and application
        
        Returns:
            tuple: (app_name, window_title)
        """
        try:
            # Get active application
            workspace = NSWorkspace.sharedWorkspace()
            active_app = workspace.activeApplication()
            app_name = active_app.get('NSApplicationName', 'Unknown')
            
            # Get window list
            window_list = CGWindowListCopyWindowInfo(
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID
            )
            
            # Find the frontmost window
            window_title = 'Unknown'
            if window_list:
                for window in window_list:
                    if window.get('kCGWindowOwnerName') == app_name:
                        window_title = window.get('kCGWindowName', 'Unknown')
                        if window_title and window_title != 'Unknown':
                            break
            
            return app_name, window_title
            
        except Exception as e:
            print(f"Error getting active window: {e}")
            return "Unknown", "Unknown"
    
    def monitor_loop(self):
        """Continuous monitoring loop"""
        while self.running:
            current_time = time.time()
            
            try:
                app_name, window_title = self.get_active_window()
                
                # Only track if app is in whitelist (or no whitelist set)
                if not self.is_app_tracked(app_name):
                    time.sleep(self.poll_interval)
                    continue
                
                with self.lock:
                    # Track window/app changes
                    if self.current_app != app_name or self.current_window != window_title:
                        self.window_switches.append({
                            'from_app': self.current_app,
                            'to_app': app_name,
                            'from_window': self.current_window,
                            'to_window': window_title,
                            'timestamp': current_time
                        })
                        
                        self.current_app = app_name
                        self.current_window = window_title
                    
                    # Track app usage time (only for allowed apps)
                    if self.last_check_time and self.current_app and self.is_app_tracked(self.current_app):
                        time_spent = current_time - self.last_check_time
                        self.app_usage[self.current_app] += time_spent
                    
                    # Record current state
                    self.active_window_history.append({
                        'app': app_name,
                        'window': window_title,
                        'timestamp': current_time
                    })
                    
                    self.last_check_time = current_time
                    
            except Exception as e:
                print(f"Error in monitor loop: {e}")
            
            time.sleep(self.poll_interval)
    
    def get_metrics(self):
        """
        Calculate current window/app metrics
        
        Returns:
            dict: Window and app switching metrics
        """
        current_time = time.time()
        
        with self.lock:
            # Filter recent switches
            recent_switches = [s for s in self.window_switches 
                             if current_time - s['timestamp'] <= self.window_size]
            
            # Calculate task switching frequency
            if recent_switches:
                time_span = max(current_time - recent_switches[0]['timestamp'], 1)
                switch_frequency = (len(recent_switches) / time_span) * 60
            else:
                switch_frequency = 0
            
            # Count unique apps in window
            recent_history = [h for h in self.active_window_history 
                            if current_time - h['timestamp'] <= self.window_size]
            unique_apps = set(h['app'] for h in recent_history if h['app'] != 'Unknown')
            active_app_count = len(unique_apps)
            
            # Calculate app focus score (inverse of switching)
            # Lower switching = higher focus
            if recent_history:
                total_time = self.window_size
                if len(recent_switches) > 0:
                    avg_time_per_app = total_time / (len(recent_switches) + 1)
                else:
                    avg_time_per_app = total_time
            else:
                avg_time_per_app = 0
            
            # Get most used apps in window
            recent_app_usage = {}
            for app, total_time in self.app_usage.items():
                if any(h['app'] == app for h in recent_history):
                    recent_app_usage[app] = total_time
            
            return {
                'task_switch_frequency': switch_frequency,  # switches per minute
                'active_app_count': active_app_count,  # unique apps
                'total_switches': len(recent_switches),
                'avg_time_per_app': avg_time_per_app,  # seconds
                'current_app': self.current_app,
                'current_window': self.current_window,
                'app_usage': dict(recent_app_usage),
                'timestamp': current_time
            }
    
    def start(self):
        """Start monitoring window events"""
        self.running = True
        self.monitor_thread = Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("Window monitor started")
    
    def stop(self):
        """Stop monitoring window events"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("Window monitor stopped")
    
    def reset(self):
        """Reset all counters"""
        with self.lock:
            self.active_window_history.clear()
            self.window_switches.clear()
            self.app_usage.clear()
            self.current_app = None
            self.current_window = None
            self.last_check_time = None
