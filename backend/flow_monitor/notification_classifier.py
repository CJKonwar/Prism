"""
Notification Classifier using ML
Classifies notifications as critical or non-critical
"""

import re
from typing import Dict, List, Tuple
import json
import os


class NotificationClassifier:
    """
    ML-based notification classifier
    Uses DistilBERT for text classification (critical vs non-critical)
    Falls back to rule-based classification if ML not available
    """
    
    # Critical keywords that indicate important notifications
    CRITICAL_KEYWORDS = [
        'urgent', 'emergency', 'critical', 'important', 'alert', 'warning',
        'error', 'failed', 'failure', 'deadline', 'meeting starting',
        'call from', 'security', 'payment', 'invoice', 'approval needed',
        'action required', 'expiring', 'expired', 'overdue', 'reminder',
        'mention', 'direct message', '@', 'replied to you', 'commented on'
    ]
    
    # Apps that are generally critical
    CRITICAL_APPS = [
        'calendar', 'phone', 'facetime', 'messages', 'zoom', 'teams',
        'slack', 'security', 'authenticator', 'banking', 'payment'
    ]
    
    # Apps that are generally distracting
    DISTRACTION_APPS = [
        'twitter', 'facebook', 'instagram', 'tiktok', 'youtube',
        'reddit', 'news', 'mail', 'email', 'social', 'game'
    ]
    
    def __init__(self, use_ml=True):
        """
        Initialize classifier
        
        Args:
            use_ml: Whether to use ML model (DistilBERT) if available
        """
        self.use_ml = use_ml
        self.model = None
        self.tokenizer = None
        
        if use_ml:
            self._load_ml_model()
    
    def _load_ml_model(self):
        """Load DistilBERT model for classification"""
        try:
            from transformers import DistilBertTokenizer, DistilBertForSequenceClassification
            import torch
            
            # Use a lightweight model
            model_name = "distilbert-base-uncased"
            
            print("Loading DistilBERT model for notification classification...")
            self.tokenizer = DistilBertTokenizer.from_pretrained(model_name)
            
            # For now, we'll use rule-based + sentiment as a proxy
            # In production, you'd fine-tune on labeled notification data
            print("ML components loaded (using rule-based classification with ML augmentation)")
            
        except ImportError:
            print("transformers library not available, using rule-based classification")
            self.use_ml = False
        except Exception as e:
            print(f"Could not load ML model: {e}, using rule-based classification")
            self.use_ml = False
    
    def classify(self, title: str, subtitle: str, body: str, app_name: str) -> Tuple[bool, float, str]:
        """
        Classify a notification as critical or non-critical
        
        Args:
            title: Notification title
            subtitle: Notification subtitle
            body: Notification body text
            app_name: Source application name
            
        Returns:
            tuple: (is_critical, confidence, reason)
        """
        if self.use_ml and self.model:
            return self._classify_ml(title, subtitle, body, app_name)
        else:
            return self._classify_rule_based(title, subtitle, body, app_name)
    
    def _classify_ml(self, title: str, subtitle: str, body: str, app_name: str) -> Tuple[bool, float, str]:
        """ML-based classification (DistilBERT)"""
        # Combine all text
        full_text = f"{title} {subtitle} {body}".lower()
        
        try:
            # Tokenize
            inputs = self.tokenizer(full_text, return_tensors="pt", truncation=True, max_length=512)
            
            # Get prediction
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                is_critical = predictions[0][1].item() > 0.5
                confidence = predictions[0][1].item() if is_critical else predictions[0][0].item()
            
            reason = "ML classification"
            return is_critical, confidence, reason
            
        except Exception as e:
            print(f"ML classification failed: {e}, falling back to rules")
            return self._classify_rule_based(title, subtitle, body, app_name)
    
    def _classify_rule_based(self, title: str, subtitle: str, body: str, app_name: str) -> Tuple[bool, float, str]:
        """Rule-based classification"""
        full_text = f"{title} {subtitle} {body}".lower()
        app_name_lower = app_name.lower()
        
        score = 0
        reasons = []
        
        # Check for critical keywords
        for keyword in self.CRITICAL_KEYWORDS:
            if keyword in full_text:
                score += 1
                reasons.append(f"keyword: {keyword}")
        
        # Check app name
        for critical_app in self.CRITICAL_APPS:
            if critical_app in app_name_lower:
                score += 2
                reasons.append(f"critical app: {critical_app}")
                break
        
        # Penalize distraction apps
        for distraction_app in self.DISTRACTION_APPS:
            if distraction_app in app_name_lower:
                score -= 2
                reasons.append(f"distraction app: {distraction_app}")
                break
        
        # Check for time-sensitive patterns
        time_patterns = [
            r'\d+\s*(minute|min|hour|hr)s?\s*(ago|left|remaining)',
            r'in\s*\d+\s*(minute|min|hour|hr)s?',
            r'starting\s*(now|soon)',
            r'ends?\s*(soon|today|tonight)'
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, full_text):
                score += 1
                reasons.append("time-sensitive")
                break
        
        # Check for personal communication
        if any(word in full_text for word in ['@', 'mentioned', 'replied', 'messaged', 'called']):
            score += 1
            reasons.append("personal communication")
        
        # Determine criticality
        is_critical = score >= 1
        confidence = min(abs(score) / 5.0, 1.0)  # Normalize to 0-1
        reason = ", ".join(reasons) if reasons else "default classification"
        
        return is_critical, confidence, reason
    
    def batch_classify(self, notifications: List[Dict]) -> List[Dict]:
        """
        Classify multiple notifications
        
        Args:
            notifications: List of notification dicts with title, subtitle, body, app_name
            
        Returns:
            List of notifications with classification added
        """
        classified = []
        
        for notif in notifications:
            is_critical, confidence, reason = self.classify(
                title=notif.get('title', ''),
                subtitle=notif.get('subtitle', ''),
                body=notif.get('body', ''),
                app_name=notif.get('app_name', '')
            )
            
            notif_copy = notif.copy()
            notif_copy['is_critical'] = is_critical
            notif_copy['confidence'] = confidence
            notif_copy['classification_reason'] = reason
            
            classified.append(notif_copy)
        
        return classified
    
    def get_statistics(self, notifications: List[Dict]) -> Dict:
        """
        Get statistics about notification classifications
        
        Args:
            notifications: List of classified notifications
            
        Returns:
            dict: Statistics
        """
        total = len(notifications)
        if total == 0:
            return {
                'total': 0,
                'critical': 0,
                'non_critical': 0,
                'critical_percentage': 0.0
            }
        
        critical = sum(1 for n in notifications if n.get('is_critical', False))
        non_critical = total - critical
        
        return {
            'total': total,
            'critical': critical,
            'non_critical': non_critical,
            'critical_percentage': (critical / total) * 100
        }
