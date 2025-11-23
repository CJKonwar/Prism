#!/usr/bin/env python3
"""
Flow State Monitor with WHITELIST MODE
Only allows specified apps, automatically minimizes all others
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flow_monitor.main import FlowMonitorSystem
from flow_monitor.gui import NotificationGUI


def main():
    """Main entry point with whitelist mode"""
    print("\n" + "="*60)
    print("PRISM - Whitelist Mode")
    print("="*60)
    print("\nWhitelist mode strictly enforces allowed apps only.")
    print("All other apps will be automatically minimized.\n")
    
    # Get allowed apps from user
    print("Enter the names of apps you want to allow (one per line).")
    print("Examples: Visual Studio Code, Terminal, Safari")
    print("Press Enter twice when done:\n")
    
    allowed_apps = ["Code", "Terminal", "Safari", "Python"]
    while True:
        app = input("App name (or press Enter to finish): ").strip()
        if not app:
            if allowed_apps:
                break
            else:
                print(" Please add at least one app!")
                continue
        allowed_apps.append(app)
        print(f"  Added: {app}")
    
    print(f"\n{len(allowed_apps)} apps allowed")
    print("\nInitializing system...\n")
    
    # Initialize the monitoring system with whitelist mode
    monitor = FlowMonitorSystem(
        analysis_interval=3.0,
        window_size=60,
        enable_amplification=True,
        whitelist_mode=True,
        allowed_apps=allowed_apps
    )
    
    # Start monitoring
    monitor.start()
    
    # Get flow amplifier
    flow_amplifier = monitor.get_flow_amplifier()
    
    if flow_amplifier:
        print("\nLaunching GUI...")
        
        # Create and run GUI
        gui = NotificationGUI(flow_amplifier, monitor)
        
        try:
            gui.run()
        except KeyboardInterrupt:
            pass
        finally:
            monitor.stop()
            
            # Print final statistics
            print("\nSession Summary:")
            trends = monitor.get_trends(window_minutes=60)
            print(f"   Average Flow Score: {trends['avg_flow_score']}")
            print(f"   Time in Flow: {trends['flow_percentage']:.1f}%")
            print(f"   Time in Deep Flow: {trends['deep_flow_percentage']:.1f}%")
            
            whitelist_controller = monitor.get_whitelist_controller()
            if whitelist_controller:
                stats = whitelist_controller.get_statistics()
                print(f"\nWhitelist Summary:")
                print(f"   Violations Blocked: {stats['violation_count']}")
                print(f"   Unauthorized Apps Minimized: {stats['minimized_apps']}")


if __name__ == "__main__":
    main()
