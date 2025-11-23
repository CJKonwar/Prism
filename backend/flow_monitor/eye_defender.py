"""
Eye Defender - 20-20-20 Rule Implementation
Helps prevent digital eye strain by blurring screen periodically
"""

import time
from threading import Thread, Lock
from datetime import datetime
try:
    from AppKit import NSScreen
    import Quartz
    import objc
except ImportError:
    print("Eye Defender requires pyobjc. Install with: pip install pyobjc")


class EyeDefender:
    """
    Implements the 20-20-20 rule for eye health
    Every X minutes, blur screen for Y seconds as a reminder to look away
    """
    
    def __init__(self, interval_minutes=1.0, blur_duration_seconds=20):
        """
        Initialize Eye Defender
        
        Args:
            interval_minutes: Minutes between reminders (default 20)
            blur_duration_seconds: How long to blur screen (default 20)
        """
        self.interval_minutes = interval_minutes
        self.blur_duration_seconds = blur_duration_seconds
        
        self.lock = Lock()
        self.running = False
        self.paused = False
        self.monitor_thread = None
        
        self.total_reminders = 0
        self.last_reminder_time = None
        self.time_remaining_seconds = 0  # Countdown timer
        self.blur_callback = None  # Callback to trigger blur on main thread
        self.blur_in_progress = False
        self.interval_changed = False  # Flag to reset timer when interval changes
        
    def set_interval(self, minutes):
        """Update reminder interval (accepts float for fractional minutes)"""
        with self.lock:
            old_interval = self.interval_minutes
            self.interval_minutes = float(minutes)
            # Signal to restart timer if Eye Defender is running
            if self.running and old_interval != self.interval_minutes:
                self.interval_changed = True
    
    def set_blur_duration(self, seconds):
        """Update blur duration"""
        with self.lock:
            self.blur_duration_seconds = seconds
    
    def set_blur_callback(self, callback):
        """Set callback function to trigger blur screen on main thread"""
        self.blur_callback = callback
    
    def get_settings(self):
        """Get current settings"""
        with self.lock:
            return {
                'interval_minutes': self.interval_minutes,
                'blur_duration_seconds': self.blur_duration_seconds,
                'total_reminders': self.total_reminders,
                'last_reminder': self.last_reminder_time,
                'is_running': self.running,
                'is_paused': self.paused,
                'time_remaining_seconds': self.time_remaining_seconds
            }
    
    def blur_screen(self):
        """Blur the screen using a semi-transparent overlay and show notification"""
        try:
            import subprocess
            import tkinter as tk
            from tkinter import ttk
            
            # Track reminder first
            with self.lock:
                self.total_reminders += 1
                self.last_reminder_time = datetime.now()
            
            print(f"\n  Eye Defender: Take a {self.blur_duration_seconds}s break!")
            print(f"   Look at something 20 feet away...")
            
            # Create blur overlay window
            blur_window = tk.Tk()
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
                                  text="Eye Break Time!", 
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
                                      text=f"{self.blur_duration_seconds}",
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
            remaining = [self.blur_duration_seconds]
            
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
            
            def fade_out():
                """Gradually fade out and close"""
                current_alpha = blur_window.attributes('-alpha')
                if current_alpha > 0:
                    blur_window.attributes('-alpha', current_alpha - 0.1)
                    blur_window.after(50, fade_out)
                else:
                    blur_window.destroy()
            
            def skip_break(event=None):
                """Allow user to skip the break"""
                blur_window.destroy()
            
            # Bind ESC key to skip
            blur_window.bind('<Escape>', skip_break)
            
            # Start fade in and countdown
            blur_window.after(100, fade_in)
            blur_window.after(1000, update_countdown)
            
            # Play sound notification
            sound_script = f'''
            display notification "Look 20 feet away for {self.blur_duration_seconds} seconds" ¬
                with title "Eye Break Time!" ¬
                sound name "Glass"
            '''
            subprocess.Popen(['osascript', '-e', sound_script], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
            
            # Run the blur window
            blur_window.mainloop()
            
        except Exception as e:
            print(f"Eye Defender error: {e}")
            # Fallback to just notification
            try:
                import subprocess
                script = f'''
                display notification "Look 20 feet away for {self.blur_duration_seconds} seconds" ¬
                    with title "Eye Break Time!" ¬
                    sound name "Glass"
                '''
                subprocess.run(['osascript', '-e', script], 
                             capture_output=True, timeout=5)
            except:
                pass
    
    def monitor_loop(self):
        """Main monitoring loop"""
        print(f"Eye Defender monitoring started. First reminder in {self.interval_minutes} minutes...")
        
        while self.running:
            try:
                if not self.paused:
                    # Wait for interval (checking every second to allow for stop/pause)
                    interval_seconds = self.interval_minutes * 60
                    elapsed = 0
                    
                    # Update time remaining and countdown
                    with self.lock:
                        self.time_remaining_seconds = interval_seconds
                    
                    while elapsed < interval_seconds and self.running and not self.paused:
                        time.sleep(1)
                        elapsed += 1
                        
                        # Check if interval was changed - restart timer
                        with self.lock:
                            if self.interval_changed:
                                self.interval_changed = False
                                print(f"Interval changed - restarting timer with {self.interval_minutes} minutes...")
                                break  # Exit inner loop to restart with new interval
                            self.time_remaining_seconds = interval_seconds - elapsed
                        
                        # If interval changed, skip to next cycle
                        if elapsed < interval_seconds and not self.running:
                            break
                    
                    if self.running and not self.paused:
                        # Trigger reminder via callback (on main thread)
                        print(f"{self.interval_minutes} minutes passed - triggering eye break...")
                        with self.lock:
                            self.time_remaining_seconds = 0
                            self.total_reminders += 1
                            self.last_reminder_time = datetime.now()
                            self.blur_in_progress = True
                        
                        # Trigger blur via callback if set
                        if self.blur_callback:
                            self.blur_callback()
                        else:
                            # Fallback: just show notification
                            self._show_notification_only()
                        
                        # Wait for blur duration
                        time.sleep(self.blur_duration_seconds + 2)  # +2 for fade animations
                        with self.lock:
                            self.blur_in_progress = False
                else:
                    # Check every second if paused
                    time.sleep(1)
                    
            except Exception as e:
                print(f"Error in Eye Defender loop: {e}")
                time.sleep(5)
    
    def start(self):
        """Start eye defender monitoring"""
        if self.running:
            return
        
        print("\n" + "="*60)
        print("EYE DEFENDER ACTIVATED")
        print("="*60)
        print(f"\nReminder Interval: Every {self.interval_minutes} minutes")
        print(f"Break Duration: {self.blur_duration_seconds} seconds")
        print("\nYou'll be reminded to look away from your screen")
        print("to prevent digital eye strain.")
        print("="*60 + "\n")
        
        self.running = True
        self.paused = False
        self.monitor_thread = Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop(self):
        """Stop eye defender monitoring"""
        if not self.running:
            return
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=3)
        
        print("\n" + "="*60)
        print("EYE DEFENDER DEACTIVATED")
        print("="*60)
        print(f"\nSession Statistics:")
        print(f"   Total reminders: {self.total_reminders}")
        if self.last_reminder_time:
            print(f"   Last reminder: {self.last_reminder_time.strftime('%H:%M:%S')}")
        print("="*60 + "\n")
    
    def pause(self):
        """Pause reminders temporarily"""
        with self.lock:
            self.paused = True
        print("Eye Defender paused")
    
    def resume(self):
        """Resume reminders"""
        with self.lock:
            self.paused = False
        print("Eye Defender resumed")
    
    def trigger_manual_break(self):
        """Manually trigger an eye break"""
        if self.running and self.blur_callback:
            print("Manual eye break triggered")
            with self.lock:
                self.total_reminders += 1
                self.last_reminder_time = datetime.now()
            self.blur_callback()
            return True
        return False
    
    def _show_notification_only(self):
        """Show notification without blur overlay (fallback)"""
        try:
            import subprocess
            sound_script = f'''
            display notification "Look 20 feet away for {self.blur_duration_seconds} seconds" ¬
                with title "Eye Break Time!" ¬
                sound name "Glass"
            '''
            subprocess.Popen(['osascript', '-e', sound_script], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        except:
            pass
