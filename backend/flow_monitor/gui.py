"""
Notification Display GUI
Shows filtered notifications and system status using Tkinter
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
from threading import Thread
import time
import json
import os
from .app_scanner import ApplicationScanner
from .eye_defender import EyeDefender


class NotificationGUI:
    """
    GUI for displaying filtered notifications and flow state information
    """
    
    def __init__(self, flow_amplifier, flow_monitor, auto_start_eye_defender=False):
        """
        Initialize the GUI
        
        Args:
            flow_amplifier: FlowAmplifier instance
            flow_monitor: FlowMonitorSystem instance
            auto_start_eye_defender: Whether to auto-start Eye Defender
        """
        self.flow_amplifier = flow_amplifier
        self.flow_monitor = flow_monitor
        self.auto_start_eye_defender = auto_start_eye_defender
        
        # Initialize Eye Defender (default values, will be updated from GUI sliders)
        self.eye_defender = EyeDefender(interval_minutes=20, blur_duration_seconds=20)
        
        self.root = tk.Tk()
        self.root.title("Prism - Flow State Monitor")
        self.root.geometry("900x700")
        
        # Configure styles
        self.setup_styles()
        
        # Create UI
        self.create_ui()
        
        # Register callbacks
        self.flow_amplifier.add_notification_callback(self.on_notification)
        
        # Set blur callback for Eye Defender (must run on main thread)
        self.eye_defender.set_blur_callback(lambda: self.root.after(0, self.show_eye_break_overlay))
        
        # Initialize Eye Defender with slider values after UI is created
        self.root.after(100, self._initialize_eye_defender_from_gui)
        
        # Auto-start Eye Defender if requested
        if self.auto_start_eye_defender:
            self.root.after(1000, self.start_eye_defender)
        
        # Start update loop
        self.running = True
        self.update_thread = Thread(target=self.update_loop, daemon=True)
        self.update_thread.start()
    
    def setup_styles(self):
        """Configure UI styles"""
        style = ttk.Style()
        style.theme_use('aqua' if 'aqua' in style.theme_names() else 'clam')
        
        # Custom colors
        self.colors = {
            'DEEP_FLOW': '#FF4500',
            'FLOW': '#FFA500',
            'FOCUSED': '#FFD700',
            'WORKING': '#32CD32',
            'DISTRACTED': '#808080'
        }
    
    def create_ui(self):
        """Create the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # === Header: Flow State Status ===
        status_frame = ttk.LabelFrame(main_frame, text="Flow State Status", padding="10")
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # Flow state display
        ttk.Label(status_frame, text="Current State:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.flow_state_label = ttk.Label(status_frame, text="WORKING", font=('Arial', 16, 'bold'))
        self.flow_state_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Flow score
        ttk.Label(status_frame, text="Flow Score:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.flow_score_label = ttk.Label(status_frame, text="0%", font=('Arial', 14))
        self.flow_score_label.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Progress bar
        self.flow_progress = ttk.Progressbar(status_frame, length=300, mode='determinate')
        self.flow_progress.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Flow duration
        ttk.Label(status_frame, text="Flow Duration:").grid(row=3, column=0, sticky=tk.W, padx=5)
        self.duration_label = ttk.Label(status_frame, text="0:00", font=('Arial', 12))
        self.duration_label.grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # === Amplification Status ===
        amp_frame = ttk.LabelFrame(main_frame, text="Amplification Status", padding="10")
        amp_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        amp_frame.columnconfigure(1, weight=1)
        
        # DND status
        ttk.Label(amp_frame, text="Do Not Disturb:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.dnd_status_label = ttk.Label(amp_frame, text="🔕 OFF", font=('Arial', 12))
        self.dnd_status_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Suppressed notifications
        ttk.Label(amp_frame, text="Suppressed Notifications:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.suppressed_label = ttk.Label(amp_frame, text="0", font=('Arial', 12))
        self.suppressed_label.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Banished apps
        ttk.Label(amp_frame, text="Banished Apps:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.banished_label = ttk.Label(amp_frame, text="0", font=('Arial', 12))
        self.banished_label.grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Whitelist violations
        ttk.Label(amp_frame, text="Whitelist Violations:").grid(row=3, column=0, sticky=tk.W, padx=5)
        self.violations_label = ttk.Label(amp_frame, text="N/A", font=('Arial', 12))
        self.violations_label.grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # === Notifications Feed ===
        notif_frame = ttk.LabelFrame(main_frame, text="Notification Feed", padding="10")
        notif_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        notif_frame.columnconfigure(0, weight=1)
        notif_frame.rowconfigure(0, weight=1)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(notif_frame)
        notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tab 1: All Notifications
        all_tab = ttk.Frame(notebook)
        notebook.add(all_tab, text="All Notifications")
        
        self.all_notif_text = scrolledtext.ScrolledText(all_tab, wrap=tk.WORD, height=15)
        self.all_notif_text.pack(fill=tk.BOTH, expand=True)
        self.all_notif_text.config(state=tk.DISABLED)
        
        # Tab 2: Suppressed Notifications
        suppressed_tab = ttk.Frame(notebook)
        notebook.add(suppressed_tab, text="Suppressed")
        
        self.suppressed_text = scrolledtext.ScrolledText(suppressed_tab, wrap=tk.WORD, height=15)
        self.suppressed_text.pack(fill=tk.BOTH, expand=True)
        self.suppressed_text.config(state=tk.DISABLED)
        
        # Tab 3: Metrics
        metrics_tab = ttk.Frame(notebook)
        notebook.add(metrics_tab, text="Metrics")
        
        self.metrics_text = scrolledtext.ScrolledText(metrics_tab, wrap=tk.WORD, height=15)
        self.metrics_text.pack(fill=tk.BOTH, expand=True)
        self.metrics_text.config(state=tk.DISABLED)
        
        # Tab 4: App Management
        apps_tab = ttk.Frame(notebook)
        notebook.add(apps_tab, text="App Settings")
        self.create_app_management_tab(apps_tab)
        
        # Tab 5: Eye Defender
        eye_tab = ttk.Frame(notebook)
        notebook.add(eye_tab, text="👁️ Eye Defender")
        self.create_eye_defender_tab(eye_tab)
        
        # === Control Buttons ===
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(button_frame, text="Reset Metrics", command=self.reset_metrics).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="View Trends", command=self.show_trends).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.quit_app).pack(side=tk.RIGHT, padx=5)
    
    def create_app_management_tab(self, parent):
        """Create the app management interface"""
        # Main container
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)  # Allowed Apps - main section
        parent.rowconfigure(2, weight=1)  # Protected Apps
        parent.rowconfigure(3, weight=1)  # Distraction Apps
        
        # === Whitelist Mode Toggle ===
        whitelist_control_frame = ttk.LabelFrame(parent, text="🔒 Whitelist Mode - Ultimate Focus", padding="10")
        whitelist_control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Description
        desc_label = ttk.Label(
            whitelist_control_frame,
            text="Add only the apps you need for focus work. All other apps will be automatically minimized.",
            foreground='gray',
            wraplength=700
        )
        desc_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        self.whitelist_enabled = tk.BooleanVar(value=False)
        whitelist_check = ttk.Checkbutton(
            whitelist_control_frame, 
            text="Enable Whitelist Mode (Strict enforcement)",
            variable=self.whitelist_enabled,
            command=self.toggle_whitelist_mode
        )
        whitelist_check.grid(row=1, column=0, sticky=tk.W)
        
        self.whitelist_status_label = ttk.Label(whitelist_control_frame, text="Status: Disabled", foreground='gray')
        self.whitelist_status_label.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        # === Allowed Apps Section (Full Width) - For Whitelist Mode ===
        allowed_frame = ttk.LabelFrame(parent, text="✅ Allowed Apps - Whitelist Mode", padding="10")
        allowed_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        allowed_frame.columnconfigure(0, weight=1)
        allowed_frame.rowconfigure(3, weight=1)
        allowed_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5), pady=0)
        allowed_frame.columnconfigure(0, weight=1)
        allowed_frame.rowconfigure(3, weight=1)
        
        # Help text
        help_text = ttk.Label(allowed_frame, 
                             text="Add apps to whitelist. All other apps will be minimized when whitelist mode is active.",
                             font=('Arial', 9), foreground='#666', wraplength=350)
        help_text.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Quick action buttons
        quick_actions_frame = ttk.Frame(allowed_frame)
        quick_actions_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        quick_actions_frame.columnconfigure(0, weight=1)
        
        ttk.Button(quick_actions_frame, text="Browse All Apps", 
                  command=self.browse_apps_for_allowed).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(quick_actions_frame, text="Add Running Apps", 
                  command=self.show_running_apps, style='Accent.TButton').grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        ttk.Button(quick_actions_frame, text="Clear All", 
                  command=self.clear_allowed_apps).grid(row=0, column=2, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Input for new allowed app
        input_frame_allowed = ttk.Frame(allowed_frame)
        input_frame_allowed.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(5, 5))
        input_frame_allowed.columnconfigure(0, weight=1)
        
        self.allowed_app_entry = ttk.Entry(input_frame_allowed, font=('Arial', 11))
        self.allowed_app_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.allowed_app_entry.bind('<Return>', lambda e: self.add_allowed_app())
        self.allowed_app_entry.insert(0, "Type app name or use buttons above...")
        self.allowed_app_entry.config(foreground='gray')
        self.allowed_app_entry.bind('<FocusIn>', self._clear_entry_placeholder)
        self.allowed_app_entry.bind('<FocusOut>', self._restore_entry_placeholder)
        
        ttk.Button(input_frame_allowed, text="Add", command=self.add_allowed_app).grid(row=0, column=1)
        
        # Listbox for allowed apps
        list_frame_allowed = ttk.Frame(allowed_frame)
        list_frame_allowed.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame_allowed.columnconfigure(0, weight=1)
        list_frame_allowed.rowconfigure(0, weight=1)
        
        scrollbar_allowed = ttk.Scrollbar(list_frame_allowed)
        scrollbar_allowed.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.allowed_apps_listbox = tk.Listbox(list_frame_allowed, yscrollcommand=scrollbar_allowed.set, 
                                               font=('Arial', 11), selectmode='extended')
        self.allowed_apps_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_allowed.config(command=self.allowed_apps_listbox.yview)
        
        # Bottom buttons
        button_frame_allowed = ttk.Frame(allowed_frame)
        button_frame_allowed.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        button_frame_allowed.columnconfigure(0, weight=1)
        
        ttk.Button(button_frame_allowed, text="Remove Selected", 
                  command=self.remove_allowed_app).grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(button_frame_allowed, text="Select All", 
                  command=lambda: self.allowed_apps_listbox.select_set(0, tk.END)).grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # === Protected Apps Section (Full Width) - For Flow Mode ===
        protected_frame = ttk.LabelFrame(parent, text="🛡️ Protected Apps (Flow Mode)", padding="10")
        protected_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        protected_frame.columnconfigure(0, weight=1)
        protected_frame.rowconfigure(2, weight=1)
        
        # Note label
        note_label = ttk.Label(protected_frame, text="Work apps never minimized during flow (e.g., VS Code, Terminal)", 
                              font=('Arial', 9), foreground='#666', wraplength=350)
        note_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Input for new protected app
        input_frame_protected = ttk.Frame(protected_frame)
        input_frame_protected.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        input_frame_protected.columnconfigure(0, weight=1)
        
        self.protected_app_entry = ttk.Entry(input_frame_protected)
        self.protected_app_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.protected_app_entry.bind('<Return>', lambda e: self.add_protected_app())
        
        ttk.Button(input_frame_protected, text="Add", command=self.add_protected_app).grid(row=0, column=1)
        
        # Listbox for protected apps
        list_frame_protected = ttk.Frame(protected_frame)
        list_frame_protected.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame_protected.columnconfigure(0, weight=1)
        list_frame_protected.rowconfigure(0, weight=1)
        
        scrollbar_protected = ttk.Scrollbar(list_frame_protected)
        scrollbar_protected.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.protected_apps_listbox = tk.Listbox(list_frame_protected, yscrollcommand=scrollbar_protected.set)
        self.protected_apps_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_protected.config(command=self.protected_apps_listbox.yview)
        
        # Remove button for protected apps
        ttk.Button(protected_frame, text="Remove Selected", 
                  command=self.remove_protected_app).grid(row=3, column=0, pady=(5, 0))
        
        # === Distraction Apps Section (Full Width) ===
        distraction_frame = ttk.LabelFrame(parent, text="🚫 Distraction Apps (Flow Mode)", padding="10")
        distraction_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        distraction_frame.columnconfigure(0, weight=1)
        distraction_frame.rowconfigure(2, weight=1)
        
        # Note label
        distraction_note = ttk.Label(distraction_frame, text="Apps that will be minimized during flow amplification (e.g., Slack, Twitter, Discord)", 
                              font=('Arial', 9), foreground='#666', wraplength=700)
        distraction_note.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Input for new distraction app
        input_frame_distraction = ttk.Frame(distraction_frame)
        input_frame_distraction.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        input_frame_distraction.columnconfigure(0, weight=1)
        
        self.distraction_app_entry = ttk.Entry(input_frame_distraction)
        self.distraction_app_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        self.distraction_app_entry.bind('<Return>', lambda e: self.add_distraction_app())
        
        ttk.Button(input_frame_distraction, text="Add", command=self.add_distraction_app).grid(row=0, column=1)
        
        # Listbox for distraction apps
        list_frame_distraction = ttk.Frame(distraction_frame)
        list_frame_distraction.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame_distraction.columnconfigure(0, weight=1)
        list_frame_distraction.rowconfigure(0, weight=1)
        
        scrollbar_distraction = ttk.Scrollbar(list_frame_distraction)
        scrollbar_distraction.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.distraction_apps_listbox = tk.Listbox(list_frame_distraction, yscrollcommand=scrollbar_distraction.set)
        self.distraction_apps_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_distraction.config(command=self.distraction_apps_listbox.yview)
        
        # Remove button for distraction apps
        ttk.Button(distraction_frame, text="Remove Selected", 
                  command=self.remove_distraction_app).grid(row=3, column=0, pady=(5, 0))
        
        # Load current apps
        self.load_app_lists()
    
    def create_eye_defender_tab(self, parent):
        """Create the Eye Defender (20-20-20 rule) interface"""
        # Main container
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)
        
        # === Eye Defender Header ===
        header_frame = ttk.LabelFrame(parent, text="👁️ Eye Defender - 20-20-20 Rule", padding="15")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        desc_text = (
            "Protect your eyes from digital strain!\n\n"
            "Every X minutes, you'll get a reminder to look away from your screen\n"
            "for Y seconds at something 20 feet away. This reduces eye fatigue and strain."
        )
        ttk.Label(header_frame, text=desc_text, foreground='#666', wraplength=800).grid(row=0, column=0, sticky=tk.W)
        
        # === Settings Frame ===
        settings_frame = ttk.LabelFrame(parent, text="⚙️ Timer Settings (Changes Apply Immediately)", padding="15")
        settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        settings_frame.columnconfigure(1, weight=1)
        
        # Help text
        help_text = "⚡ Adjust sliders anytime - settings update instantly, even while Eye Defender is running!"
        ttk.Label(settings_frame, text=help_text, foreground='#2196F3', font=('Arial', 9), wraplength=800).grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Interval setting
        ttk.Label(settings_frame, text="Reminder Interval:", font=('Arial', 11)).grid(row=1, column=0, sticky=tk.W, pady=10)
        
        interval_frame = ttk.Frame(settings_frame)
        interval_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=10, padx=(10, 0))
        
        self.interval_var = tk.DoubleVar(value=20.0)
        # Range: 0.5 to 30 minutes (30 seconds to 30 minutes)
        self.interval_scale = ttk.Scale(interval_frame, from_=0.5, to=30, orient=tk.HORIZONTAL,
                                       variable=self.interval_var, command=self.update_eye_defender_interval)
        self.interval_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.interval_label = ttk.Label(interval_frame, text="20 min", font=('Arial', 12, 'bold'))
        self.interval_label.pack(side=tk.RIGHT)
        
        # Duration setting
        ttk.Label(settings_frame, text="Break Duration (seconds):", font=('Arial', 11)).grid(row=2, column=0, sticky=tk.W, pady=10)
        
        duration_frame = ttk.Frame(settings_frame)
        duration_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=10, padx=(10, 0))
        
        self.duration_var = tk.IntVar(value=20)
        self.duration_scale = ttk.Scale(duration_frame, from_=10, to=60, orient=tk.HORIZONTAL,
                                       variable=self.duration_var, command=self.update_eye_defender_duration)
        self.duration_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.duration_label = ttk.Label(duration_frame, text="20 sec", font=('Arial', 12, 'bold'))
        self.duration_label.pack(side=tk.RIGHT)
        
        # === Control Frame ===
        control_frame = ttk.LabelFrame(parent, text="🎮 Controls", padding="15")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N), padx=10, pady=10)
        
        # Status display
        status_display_frame = ttk.Frame(control_frame)
        status_display_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(status_display_frame, text="Status:", font=('Arial', 11)).pack(side=tk.LEFT, padx=(0, 10))
        self.eye_status_label = ttk.Label(status_display_frame, text="Disabled", 
                                         font=('Arial', 12, 'bold'), foreground='gray')
        self.eye_status_label.pack(side=tk.LEFT)
        
        # Timer display (countdown)
        timer_frame = ttk.Frame(control_frame)
        timer_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(timer_frame, text="Next Break In:", font=('Arial', 11)).pack(side=tk.LEFT, padx=(0, 10))
        self.eye_timer_label = ttk.Label(timer_frame, text="--:--", 
                                        font=('Arial', 20, 'bold'), foreground='#2196F3')
        self.eye_timer_label.pack(side=tk.LEFT)
        
        # Stats display
        stats_frame = ttk.Frame(control_frame)
        stats_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(stats_frame, text="Total Reminders:", font=('Arial', 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.eye_reminders_label = ttk.Label(stats_frame, text="0", font=('Arial', 10, 'bold'))
        self.eye_reminders_label.pack(side=tk.LEFT, padx=(0, 20))
        
        ttk.Label(stats_frame, text="Last Reminder:", font=('Arial', 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.eye_last_reminder_label = ttk.Label(stats_frame, text="Never", font=('Arial', 10))
        self.eye_last_reminder_label.pack(side=tk.LEFT)
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X)
        
        self.eye_start_btn = ttk.Button(button_frame, text="▶️ Start Eye Defender", 
                                       command=self.start_eye_defender, style='Accent.TButton')
        self.eye_start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.eye_stop_btn = ttk.Button(button_frame, text="⏹️ Stop", 
                                      command=self.stop_eye_defender, state=tk.DISABLED)
        self.eye_stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.eye_pause_btn = ttk.Button(button_frame, text="⏸️ Pause", 
                                       command=self.pause_eye_defender, state=tk.DISABLED)
        self.eye_pause_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="👁️ Take Break Now", 
                  command=self.manual_eye_break).pack(side=tk.LEFT)
    
    def _initialize_eye_defender_from_gui(self):
        """Initialize Eye Defender with current slider values"""
        interval_minutes = self.interval_var.get()
        duration_seconds = self.duration_var.get()
        self.eye_defender.set_interval(interval_minutes)
        self.eye_defender.set_blur_duration(duration_seconds)
        print(f"👁️  Eye Defender configured: {interval_minutes} min interval, {duration_seconds} sec breaks")
    
    def update_eye_defender_interval(self, value):
        """Update interval label and eye defender setting"""
        minutes = float(value)
        # Format display based on value
        if minutes < 1:
            seconds = int(minutes * 60)
            self.interval_label.config(text=f"{seconds} sec")
        elif minutes == int(minutes):
            self.interval_label.config(text=f"{int(minutes)} min")
        else:
            self.interval_label.config(text=f"{minutes:.1f} min")
        
        # Update interval (will auto-restart timer if running)
        self.eye_defender.set_interval(minutes)
        
        # Show feedback if Eye Defender is running
        settings = self.eye_defender.get_settings()
        if settings['is_running'] and not settings['is_paused']:
            self.eye_status_label.config(text="⚡ Timer Restarted", foreground='#FF9800')
            print(f"⚙️  Eye Defender interval changed to {minutes:.1f} minutes (timer restarted)")
            # Reset label after 2 seconds
            self.root.after(2000, lambda: self.eye_status_label.config(text="Active ✓", foreground='green'))
    
    def update_eye_defender_duration(self, value):
        """Update duration label and eye defender setting"""
        seconds = int(float(value))
        self.duration_label.config(text=f"{seconds} sec")
        self.eye_defender.set_blur_duration(seconds)
        
        # Show feedback if Eye Defender is running
        settings = self.eye_defender.get_settings()
        if settings['is_running']:
            print(f"⚙️  Eye Defender break duration changed to {seconds} seconds")
    
    def start_eye_defender(self):
        """Start the eye defender"""
        self.eye_defender.start()
        self.eye_status_label.config(text="Active ✓", foreground='green')
        self.eye_start_btn.config(state=tk.DISABLED)
        self.eye_stop_btn.config(state=tk.NORMAL)
        self.eye_pause_btn.config(state=tk.NORMAL)
        print("✓ Eye Defender started")
    
    def stop_eye_defender(self):
        """Stop the eye defender"""
        self.eye_defender.stop()
        self.eye_status_label.config(text="Disabled", foreground='gray')
        self.eye_start_btn.config(state=tk.NORMAL)
        self.eye_stop_btn.config(state=tk.DISABLED)
        self.eye_pause_btn.config(state=tk.DISABLED, text="⏸️ Pause")
        print("✓ Eye Defender stopped")
    
    def pause_eye_defender(self):
        """Pause/resume the eye defender"""
        settings = self.eye_defender.get_settings()
        if settings['is_paused']:
            self.eye_defender.resume()
            self.eye_pause_btn.config(text="⏸️ Pause")
            self.eye_status_label.config(text="Active ✓", foreground='green')
        else:
            self.eye_defender.pause()
            self.eye_pause_btn.config(text="▶️ Resume")
            self.eye_status_label.config(text="Paused", foreground='orange')
    
    def manual_eye_break(self):
        """Trigger a manual eye break"""
        if self.eye_defender.trigger_manual_break():
            pass  # Callback will handle the blur overlay
        else:
            messagebox.showwarning("Not Active", "Eye Defender is not running. Start it first!")
    
    def show_eye_break_overlay(self):
        """Show eye break blur overlay (runs on main thread)"""
        try:
            import subprocess
            import os
            
            # Get blur duration from eye defender
            settings = self.eye_defender.get_settings()
            blur_duration = settings['blur_duration_seconds']
            
            # Get path to music file
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            music_path = os.path.join(current_dir, 'assets', 'calm_music.mp3')
            
            # Start playing music if file exists
            music_process = None
            if os.path.exists(music_path):
                try:
                    # Try using pygame for music playback
                    try:
                        import pygame
                        pygame.mixer.init()
                        pygame.mixer.music.load(music_path)
                        pygame.mixer.music.play()
                        print(f"🎵 Playing calm music for {blur_duration} seconds...")
                    except ImportError:
                        # Fallback to afplay on macOS
                        music_process = subprocess.Popen(['afplay', music_path])
                        print(f"🎵 Playing calm music (afplay) for {blur_duration} seconds...")
                except Exception as e:
                    print(f"⚠️  Could not play music: {e}")
            else:
                print(f"⚠️  Music file not found: {music_path}")
            
            # Create blur overlay window
            blur_window = tk.Toplevel(self.root)
            blur_window.title("Eye Break")
            
            # Make it fullscreen and on top
            blur_window.attributes('-fullscreen', True)
            blur_window.attributes('-topmost', True)
            blur_window.attributes('-alpha', 0.0)  # Start transparent
            
            # Semi-transparent dark background
            blur_window.configure(bg='#000000')
            
            # Center frame for message
            center_frame = ttk.Frame(blur_window)
            center_frame.place(relx=0.5, rely=0.5, anchor='center')
            
            # Create message label
            message_frame = tk.Frame(center_frame, bg='#1e1e1e', padx=40, pady=30, relief=tk.RAISED, bd=3)
            message_frame.pack()
            
            title_label = tk.Label(message_frame, 
                                  text="👁️ Eye Break Time!", 
                                  font=('Arial', 36, 'bold'),
                                  fg='#4CAF50',
                                  bg='#1e1e1e')
            title_label.pack(pady=(0, 20))
            
            instruction_label = tk.Label(message_frame,
                                        text=f"Look at something 20 feet away",
                                        font=('Arial', 24),
                                        fg='white',
                                        bg='#1e1e1e')
            instruction_label.pack(pady=(0, 10))
            
            # Countdown label
            countdown_label = tk.Label(message_frame,
                                      text=f"{blur_duration}",
                                      font=('Arial', 48, 'bold'),
                                      fg='#FFC107',
                                      bg='#1e1e1e')
            countdown_label.pack(pady=20)
            
            hint_label = tk.Label(message_frame,
                                 text="Press ESC to skip",
                                 font=('Arial', 12),
                                 fg='#888888',
                                 bg='#1e1e1e')
            hint_label.pack()
            
            # Countdown state
            remaining = [blur_duration]
            
            def fade_in():
                """Gradually fade in the overlay"""
                current_alpha = blur_window.attributes('-alpha')
                if current_alpha < 0.85:
                    blur_window.attributes('-alpha', current_alpha + 0.05)
                    blur_window.after(50, fade_in)
            
            def update_countdown():
                """Update countdown timer"""
                if remaining[0] > 0:
                    countdown_label.config(text=str(remaining[0]))
                    remaining[0] -= 1
                    blur_window.after(1000, update_countdown)
                else:
                    fade_out()
            
            def stop_music():
                """Stop music playback"""
                try:
                    # Stop pygame music if it was used
                    try:
                        import pygame
                        if pygame.mixer.get_init():
                            pygame.mixer.music.stop()
                            pygame.mixer.quit()
                    except:
                        pass
                    
                    # Stop afplay process if it was used
                    if music_process and music_process.poll() is None:
                        music_process.terminate()
                except Exception as e:
                    print(f"⚠️  Error stopping music: {e}")
            
            def fade_out():
                """Gradually fade out and close"""
                current_alpha = blur_window.attributes('-alpha')
                if current_alpha > 0:
                    blur_window.attributes('-alpha', current_alpha - 0.1)
                    blur_window.after(50, fade_out)
                else:
                    stop_music()
                    blur_window.destroy()
            
            def skip_break(event=None):
                """Allow user to skip the break"""
                stop_music()
                blur_window.destroy()
            
            # Bind ESC key to skip
            blur_window.bind('<Escape>', skip_break)
            
            # Start fade in and countdown
            blur_window.after(100, fade_in)
            blur_window.after(1000, update_countdown)
            
            # Schedule music to stop after blur duration (in milliseconds)
            blur_window.after(blur_duration * 1000, stop_music)
            
            # Play sound notification
            sound_script = f'''
            display notification "Look 20 feet away for {blur_duration} seconds" ¬
                with title "👁️ Eye Break Time!" ¬
                sound name "Glass"
            '''
            subprocess.Popen(['osascript', '-e', sound_script], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
        except Exception as e:
            print(f"⚠️  Error showing eye break overlay: {e}")
    
    def load_app_lists(self):
        """Load current app lists from flow amplifier"""
        # Load from saved config if exists
        self.load_app_config()
        
        # Clear listboxes
        self.allowed_apps_listbox.delete(0, tk.END)
        self.protected_apps_listbox.delete(0, tk.END)
        self.distraction_apps_listbox.delete(0, tk.END)
        
        # Load allowed apps (for whitelist mode)
        whitelist_controller = self.flow_monitor.get_whitelist_controller()
        if whitelist_controller:
            for app in sorted(whitelist_controller.get_allowed_apps()):
                self.allowed_apps_listbox.insert(tk.END, app)
        
        # Load protected apps
        for app in sorted(self.flow_amplifier.PROTECTED_APPS):
            self.protected_apps_listbox.insert(tk.END, app)
        
        # Load distraction apps
        for app in sorted(self.flow_amplifier.DISTRACTION_APPS):
            self.distraction_apps_listbox.insert(tk.END, app)
    
    def load_app_config(self):
        """Load app lists from config file"""
        config_file = 'app_config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.flow_amplifier.PROTECTED_APPS = config.get('protected_apps', self.flow_amplifier.PROTECTED_APPS)
                    self.flow_amplifier.DISTRACTION_APPS = config.get('distraction_apps', self.flow_amplifier.DISTRACTION_APPS)
                    
                    # Load allowed apps for whitelist
                    whitelist_controller = self.flow_monitor.get_whitelist_controller()
                    if whitelist_controller and 'allowed_apps' in config:
                        whitelist_controller.set_allowed_apps(config['allowed_apps'])
                        self.flow_monitor.set_allowed_apps(config['allowed_apps'])
                    
                    print(f"✓ Loaded app configuration from {config_file}")
            except Exception as e:
                print(f"⚠️  Could not load app config: {e}")
    
    def save_app_config(self):
        """Save app lists to config file"""
        config_file = 'app_config.json'
        try:
            config = {
                'protected_apps': self.flow_amplifier.PROTECTED_APPS,
                'distraction_apps': self.flow_amplifier.DISTRACTION_APPS
            }
            
            # Save allowed apps if whitelist controller exists
            whitelist_controller = self.flow_monitor.get_whitelist_controller()
            if whitelist_controller:
                config['allowed_apps'] = whitelist_controller.get_allowed_apps()
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✓ Saved app configuration to {config_file}")
        except Exception as e:
            print(f"⚠️  Could not save app config: {e}")
    
    def add_protected_app(self):
        """Add a new protected app"""
        app_name = self.protected_app_entry.get().strip()
        if not app_name:
            return
        
        if app_name in self.flow_amplifier.PROTECTED_APPS:
            messagebox.showwarning("Duplicate", f"'{app_name}' is already in the protected apps list.")
            return
        
        if app_name in self.flow_amplifier.DISTRACTION_APPS:
            messagebox.showwarning("Conflict", f"'{app_name}' is in the distraction apps list. Remove it from there first.")
            return
        
        self.flow_amplifier.PROTECTED_APPS.append(app_name)
        self.protected_apps_listbox.insert(tk.END, app_name)
        self.protected_app_entry.delete(0, tk.END)
        self.save_app_config()
        print(f"✓ Added protected app: {app_name}")
    
    def remove_protected_app(self):
        """Remove selected protected app"""
        selection = self.protected_apps_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an app to remove.")
            return
        
        index = selection[0]
        app_name = self.protected_apps_listbox.get(index)
        
        if messagebox.askyesno("Confirm", f"Remove '{app_name}' from protected apps?"):
            if app_name in self.flow_amplifier.PROTECTED_APPS:
                self.flow_amplifier.PROTECTED_APPS.remove(app_name)
                self.protected_apps_listbox.delete(index)
                self.save_app_config()
                print(f"✓ Removed protected app: {app_name}")
    
    def add_distraction_app(self):
        """Add a new distraction app"""
        app_name = self.distraction_app_entry.get().strip()
        if not app_name:
            return
        
        if app_name in self.flow_amplifier.DISTRACTION_APPS:
            messagebox.showwarning("Duplicate", f"'{app_name}' is already in the distraction apps list.")
            return
        
        if app_name in self.flow_amplifier.PROTECTED_APPS:
            messagebox.showwarning("Conflict", f"'{app_name}' is in the protected apps list. Remove it from there first.")
            return
        
        self.flow_amplifier.DISTRACTION_APPS.append(app_name)
        self.distraction_apps_listbox.insert(tk.END, app_name)
        self.distraction_app_entry.delete(0, tk.END)
        self.save_app_config()
        print(f"✓ Added distraction app: {app_name}")
    
    def remove_distraction_app(self):
        """Remove selected distraction app"""
        selection = self.distraction_apps_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an app to remove.")
            return
        
        index = selection[0]
        app_name = self.distraction_apps_listbox.get(index)
        
        if messagebox.askyesno("Confirm", f"Remove '{app_name}' from distraction apps?"):
            if app_name in self.flow_amplifier.DISTRACTION_APPS:
                self.flow_amplifier.DISTRACTION_APPS.remove(app_name)
                self.distraction_apps_listbox.delete(index)
                self.save_app_config()
                print(f"✓ Removed distraction app: {app_name}")
    
    def toggle_whitelist_mode(self):
        """Toggle whitelist mode on/off"""
        whitelist_controller = self.flow_monitor.get_whitelist_controller()
        
        if not whitelist_controller:
            messagebox.showwarning(
                "Not Available",
                "Whitelist mode was not enabled at startup. Please restart with whitelist mode enabled."
            )
            self.whitelist_enabled.set(False)
            return
        
        if self.whitelist_enabled.get():
            # Enable whitelist mode
            apps = whitelist_controller.get_allowed_apps()
            if not apps:
                messagebox.showwarning(
                    "No Apps",
                    "Please add at least one app to the Allowed Apps list before enabling whitelist mode."
                )
                self.whitelist_enabled.set(False)
                return
            
            whitelist_controller.start()
            self.whitelist_status_label.config(text=f"Status: Active ({len(apps)} apps allowed)", foreground='green')
            print("✓ Whitelist mode enabled")
        else:
            # Disable whitelist mode
            whitelist_controller.stop()
            self.whitelist_status_label.config(text="Status: Disabled", foreground='gray')
            print("✓ Whitelist mode disabled")
    
    def _clear_entry_placeholder(self, event):
        """Clear placeholder text when entry is focused"""
        if self.allowed_app_entry.get() == "Type app name or use buttons above...":
            self.allowed_app_entry.delete(0, tk.END)
            self.allowed_app_entry.config(foreground='black')
    
    def _restore_entry_placeholder(self, event):
        """Restore placeholder text when entry loses focus"""
        if not self.allowed_app_entry.get().strip():
            self.allowed_app_entry.insert(0, "Type app name or use buttons above...")
            self.allowed_app_entry.config(foreground='gray')
    
    def add_allowed_app(self):
        """Add a new allowed app to whitelist"""
        app_name = self.allowed_app_entry.get().strip()
        if not app_name or app_name == "Type app name or use buttons above...":
            return
        
        whitelist_controller = self.flow_monitor.get_whitelist_controller()
        if not whitelist_controller:
            messagebox.showwarning(
                "Not Available",
                "Whitelist mode is not available. Restart with whitelist mode enabled."
            )
            return
        
        current_apps = set(whitelist_controller.get_allowed_apps())
        
        if app_name in current_apps:
            messagebox.showwarning("Duplicate", f"'{app_name}' is already in the allowed apps list.")
            return
        
        whitelist_controller.add_allowed_app(app_name)
        self.flow_monitor.set_allowed_apps(whitelist_controller.get_allowed_apps())
        self.allowed_apps_listbox.insert(tk.END, app_name)
        self.allowed_app_entry.delete(0, tk.END)
        self.save_app_config()
        print(f"✓ Added allowed app: {app_name}")
        
        # Update status label
        if self.whitelist_enabled.get():
            apps = whitelist_controller.get_allowed_apps()
            self.whitelist_status_label.config(text=f"Status: Active ({len(apps)} apps allowed)")
    
    def remove_allowed_app(self):
        """Remove selected allowed apps from whitelist (supports multi-select)"""
        selections = self.allowed_apps_listbox.curselection()
        if not selections:
            messagebox.showinfo("No Selection", "Please select one or more apps to remove.")
            return
        
        # Get all selected app names
        selected_apps = [self.allowed_apps_listbox.get(idx) for idx in selections]
        
        if len(selected_apps) == 1:
            confirm_msg = f"Remove '{selected_apps[0]}' from allowed apps?"
        else:
            confirm_msg = f"Remove {len(selected_apps)} apps from allowed list?"
        
        if messagebox.askyesno("Confirm", confirm_msg):
            whitelist_controller = self.flow_monitor.get_whitelist_controller()
            if whitelist_controller:
                # Remove from controller
                for app_name in selected_apps:
                    whitelist_controller.remove_allowed_app(app_name)
                
                # Update system
                self.flow_monitor.set_allowed_apps(whitelist_controller.get_allowed_apps())
                
                # Remove from listbox (in reverse to maintain indices)
                for idx in reversed(selections):
                    self.allowed_apps_listbox.delete(idx)
                
                self.save_app_config()
                print(f"✓ Removed {len(selected_apps)} allowed app(s)")
                
                # Update status label
                if self.whitelist_enabled.get():
                    apps = whitelist_controller.get_allowed_apps()
                    self.whitelist_status_label.config(text=f"Status: Active ({len(apps)} apps allowed)")
    
    def clear_allowed_apps(self):
        """Clear all allowed apps from whitelist"""
        whitelist_controller = self.flow_monitor.get_whitelist_controller()
        if not whitelist_controller:
            messagebox.showwarning(
                "Not Available",
                "Whitelist mode is not available. Restart with whitelist mode enabled."
            )
            return
        
        current_apps = whitelist_controller.get_allowed_apps()
        if not current_apps:
            messagebox.showinfo("Empty", "No apps in the allowed list.")
            return
        
        if messagebox.askyesno("Confirm", f"Remove all {len(current_apps)} apps from allowed list?"):
            # Clear controller
            whitelist_controller.set_allowed_apps([])
            self.flow_monitor.set_allowed_apps([])
            
            # Clear listbox
            self.allowed_apps_listbox.delete(0, tk.END)
            
            self.save_app_config()
            print("✓ Cleared all allowed apps")
            
            # Update status label
            if self.whitelist_enabled.get():
                self.whitelist_status_label.config(text="Status: Active (0 apps allowed)", foreground='orange')
                messagebox.showwarning(
                    "Warning",
                    "Whitelist is active but no apps are allowed. Add apps or disable whitelist mode."
                )
    
    def browse_apps_for_allowed(self):
        """Open app browser dialog for selecting allowed apps"""
        self.open_app_browser(mode='allowed')
    
    def show_running_apps(self):
        """Show currently running apps for quick whitelist"""
        self.open_running_apps_dialog()
    
    def open_running_apps_dialog(self):
        """Open a dialog showing currently running apps for quick selection"""
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Currently Running Applications")
        dialog.geometry("600x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main container
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Info label
        info_text = "Select currently running apps to add to your whitelist. Apps with ✓ are already allowed."
        info_label = ttk.Label(main_frame, text=info_text, wraplength=550)
        info_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Status label
        status_label = ttk.Label(main_frame, text="Loading running apps...", foreground='gray')
        status_label.grid(row=1, column=0, sticky=tk.W, pady=(0, 10))
        
        # Apps list frame
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Listbox for apps
        apps_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, 
                                  selectmode='extended', font=('Arial', 12))
        apps_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=apps_listbox.yview)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, sticky=tk.E, pady=(10, 0))
        
        selected_apps = []
        
        def load_running_apps():
            """Load currently running apps"""
            try:
                scanner = ApplicationScanner()
                running_apps = scanner.get_running_apps()
                
                def populate_list():
                    apps_listbox.delete(0, tk.END)
                    
                    # Get current whitelist
                    whitelist_controller = self.flow_monitor.get_whitelist_controller()
                    current_apps = set(whitelist_controller.get_allowed_apps()) if whitelist_controller else set()
                    
                    if not running_apps:
                        status_label.config(text="No running apps found", foreground='orange')
                        return
                    
                    # Add to listbox
                    for app in sorted(running_apps):
                        display_name = app
                        if app in current_apps:
                            display_name = f"{app} ✓"
                        apps_listbox.insert(tk.END, display_name)
                    
                    status_label.config(text=f"Found {len(running_apps)} running applications", foreground='green')
                
                dialog.after(0, populate_list)
                
            except Exception as e:
                dialog.after(0, lambda: status_label.config(
                    text=f"Error loading apps: {e}", foreground='red'))
        
        def add_selected():
            """Add selected apps to whitelist"""
            selections = apps_listbox.curselection()
            if not selections:
                messagebox.showinfo("No Selection", "Please select one or more applications to add.")
                return
            
            for idx in selections:
                app_text = apps_listbox.get(idx)
                # Remove ✓ if present
                app_name = app_text.replace(' ✓', '').strip()
                selected_apps.append(app_name)
            
            dialog.destroy()
        
        def select_all():
            """Select all apps in the list"""
            apps_listbox.select_set(0, tk.END)
        
        def cancel():
            dialog.destroy()
        
        # Add buttons
        ttk.Button(button_frame, text="Select All", command=select_all).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Cancel", command=cancel).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(button_frame, text="Add Selected", command=add_selected).grid(row=0, column=2)
        
        # Load apps in background
        Thread(target=load_running_apps, daemon=True).start()
        
        # Wait for dialog to close
        dialog.wait_window()
        
        # Add selected apps to whitelist
        if selected_apps:
            whitelist_controller = self.flow_monitor.get_whitelist_controller()
            if not whitelist_controller:
                messagebox.showwarning(
                    "Not Available",
                    "Whitelist mode is not available. Restart with whitelist mode enabled."
                )
                return
            
            current_apps = set(whitelist_controller.get_allowed_apps())
            newly_added = []
            
            for app_name in selected_apps:
                if app_name not in current_apps:
                    whitelist_controller.add_allowed_app(app_name)
                    self.allowed_apps_listbox.insert(tk.END, app_name)
                    newly_added.append(app_name)
            
            if newly_added:
                self.flow_monitor.set_allowed_apps(whitelist_controller.get_allowed_apps())
                self.save_app_config()
                print(f"✓ Added {len(newly_added)} running apps: {', '.join(newly_added)}")
                
                # Update status label
                if self.whitelist_enabled.get():
                    apps = whitelist_controller.get_allowed_apps()
                    self.whitelist_status_label.config(text=f"Status: Active ({len(apps)} apps allowed)")
                
                messagebox.showinfo("Success", f"Added {len(newly_added)} running application(s) to allowed list.")
            else:
                messagebox.showinfo("Info", "All selected apps were already in the list.")
    
    def open_app_browser(self, mode='allowed'):
        """Open a dialog to browse and select installed applications
        
        Args:
            mode: 'allowed' for whitelist apps
        """
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Browse Installed Applications")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Main container
        main_frame = ttk.Frame(dialog, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        dialog.columnconfigure(0, weight=1)
        dialog.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Info label
        info_text = "Select applications to add to your allowed list. Only these apps will be permitted in whitelist mode."
        ttk.Label(main_frame, text=info_text, wraplength=650).grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        
        # Search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        search_frame.columnconfigure(1, weight=1)
        
        ttk.Label(search_frame, text="Search:").grid(row=0, column=0, padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Apps list frame
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Treeview for apps
        columns = ('name',)
        tree = ttk.Treeview(list_frame, columns=columns, show='tree headings', 
                           yscrollcommand=scrollbar.set, selectmode='extended')
        tree.heading('#0', text='Category')
        tree.heading('name', text='Application')
        tree.column('#0', width=150)
        tree.column('name', width=500)
        tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=tree.yview)
        
        # Status label
        status_label = ttk.Label(main_frame, text="Loading applications...", foreground='gray')
        status_label.grid(row=3, column=0, sticky=tk.W, pady=(5, 0))
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, sticky=tk.E, pady=(10, 0))
        
        selected_apps = []
        
        def load_apps():
            """Load applications in background thread"""
            try:
                scanner = ApplicationScanner()
                categories = scanner.get_app_categories()
                
                def populate_tree():
                    tree.delete(*tree.get_children())
                    
                    # Get current whitelist to mark already added apps
                    whitelist_controller = self.flow_monitor.get_whitelist_controller()
                    current_apps = set(whitelist_controller.get_allowed_apps()) if whitelist_controller else set()
                    
                    for category, apps in sorted(categories.items()):
                        if not apps:
                            continue
                        
                        # Add category node
                        parent = tree.insert('', 'end', text=f"{category} ({len(apps)})", open=False)
                        
                        for app in sorted(apps):
                            # Mark if already in list
                            display_name = app
                            if app in current_apps:
                                display_name = f"{app} ✓"
                            
                            tree.insert(parent, 'end', values=(display_name,), tags=(app,))
                    
                    status_label.config(text=f"Found {sum(len(apps) for apps in categories.values())} applications")
                
                dialog.after(0, populate_tree)
            except Exception as e:
                dialog.after(0, lambda: status_label.config(text=f"Error loading apps: {e}", foreground='red'))
        
        def filter_apps(*args):
            """Filter apps based on search text"""
            query = search_var.get().lower()
            if not query:
                load_apps()
                return
            
            try:
                scanner = ApplicationScanner()
                matching_apps = scanner.search_apps(query)
                
                tree.delete(*tree.get_children())
                
                if matching_apps:
                    parent = tree.insert('', 'end', text=f"Search Results ({len(matching_apps)})", open=True)
                    for app in matching_apps:
                        tree.insert(parent, 'end', values=(app['name'],), tags=(app['name'],))
                    status_label.config(text=f"Found {len(matching_apps)} matching applications")
                else:
                    status_label.config(text="No matching applications found")
            except Exception as e:
                status_label.config(text=f"Search error: {e}", foreground='red')
        
        def add_selected():
            """Add selected apps to the list"""
            selections = tree.selection()
            if not selections:
                messagebox.showinfo("No Selection", "Please select one or more applications to add.")
                return
            
            added = []
            for item in selections:
                # Get app name from tags
                tags = tree.item(item, 'tags')
                if tags:
                    app_name = tags[0]
                    if app_name:
                        added.append(app_name)
            
            if added:
                selected_apps.extend(added)
                dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        # Bind search
        search_var.trace('w', filter_apps)
        
        # Add buttons
        ttk.Button(button_frame, text="Cancel", command=cancel).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(button_frame, text="Add Selected", command=add_selected).grid(row=0, column=1)
        
        # Load apps in background
        Thread(target=load_apps, daemon=True).start()
        
        # Wait for dialog to close
        dialog.wait_window()
        
        # Add selected apps to the appropriate list
        if selected_apps:
            whitelist_controller = self.flow_monitor.get_whitelist_controller()
            if not whitelist_controller:
                messagebox.showwarning(
                    "Not Available",
                    "Whitelist mode is not available. Restart with whitelist mode enabled."
                )
                return
            
            current_apps = set(whitelist_controller.get_allowed_apps())
            newly_added = []
            
            for app_name in selected_apps:
                if app_name not in current_apps:
                    whitelist_controller.add_allowed_app(app_name)
                    self.allowed_apps_listbox.insert(tk.END, app_name)
                    newly_added.append(app_name)
            
            if newly_added:
                self.flow_monitor.set_allowed_apps(whitelist_controller.get_allowed_apps())
                self.save_app_config()
                print(f"✓ Added {len(newly_added)} apps: {', '.join(newly_added)}")
                
                # Update status label
                if self.whitelist_enabled.get():
                    apps = whitelist_controller.get_allowed_apps()
                    self.whitelist_status_label.config(text=f"Status: Active ({len(apps)} apps allowed)")
                
                messagebox.showinfo("Success", f"Added {len(newly_added)} application(s) to allowed list.")
            else:
                messagebox.showinfo("Info", "All selected apps were already in the list.")
    
    def on_notification(self, notification_data):
        """Handle new notification"""
        timestamp = datetime.fromtimestamp(notification_data['timestamp']).strftime('%H:%M:%S')
        
        # Format notification
        text = f"[{timestamp}] "
        if notification_data['is_critical']:
            text += "✅ ALLOWED - "
        else:
            text += "🚫 BLOCKED - "
        
        text += f"{notification_data['app_name']}: {notification_data['title']}\n"
        text += f"   Reason: {notification_data['reason']} (Confidence: {notification_data['confidence']:.2f})\n\n"
        
        # Add to all notifications
        self.all_notif_text.config(state=tk.NORMAL)
        self.all_notif_text.insert(tk.END, text)
        self.all_notif_text.see(tk.END)
        self.all_notif_text.config(state=tk.DISABLED)
        
        # Add to suppressed if blocked
        if not notification_data['was_shown']:
            self.suppressed_text.config(state=tk.NORMAL)
            self.suppressed_text.insert(tk.END, text)
            self.suppressed_text.see(tk.END)
            self.suppressed_text.config(state=tk.DISABLED)
    
    def update_loop(self):
        """Continuously update the display"""
        while self.running:
            try:
                self.update_display()
            except Exception as e:
                print(f"Error updating display: {e}")
            time.sleep(1)
    
    def update_display(self):
        """Update all display elements"""
        # Get current flow state
        flow_analysis = self.flow_monitor.get_current_state()
        amp_stats = self.flow_amplifier.get_statistics()
        
        # Update flow state
        state = flow_analysis['flow_state']
        score = flow_analysis['flow_score']
        duration = flow_analysis['flow_duration']
        
        self.flow_state_label.config(text=state, foreground=self.colors.get(state, 'black'))
        self.flow_score_label.config(text=f"{score:.1f}%")
        self.flow_progress['value'] = score
        
        # Format duration
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        self.duration_label.config(text=f"{minutes}:{seconds:02d}")
        
        # Update amplification status
        if amp_stats['dnd_enabled']:
            self.dnd_status_label.config(text="🔕 ON", foreground='red')
        else:
            self.dnd_status_label.config(text="🔔 OFF", foreground='green')
        
        self.suppressed_label.config(text=str(amp_stats['suppressed_count']))
        self.banished_label.config(text=str(amp_stats['banished_apps']))
        
        # Update whitelist status
        whitelist_controller = self.flow_monitor.get_whitelist_controller()
        if whitelist_controller:
            whitelist_stats = whitelist_controller.get_statistics()
            self.violations_label.config(text=str(whitelist_stats['violation_count']))
        else:
            self.violations_label.config(text="N/A")
        
        # Update Eye Defender stats
        eye_settings = self.eye_defender.get_settings()
        self.eye_reminders_label.config(text=str(eye_settings['total_reminders']))
        if eye_settings['last_reminder']:
            self.eye_last_reminder_label.config(
                text=eye_settings['last_reminder'].strftime('%H:%M:%S'))
        
        # Update countdown timer
        if eye_settings['is_running'] and not eye_settings['is_paused']:
            time_remaining = eye_settings['time_remaining_seconds']
            minutes = time_remaining // 60
            seconds = time_remaining % 60
            self.eye_timer_label.config(text=f"{minutes:02d}:{seconds:02d}", foreground='#2196F3')
        elif eye_settings['is_paused']:
            self.eye_timer_label.config(text="PAUSED", foreground='orange')
        else:
            self.eye_timer_label.config(text="--:--", foreground='gray')
        
        # Update metrics
        metrics = self.flow_monitor.get_detailed_metrics()
        self.update_metrics_display(metrics)
    
    def update_metrics_display(self, metrics):
        """Update metrics tab"""
        text = "=== Real-Time Metrics ===\n\n"
        
        # Keyboard metrics
        text += "📝 Keyboard:\n"
        text += f"  Typing Cadence: {metrics['keyboard']['typing_cadence']:.1f} keys/min\n"
        text += f"  Avg Latency: {metrics['keyboard']['avg_inter_key_latency']:.3f}s\n"
        text += f"  Error Rate: {metrics['keyboard']['error_rate']:.2%}\n\n"
        
        # Mouse metrics
        text += "🖱️ Mouse:\n"
        text += f"  Movement Rate: {metrics['mouse']['mouse_move_rate']:.1f} moves/min\n"
        text += f"  Scroll Velocity: {metrics['mouse']['scroll_velocity']:.2f}\n"
        text += f"  Scroll Bursts: {metrics['mouse']['scroll_bursts']}\n\n"
        
        # Window metrics
        text += "🪟 Window:\n"
        text += f"  Task Switches: {metrics['window']['task_switch_frequency']:.1f}/min\n"
        text += f"  Active Apps: {metrics['window']['active_app_count']}\n"
        text += f"  Current App: {metrics['window']['current_app']}\n\n"
        
        # Trends
        text += "📊 Trends (10 min):\n"
        text += f"  Avg Flow Score: {metrics['trends']['avg_flow_score']:.1f}\n"
        text += f"  Time in Flow: {metrics['trends']['flow_percentage']:.1f}%\n"
        text += f"  Trend: {metrics['trends']['trend']}\n"
        
        self.metrics_text.config(state=tk.NORMAL)
        self.metrics_text.delete(1.0, tk.END)
        self.metrics_text.insert(tk.END, text)
        self.metrics_text.config(state=tk.DISABLED)
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.flow_monitor.reset()
        print("✓ Metrics reset")
    
    def show_trends(self):
        """Show trends in a popup"""
        trends = self.flow_monitor.get_trends(window_minutes=30)
        
        popup = tk.Toplevel(self.root)
        popup.title("Flow State Trends")
        popup.geometry("400x300")
        
        text_widget = scrolledtext.ScrolledText(popup, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        trend_text = "=== 30-Minute Trends ===\n\n"
        trend_text += f"Average Flow Score: {trends['avg_flow_score']:.1f}\n"
        trend_text += f"Time in Flow: {trends['flow_percentage']:.1f}%\n"
        trend_text += f"Time in Deep Flow: {trends['deep_flow_percentage']:.1f}%\n"
        trend_text += f"Trend Direction: {trends['trend']}\n"
        trend_text += f"Samples: {trends['samples']}\n"
        
        text_widget.insert(tk.END, trend_text)
        text_widget.config(state=tk.DISABLED)
    
    def quit_app(self):
        """Quit the application"""
        self.running = False
        self.eye_defender.stop()
        self.flow_monitor.stop()
        self.root.quit()
    
    def run(self):
        """Run the GUI main loop"""
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.root.mainloop()
