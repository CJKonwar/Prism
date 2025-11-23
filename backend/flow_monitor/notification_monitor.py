"""
Notification Monitor and Classifier
Monitors system notifications and classifies them using ML
"""

import time
import sqlite3
from datetime import datetime
from threading import Thread, Lock
from collections import deque
import os

# macOS notification monitoring
try:
    from Foundation import NSUserNotificationCenter, NSObject
    from AppKit import NSWorkspace
    import objc
    MACOS_AVAILABLE = True
except ImportError:
    MACOS_AVAILABLE = False
    print("Warning: macOS notification APIs not available")


class NotificationObserver(NSObject):
    """Observer for macOS notifications"""
    
    def init(self):
        self = objc.super(NotificationObserver, self).init()
        if self is None:
            return None
        self.notifications = deque(maxlen=100)
        self.lock = Lock()
        return self
    
    def userNotificationCenter_didDeliverNotification_(self, center, notification):
        """Called when a notification is delivered"""
        with self.lock:
            notif_data = {
                'title': str(notification.title()) if notification.title() else '',
                'subtitle': str(notification.subtitle()) if notification.subtitle() else '',
                'informative_text': str(notification.informativeText()) if notification.informativeText() else '',
                'identifier': str(notification.identifier()) if notification.identifier() else '',
                'timestamp': time.time()
            }
            self.notifications.append(notif_data)
    
    def get_notifications(self):
        """Get all captured notifications"""
        with self.lock:
            return list(self.notifications)


class NotificationMonitor:
    """
    Monitors system notifications and stores them for classification
    """
    
    def __init__(self, db_path='notifications.db'):
        """
        Initialize notification monitor
        
        Args:
            db_path: Path to SQLite database for storing notifications
        """
        self.db_path = db_path
        self.running = False
        self.monitor_thread = None
        self.lock = Lock()
        
        # Notification storage
        self.recent_notifications = deque(maxlen=100)
        self.notification_count = 0
        self.notification_click_rate = 0.0
        
        # macOS observer
        self.observer = None
        if MACOS_AVAILABLE:
            self.observer = NotificationObserver.alloc().init()
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for notifications"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                subtitle TEXT,
                body TEXT,
                app_name TEXT,
                timestamp REAL,
                is_critical INTEGER DEFAULT 0,
                was_shown INTEGER DEFAULT 1,
                was_clicked INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def store_notification(self, title, subtitle, body, app_name, is_critical=False, was_shown=True):
        """Store notification in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO notifications (title, subtitle, body, app_name, timestamp, is_critical, was_shown)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, subtitle, body, app_name, time.time(), int(is_critical), int(was_shown)))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error storing notification: {e}")
    
    def monitor_loop(self):
        """Continuous monitoring loop"""
        if not MACOS_AVAILABLE or not self.observer:
            print("macOS notification monitoring not available")
            return
        
        # Register observer
        center = NSUserNotificationCenter.defaultUserNotificationCenter()
        center.setDelegate_(self.observer)
        
        while self.running:
            try:
                # Get new notifications from observer
                notifications = self.observer.get_notifications()
                
                with self.lock:
                    for notif in notifications:
                        if notif not in self.recent_notifications:
                            self.recent_notifications.append(notif)
                            self.notification_count += 1
                            
                            # Store in database
                            self.store_notification(
                                title=notif['title'],
                                subtitle=notif['subtitle'],
                                body=notif['informative_text'],
                                app_name='System',
                                is_critical=False,
                                was_shown=True
                            )
                
            except Exception as e:
                print(f"Error in notification monitor loop: {e}")
            
            time.sleep(1)
    
    def get_metrics(self, window_seconds=60):
        """
        Get notification metrics for flow state detection
        
        Args:
            window_seconds: Time window for metrics
            
        Returns:
            dict: Notification metrics
        """
        current_time = time.time()
        
        with self.lock:
            # Filter recent notifications
            recent = [n for n in self.recent_notifications 
                     if current_time - n['timestamp'] <= window_seconds]
            
            notification_count = len(recent)
            
            # Calculate notification rate
            if recent:
                time_span = max(current_time - recent[0]['timestamp'], 1)
                notification_rate = (notification_count / time_span) * 60
            else:
                notification_rate = 0
            
            return {
                'notification_count': notification_count,
                'notification_rate': notification_rate,  # per minute
                'notification_click_rate': self.notification_click_rate,
                'timestamp': current_time
            }
    
    def get_recent_notifications(self, limit=10):
        """Get recent notifications"""
        with self.lock:
            return list(self.recent_notifications)[-limit:]
    
    def start(self):
        """Start monitoring notifications"""
        if not MACOS_AVAILABLE:
            print("Notification monitoring not available (macOS only)")
            return
        
        self.running = True
        self.monitor_thread = Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("Notification monitor started")
    
    def stop(self):
        """Stop monitoring notifications"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        print("Notification monitor stopped")
    
    def reset(self):
        """Reset notification counters"""
        with self.lock:
            self.recent_notifications.clear()
            self.notification_count = 0
            self.notification_click_rate = 0.0
