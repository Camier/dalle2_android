"""
Privacy-compliant analytics and monitoring
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import hashlib
import threading

class PrivacyCompliantAnalytics:
    """Analytics that respect user privacy"""
    
    def __init__(self, analytics_dir: str = "analytics"):
        self.analytics_dir = Path(analytics_dir)
        self.analytics_dir.mkdir(exist_ok=True)
        
        self.session_id = self._generate_session_id()
        self.events_buffer = []
        self.metrics_buffer = []
        
        self.consent_given = False
        self.flush_interval = 60  # seconds
        
        self._start_flush_timer()
    
    def _generate_session_id(self) -> str:
        """Generate anonymous session ID"""
        timestamp = str(time.time())
        return hashlib.sha256(timestamp.encode()).hexdigest()[:16]
    
    def set_consent(self, consent: bool):
        """Set user consent for analytics"""
        self.consent_given = consent
        if consent:
            self._flush_buffers()
        else:
            # Clear all data if consent withdrawn
            self.events_buffer.clear()
            self.metrics_buffer.clear()
    
    def track_event(self, event_name: str, properties: Optional[Dict[str, Any]] = None):
        """Track an event (only if consent given)"""
        if not self.consent_given:
            return
        
        event = {
            "event": event_name,
            "timestamp": time.time(),
            "session_id": self.session_id,
            "properties": self._sanitize_properties(properties or {})
        }
        
        self.events_buffer.append(event)
    
    def track_metric(self, metric_name: str, value: float, unit: str = ""):
        """Track a metric (only if consent given)"""
        if not self.consent_given:
            return
        
        metric = {
            "metric": metric_name,
            "value": value,
            "unit": unit,
            "timestamp": time.time(),
            "session_id": self.session_id
        }
        
        self.metrics_buffer.append(metric)
    
    def _sanitize_properties(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Remove any PII from properties"""
        sanitized = {}
        
        # Whitelist of allowed property names
        allowed_keys = {
            "screen_name", "action_type", "success", "error_type",
            "duration_ms", "item_count", "feature_used"
        }
        
        for key, value in properties.items():
            if key in allowed_keys:
                # Further sanitize values
                if isinstance(value, str):
                    # Remove potential PII patterns
                    value = self._remove_pii(value)
                sanitized[key] = value
        
        return sanitized
    
    def _remove_pii(self, text: str) -> str:
        """Remove potential PII from text"""
        import re
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '[EMAIL]', text)
        
        # Remove phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        
        # Remove IP addresses
        text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]', text)
        
        return text
    
    def _start_flush_timer(self):
        """Start timer to periodically flush buffers"""
        def flush_periodically():
            while True:
                time.sleep(self.flush_interval)
                self._flush_buffers()
        
        flush_thread = threading.Thread(target=flush_periodically, daemon=True)
        flush_thread.start()
    
    def _flush_buffers(self):
        """Save buffered events and metrics to disk"""
        if not self.consent_given:
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save events
        if self.events_buffer:
            events_file = self.analytics_dir / f"events_{timestamp}.json"
            with open(events_file, 'w') as f:
                json.dump(self.events_buffer, f, indent=2)
            self.events_buffer.clear()
        
        # Save metrics
        if self.metrics_buffer:
            metrics_file = self.analytics_dir / f"metrics_{timestamp}.json"
            with open(metrics_file, 'w') as f:
                json.dump(self.metrics_buffer, f, indent=2)
            self.metrics_buffer.clear()
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        return {
            "session_id": self.session_id,
            "events_count": len(self.events_buffer),
            "metrics_count": len(self.metrics_buffer),
            "consent_given": self.consent_given
        }

class PerformanceMonitor:
    """Monitor app performance metrics"""
    
    def __init__(self, analytics: PrivacyCompliantAnalytics):
        self.analytics = analytics
        self.operation_timers = {}
        
    def start_operation(self, operation_name: str):
        """Start timing an operation"""
        self.operation_timers[operation_name] = time.time()
    
    def end_operation(self, operation_name: str, success: bool = True):
        """End timing an operation and track metric"""
        if operation_name not in self.operation_timers:
            return
        
        duration = (time.time() - self.operation_timers[operation_name]) * 1000  # ms
        del self.operation_timers[operation_name]
        
        # Track metric
        self.analytics.track_metric(
            f"operation_duration_{operation_name}",
            duration,
            "ms"
        )
        
        # Track event
        self.analytics.track_event(
            f"operation_completed",
            {
                "operation": operation_name,
                "duration_ms": duration,
                "success": success
            }
        )
    
    def track_memory_usage(self):
        """Track current memory usage"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            self.analytics.track_metric("memory_usage_mb", memory_mb, "MB")
        except:
            pass
    
    def track_api_latency(self, endpoint: str, latency_ms: float):
        """Track API latency"""
        self.analytics.track_metric(
            f"api_latency_{endpoint}",
            latency_ms,
            "ms"
        )

class CrashReporter:
    """Privacy-compliant crash reporting"""
    
    def __init__(self, crash_dir: str = "crash_reports"):
        self.crash_dir = Path(crash_dir)
        self.crash_dir.mkdir(exist_ok=True)
        
    def report_crash(self, exception: Exception, context: Optional[Dict[str, Any]] = None):
        """Report a crash with sanitized information"""
        import traceback
        
        crash_data = {
            "timestamp": datetime.now().isoformat(),
            "exception_type": type(exception).__name__,
            "exception_message": self._sanitize_message(str(exception)),
            "traceback": self._sanitize_traceback(traceback.format_exc()),
            "context": self._sanitize_context(context or {})
        }
        
        # Save crash report
        crash_file = self.crash_dir / f"crash_{int(time.time())}.json"
        with open(crash_file, 'w') as f:
            json.dump(crash_data, f, indent=2)
    
    def _sanitize_message(self, message: str) -> str:
        """Remove sensitive information from error messages"""
        # Remove file paths that might contain usernames
        import re
        message = re.sub(r'/home/\w+/', '/home/[USER]/', message)
        message = re.sub(r'C:\\Users\\\w+\\', 'C:\\Users\\[USER]\\', message)
        
        return message
    
    def _sanitize_traceback(self, tb: str) -> str:
        """Sanitize traceback information"""
        # Similar sanitization as messages
        return self._sanitize_message(tb)
    
    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize context information"""
        safe_keys = {"screen", "action", "feature", "error_code"}
        return {k: v for k, v in context.items() if k in safe_keys}
