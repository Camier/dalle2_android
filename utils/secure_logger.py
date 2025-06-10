"""
Secure Logging Implementation
Prevents sensitive data leakage in logs
"""

import re
import logging
from functools import wraps
from kivy.logger import Logger as KivyLogger

class SecureLogger:
    """
    Logger that redacts sensitive information
    """
    
    # Patterns for sensitive data
    SENSITIVE_PATTERNS = [
        (r'sk-[a-zA-Z0-9]{48}', 'sk-***REDACTED***'),  # API keys
        (r'\b\d{16}\b', '****-****-****-****'),  # Credit cards
        (r'\b\d{3}-\d{2}-\d{4}\b', '***-**-****'),  # SSN
        (r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '***@***.***'),  # Email
        (r'"password"\s*:\s*"[^"]*"', '"password": "***REDACTED***"'),  # Passwords in JSON
        (r'Bearer [a-zA-Z0-9\-._~+/]+=*', 'Bearer ***REDACTED***'),  # Bearer tokens
    ]
    
    def __init__(self, name='DALLE-App'):
        self.name = name
        self.production_mode = self._is_production()
    
    def _is_production(self):
        """Check if running in production mode"""
        import os
        return os.environ.get('PRODUCTION', '0') == '1'
    
    def _redact_sensitive_data(self, message: str) -> str:
        """Redact sensitive information from log messages"""
        if not isinstance(message, str):
            message = str(message)
        
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, replacement, message)
        
        return message
    
    def _should_log(self, level: str) -> bool:
        """Determine if message should be logged based on environment"""
        if self.production_mode:
            # In production, only log warnings and errors
            return level in ['WARNING', 'ERROR', 'CRITICAL']
        return True
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        if self._should_log('DEBUG'):
            safe_message = self._redact_sensitive_data(message)
            KivyLogger.debug(f"{self.name}: {safe_message}")
    
    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        if self._should_log('INFO'):
            safe_message = self._redact_sensitive_data(message)
            KivyLogger.info(f"{self.name}: {safe_message}")
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        if self._should_log('WARNING'):
            safe_message = self._redact_sensitive_data(message)
            KivyLogger.warning(f"{self.name}: {safe_message}")
    
    def error(self, message: str, *args, **kwargs):
        """Log error message"""
        if self._should_log('ERROR'):
            safe_message = self._redact_sensitive_data(message)
            # Don't log stack traces in production
            if self.production_mode and 'exc_info' in kwargs:
                kwargs['exc_info'] = False
            KivyLogger.error(f"{self.name}: {safe_message}")
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message"""
        if self._should_log('CRITICAL'):
            safe_message = self._redact_sensitive_data(message)
            KivyLogger.critical(f"{self.name}: {safe_message}")

def log_function_call(logger_name='DALLE-App'):
    """
    Decorator to log function calls securely
    """
    logger = SecureLogger(logger_name)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Log function entry (debug only)
            logger.debug(f"Entering {func.__name__}")
            
            try:
                result = func(*args, **kwargs)
                logger.debug(f"Exiting {func.__name__} successfully")
                return result
            except Exception as e:
                # Log error without exposing sensitive details
                logger.error(f"Error in {func.__name__}: {type(e).__name__}")
                raise
        
        return wrapper
    
    return decorator

# Create global secure logger instance
secure_logger = SecureLogger('DALLE-App')
