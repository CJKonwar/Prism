"""
Whitelist Mode Controller
Strictly enforces only allowed apps and minimizes all others
"""

import time
from threading import Thread, Lock
from typing import List, Set
from AppKit import NSWorkspace
import subprocess


class WhitelistController:
    """
    Controls app access in whitelist mode
    Only allows user-specified apps, minimizes everything else
    """
    
    def __init__(self, allowed_apps: List[str] = None):
        """
        Initialize whitelist controller
        
        Args:
            allowed_apps: List of app names that are allowed to run
        """
        self.allowed_apps = set(allowed_apps) if allowed_apps else set()
        self.system_apps = {
            'Finder', 'Dock', 'SystemUIServer', 'ControlCenter',
            'WindowServer', 'loginwindow', 'UserEventAgent'
        }
        
        self.lock = Lock()
        self.running = False
        self.monitor_thread = None
        self.check_interval = 2.0  # Check every 2 seconds
        
        self.minimized_apps = []
        self.violation_count = 0
        
    def add_allowed_app(self, app_name: str):
        """Add an app to the whitelist"""
        with self.lock:
            self.allowed_apps.add(app_name)
    
    def remove_allowed_app(self, app_name: str):
        """Remove an app from the whitelist"""
        with self.lock:
            if app_name in self.allowed_apps:
                self.allowed_apps.remove(app_name)
    
    def get_allowed_apps(self) -> List[str]:
        """Get list of allowed apps"""
        with self.lock:
            return sorted(list(self.allowed_apps))
    
    def set_allowed_apps(self, apps: List[str]):
        """Set the entire whitelist"""
        with self.lock:
            self.allowed_apps = set(apps)
    
    def is_app_allowed(self, app_name: str) -> bool:
        """Check if an app is allowed"""
        with self.lock:
            return (app_name in self.allowed_apps or 
                   app_name in self.system_apps or
                   app_name.startswith('com.apple.'))
    
    def minimize_app(self, app_name: str) -> bool:
        """Minimize an unauthorized app"""
        try:
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set visible to false
                end tell
            end tell
            '''
            
            subprocess.run(['osascript', '-e', script], 
                         check=False, timeout=2, 
                         capture_output=True)
            
            with self.lock:
                if app_name not in self.minimized_apps:
                    self.minimized_apps.append(app_name)
                    self.violation_count += 1
            
            print(f"Minimized unauthorized app: {app_name}")
            return True
            
        except Exception as e:
            print(f"Could not minimize {app_name}: {e}")
            return False
    
    def enforce_whitelist(self):
        """Check all running apps and minimize unauthorized ones"""
        try:
            workspace = NSWorkspace.sharedWorkspace()
            running_apps = workspace.runningApplications()
            
            for app in running_apps:
                app_name = app.localizedName()
                
                # Skip if allowed
                if self.is_app_allowed(app_name):
                    continue
                
                # Skip hidden apps
                if app.isHidden():
                    continue
                
                # Minimize unauthorized app
                self.minimize_app(app_name)
                
        except Exception as e:
            print(f"Error enforcing whitelist: {e}")
    
    def monitor_loop(self):
        """Continuous monitoring and enforcement"""
        while self.running:
            try:
                self.enforce_whitelist()
            except Exception as e:
                print(f"Error in whitelist monitor loop: {e}")
            
            time.sleep(self.check_interval)
    
    def start(self):
        """Start whitelist enforcement"""
        if self.running:
            return
        
        print("\n" + "="*60)
        print("WHITELIST MODE ACTIVATED")
        print("="*60)
        print("\nAllowed Apps:")
        for app in sorted(self.allowed_apps):
            print(f"  [*] {app}")
        print("\nAll other apps will be automatically minimized")
        print("="*60 + "\n")
        
        self.running = True
        self.monitor_thread = Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop(self):
        """Stop whitelist enforcement"""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=3)
        
        print("\n" + "="*60)
        print("WHITELIST MODE DEACTIVATED")
        print("="*60)
        print(f"\nSession Statistics:")
        print(f"   Violations blocked: {self.violation_count}")
        print(f"   Apps minimized: {len(set(self.minimized_apps))}")
        print("="*60 + "\n")
    
    def get_statistics(self) -> dict:
        """Get whitelist enforcement statistics"""
        with self.lock:
            return {
                'active': self.running,
                'allowed_apps': len(self.allowed_apps),
                'violation_count': self.violation_count,
                'minimized_apps': len(set(self.minimized_apps)),
                'minimized_app_list': list(set(self.minimized_apps))
            }
    
    def reset_statistics(self):
        """Reset violation counters"""
        with self.lock:
            self.minimized_apps.clear()
            self.violation_count = 0
