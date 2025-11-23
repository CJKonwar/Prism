"""
Flow Monitor - Main Orchestration
Coordinates all monitoring modules and provides unified interface
"""

import time
import json
from threading import Thread, Event
from flow_monitor.keyboard_monitor import KeyboardMonitor
from flow_monitor.mouse_monitor import MouseMonitor
from flow_monitor.window_monitor import WindowMonitor
from flow_monitor.flow_detector import FlowStateDetector
from flow_monitor.notification_monitor import NotificationMonitor
from flow_monitor.flow_amplifier import FlowAmplifier
from flow_monitor.whitelist_controller import WhitelistController
from flow_monitor.mood_monitor import MoodMonitor


class FlowMonitorSystem:
    """
    Main system that coordinates all monitoring and analysis
    """
    
    def __init__(self, analysis_interval=5.0, window_size=60, enable_amplification=True, whitelist_mode=False, allowed_apps=None, enable_mood_monitor=False):
        """
        Initialize the flow monitoring system
        
        Args:
            analysis_interval: Seconds between flow state analyses
            window_size: Time window for metric calculation (seconds)
            enable_amplification: Enable flow state amplification features
            whitelist_mode: Enable strict whitelist mode (only allow specified apps)
            allowed_apps: List of apps to allow in whitelist mode
            enable_mood_monitor: Enable webcam-based mood monitoring
        """
        self.analysis_interval = analysis_interval
        self.window_size = window_size
        self.enable_amplification = enable_amplification
        self.whitelist_mode = whitelist_mode
        self.enable_mood_monitor = enable_mood_monitor
        
        # Initialize monitors
        self.keyboard_monitor = KeyboardMonitor(window_size=window_size)
        self.mouse_monitor = MouseMonitor(window_size=window_size)
        self.window_monitor = WindowMonitor(window_size=window_size, allowed_apps=allowed_apps)
        self.notification_monitor = NotificationMonitor()
        self.flow_detector = FlowStateDetector(history_size=20)
        
        # Initialize mood monitor if enabled
        self.mood_monitor = None
        if enable_mood_monitor:
            self.mood_monitor = MoodMonitor(check_interval=5)
        
        # Initialize whitelist controller
        self.whitelist_controller = None
        if whitelist_mode:
            self.whitelist_controller = WhitelistController(allowed_apps=allowed_apps)
        
        # Initialize flow amplifier if enabled
        self.flow_amplifier = None
        if enable_amplification:
            self.flow_amplifier = FlowAmplifier(
                notification_monitor=self.notification_monitor,
                flow_state_callback=self._on_flow_state_change
            )
        
        # Control
        self.running = False
        self.analysis_thread = None
        self.stop_event = Event()
        
        # Callbacks
        self.flow_state_callbacks = []
        
    def add_flow_state_callback(self, callback):
        """
        Add a callback function to be called when flow state changes
        
        Args:
            callback: Function that takes flow_analysis dict as parameter
        """
        self.flow_state_callbacks.append(callback)
    
    def analysis_loop(self):
        """Continuous analysis loop"""
        last_flow_state = None
        
        while self.running and not self.stop_event.is_set():
            try:
                # Collect metrics from all monitors
                keyboard_metrics = self.keyboard_monitor.get_metrics()
                mouse_metrics = self.mouse_monitor.get_metrics()
                window_metrics = self.window_monitor.get_metrics()
                notification_metrics = self.notification_monitor.get_metrics()
                
                # Merge notification metrics into window metrics
                window_metrics.update(notification_metrics)
                
                # Analyze flow state
                flow_analysis = self.flow_detector.analyze(
                    keyboard_metrics,
                    mouse_metrics,
                    window_metrics
                )
                
                # Update flow amplifier if enabled
                if self.flow_amplifier:
                    self.flow_amplifier.update_flow_state(
                        flow_analysis['flow_state'],
                        flow_analysis['flow_level']
                    )
                
                # Log flow state
                self._log_flow_state(flow_analysis)
                
                # Trigger callbacks on state change
                current_state = flow_analysis['flow_state']
                if current_state != last_flow_state:
                    self._trigger_callbacks(flow_analysis)
                    last_flow_state = current_state
                
            except Exception as e:
                print(f"Error in analysis loop: {e}")
            
            # Wait for next analysis
            self.stop_event.wait(self.analysis_interval)
    
    def _log_flow_state(self, flow_analysis):
        """Log the current flow state"""
        state = flow_analysis['flow_state']
        score = flow_analysis['flow_score']
        duration = flow_analysis['flow_duration']
        
        # Create status bar
        bar_length = 20
        filled = int((score / 100) * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        # Status emoji
        emoji_map = {
            'DEEP_FLOW': '🔥',
            'FLOW': '✨',
            'FOCUSED': '🎯',
            'WORKING': '💻',
            'DISTRACTED': '😵'
        }
        
        emoji = emoji_map.get(state, '❓')
        
        print(f"\r{emoji} {state:12} | {bar} {score:5.1f}% | Duration: {duration:6.1f}s", end='', flush=True)
    
    def _trigger_callbacks(self, flow_analysis):
        """Trigger registered callbacks"""
        for callback in self.flow_state_callbacks:
            try:
                callback(flow_analysis)
            except Exception as e:
                print(f"Error in callback: {e}")
    
    def _on_flow_state_change(self, state_info):
        """Internal callback for flow state changes"""
        pass  # Handled by flow_amplifier
    
    def start(self):
        """Start the flow monitoring system"""
        if self.running:
            print("Flow monitor is already running")
            return
        
        print("\n" + "="*60)
        print("🚀 Starting Flow State Detection System")
        print("="*60)
        
        # Start whitelist controller if enabled
        if self.whitelist_controller:
            self.whitelist_controller.start()
        
        # Start mood monitor if enabled
        if self.mood_monitor:
            self.mood_monitor.start()
        
        # Start all monitors
        self.keyboard_monitor.start()
        self.mouse_monitor.start()
        self.window_monitor.start()
        self.notification_monitor.start()
        
        # Start analysis loop
        self.running = True
        self.stop_event.clear()
        self.analysis_thread = Thread(target=self.analysis_loop, daemon=True)
        self.analysis_thread.start()
        
        print("✓ All systems operational")
        if self.flow_amplifier:
            print("✓ Flow amplification ready")
        if self.whitelist_controller:
            print("✓ Whitelist mode active")
        if self.mood_monitor:
            print("✓ Mood monitoring active")
        print("="*60)
        print("\nMonitoring your flow state... (Press Ctrl+C to stop)\n")
    
    def stop(self):
        """Stop the flow monitoring system"""
        if not self.running:
            return
        
        print("\n\n" + "="*60)
        print("🛑 Stopping Flow State Detection System")
        print("="*60)
        
        self.running = False
        self.stop_event.set()
        
        # Stop whitelist controller if active
        if self.whitelist_controller:
            self.whitelist_controller.stop()
        
        # Stop mood monitor if active
        if self.mood_monitor:
            self.mood_monitor.stop()
        
        # Stop flow amplification if active
        if self.flow_amplifier and self.flow_amplifier.is_amplifying:
            self.flow_amplifier.stop_amplification()
        
        # Stop all monitors
        self.keyboard_monitor.stop()
        self.mouse_monitor.stop()
        self.window_monitor.stop()
        self.notification_monitor.stop()
        
        # Wait for analysis thread
        if self.analysis_thread:
            self.analysis_thread.join(timeout=2)
        
        print("✓ All systems stopped")
        print("="*60 + "\n")
    
    def get_current_state(self):
        """
        Get the current flow state
        
        Returns:
            dict: Current flow analysis
        """
        keyboard_metrics = self.keyboard_monitor.get_metrics()
        mouse_metrics = self.mouse_monitor.get_metrics()
        window_metrics = self.window_monitor.get_metrics()
        
        return self.flow_detector.analyze(
            keyboard_metrics,
            mouse_metrics,
            window_metrics
        )
    
    def get_trends(self, window_minutes=10):
        """
        Get flow state trends
        
        Args:
            window_minutes: Time window for trend analysis
            
        Returns:
            dict: Trend analysis
        """
        return self.flow_detector.get_flow_trends(window_minutes)
    
    def get_detailed_metrics(self):
        """
        Get detailed metrics from all monitors
        
        Returns:
            dict: All metrics
        """
        metrics = {
            'keyboard': self.keyboard_monitor.get_metrics(),
            'mouse': self.mouse_monitor.get_metrics(),
            'window': self.window_monitor.get_metrics(),
            'notifications': self.notification_monitor.get_metrics(),
            'flow': self.get_current_state(),
            'trends': self.get_trends()
        }
        
        if self.flow_amplifier:
            metrics['amplification'] = self.flow_amplifier.get_statistics()
        
        if self.whitelist_controller:
            metrics['whitelist'] = self.whitelist_controller.get_statistics()
        
        if self.mood_monitor:
            metrics['mood'] = self.mood_monitor.get_statistics()
            metrics['mood_current'] = self.mood_monitor.get_current_mood()
            metrics['mood_trend'] = self.mood_monitor.get_mood_trend(window_minutes=10)
        
        return metrics
    
    def reset(self):
        """Reset all monitors and history"""
        self.keyboard_monitor.reset()
        self.mouse_monitor.reset()
        self.window_monitor.reset()
        self.notification_monitor.reset()
        print("✓ All metrics reset")
    
    def get_flow_amplifier(self):
        """Get the flow amplifier instance"""
        return self.flow_amplifier
    
    def get_whitelist_controller(self):
        """Get the whitelist controller instance"""
        return self.whitelist_controller
    
    def get_mood_monitor(self):
        """Get the mood monitor instance"""
        return self.mood_monitor
    
    def set_allowed_apps(self, apps):
        """Update the list of allowed apps"""
        if self.whitelist_controller:
            self.whitelist_controller.set_allowed_apps(apps)
        if self.window_monitor:
            self.window_monitor.set_allowed_apps(apps)


def main():
    """Main entry point for testing"""
    monitor = FlowMonitorSystem(analysis_interval=3.0)
    
    # Example callback
    def on_flow_state_change(analysis):
        if analysis['in_flow']:
            print(f"\n🎉 Entered flow state: {analysis['flow_state']}")
        else:
            print(f"\n⚠️  Left flow state: {analysis['flow_state']}")
    
    monitor.add_flow_state_callback(on_flow_state_change)
    
    try:
        monitor.start()
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        monitor.stop()
        
        # Print final statistics
        print("\n📊 Session Summary:")
        trends = monitor.get_trends(window_minutes=60)
        print(f"   Average Flow Score: {trends['avg_flow_score']}")
        print(f"   Time in Flow: {trends['flow_percentage']:.1f}%")
        print(f"   Time in Deep Flow: {trends['deep_flow_percentage']:.1f}%")
        print(f"   Overall Trend: {trends['trend']}")


if __name__ == "__main__":
    main()
