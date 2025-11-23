# Prism - AI Flow State Facilitator

Real-time flow state detection and intelligent focus protection for macOS.

## Features

- **🎯 Real-Time Flow Detection**: Monitors keyboard, mouse, and window activity to detect deep focus states
- **🤖 AI-Powered Productivity Assistant**: Google Gemini analyzes your work patterns and provides personalized interventions
- **🛡️ Smart Notification Firewall**: ML-based filtering blocks distracting notifications during flow
- **🔒 Whitelist Mode**: Only allowed apps run, others auto-minimized for maximum focus
- **📊 Session Analytics**: Comprehensive logging with visual graphs of flow states, mood, and productivity
- **🎵 Wellness Integration**: Emotion detection, calm music therapy, breathing exercises, and eye break reminders
- **💬 Conversation History**: AI remembers past recommendations for context-aware suggestions
- **📱 Live Dashboard**: Real-time metrics with 8 specialized tabs for complete visibility

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

## How It Works

### 1. **Real-Time Monitoring** (Every 5 seconds)
- Captures keyboard typing patterns, mouse movements, and window switches
- Analyzes behavioral metrics to calculate flow score (0-100)
- Classifies current state: DEEP_FLOW → FLOW → FOCUSED → WORKING → DISTRACTED

### 2. **Intelligent Protection**
- Auto-enables Do Not Disturb when entering FLOW/DEEP_FLOW states
- ML classifier filters notifications (blocks distractions, allows urgent ones)
- Whitelist mode minimizes non-approved apps
- Moves distracting apps to hidden virtual desktops

### 3. **AI Assistant** (Every 30 seconds)
- Analyzes session data: flow score, mood, activity, app usage
- Provides context-aware recommendations via Google Gemini
- Suggests: breathing exercises, eye breaks, calm music, DND mode, encouragement
- Tracks conversation history to avoid repetitive suggestions

### 4. **Session Analytics**
- Logs all data as JSON files in `session_logs/` directory
- Generates visual graphs: flow distribution, mood trends, activity metrics, app usage
- Tracks productivity percentage, typing speed, task switching patterns

### 5. **Wellness Features**
- **Mood Monitor**: Webcam emotion detection (anger, stress, frustration alerts)
- **Music Therapy**: Plays calm music from assets folder for stress relief
- **Eye Defender**: 20-20-20 rule reminders with fullscreen overlays
- **Breathing Exercises**: Interactive meditation game for stress reduction

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

## Dashboard Tabs

The GUI provides 6 specialized tabs for complete system control:

1. **Metrics**: Real-time stats - typing speed, mouse activity, DND status, task switches
2. **App Settings**: Whitelist management with "Add Running Apps" quick-add feature
3. **Eye Defender**: Manual 20-20-20 eye break trigger with fullscreen overlay
4. **Mood Monitor**: Current emotion display with start/stop controls
5. **Session Stats**: Visual graphs of flow analysis, mood trends, activity, app usage (with mouse scrolling)
6. **AI Recommendations**: Personalized insights + full conversation history

## Architecture

```
backend/
├── flow_monitor/
│   ├── __init__.py
│   ├── keyboard_monitor.py          # Keyboard tracking & typing patterns
│   ├── mouse_monitor.py             # Mouse movement & scroll analysis
│   ├── window_monitor.py            # Window/app tracking & task switching
│   ├── flow_detector.py             # AI flow state detection algorithm
│   ├── notification_monitor.py      # System notification capture
│   ├── notification_classifier.py   # ML notification filtering
│   ├── system_control.py            # DND and system control APIs
│   ├── flow_amplifier.py            # Flow protection orchestration
│   ├── whitelist_controller.py      # Strict app enforcement
│   ├── mood_monitor.py              # Webcam emotion detection
│   ├── session_logger.py            # JSON session data logging
│   ├── ai_assistant.py              # Google Gemini integration
│   ├── app_scanner.py               # Installed app discovery
│   ├── eye_defender.py              # Eye break screen overlay
│   ├── gui.py                       # Modern Tkinter interface
│   └── main.py                      # System orchestration
├── assets/
│   └── calm_music.mp3               # Calming music for stress relief
├── session_logs/                    # Auto-generated session JSON files
├── run_with_gui.py                  # GUI launcher
├── run_whitelist_mode.py            # Whitelist-only mode launcher
├── run_monitor.py                   # CLI monitoring mode
├── requirements.txt
└── app_config.json                  # User configuration storage
```

## Flow Detection Algorithm

The system uses a weighted scoring algorithm that considers:

1. **Typing Consistency (25%)**: Steady cadence, low inter-key latency variance, few backspace errors
2. **Task Focus (30%)**: Minimal app switching, few active apps, sustained attention per app
3. **Mouse Behavior (20%)**: Moderate movement, consistent scroll velocity, low scroll bursts
4. **Engagement (25%)**: Active typing and scrolling patterns indicating deep work

Each metric contributes to a flow score (0-100) that determines the current flow state.

## AI Assistant Capabilities

Powered by **Google Gemini 2.5 Flash**, the AI assistant:

- Analyzes session data every 30 seconds
- Detects stress, frustration, low productivity, and fatigue patterns
- Provides personalized interventions:
  - **Breathing exercises** for stress/anger
  - **Calm music** (5-30 min) for frustration
  - **Eye breaks** for extended screen time (>60 min)
  - **DND mode** suggestions for low flow scores
  - **Encouragement** for high productivity
- Tracks conversation history to provide context-aware recommendations
- Saves all recommendations to analysis logs

## Environment Setup

### Required Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
GENAI_API_KEY=your_google_gemini_api_key_here
```

Get your API key from: https://ai.google.dev/

### Installation

```bash
cd backend
pip install -r requirements.txt
```

**Required packages**: `pynput`, `psutil`, `pillow`, `google-genai`, `python-dotenv`, `opencv-python`, `deepface`, `matplotlib`

## Requirements

- **Python 3.8+**
- **macOS 10.14+**
- **Google Gemini API Key** (for AI assistant)
- **Webcam** (optional, for mood monitoring)
- **macOS Permissions** (grant in System Preferences → Security & Privacy → Privacy):
  - ✅ Accessibility
  - ✅ Input Monitoring
  - ✅ Screen Recording (for window tracking)
  - ✅ Camera (optional, for mood monitoring)

## Session Data

All session data is automatically saved as JSON files in `session_logs/` directory:

- **Filename format**: `session_YYYYMMDD_HHMMSS.json`
- **Contains**:
  - Session info (duration, total updates)
  - Flow state analysis (scores, percentages, productivity)
  - Activity metrics (typing speed, mouse movement, task switches)
  - App usage (top 5 apps with usage percentages)
  - Mood analysis (emotion distribution, stress alerts)
  - AI recommendations log

## Contributing

Contributions welcome! Areas for enhancement:

- Cross-platform support (Windows, Linux)
- Additional AI models integration
- Custom flow detection thresholds
- More wellness interventions
- Mobile companion app

## License

MIT License - See LICENSE file for details
