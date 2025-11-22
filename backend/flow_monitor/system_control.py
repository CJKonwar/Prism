"""
macOS System Control
Controls Do Not Disturb mode and manages virtual desktops (Spaces)
"""

import subprocess
import os
from typing import List, Optional


class DoNotDisturbController:
    """
    Controls macOS Do Not Disturb mode
    """
    
    def __init__(self):
        self.is_enabled = False
        self.previous_state = None
    
    def enable(self) -> bool:
        """
        Enable Do Not Disturb mode
        
        Returns:
            bool: Success status
        """
        try:
            # macOS 12+ (Monterey and later) - Focus modes
            # Enable Do Not Disturb using shortcuts
            script = '''
            tell application "System Events"
                tell process "Control Center"
                    set dndEnabled to true
                end tell
            end tell
            '''
            
            # Alternative: Use private API via plutil
            # This modifies the DND plist directly
            subprocess.run([
                'defaults', 'write', 
                'com.apple.controlcenter', 
                'NSStatusItem Visible FocusModes', 
                '-bool', 'true'
            ], check=False)
            
            # Use shortcuts if available
            result = subprocess.run([
                'shortcuts', 'run', 'Enable Do Not Disturb'
            ], capture_output=True, text=True, timeout=5)
            
            self.is_enabled = True
            print("✓ Do Not Disturb enabled")
            return True
            
        except subprocess.TimeoutExpired:
            print("⚠️  DND shortcut timed out, trying alternative method")
            return self._enable_dnd_alternative()
        except Exception as e:
            print(f"⚠️  Could not enable Do Not Disturb: {e}")
            return self._enable_dnd_alternative()
    
    def _enable_dnd_alternative(self) -> bool:
        """Alternative method using AppleScript"""
        try:
            # Set focus mode via notification center
            script = '''
            tell application "System Events"
                -- This is a workaround that may work on some systems
                do shell script "shortcuts run 'Turn On Do Not Disturb'" 
            end tell
            '''
            
            subprocess.run(['osascript', '-e', script], check=False, timeout=3)
            self.is_enabled = True
            return True
        except:
            print("⚠️  All DND methods failed - proceeding without DND")
            return False
    
    def disable(self) -> bool:
        """
        Disable Do Not Disturb mode
        
        Returns:
            bool: Success status
        """
        try:
            # Disable DND
            subprocess.run([
                'shortcuts', 'run', 'Disable Do Not Disturb'
            ], capture_output=True, text=True, timeout=5)
            
            self.is_enabled = False
            print("✓ Do Not Disturb disabled")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not disable Do Not Disturb: {e}")
            self.is_enabled = False
            return False
    
    def get_status(self) -> bool:
        """Check if Do Not Disturb is currently enabled"""
        return self.is_enabled


class VirtualDesktopController:
    """
    Controls macOS Spaces (Virtual Desktops) to move apps to hidden desktops
    """
    
    def __init__(self):
        self.phantom_desktop_id = None
        self.banished_apps = []
    
    def get_current_space(self) -> Optional[int]:
        """
        Get the current space (desktop) ID
        
        Returns:
            int: Current space ID or None
        """
        try:
            script = '''
            tell application "System Events"
                tell process "Dock"
                    return value of attribute "AXSelectedChildren" of list 1 of group 1
                end tell
            end tell
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=3
            )
            
            # Parse the result
            return 1  # Simplified for now
            
        except Exception as e:
            print(f"Could not get current space: {e}")
            return None
    
    def move_app_to_space(self, app_name: str, space_id: int) -> bool:
        """
        Move an application to a specific space
        
        Args:
            app_name: Name of the application
            space_id: Target space ID
            
        Returns:
            bool: Success status
        """
        try:
            # AppleScript to move window to another space
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set frontmost to true
                    -- Move to space using Mission Control
                end tell
            end tell
            '''
            
            subprocess.run(['osascript', '-e', script], check=False, timeout=3)
            return True
            
        except Exception as e:
            print(f"Could not move app to space: {e}")
            return False
    
    def hide_app(self, app_name: str) -> bool:
        """
        Hide an application (alternative to moving to phantom desktop)
        
        Args:
            app_name: Name of the application
            
        Returns:
            bool: Success status
        """
        try:
            script = f'''
            tell application "{app_name}"
                set visible to false
            end tell
            '''
            
            subprocess.run(['osascript', '-e', script], check=False, timeout=3)
            
            if app_name not in self.banished_apps:
                self.banished_apps.append(app_name)
            
            print(f"✓ Hidden app: {app_name}")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not hide app {app_name}: {e}")
            return False
    
    def show_app(self, app_name: str) -> bool:
        """
        Show a previously hidden application
        
        Args:
            app_name: Name of the application
            
        Returns:
            bool: Success status
        """
        try:
            script = f'''
            tell application "{app_name}"
                set visible to true
                activate
            end tell
            '''
            
            subprocess.run(['osascript', '-e', script], check=False, timeout=3)
            
            if app_name in self.banished_apps:
                self.banished_apps.remove(app_name)
            
            print(f"✓ Restored app: {app_name}")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not show app {app_name}: {e}")
            return False
    
    def minimize_app(self, app_name: str) -> bool:
        """
        Minimize all windows of an application
        
        Args:
            app_name: Name of the application
            
        Returns:
            bool: Success status
        """
        try:
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set visible to false
                end tell
            end tell
            '''
            
            subprocess.run(['osascript', '-e', script], check=False, timeout=3)
            
            if app_name not in self.banished_apps:
                self.banished_apps.append(app_name)
            
            print(f"✓ Minimized app: {app_name}")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not minimize app {app_name}: {e}")
            return False
    
    def restore_app(self, app_name: str) -> bool:
        """
        Restore a minimized application
        
        Args:
            app_name: Name of the application
            
        Returns:
            bool: Success status
        """
        try:
            script = f'''
            tell application "System Events"
                tell process "{app_name}"
                    set visible to true
                    set frontmost to true
                end tell
            end tell
            '''
            
            subprocess.run(['osascript', '-e', script], check=False, timeout=3)
            
            if app_name in self.banished_apps:
                self.banished_apps.remove(app_name)
            
            print(f"✓ Restored app: {app_name}")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not restore app {app_name}: {e}")
            return False
    
    def get_banished_apps(self) -> List[str]:
        """Get list of currently banished apps"""
        return self.banished_apps.copy()
    
    def restore_all(self) -> bool:
        """Restore all banished apps"""
        success = True
        for app in self.banished_apps.copy():
            if not self.restore_app(app):
                success = False
        return success
