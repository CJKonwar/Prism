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


class NotificationGUI:
    """
    GUI for displaying filtered notifications and flow state information
    """
    
    def __init__(self, flow_amplifier, flow_monitor):
        """
        Initialize the GUI
        
        Args:
            flow_amplifier: FlowAmplifier instance
            flow_monitor: FlowMonitorSystem instance
        """
        self.flow_amplifier = flow_amplifier
        self.flow_monitor = flow_monitor
        
        self.root = tk.Tk()
        self.root.title("Prism - Flow State Monitor")
        self.root.geometry("900x700")
        
        # Configure styles
        self.setup_styles()
        
        # Create UI
        self.create_ui()
        
        # Register callbacks
        self.flow_amplifier.add_notification_callback(self.on_notification)
        
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
        self.flow_monitor.stop()
        self.root.quit()
    
    def run(self):
        """Run the GUI main loop"""
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.root.mainloop()
