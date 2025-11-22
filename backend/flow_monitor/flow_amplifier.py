"""
Flow State Amplification System
Dynamically protects and amplifies flow state by controlling the digital environment
"""

import time
from threading import Thread, Lock
from typing import Dict, List, Optional, Callable

from flow_monitor.notification_monitor import NotificationMonitor
from flow_monitor.notification_classifier import NotificationClassifier
from flow_monitor.system_control import DoNotDisturbController, VirtualDesktopController


class FlowAmplifier:
    """
    Amplifies and protects flow state by:
    1. Suppressing non-critical notifications
    2. Activating Do Not Disturb
    3. Banishing distracting apps to phantom desktop
    4. Blocking known distraction patterns
    """
    
    # Known distraction apps/websites
    DISTRACTION_APPS = [
        'Twitter', 'Facebook', 'Instagram', 'TikTok', 'Reddit',
        'YouTube', 'Netflix', 'Discord', 'Telegram', 'WhatsApp',
        'News', 'Safari', 'Chrome', 'Firefox'  # Browsers can be distracting
    ]
    
    # Apps that should never be blocked (critical tools)
    PROTECTED_APPS = [
        'Terminal', 'iTerm', 'Visual Studio Code', 'Xcode',
        'PyCharm', 'IntelliJ IDEA', 'Sublime Text', 'Vim',
        'Calendar', 'Messages', 'FaceTime', 'Zoom', 'Teams'
    ]
    
    def __init__(self, 
                 notification_monitor: NotificationMonitor,
                 flow_state_callback: Optional[Callable] = None):
        """
        Initialize flow amplifier
        
        Args:
            notification_monitor: NotificationMonitor instance
            flow_state_callback: Callback for flow state changes
        """
        self.notification_monitor = notification_monitor
        self.classifier = NotificationClassifier(use_ml=True)
        self.dnd_controller = DoNotDisturbController()
        self.desktop_controller = VirtualDesktopController()
        
        self.lock = Lock()
        self.is_amplifying = False
        self.current_flow_state = 'WORKING'
        self.flow_level = 0
        
        # Tracking
        self.suppressed_notifications = []
        self.banished_apps = []
        self.amplification_start_time = None
        
        # Callbacks
        self.flow_state_callback = flow_state_callback
        self.notification_callbacks = []
        
    def add_notification_callback(self, callback: Callable):
        """Add callback for notification events"""
        self.notification_callbacks.append(callback)
    
    def start_amplification(self, flow_state: str, flow_level: int):
        """
        Start flow state amplification
        
        Args:
            flow_state: Current flow state (e.g., 'FLOW', 'DEEP_FLOW')
            flow_level: Flow level (0-4)
        """
        with self.lock:
            if self.is_amplifying:
                return
            
            self.is_amplifying = True
            self.current_flow_state = flow_state
            self.flow_level = flow_level
            self.amplification_start_time = time.time()
            
            print("\n" + "="*60)
            print("🔥 FLOW STATE AMPLIFICATION ACTIVATED")
            print("="*60)
            
            # 1. Enable Do Not Disturb
            print("\n📵 Activating Do Not Disturb mode...")
            self.dnd_controller.enable()
            
            # 2. Identify and banish distracting apps
            if flow_level >= 3:  # FLOW or DEEP_FLOW
                print("\n👻 Activating Phantom Desktop...")
                self._banish_distracting_apps()
            
            # 3. Start notification filtering
            print("\n🛡️  Smart Notification Firewall active")
            print("    Only critical notifications will be shown")
            
            print("\n✓ Flow amplification system engaged")
            print("="*60 + "\n")
    
    def stop_amplification(self):
        """Stop flow state amplification and restore normal state"""
        with self.lock:
            if not self.is_amplifying:
                return
            
            duration = time.time() - self.amplification_start_time if self.amplification_start_time else 0
            
            print("\n" + "="*60)
            print("🔓 FLOW STATE AMPLIFICATION DEACTIVATED")
            print("="*60)
            print(f"\n⏱️  Flow session duration: {duration/60:.1f} minutes")
            
            # 1. Disable Do Not Disturb
            print("\n📳 Restoring notifications...")
            self.dnd_controller.disable()
            
            # 2. Restore banished apps
            print("\n🔄 Restoring banished apps...")
            self._restore_banished_apps()
            
            # 3. Show summary
            print(f"\n📊 Session Summary:")
            print(f"    Notifications suppressed: {len(self.suppressed_notifications)}")
            print(f"    Apps banished: {len(self.banished_apps)}")
            
            print("\n✓ Normal mode restored")
            print("="*60 + "\n")
            
            self.is_amplifying = False
            self.suppressed_notifications.clear()
    
    def _banish_distracting_apps(self):
        """Move distracting apps to phantom desktop"""
        from AppKit import NSWorkspace
        
        workspace = NSWorkspace.sharedWorkspace()
        running_apps = workspace.runningApplications()
        
        banished_count = 0
        
        for app in running_apps:
            app_name = app.localizedName()
            
            # Skip protected apps
            if app_name in self.PROTECTED_APPS:
                continue
            
            # Check if it's a distraction app
            if app_name in self.DISTRACTION_APPS:
                # Minimize/hide the app
                success = self.desktop_controller.minimize_app(app_name)
                if success:
                    self.banished_apps.append(app_name)
                    banished_count += 1
                    print(f"    👻 Banished: {app_name}")
        
        if banished_count == 0:
            print("    ✓ No distracting apps currently running")
        else:
            print(f"    ✓ Banished {banished_count} distracting app(s)")
    
    def _restore_banished_apps(self):
        """Restore all banished apps"""
        if not self.banished_apps:
            print("    ✓ No apps to restore")
            return
        
        for app_name in self.banished_apps.copy():
            self.desktop_controller.restore_app(app_name)
            print(f"    🔄 Restored: {app_name}")
        
        self.banished_apps.clear()
    
    def process_notification(self, title: str, subtitle: str, body: str, app_name: str) -> bool:
        """
        Process incoming notification through the firewall
        
        Args:
            title: Notification title
            subtitle: Notification subtitle
            body: Notification body
            app_name: Source application
            
        Returns:
            bool: True if notification should be shown, False if suppressed
        """
        # If not amplifying, allow all notifications
        if not self.is_amplifying:
            return True
        
        # Classify notification
        is_critical, confidence, reason = self.classifier.classify(
            title, subtitle, body, app_name
        )
        
        # Log the decision
        notification_data = {
            'title': title,
            'subtitle': subtitle,
            'body': body,
            'app_name': app_name,
            'is_critical': is_critical,
            'confidence': confidence,
            'reason': reason,
            'timestamp': time.time(),
            'was_shown': is_critical
        }
        
        # Notify callbacks
        for callback in self.notification_callbacks:
            try:
                callback(notification_data)
            except Exception as e:
                print(f"Error in notification callback: {e}")
        
        # Suppress non-critical notifications
        if not is_critical:
            self.suppressed_notifications.append(notification_data)
            return False
        
        return True
    
    def get_suppressed_notifications(self) -> List[Dict]:
        """Get list of suppressed notifications"""
        with self.lock:
            return self.suppressed_notifications.copy()
    
    def get_statistics(self) -> Dict:
        """Get amplification statistics"""
        with self.lock:
            if self.amplification_start_time:
                duration = time.time() - self.amplification_start_time
            else:
                duration = 0
            
            return {
                'is_amplifying': self.is_amplifying,
                'flow_state': self.current_flow_state,
                'flow_level': self.flow_level,
                'duration': duration,
                'dnd_enabled': self.dnd_controller.get_status(),
                'suppressed_count': len(self.suppressed_notifications),
                'banished_apps': len(self.banished_apps),
                'banished_app_list': self.banished_apps.copy()
            }
    
    def update_flow_state(self, flow_state: str, flow_level: int):
        """
        Update current flow state and adjust amplification
        
        Args:
            flow_state: New flow state
            flow_level: New flow level
        """
        with self.lock:
            previous_state = self.current_flow_state
            self.current_flow_state = flow_state
            self.flow_level = flow_level
            
            # Start amplification if entering flow
            if flow_level >= 3 and not self.is_amplifying:  # FLOW or DEEP_FLOW
                self.start_amplification(flow_state, flow_level)
            
            # Stop amplification if leaving flow
            elif flow_level < 3 and self.is_amplifying:
                self.stop_amplification()
            
            # Notify callback
            if self.flow_state_callback and previous_state != flow_state:
                try:
                    self.flow_state_callback({
                        'previous_state': previous_state,
                        'current_state': flow_state,
                        'flow_level': flow_level,
                        'is_amplifying': self.is_amplifying
                    })
                except Exception as e:
                    print(f"Error in flow state callback: {e}")
