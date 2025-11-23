"""
Mood Monitor - Real-time emotion detection using webcam
Integrates with Flow State Detection System
"""

import cv2
import time
from threading import Thread, Lock
from collections import deque
from datetime import datetime


class MoodMonitor:
    """
    Monitors user's mood/emotion via webcam using DeepFace
    Tracks emotional state to enhance flow state detection
    """
    
    def __init__(self, check_interval=5):
        """
        Initialize mood monitor
        
        Args:
            check_interval: Seconds between emotion checks (default: 5)
        """
        self.check_interval = check_interval
        self.cap = None
        self.running = False
        self.monitor_thread = None
        
        self.lock = Lock()
        self.current_mood = "neutral"
        self.last_check = 0
        
        # Mood history for trends
        self.mood_history = deque(maxlen=100)
        
        # Mood categories and their flow impact
        self.mood_categories = {
            'positive': ['happy', 'neutral'],
            'focused': ['neutral'],
            'frustrated': ['angry', 'disgust'],
            'stressed': ['fear', 'sad'],
            'disengaged': ['surprise']
        }
        
        # Counters
        self.total_checks = 0
        self.frustration_count = 0
        self.positive_count = 0
        
        # Callbacks for mood changes
        self.mood_callbacks = []
        
    def add_mood_callback(self, callback):
        """Add callback function for mood changes"""
        self.mood_callbacks.append(callback)
    
    def _trigger_callbacks(self, mood_data):
        """Trigger all registered callbacks"""
        for callback in self.mood_callbacks:
            try:
                callback(mood_data)
            except Exception as e:
                print(f"Error in mood callback: {e}")
    
    def analyze_frame(self, frame):
        """
        Analyze frame for emotion using DeepFace
        
        Args:
            frame: OpenCV frame/image
            
        Returns:
            str: Detected emotion or "No Face"
        """
        try:
            # Lazy import to avoid loading heavy libraries if not used
            from deepface import DeepFace
            
            # DeepFace analyzes the image for emotion
            # enforce_detection=False prevents crash if face is not found
            analysis = DeepFace.analyze(frame, actions=['emotion'], 
                                      enforce_detection=False, silent=True)
            
            # DeepFace returns a list of dicts. Get the first face.
            if isinstance(analysis, list):
                return analysis[0]['dominant_emotion']
            else:
                return analysis['dominant_emotion']
        except ImportError:
            print("DeepFace not installed. Install with: pip install deepface")
            return "unavailable"
        except Exception as e:
            # Silently handle errors (no face, bad frame, etc.)
            return "no_face"
    
    def monitor_loop(self):
        """Main monitoring loop"""
        print("Mood Monitor starting...")
        
        # Initialize webcam
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                print("Could not open webcam")
                self.running = False
                return
        except Exception as e:
            print(f"Error opening webcam: {e}")
            self.running = False
            return
        
        print("Webcam initialized")
        
        while self.running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(1)
                    continue
                
                # Check emotion at intervals
                current_time = time.time()
                if current_time - self.last_check >= self.check_interval:
                    emotion = self.analyze_frame(frame)
                    
                    if emotion not in ["no_face", "unavailable"]:
                        self._process_emotion(emotion)
                        self.last_check = current_time
                    
            except Exception as e:
                print(f"Error in mood monitor loop: {e}")
                time.sleep(5)
        
        # Cleanup
        if self.cap:
            self.cap.release()
        print("Mood monitor stopped")
    
    def _process_emotion(self, emotion):
        """Process detected emotion and trigger appropriate responses"""
        with self.lock:
            old_mood = self.current_mood
            self.current_mood = emotion
            self.total_checks += 1
            
            # Record in history
            self.mood_history.append({
                'emotion': emotion,
                'timestamp': time.time(),
                'datetime': datetime.now()
            })
            
            # Update counters
            if emotion in ['angry', 'disgust']:
                self.frustration_count += 1
            elif emotion in ['happy', 'neutral']:
                self.positive_count += 1
            
            # Prepare mood data
            mood_data = {
                'emotion': emotion,
                'category': self._categorize_mood(emotion),
                'timestamp': time.time(),
                'changed': emotion != old_mood
            }
            
            # Trigger appropriate response
            if emotion in ['angry', 'disgust']:
                print(f"Frustration detected ({emotion}). User may be stuck.")
                mood_data['alert'] = 'frustration'
                mood_data['suggestion'] = 'Take a break or try a different approach'
                
            elif emotion == 'neutral':
                if old_mood in ['angry', 'disgust', 'fear', 'sad']:
                    print(f"Mood improved: {old_mood} -> {emotion}")
                mood_data['alert'] = 'focused'
                
            elif emotion in ['fear', 'sad']:
                print(f"User appears {emotion}. May need encouragement.")
                mood_data['alert'] = 'stressed'
                mood_data['suggestion'] = 'Consider taking a short break'
                
            elif emotion == 'happy':
                print(f"Positive mood detected ({emotion})")
                mood_data['alert'] = 'positive'
            
            # Trigger callbacks
            self._trigger_callbacks(mood_data)
    
    def _categorize_mood(self, emotion):
        """Categorize emotion into broader categories"""
        for category, emotions in self.mood_categories.items():
            if emotion in emotions:
                return category
        return 'other'
    
    def get_current_mood(self):
        """Get current detected mood"""
        with self.lock:
            return {
                'emotion': self.current_mood,
                'category': self._categorize_mood(self.current_mood),
                'timestamp': self.last_check
            }
    
    def get_statistics(self):
        """Get mood monitoring statistics"""
        with self.lock:
            # Calculate mood distribution
            mood_counts = {}
            for entry in self.mood_history:
                emotion = entry['emotion']
                mood_counts[emotion] = mood_counts.get(emotion, 0) + 1
            
            # Calculate percentages
            total = len(self.mood_history)
            mood_percentages = {}
            if total > 0:
                for emotion, count in mood_counts.items():
                    mood_percentages[emotion] = (count / total) * 100
            
            return {
                'current_mood': self.current_mood,
                'total_checks': self.total_checks,
                'frustration_count': self.frustration_count,
                'positive_count': self.positive_count,
                'mood_distribution': mood_counts,
                'mood_percentages': mood_percentages,
                'history_size': len(self.mood_history)
            }
    
    def get_mood_trend(self, window_minutes=10):
        """
        Get mood trend over time window
        
        Args:
            window_minutes: Time window to analyze
            
        Returns:
            dict: Mood trend analysis
        """
        current_time = time.time()
        window_seconds = window_minutes * 60
        
        with self.lock:
            # Filter recent history
            recent = [entry for entry in self.mood_history
                     if current_time - entry['timestamp'] <= window_seconds]
            
            if not recent:
                return {
                    'trend': 'neutral',
                    'dominant_mood': 'neutral',
                    'frustration_level': 0
                }
            
            # Count emotions
            emotion_counts = {}
            for entry in recent:
                emotion = entry['emotion']
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            
            # Determine dominant mood
            dominant_mood = max(emotion_counts.items(), key=lambda x: x[1])[0]
            
            # Calculate frustration level
            frustration_emotions = ['angry', 'disgust', 'fear', 'sad']
            frustration_count = sum(emotion_counts.get(e, 0) for e in frustration_emotions)
            frustration_level = (frustration_count / len(recent)) * 100
            
            # Determine trend
            if frustration_level > 50:
                trend = 'declining'
            elif dominant_mood in ['happy', 'neutral']:
                trend = 'stable'
            else:
                trend = 'mixed'
            
            return {
                'trend': trend,
                'dominant_mood': dominant_mood,
                'frustration_level': frustration_level,
                'emotion_counts': emotion_counts,
                'sample_size': len(recent)
            }
    
    def start(self):
        """Start mood monitoring"""
        if self.running:
            print("Mood monitor already running")
            return
        
        print("\n" + "="*60)
        print("MOOD MONITOR ACTIVATED")
        print("="*60)
        print(f"\nCheck Interval: Every {self.check_interval} seconds")
        print("Monitoring facial expressions for emotional state...")
        print("="*60 + "\n")
        
        self.running = True
        self.monitor_thread = Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop(self):
        """Stop mood monitoring"""
        if not self.running:
            return
        
        print("\n" + "="*60)
        print("MOOD MONITOR DEACTIVATED")
        print("="*60)
        
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=3)
        
        # Print statistics
        stats = self.get_statistics()
        print(f"\nSession Statistics:")
        print(f"   Total Checks: {stats['total_checks']}")
        print(f"   Current Mood: {stats['current_mood']}")
        print(f"   Frustration Events: {stats['frustration_count']}")
        print(f"   Positive Moods: {stats['positive_count']}")
        
        if stats['mood_distribution']:
            print(f"\n   Mood Distribution:")
            for mood, count in stats['mood_distribution'].items():
                percentage = stats['mood_percentages'].get(mood, 0)
                print(f"      {mood}: {count} ({percentage:.1f}%)")
        
        print("="*60 + "\n")
    
    def reset(self):
        """Reset mood history and counters"""
        with self.lock:
            self.mood_history.clear()
            self.frustration_count = 0
            self.positive_count = 0
            self.total_checks = 0
            print("Mood monitor reset")


if __name__ == "__main__":
    """Test mood monitor standalone"""
    monitor = MoodMonitor(check_interval=3)
    
    def on_mood_change(mood_data):
        print(f"Mood Event: {mood_data['emotion']} ({mood_data['category']})")
        if 'alert' in mood_data:
            print(f"   Alert: {mood_data['alert']}")
        if 'suggestion' in mood_data:
            print(f"   Suggestion: {mood_data['suggestion']}")
    
    monitor.add_mood_callback(on_mood_change)
    
    try:
        monitor.start()
        
        print("\nMood monitor running... Press Ctrl+C to stop\n")
        
        while True:
            time.sleep(10)
            
            # Print periodic updates
            stats = monitor.get_statistics()
            trend = monitor.get_mood_trend(window_minutes=5)
            
            print(f"\nStatus Update:")
            print(f"   Current: {stats['current_mood']}")
            print(f"   Trend: {trend['trend']} (dominant: {trend['dominant_mood']})")
            print(f"   Frustration Level: {trend['frustration_level']:.1f}%\n")
            
    except KeyboardInterrupt:
        monitor.stop()
        print("\nMood monitor test completed")
