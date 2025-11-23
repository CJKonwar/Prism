"""
AI Assistant using Gemini
Analyzes session data and provides intelligent interventions
"""

import json
import os
import time
from datetime import datetime
from threading import Thread, Lock
from google import genai
from google.genai import types
from dotenv import load_dotenv


load_dotenv()


class AIAssistant:
    """
    AI-powered assistant that monitors session data and suggests interventions
    """
    
    def __init__(self, session_logger, check_interval=30):
        """
        Initialize AI Assistant
        
        Args:
            session_logger: SessionLogger instance
            check_interval: Seconds between checks (default: 30)
        """
        self.session_logger = session_logger
        self.check_interval = check_interval
        
        # Gemini client
        self.client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))
        
        # Define available system tools
        self.system_tools = self._define_system_tools()
        
        # Configure Gemini with tools
        self.tools = types.Tool(function_declarations=self.system_tools)
        self.config = types.GenerateContentConfig(tools=[self.tools])
        
        # Threading
        self.running = False
        self.lock = Lock()
        self.ai_thread = None
        
        # Callbacks for system actions
        self.action_callbacks = {}
        
        # Analysis history
        self.analysis_history = []
        
        # Conversation history for context continuity
        self.conversation_history = []
        
        # Music playback state
        self.music_playing = False
        self.music_process = None
        
        print("AI Assistant initialized with Gemini")
        print(f"   Available tools: {len(self.system_tools)}")
    
    def _define_system_tools(self):
        """Define available system tools for Gemini"""
        return [
            {
                "name": "show_suggestion_notification",
                "description": "**PRIMARY TOOL** - ALWAYS use this tool for ALL recommendations. Shows a notification popup with a suggestion. The user can choose to accept or dismiss. NEVER call other action tools directly - always use this notification tool instead.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Title of the notification (e.g., 'Stress Detected', 'Low Focus Alert')"
                        },
                        "message": {
                            "type": "string",
                            "description": "Main message explaining the situation and suggestion"
                        },
                        "suggestion_type": {
                            "type": "string",
                            "enum": ["breathing_exercise", "eye_break", "calm_music", "dnd_mode", "take_break", "block_app", "encouragement"],
                            "description": "Type of suggestion to offer"
                        },
                        "action_params": {
                            "type": "object",
                            "description": "Parameters to pass to the action if user accepts (e.g., duration, app_name, etc.)"
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["info", "warning", "urgent"],
                            "description": "Severity level affects notification styling",
                            "default": "info"
                        }
                    },
                    "required": ["title", "message", "suggestion_type"]
                }
            },
            {
                "name": "start_breathing_exercise",
                "description": "[INTERNAL USE ONLY - Called by notification system] Triggers the interactive breathing meditation game to help user relax and refocus. DO NOT call this directly - use show_suggestion_notification instead.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for suggesting breathing exercise (e.g., 'high stress detected', 'low flow score')"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Suggested duration in minutes (1-5)",
                            "default": 2
                        }
                    },
                    "required": ["reason"]
                }
            },
            {
                "name": "trigger_eye_break",
                "description": "[INTERNAL USE ONLY - Called by notification system] Triggers the 20-20-20 eye break screen. DO NOT call this directly - use show_suggestion_notification instead.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for eye break (e.g., 'extended screen time', 'preventing eye strain')"
                        },
                        "duration_seconds": {
                            "type": "integer",
                            "description": "Duration of break in seconds (10-60)",
                            "default": 20
                        }
                    },
                    "required": ["reason"]
                }
            },
            {
                "name": "play_calm_music",
                "description": "[INTERNAL USE ONLY - Called by notification system] Plays soothing calm music. DO NOT call this directly - use show_suggestion_notification instead.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for playing music (e.g., 'enhancing focus', 'reducing stress')"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "How long to play (5-30 minutes)",
                            "default": 0.1
                        }
                    },
                    "required": ["reason"]
                }
            },
            {
                "name": "enable_do_not_disturb",
                "description": "[INTERNAL USE ONLY - Called by notification system] Enables Do Not Disturb mode. DO NOT call this directly - use show_suggestion_notification instead.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for DND (e.g., 'entering flow state', 'high distraction detected')"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "How long to enable DND (15-120 minutes)",
                            "default": 60
                        }
                    },
                    "required": ["reason"]
                }
            },
            {
                "name": "suggest_break",
                "description": "[INTERNAL USE ONLY - Called by notification system] Suggests a break. DO NOT call this directly - use show_suggestion_notification instead.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for break suggestion (e.g., 'low flow score detected', 'extended work session')"
                        },
                        "break_type": {
                            "type": "string",
                            "enum": ["short_break", "long_break", "walk_break", "stretch_break"],
                            "description": "Type of break to suggest"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Suggested break duration (5-30 minutes)",
                            "default": 10
                        }
                    },
                    "required": ["reason", "break_type"]
                }
            },
            {
                "name": "banish_distracting_app",
                "description": "[INTERNAL USE ONLY - Called by notification system] Blocks a distracting app. DO NOT call this directly - use show_suggestion_notification instead.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "app_name": {
                            "type": "string",
                            "description": "Name of the app to banish"
                        },
                        "reason": {
                            "type": "string",
                            "description": "Reason for banishing (e.g., 'frequent switching detected', 'distraction source')"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "How long to keep app banished (15-120 minutes)",
                            "default": 30
                        }
                    },
                    "required": ["app_name", "reason"]
                }
            },
            {
                "name": "provide_encouragement",
                "description": "[INTERNAL USE ONLY - Called by notification system] Displays encouragement. DO NOT call this directly - use show_suggestion_notification instead.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Encouraging message to display"
                        },
                        "context": {
                            "type": "string",
                            "description": "Context for encouragement (e.g., 'high flow achievement', 'consistency milestone')"
                        }
                    },
                    "required": ["message", "context"]
                }
            }
        ]
    
    def register_callback(self, tool_name, callback):
        """
        Register callback for tool execution
        
        Args:
            tool_name: Name of the tool
            callback: Function to call when tool is triggered
        """
        self.action_callbacks[tool_name] = callback
        print(f"Registered callback for: {tool_name}")
    
    def start(self):
        """Start the AI assistant"""
        if self.running:
            print("AI Assistant already running")
            return
        
        self.running = True
        self.ai_thread = Thread(target=self._analysis_loop, daemon=True)
        self.ai_thread.start()
        print("AI Assistant started")
    
    def stop(self):
        """Stop the AI assistant"""
        if not self.running:
            return
        
        self.running = False
        print("AI Assistant stopped")
    
    def _analysis_loop(self):
        """Main analysis loop"""
        while self.running:
            try:
                self._analyze_session_and_act()
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"Error in AI Assistant: {e}")
                import traceback
                traceback.print_exc()
    
    def _analyze_session_and_act(self):
        """Analyze current session data and take actions"""
        try:
            # Get session log file path
            log_file = self.session_logger.get_log_file_path()
            
            if not os.path.exists(log_file):
                print("Session log file not found yet")
                return
            
            # Read session data with error handling
            try:
                with open(log_file, 'r') as f:
                    content = f.read()
                    if not content.strip():
                        print("Session log file is empty")
                        return
                    session_data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON in session log file: {e}")
                print("The file may be corrupted or still being written. Skipping this analysis.")
                return
            except Exception as e:
                print(f"Error reading session log file: {e}")
                return
            
            if 'summary' not in session_data:
                print("Session summary not available yet")
                return
            
            summary = session_data['summary']
            
            # Build context for Gemini
            context = self._build_context(summary)
            
            # Build conversation history context
            history_context = ""
            if self.conversation_history:
                recent_history = self.conversation_history[-5:]  # Last 5 interactions
                history_context = "\n\nRecent Interaction History:\n"
                for idx, interaction in enumerate(recent_history, 1):
                    history_context += f"{idx}. [{interaction['timestamp']}] {interaction['action']}"
                    if 'title' in interaction.get('arguments', {}):
                        history_context += f" - {interaction['arguments']['title']}"
                    history_context += "\n"
            
            # Ask Gemini for recommendations
            prompt = f"""You are an AI productivity assistant monitoring a user's work session in real-time. 

Current Session Data:
{json.dumps(context, indent=2)}{history_context}

CRITICAL INSTRUCTION: You MUST use ONLY the 'show_suggestion_notification' tool for ALL recommendations. 

The other tools (start_breathing_exercise, trigger_eye_break, etc.) are marked as [INTERNAL USE ONLY] and should NEVER be called by you directly. They are executed automatically when the user accepts a notification.

Your ONLY allowed action is: show_suggestion_notification

Based on this data, analyze the user's current state and create ONE notification suggestion.

Consider:
- Flow state and productivity scores (avg < 40 = low, > 70 = high)
- Mood and emotional state (angry/frustrated = stress, happy = positive)
- Activity levels (low typing/mouse = inactive, high task switching = distracted)
- Time in session and app usage patterns
- Signs of stress, fatigue, or distraction

Examples:
- If mood shows "angry" with frustration alerts → show_suggestion_notification with title="Extreme Frustration Detected", suggestion_type="breathing_exercise" or "calm_music", severity="urgent"
- If stress/negative emotions detected → show_suggestion_notification with suggestion_type="calm_music" to help user relax with soothing music
- If low flow score (< 40) for extended period → show_suggestion_notification with suggestion_type="take_break" or "dnd_mode"
- If extended screen time (> 60 min) → show_suggestion_notification with suggestion_type="eye_break"
- If everything is good → show_suggestion_notification with suggestion_type="encouragement"

Music Feature: Use suggestion_type="calm_music" when detecting frustration, anger, stress, or anxiety to play calming music from assets folder. Include action_params with duration_minutes (5-30).

Create clear, empathetic messages that explain WHY you're suggesting the action.

Respond by calling show_suggestion_notification tool."""

            # Call Gemini with tools
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=self.config,
            )
            
            # Check for function call
            if response.candidates[0].content.parts[0].function_call:
                function_call = response.candidates[0].content.parts[0].function_call
                
                print(f"\nAI Recommendation:")
                print(f"   Action: {function_call.name}")
                print(f"   Arguments: {dict(function_call.args)}")
                
                # Log analysis
                analysis = {
                    'timestamp': datetime.now().isoformat(),
                    'action': function_call.name,
                    'arguments': dict(function_call.args),
                    'context': context
                }
                
                with self.lock:
                    self.analysis_history.append(analysis)
                    # Also track in conversation history (without full context)
                    self.conversation_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'action': function_call.name,
                        'arguments': dict(function_call.args)
                    })
                
                # Execute action if callback registered
                if function_call.name in self.action_callbacks:
                    try:
                        self.action_callbacks[function_call.name](**dict(function_call.args))
                        print(f"   Action executed")
                    except Exception as e:
                        print(f"   Error executing action: {e}")
                else:
                    print(f"   No callback registered for: {function_call.name}")
            else:
                print("\nAI Analysis: No specific action needed")
                if hasattr(response, 'text'):
                    print(f"   {response.text}")
                    
        except Exception as e:
            print(f"Error analyzing session: {e}")
            import traceback
            traceback.print_exc()
    
    def _build_context(self, summary):
        """Build context from session summary"""
        context = {
            'session_duration_minutes': summary.get('session_info', {}).get('duration_minutes', 0),
            'total_updates': summary.get('session_info', {}).get('total_updates', 0)
        }
        
        # Flow state analysis
        if 'flow_state_analysis' in summary:
            flow = summary['flow_state_analysis']
            context['flow_state'] = {
                'avg_score': flow.get('avg_flow_score', 0),
                'productivity_score': flow.get('productivity_score', 0),
                'current_state_distribution': flow.get('state_distribution', {}),
                'state_percentages': flow.get('state_percentages', {})
            }
        
        # Activity metrics
        if 'activity_metrics' in summary:
            activity = summary['activity_metrics']
            context['activity'] = {
                'typing_cadence': activity.get('avg_typing_cadence_keys_per_min', 0),
                'mouse_movement': activity.get('avg_mouse_movement_per_min', 0),
                'task_switches': activity.get('avg_task_switches_per_min', 0)
            }
        
        # Mood analysis
        if 'mood_analysis' in summary and 'note' not in summary['mood_analysis']:
            mood = summary['mood_analysis']
            context['mood'] = {
                'emotions': mood.get('all_emotions', {}),
                'dominant_emotion': mood.get('dominant_emotion', 'unknown'),
                'alerts': mood.get('alerts', {})
            }
        
        # App usage
        if 'app_usage' in summary:
            apps = summary['app_usage']
            context['app_usage'] = {
                'total_apps': apps.get('total_apps_used', 0),
                'top_app': apps.get('top_5_apps', [{}])[0] if apps.get('top_5_apps') else {}
            }
        
        return context
    
    def get_analysis_history(self):
        """Get history of AI recommendations"""
        with self.lock:
            return self.analysis_history.copy()
    
    def get_conversation_history(self):
        """Get conversation history"""
        with self.lock:
            return self.conversation_history.copy()
    
    def play_calm_music(self, reason="stress relief", duration_minutes=0.1):
        """Play calm music from assets folder"""
        try:
            if self.music_playing:
                print("Music already playing")
                return
            
            # Get path to music file
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            music_path = os.path.join(backend_dir, 'assets', 'music_reco.mp3')
            
            if not os.path.exists(music_path):
                print(f"Music file not found: {music_path}")
                return
            
            print(f"Playing calm music for {reason}...")
            
            try:
                import pygame
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play()
                self.music_playing = True
                print(f"Calm music playing (pygame) - Duration: {duration_minutes} min")
                
                # Schedule stop after duration
                def stop_music():
                    time.sleep(duration_minutes * 60)
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.stop()
                    self.music_playing = False
                    print("Calm music stopped")
                
                Thread(target=stop_music, daemon=True).start()
                
            except ImportError:
                # Fallback to system player on macOS
                import subprocess
                self.music_process = subprocess.Popen(
                    ['afplay', music_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.music_playing = True
                print(f"Calm music playing (afplay) - Duration: {duration_minutes} min")
                
                # Schedule stop after duration
                def stop_afplay():
                    time.sleep(duration_minutes * 60)
                    if self.music_process:
                        self.music_process.terminate()
                    self.music_playing = False
                    print("Calm music stopped")
                
                Thread(target=stop_afplay, daemon=True).start()
                
        except Exception as e:
            print(f"Error playing music: {e}")
            import traceback
            traceback.print_exc()
    
    def stop_music(self):
        """Stop currently playing music"""
        try:
            import pygame
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                print("Music stopped (pygame)")
        except:
            pass
        
        if self.music_process:
            self.music_process.terminate()
            self.music_process = None
            print("Music stopped (afplay)")
        
        self.music_playing = False
    
    def save_analysis_log(self, output_dir=None):
        """Save analysis history to file"""
        if output_dir is None:
            output_dir = os.path.dirname(self.session_logger.get_log_file_path())
        
        log_file = os.path.join(
            output_dir, 
            f'ai_analysis_{self.session_logger.session_id}.json'
        )
        
        with self.lock:
            with open(log_file, 'w') as f:
                json.dump({
                    'session_id': self.session_logger.session_id,
                    'total_recommendations': len(self.analysis_history),
                    'recommendations': self.analysis_history,
                    'conversation_history': self.conversation_history
                }, f, indent=2)
        
        print(f"AI analysis log saved: {log_file}")
        return log_file
