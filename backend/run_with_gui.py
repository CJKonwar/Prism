#!/usr/bin/env python3
"""
Flow State Monitor with GUI
Run this script to start monitoring with the graphical interface
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flow_monitor.main import FlowMonitorSystem
from flow_monitor.gui import NotificationGUI


def main(eye_defender_enabled=True):
    """
    Main entry point with GUI
    
    Args:
        eye_defender_enabled: Whether to automatically start Eye Defender (default: True)
    """
    print("\n" + "="*60)
    print("🎯 PRISM - AI Flow State Facilitator")
    print("="*60)
    print("\nInitializing system...\n")
    
    # Initialize the monitoring system with amplification and whitelist support
    monitor = FlowMonitorSystem(
        analysis_interval=3.0,
        window_size=60,
        enable_amplification=True,
        whitelist_mode=True,  # Can be enabled from GUI
        allowed_apps=["Code", "Terminal", "Safari", "Python"],  # Will be set from GUI
        enable_mood_monitor=True  # Enable webcam-based mood monitoring
    )
    
    # Start monitoring
    monitor.start()
    
    # Get flow amplifier
    flow_amplifier = monitor.get_flow_amplifier()
    
    if flow_amplifier:
        print("\n🎨 Launching GUI...")
        if eye_defender_enabled:
            print("👁️  Eye Defender will auto-start...")
        
        # Create and run GUI
        gui = NotificationGUI(flow_amplifier, monitor, auto_start_eye_defender=eye_defender_enabled)
        
        try:
            gui.run()
        except KeyboardInterrupt:
            pass
        finally:
            monitor.stop()
            
            # Print final statistics
            print("\n📊 Session Summary:")
            trends = monitor.get_trends(window_minutes=60)
            print(f"   Average Flow Score: {trends['avg_flow_score']}")
            print(f"   Time in Flow: {trends['flow_percentage']:.1f}%")
            print(f"   Time in Deep Flow: {trends['deep_flow_percentage']:.1f}%")
            print(f"   Overall Trend: {trends['trend']}")
            
            if flow_amplifier:
                amp_stats = flow_amplifier.get_statistics()
                print(f"\n🛡️  Amplification Summary:")
                print(f"   Notifications Suppressed: {amp_stats['suppressed_count']}")
                print(f"   Apps Banished: {amp_stats['banished_apps']}")
    else:
        print("⚠️  Flow amplification not available")
        print("Running in monitoring-only mode")
        
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            monitor.stop()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Prism - AI Flow State Facilitator')
    parser.add_argument('--no-eye-defender', action='store_true',
                      help='Disable Eye Defender auto-start (default: enabled)')
    
    args = parser.parse_args()
    
    # Eye Defender is enabled by default, disabled only with --no-eye-defender flag
    main(eye_defender_enabled=not args.no_eye_defender)
