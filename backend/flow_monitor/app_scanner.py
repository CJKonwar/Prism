"""
Application Scanner
Scans macOS Applications folder and returns list of installed apps
Also provides functionality to get currently running apps
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Set


class ApplicationScanner:
    """
    Scans for installed applications on macOS
    """
    
    def __init__(self):
        self.app_locations = [
            '/Applications',
            '/System/Applications',
            os.path.expanduser('~/Applications')
        ]
    
    def get_installed_apps(self) -> List[Dict[str, str]]:
        """
        Get list of all installed applications
        
        Returns:
            List of dicts with 'name' and 'path' keys
        """
        apps = []
        seen_names = set()
        
        for location in self.app_locations:
            if not os.path.exists(location):
                continue
            
            try:
                for item in os.listdir(location):
                    if item.endswith('.app'):
                        # Get app name without .app extension
                        app_name = item[:-4]
                        
                        # Skip duplicates
                        if app_name in seen_names:
                            continue
                        
                        # Skip system utilities we don't want to block
                        if self._is_system_app(app_name):
                            continue
                        
                        full_path = os.path.join(location, item)
                        apps.append({
                            'name': app_name,
                            'path': full_path
                        })
                        seen_names.add(app_name)
                        
            except PermissionError:
                # Skip directories we can't access
                continue
        
        # Sort by name
        apps.sort(key=lambda x: x['name'].lower())
        return apps
    
    def _is_system_app(self, app_name: str) -> bool:
        """Check if app is a critical system app that shouldn't be managed"""
        system_apps = {
            'Finder', 'Dock', 'Launchpad', 'Mission Control',
            'System Preferences', 'System Settings', 'Activity Monitor',
            'Console', 'Terminal', 'Automator', 'Script Editor'
        }
        return app_name in system_apps
    
    def get_app_categories(self) -> Dict[str, List[str]]:
        """
        Categorize apps by type (best effort)
        
        Returns:
            Dict with category names as keys and app name lists as values
        """
        apps = self.get_installed_apps()
        categories = {
            'Development': [],
            'Browsers': [],
            'Communication': [],
            'Productivity': [],
            'Media': [],
            'Utilities': [],
            'Other': []
        }
        
        for app in apps:
            name = app['name'].lower()
            app_name = app['name']
            
            # Development
            if any(keyword in name for keyword in ['code', 'xcode', 'pycharm', 'intellij', 
                                                     'visual studio', 'sublime', 'atom', 
                                                     'eclipse', 'android studio', 'iterm']):
                categories['Development'].append(app_name)
            
            # Browsers
            elif any(keyword in name for keyword in ['safari', 'chrome', 'firefox', 'edge', 
                                                       'brave', 'opera', 'arc']):
                categories['Browsers'].append(app_name)
            
            # Communication
            elif any(keyword in name for keyword in ['slack', 'teams', 'zoom', 'discord', 
                                                       'telegram', 'whatsapp', 'messages', 
                                                       'mail', 'outlook', 'skype']):
                categories['Communication'].append(app_name)
            
            # Productivity
            elif any(keyword in name for keyword in ['notion', 'evernote', 'notes', 'pages', 
                                                       'word', 'excel', 'powerpoint', 'keynote',
                                                       'numbers', 'obsidian', 'bear']):
                categories['Productivity'].append(app_name)
            
            # Media
            elif any(keyword in name for keyword in ['spotify', 'music', 'itunes', 'vlc', 
                                                       'quicktime', 'final cut', 'imovie',
                                                       'photoshop', 'illustrator', 'preview']):
                categories['Media'].append(app_name)
            
            # Utilities
            elif any(keyword in name for keyword in ['calculator', 'calendar', 'clock', 
                                                       'reminders', 'contacts', 'maps']):
                categories['Utilities'].append(app_name)
            
            # Other
            else:
                categories['Other'].append(app_name)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def search_apps(self, query: str) -> List[Dict[str, str]]:
        """
        Search for apps by name
        
        Args:
            query: Search query string
            
        Returns:
            List of matching apps
        """
        apps = self.get_installed_apps()
        query_lower = query.lower()
        
        return [app for app in apps if query_lower in app['name'].lower()]
    
    def get_running_apps(self) -> List[str]:
        """
        Get list of currently running applications (excluding system apps)
        
        Returns:
            List of running app names
        """
        try:
            # Use osascript to get running apps from System Events
            script = '''
            tell application "System Events"
                set appList to name of every application process whose background only is false
            end tell
            return appList
            '''
            
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse the comma-separated list
                apps_str = result.stdout.strip()
                if apps_str:
                    apps = [app.strip() for app in apps_str.split(',')]
                    # Filter out system apps
                    return [app for app in apps if not self._is_system_app(app)]
            
            return []
            
        except Exception as e:
            print(f"Error getting running apps: {e}")
            return []
    
    def get_running_apps_detailed(self) -> List[Dict[str, str]]:
        """
        Get detailed info about currently running applications
        
        Returns:
            List of dicts with 'name' and 'status' keys
        """
        running = self.get_running_apps()
        return [{'name': app, 'status': 'running'} for app in running]
