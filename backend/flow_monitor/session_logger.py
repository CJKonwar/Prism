"""
Session Logger
Saves comprehensive session summaries to JSON file every minute
"""

import json
import os
from datetime import datetime
from threading import Thread, Lock
import time


class SessionLogger:
    """
    Logs session data including flow state, mood, and activity metrics
    """
    
    def __init__(self, flow_monitor, output_dir=None, log_interval=30):
        """
        Initialize the session logger
        
        Args:
            flow_monitor: FlowMonitorSystem instance
            output_dir: Directory to save logs (defaults to parent of backend folder)
            log_interval: Seconds between log saves (default: 60 = 1 minute)
        """
        self.flow_monitor = flow_monitor
        self.log_interval = log_interval
        
        # Set output directory to parent of backend folder if not specified
        if output_dir is None:
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.output_dir = os.path.join(os.path.dirname(backend_dir), 'session_logs')
        else:
            self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Session tracking
        self.session_start_time = datetime.now()
        self.session_id = self.session_start_time.strftime('%Y%m%d_%H%M%S')
        self.log_file = os.path.join(self.output_dir, f'session_{self.session_id}.json')
        
        # Threading
        self.running = False
        self.lock = Lock()
        self.log_thread = None
        
        # Session data accumulator - only store aggregated data, not snapshots
        self.session_data = {
            'session_id': self.session_id,
            'start_time': self.session_start_time.isoformat(),
            'end_time': None,
            'duration_seconds': 0
        }
        
        # Accumulators for statistics
        self.flow_scores = []
        self.state_counts = {}
        self.state_durations = {}
        self.typing_cadences = []
        self.mouse_movements = []
        self.task_switches = []
        self.mood_counts = {}
        self.mood_stats = {'frustration': 0, 'stress': 0, 'positive': 0}
        self.app_usage = {}
        self.update_count = 0
        
        print(f"Session logger initialized")
        print(f"   Log file: {self.log_file}")
    
    def start(self):
        """Start the session logger"""
        if self.running:
            print("Session logger already running")
            return
        
        self.running = True
        self.log_thread = Thread(target=self._log_loop, daemon=True)
        self.log_thread.start()
        print("Session logger started")
    
    def stop(self):
        """Stop the session logger and save final snapshot"""
        if not self.running:
            return
        
        self.running = False
        
        # Save one final snapshot before stopping
        self._save_snapshot()
        
        # Update session end time
        with self.lock:
            self.session_data['end_time'] = datetime.now().isoformat()
            self.session_data['duration_seconds'] = (
                datetime.now() - self.session_start_time
            ).total_seconds()
        
        # Save final file
        self._save_to_file()
        print("Session logger stopped")
    
    def _log_loop(self):
        """Main logging loop"""
        while self.running:
            try:
                self._save_snapshot()
                time.sleep(self.log_interval)
            except Exception as e:
                print(f"Error in session logger: {e}")
                import traceback
                traceback.print_exc()
    
    def _save_snapshot(self):
        """Capture and accumulate current metrics, then save summary"""
        try:
            # Get all metrics from flow monitor
            metrics = self.flow_monitor.get_detailed_metrics()
            flow_state = self.flow_monitor.get_current_state()
            
            with self.lock:
                self.update_count += 1
                
                # Accumulate flow scores
                self.flow_scores.append(flow_state.get('flow_score', 0))
                
                # Track state counts and durations
                state = flow_state.get('flow_state', 'UNKNOWN')
                self.state_counts[state] = self.state_counts.get(state, 0) + 1
                self.state_durations[state] = self.state_durations.get(state, 0) + flow_state.get('flow_duration', 0)
                
                # Accumulate activity metrics
                self.typing_cadences.append(metrics['keyboard']['typing_cadence'])
                self.mouse_movements.append(metrics['mouse']['mouse_move_rate'])
                self.task_switches.append(metrics['window']['task_switch_frequency'])
                
                # Track app usage
                current_app = metrics['window']['current_app']
                self.app_usage[current_app] = self.app_usage.get(current_app, 0) + 1
                
                # Accumulate mood data if available
                if 'mood' in metrics:
                    current_emotion = metrics.get('mood_current', {}).get('emotion', 'unknown')
                    self.mood_counts[current_emotion] = self.mood_counts.get(current_emotion, 0) + 1
                    
                    # Store cumulative alert counts from mood monitor
                    self.mood_stats['frustration'] = metrics['mood'].get('frustration_count', 0)
                    self.mood_stats['stress'] = metrics['mood'].get('stress_count', 0)
                    self.mood_stats['positive'] = metrics['mood'].get('positive_count', 0)
                    
                    # Store all emotion counts from mood monitor
                    if 'emotion_counts' in metrics['mood']:
                        for emotion, count in metrics['mood']['emotion_counts'].items():
                            if emotion not in self.mood_counts:
                                self.mood_counts[emotion] = 0
                            # Update with latest count from monitor
                            if count > self.mood_counts.get(emotion, 0):
                                self.mood_counts[emotion] = count
            
            # Save summary to file
            self._save_to_file()
            
            print(f"Session updated (update #{self.update_count})")
            
        except Exception as e:
            print(f"Error saving snapshot: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_to_file(self):
        """Save session summary to JSON file"""
        try:
            with self.lock:
                # Calculate session duration
                session_duration = (datetime.now() - self.session_start_time).total_seconds()
                duration_minutes = session_duration / 60
                
                # Update session data
                self.session_data['end_time'] = datetime.now().isoformat()
                self.session_data['duration_seconds'] = round(session_duration, 2)
                
                if self.update_count > 0:
                    # Flow score statistics
                    avg_flow_score = sum(self.flow_scores) / len(self.flow_scores) if self.flow_scores else 0
                    max_flow_score = max(self.flow_scores) if self.flow_scores else 0
                    min_flow_score = min(self.flow_scores) if self.flow_scores else 0
                    
                    # Calculate state percentages
                    total_updates = self.update_count
                    state_percentages = {
                        state: (count / total_updates * 100) 
                        for state, count in self.state_counts.items()
                    }
                    
                    # Activity metrics averages
                    avg_typing = sum(self.typing_cadences) / len(self.typing_cadences) if self.typing_cadences else 0
                    avg_mouse = sum(self.mouse_movements) / len(self.mouse_movements) if self.mouse_movements else 0
                    avg_switches = sum(self.task_switches) / len(self.task_switches) if self.task_switches else 0
                    
                    # Mood distribution
                    mood_percentages = {}
                    if self.mood_counts:
                        total_mood = sum(self.mood_counts.values())
                        mood_percentages = {
                            emotion: (count / total_mood * 100)
                            for emotion, count in self.mood_counts.items()
                        }
                    
                    # Top apps
                    top_apps = sorted(self.app_usage.items(), key=lambda x: x[1], reverse=True)[:5]
                    
                    # Productivity score
                    productivity_score = (
                        self.state_counts.get('DEEP_FLOW', 0) * 100 +
                        self.state_counts.get('FLOW', 0) * 80 +
                        self.state_counts.get('FOCUSED', 0) * 60 +
                        self.state_counts.get('WORKING', 0) * 40 +
                        self.state_counts.get('DISTRACTED', 0) * 10
                    ) / total_updates if total_updates > 0 else 0
                    
                    # Build comprehensive summary
                    self.session_data['summary'] = {
                        'session_info': {
                            'total_updates': self.update_count,
                            'duration_seconds': round(session_duration, 2),
                            'duration_minutes': round(duration_minutes, 2),
                            'last_updated': datetime.now().isoformat()
                        },
                        'flow_state_analysis': {
                            'avg_flow_score': round(avg_flow_score, 2),
                            'max_flow_score': round(max_flow_score, 2),
                            'min_flow_score': round(min_flow_score, 2),
                            'productivity_score': round(productivity_score, 2),
                            'state_distribution': self.state_counts,
                            'state_percentages': {k: round(v, 2) for k, v in state_percentages.items()},
                            'state_durations_seconds': {k: round(v, 2) for k, v in self.state_durations.items()}
                        },
                        'activity_metrics': {
                            'avg_typing_cadence_keys_per_min': round(avg_typing, 2),
                            'avg_mouse_movement_per_min': round(avg_mouse, 2),
                            'avg_task_switches_per_min': round(avg_switches, 2)
                        },
                        'mood_analysis': {
                            'all_emotions': {
                                'happy': self.mood_counts.get('happy', 0),
                                'sad': self.mood_counts.get('sad', 0),
                                'angry': self.mood_counts.get('angry', 0),
                                'fear': self.mood_counts.get('fear', 0),
                                'surprise': self.mood_counts.get('surprise', 0),
                                'disgust': self.mood_counts.get('disgust', 0),
                                'neutral': self.mood_counts.get('neutral', 0)
                            },
                            'emotion_percentages': {k: round(v, 2) for k, v in mood_percentages.items()},
                            'alerts': {
                                'frustration_count': self.mood_stats['frustration'],
                                'stress_count': self.mood_stats['stress'],
                                'positive_count': self.mood_stats['positive']
                            },
                            'dominant_emotion': max(self.mood_counts.items(), key=lambda x: x[1])[0] if self.mood_counts else 'none'
                        } if self.mood_counts else {
                            'note': 'Mood monitoring not active or no emotions detected'
                        },
                        'app_usage': {
                            'total_apps_used': len(self.app_usage),
                            'top_5_apps': [
                                {
                                    'app': app, 
                                    'count': count, 
                                    'percentage': round(count/total_updates*100, 2)
                                } 
                                for app, count in top_apps
                            ],
                            'all_apps': self.app_usage
                        }
                    }
                else:
                    # No data collected yet
                    self.session_data['summary'] = {
                        'session_info': {
                            'total_updates': 0,
                            'duration_seconds': round(session_duration, 2),
                            'duration_minutes': round(duration_minutes, 2),
                            'last_updated': datetime.now().isoformat(),
                            'note': 'Session active but no data collected yet. Wait for first update.'
                        }
                    }
                
                # Write to file
                with open(self.log_file, 'w') as f:
                    json.dump(self.session_data, f, indent=2)
                    
        except Exception as e:
            print(f"Error writing to log file: {e}")
            import traceback
            traceback.print_exc()
    
    def get_log_file_path(self):
        """Get the path to the current log file"""
        return self.log_file
    
    def get_session_summary(self):
        """Get current session summary"""
        with self.lock:
            return self.session_data.get('summary', {})
