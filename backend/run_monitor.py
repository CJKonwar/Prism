#!/usr/bin/env python3
"""
Flow State Monitor - Standalone Runner
Run this script to start monitoring your flow state
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flow_monitor.main import main

if __name__ == "__main__":
    main()
