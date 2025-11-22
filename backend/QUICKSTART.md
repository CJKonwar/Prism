# Prism - Quick Start

## 1. Install & Setup

```bash
cd backend
pip3 install -r requirements.txt
python3 run_with_gui.py
```

**Grant Permissions**: System Preferences → Security & Privacy → Privacy

- ✅ Accessibility
- ✅ Input Monitoring
- ✅ Screen Recording

## 2. Set Up Whitelist Mode (Recommended)

**In the GUI:**

1. Go to **"App Settings"** tab
2. Click **"Add Running Apps"** - instantly add what you're using now
3. Or click **"Browse All Apps"** - select from all installed apps
4. Enable **"Whitelist Mode"** checkbox
5. Done! Only your apps allowed, rest minimized

**Example Workflow:**

```
Working on coding project?
→ Click "Add Running Apps"
→ See: VS Code, Terminal, Safari, Spotify
→ Select all → Add
→ Enable Whitelist
→ Focus!
```

## 3. How It Works

### Without Whitelist (Flow Amplification Only)

- System monitors your behavior
- When flow detected → Activates DND
- Blocks distracting notifications
- Hides distraction apps temporarily

### With Whitelist (Maximum Focus)

- Only allowed apps can run
- Any other app → Instantly minimized
- No distractions possible
- Perfect for deep work sessions
- Flow state display
- Automatic amplification

## What Happens When You Run It

### Phase 1: Initialization (5 seconds)

```
🚀 Starting Flow State Detection System
✓ Keyboard monitor started
✓ Mouse monitor started
✓ Window monitor started
✓ Notification monitor started
✓ All systems operational
```

### Phase 2: Monitoring (Continuous)

```
💻 WORKING      | ████████░░░░░░░░░░░░   40.0% | Duration:    0.0s
```

The system tracks:

- Typing patterns (cadence, rhythm, errors)
- Mouse behavior (movement, scrolling)
- Task switching (window changes)
- App usage patterns

### Phase 3: Flow Detection

When you enter a flow state (65+ score):

```
✨ FLOW         | ████████████████░░░░   75.0% | Duration:   45.2s
```

### Phase 4: Amplification (Automatic)

At flow level ≥3 (FLOW or DEEP_FLOW):

```
============================================================
🔥 FLOW STATE AMPLIFICATION ACTIVATED
============================================================

📵 Activating Do Not Disturb mode...
✓ Do Not Disturb enabled

👻 Activating Phantom Desktop...
    👻 Banished: Twitter
    👻 Banished: Discord
    ✓ Banished 2 distracting app(s)

🛡️  Smart Notification Firewall active
    Only critical notifications will be shown

✓ Flow amplification system engaged
============================================================
```

### Phase 5: Flow End (Automatic Restoration)

When flow score drops below 45:

```
============================================================
🔓 FLOW STATE AMPLIFICATION DEACTIVATED
============================================================

⏱️  Flow session duration: 15.3 minutes

📳 Restoring notifications...
✓ Do Not Disturb disabled

🔄 Restoring banished apps...
    🔄 Restored: Twitter
    🔄 Restored: Discord

📊 Session Summary:
    Notifications suppressed: 23
    Apps banished: 2

✓ Normal mode restored
============================================================
```

## Understanding Flow States

### 🔥 DEEP_FLOW (80-100)

**Indicators:**

- Consistent, rapid typing
- Minimal errors
- Zero task switching
- Single app focus
- No distractions

**Amplification:**

- Full DND mode
- All non-critical notifications blocked
- Distraction apps banished

### ✨ FLOW (65-79)

**Indicators:**

- Steady typing rhythm
- Low error rate
- Minimal task switching
- 1-2 apps active

**Amplification:**

- DND enabled
- Most notifications blocked
- Key distraction apps hidden

### 🎯 FOCUSED (45-64)

**Indicators:**

- Active typing
- Moderate task switching
- 2-3 apps in use

**Amplification:**

- None (monitoring only)

### 💻 WORKING (25-44)

**Indicators:**

- Intermittent activity
- Frequent switching
- Multiple apps

**Amplification:**

- None

### 😵 DISTRACTED (0-24)

