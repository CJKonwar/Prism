# Prism - AI Flow State Facilitator

Real-time flow state detection and intelligent focus protection for macOS.

## Features

- ** Real-Time Flow Detection**: Monitors keyboard, mouse, and window activity to detect deep focus
- ** Smart Notification Firewall**: ML-based filtering blocks distracting notifications
- ** Whitelist Mode**: Only allowed apps run, others auto-minimized
- ** App Browser**: Point-and-click selection of installed or running apps
- ** Do Not Disturb**: Automatic DND activation during flow
- ** Live Dashboard**: Real-time metrics and flow visualization

## Quick Start

```bash
cd backend
pip install -r requirements.txt
python3 run_with_gui.py
```

### macOS Permissions Required

Grant permissions in **System Preferences → Security & Privacy → Privacy**:

- ✅ Accessibility
- ✅ Input Monitoring
- ✅ Screen Recording

## Whitelist Mode - Ultimate Focus

1. **Launch GUI**: `python3 run_with_gui.py`
2. **Go to "App Settings" tab**
3. **Add Your Focus Apps**:
   - Click "Add Running Apps" to add what you're currently using
   - Or click "Browse All Apps" to select from all installed apps
   - Or type app names manually
4. **Enable Whitelist Mode**: Check the box
5. **Focus**: Only your selected apps will run, everything else gets minimized


### Flow State Levels

- **🔥 DEEP_FLOW** (Score: 80-100): Optimal flow state - peak performance
- **✨ FLOW** (Score: 65-79): Good flow state - highly focused
- **🎯 FOCUSED** (Score: 45-64): Focused work but not in flow
- **💻 WORKING** (Score: 25-44): Active but distracted
- **😵 DISTRACTED** (Score: 0-24): Not focused

### Metrics Tracked

#### Keyboard Metrics

- `typing_cadence`: Keys per minute
- `avg_inter_key_latency`: Average time between keypresses
- `error_rate`: Ratio of backspace/delete to total keys

#### Mouse Metrics

- `mouse_move_rate`: Mouse movements per minute
- `scroll_velocity`: Scroll speed
- `scroll_bursts`: Rapid scrolling events

#### Window Metrics

- `task_switch_frequency`: Window/app switches per minute
- `active_app_count`: Number of unique apps used
- `avg_time_per_app`: Average time spent per app


## Quick Start

### GUI Mode (Recommended)

```bash
cd backend
python3 run_with_gui.py
```

### Whitelist Mode

```bash
cd backend
python3 run_whitelist_mode.py
```

## Architecture

```
backend/
├── flow_monitor/
│   ├── __init__.py
│   ├── keyboard_monitor.py          # Keyboard tracking
│   ├── mouse_monitor.py             # Mouse tracking
│   ├── window_monitor.py            # Window/app tracking
│   ├── flow_detector.py             # AI flow state detection
│   ├── notification_monitor.py      # System notification capture
│   ├── notification_classifier.py   # ML notification filtering
│   ├── system_control.py            # DND and system control
│   ├── flow_amplifier.py            # Flow protection orchestration
│   ├── whitelist_controller.py      # Strict app enforcement
│   ├── app_scanner.py               # Installed app discovery
│   ├── gui.py                       # Tkinter interface
│   └── main.py                      # System orchestration
├── run_with_gui.py                  # GUI launcher
├── run_whitelist_mode.py            # Whitelist launcher
├── requirements.txt
└── *.md                             # Documentation
```

## How Flow Detection Works

The system uses a weighted scoring algorithm that considers:

1. **Typing Consistency (25%)**: Steady cadence, low variance, few errors
2. **Task Focus (30%)**: Minimal switching, few apps, sustained attention
3. **Mouse Behavior (20%)**: Moderate movement, low scroll bursts
4. **Engagement (25%)**: Active typing and scrolling

Each metric contributes to a flow score (0-100) that determines the current flow state.

## Requirements

- Python 3.7+
- macOS 10.14+
- Accessibility permissions
- Input monitoring permissions