**Indicators:**

- Minimal typing
- Constant switching
- Many apps active
- High scroll bursts

**Amplification:**

- None

## Using the GUI

### Main Window Sections

1. **Flow State Status**

   - Current state and emoji
   - Flow score (0-100%)
   - Progress bar
   - Flow duration timer

2. **Amplification Status**

   - Do Not Disturb: 🔕 ON / 🔔 OFF
   - Suppressed notification count
   - Banished apps count

3. **Notification Feed** (Tabs)

   - **All Notifications**: Complete log with classification
   - **Suppressed**: Only blocked notifications
   - **Metrics**: Real-time system metrics

4. **Controls**
   - Reset Metrics: Clear all history
   - View Trends: 30-minute analytics
   - Exit: Graceful shutdown

### Reading Notification Classifications

```
[14:32:15] ✅ ALLOWED - Calendar: Meeting in 5 minutes
   Reason: keyword: meeting, time-sensitive (Confidence: 0.85)

[14:32:20] 🚫 BLOCKED - Twitter: New mentions
   Reason: distraction app: twitter (Confidence: 0.92)
```

## Keyboard Shortcuts

- `Ctrl+C`: Graceful shutdown
- GUI window close: Automatic cleanup

## Tips for Optimal Flow Detection

### Do:

✓ Work on a single task
✓ Keep typing rhythm consistent
✓ Stay in one or two apps
✓ Minimize task switching
✓ Let the system learn your patterns

### Don't:

✗ Rapidly switch between apps
✗ Take long pauses (breaks are fine)
✗ Keep many apps open
✗ Frantically scroll

## Customization

### Manage Apps via GUI (Recommended)

**In the GUI, go to "App Settings" tab:**

1. **Browse Installed Apps** (Easy Way):

   - Click "Browse Apps" button
   - See all installed applications organized by category
   - Search for specific apps
   - Select multiple apps at once
   - Click "Add Selected" to add them to your allowed list

2. **Manual Entry** (Alternative):

   - Type app name in the text field
   - Click "Add" button
   - Remove by selecting and clicking "Remove Selected"

3. **App Lists**:
   - **Allowed Apps**: Only these apps permitted in whitelist mode
   - **Protected Apps**: Never banished during flow amplification
   - **Distraction Apps**: Auto-hidden when in deep flow

**See APP_BROWSER.md for detailed guide on app selection.**

### Adjust Flow Thresholds

Edit `backend/flow_monitor/flow_detector.py`:

```python
THRESHOLDS = {
    'typing_cadence_min': 30,      # Lower = less typing needed
    'error_rate_max': 0.15,        # Higher = more forgiving
    'task_switch_max': 5,          # Higher = more switching allowed
}
```

### Customize Distraction Apps (Code Method)

Edit `backend/flow_monitor/flow_amplifier.py`:

```python
DISTRACTION_APPS = [
    'Twitter', 'Facebook',  # Add your distractions
]

PROTECTED_APPS = [
    'Terminal', 'VS Code',  # Add your work tools
]
```

### Change Analysis Interval

```python
monitor = FlowMonitorSystem(
    analysis_interval=3.0,  # Seconds between analyses
    window_size=60          # Metric time window (seconds)
)
```

## Troubleshooting

### No keyboard/mouse monitoring

→ Grant Accessibility and Input Monitoring permissions

### Window tracking not working

→ Grant Screen Recording permission

### Apps not being banished

→ Check app names in System Activity Monitor

### Do Not Disturb not activating

→ Create Shortcuts for DND control (see FLOW_AMPLIFICATION.md)

### High CPU usage

→ Increase `analysis_interval` to 5-10 seconds

## Data & Privacy

- All data stored locally in `notifications.db`
- No network connections
- No telemetry or tracking
- Delete database anytime: `rm notifications.db`

## Support

For issues, check:

1. `backend/README.md` - Full documentation
2. `backend/FLOW_AMPLIFICATION.md` - Amplification details
3. Terminal output for error messages

## Next Steps

1. Run for a few hours to let the system learn your patterns
2. Review the GUI metrics to understand your work habits
3. Customize thresholds and app lists
4. Check trends to optimize your flow sessions
