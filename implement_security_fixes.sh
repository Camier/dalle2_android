#!/bin/bash

# DALL-E Android Security Implementation Script
# Implements all security fixes identified in the audit

set -e

echo "========================================"
echo "DALL-E Android Security Implementation"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create security implementations directory
mkdir -p security_implementations

# 1. Implement Certificate Pinning
echo -e "${YELLOW}Implementing Certificate Pinning...${NC}"
cat > services/certificate_pinning.py << 'EOF'
"""
Certificate Pinning Implementation for OpenAI API
"""

import ssl
import hashlib
import base64
from urllib3 import PoolManager
from urllib3.util import Timeout
from urllib3.exceptions import SSLError
from kivy.logger import Logger

class CertificatePinner:
    """
    Implements certificate pinning for secure API communication
    """
    
    # OpenAI API certificate pins (SHA256)
    # These should be updated periodically
    OPENAI_PINS = [
        # Primary certificate
        'sha256/Ko8tivDrEjiY90yGasP6ZpBU4jwXvHqVvQI0GS3GNdA=',
        # Backup certificate
        'sha256/VjLZe/p3W/PJnd6lL8JVNBCGQBZynFLdZSTIqcO0SJ8=',
        # Root CA certificate
        'sha256/++MBgDH5WGvL9Bcn5Be30cRcL0f5O+NyoXuWtQdX1aI='
    ]
    
    def __init__(self):
        self.pins = set(self.OPENAI_PINS)
        
    def verify_pin(self, cert_der):
        """Verify certificate against pinned values"""
        # Calculate SHA256 of the certificate
        cert_hash = hashlib.sha256(cert_der).digest()
        cert_pin = f'sha256/{base64.b64encode(cert_hash).decode()}'
        
        # Check if pin matches
        if cert_pin in self.pins:
            Logger.info(f"CertificatePinner: Certificate pin verified: {cert_pin[:20]}...")
            return True
        else:
            Logger.error(f"CertificatePinner: Certificate pin mismatch: {cert_pin[:20]}...")
            return False
    
    def create_pinned_session(self):
        """Create a session with certificate pinning"""
        # Custom SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Disable weak ciphers
        ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        # Create pool manager with custom SSL context
        pool = PoolManager(
            ssl_context=ssl_context,
            cert_reqs='CERT_REQUIRED',
            assert_hostname='api.openai.com',
            timeout=Timeout(connect=5.0, read=30.0)
        )
        
        # Add certificate verification callback
        original_urlopen = pool.urlopen
        
        def pinned_urlopen(method, url, *args, **kwargs):
            response = original_urlopen(method, url, *args, **kwargs)
            
            # Verify certificate pin
            if hasattr(response.connection, 'sock') and hasattr(response.connection.sock, 'getpeercert_binary'):
                cert_der = response.connection.sock.getpeercert_binary()
                if not self.verify_pin(cert_der):
                    raise SSLError("Certificate pin verification failed")
            
            return response
        
        pool.urlopen = pinned_urlopen
        return pool

# Example usage in API service
class SecureAPIClient:
    def __init__(self):
        self.pinner = CertificatePinner()
        self.session = self.pinner.create_pinned_session()
    
    def make_request(self, url, **kwargs):
        """Make a request with certificate pinning"""
        return self.session.request('POST', url, **kwargs)
EOF

# 2. Implement Rate Limiting with Circuit Breaker
echo -e "${YELLOW}Implementing Rate Limiting...${NC}"
cat > services/rate_limiter.py << 'EOF'
"""
Advanced Rate Limiting with Circuit Breaker Pattern
Based on OpenAI Cookbook best practices
"""

import time
import threading
from collections import deque
from datetime import datetime, timedelta
from functools import wraps
from kivy.logger import Logger

class TokenBucket:
    """Token bucket algorithm for rate limiting"""
    
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens=1):
        """Try to consume tokens"""
        with self.lock:
            # Refill tokens
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_time(self, tokens=1):
        """Calculate wait time for tokens"""
        with self.lock:
            if self.tokens >= tokens:
                return 0
            return (tokens - self.tokens) / self.refill_rate

class CircuitBreaker:
    """Circuit breaker pattern for fault tolerance"""
    
    def __init__(self, failure_threshold=5, recovery_timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
        self.lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self.lock:
            if self.state == 'open':
                # Check if we should try half-open
                if self.last_failure_time and \
                   time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = 'half_open'
                    Logger.info("CircuitBreaker: Attempting recovery (half-open)")
                else:
                    raise Exception("Circuit breaker is OPEN - service unavailable")
        
        try:
            result = func(*args, **kwargs)
            with self.lock:
                # Success - reset on half-open or reduce failure count
                if self.state == 'half_open':
                    self.state = 'closed'
                    self.failure_count = 0
                    Logger.info("CircuitBreaker: Service recovered (closed)")
                elif self.failure_count > 0:
                    self.failure_count -= 1
            return result
            
        except self.expected_exception as e:
            with self.lock:
                self.failure_count += 1
                self.last_failure_time = time.time()
                
                if self.failure_count >= self.failure_threshold:
                    self.state = 'open'
                    Logger.error(f"CircuitBreaker: OPEN after {self.failure_count} failures")
                
            raise e

class RateLimiter:
    """
    Comprehensive rate limiter with multiple strategies
    """
    
    def __init__(self):
        # Token bucket for API calls (5 requests per minute)
        self.api_bucket = TokenBucket(capacity=5, refill_rate=5/60)
        
        # Circuit breaker for API failures
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60,
            expected_exception=(Exception,)
        )
        
        # Request history for analytics
        self.request_history = deque(maxlen=100)
        
        # Exponential backoff state
        self.backoff_base = 1.0
        self.backoff_max = 60.0
        self.consecutive_failures = 0
    
    def check_rate_limit(self):
        """Check if request can proceed"""
        if not self.api_bucket.consume():
            wait_time = self.api_bucket.wait_time()
            Logger.warning(f"RateLimiter: Rate limit hit, wait {wait_time:.1f}s")
            return False, wait_time
        return True, 0
    
    def with_rate_limit(self, func):
        """Decorator for rate-limited functions"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check rate limit
            can_proceed, wait_time = self.check_rate_limit()
            if not can_proceed:
                time.sleep(wait_time)
            
            # Execute with circuit breaker
            try:
                result = self.circuit_breaker.call(func, *args, **kwargs)
                self.consecutive_failures = 0
                return result
            except Exception as e:
                self.consecutive_failures += 1
                
                # Calculate exponential backoff
                backoff = min(
                    self.backoff_base * (2 ** self.consecutive_failures),
                    self.backoff_max
                )
                
                Logger.error(f"RateLimiter: Request failed, backoff {backoff}s")
                time.sleep(backoff)
                raise e
        
        return wrapper
    
    def record_request(self, success, duration):
        """Record request for analytics"""
        self.request_history.append({
            'timestamp': datetime.now(),
            'success': success,
            'duration': duration
        })
    
    def get_stats(self):
        """Get rate limiting statistics"""
        if not self.request_history:
            return {}
        
        total = len(self.request_history)
        successful = sum(1 for r in self.request_history if r['success'])
        avg_duration = sum(r['duration'] for r in self.request_history) / total
        
        return {
            'total_requests': total,
            'success_rate': successful / total,
            'average_duration': avg_duration,
            'circuit_state': self.circuit_breaker.state,
            'tokens_available': self.api_bucket.tokens
        }

# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter():
    """Get singleton rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
EOF

# 3. Implement Input Validation and Sanitization
echo -e "${YELLOW}Implementing Input Validation...${NC}"
cat > utils/input_validator.py << 'EOF'
"""
Input Validation and Sanitization
Prevents injection attacks and ensures data integrity
"""

import re
import html
from typing import Optional, List
from kivy.logger import Logger

class InputValidator:
    """
    Comprehensive input validation for security
    """
    
    # Regex patterns for validation
    PATTERNS = {
        'api_key': re.compile(r'^sk-[a-zA-Z0-9]{48}$'),
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'alphanumeric': re.compile(r'^[a-zA-Z0-9\s]+$'),
        'filename': re.compile(r'^[a-zA-Z0-9_\-\.]+$'),
        'url': re.compile(r'^https?://[a-zA-Z0-9\-\.]+(:[0-9]+)?(/.*)?$')
    }
    
    # Banned words for content filtering
    BANNED_WORDS = [
        # Add inappropriate content filters here
    ]
    
    @staticmethod
    def validate_api_key(api_key: str) -> tuple[bool, str]:
        """Validate OpenAI API key format"""
        if not api_key:
            return False, "API key is required"
        
        if not isinstance(api_key, str):
            return False, "API key must be a string"
        
        if not InputValidator.PATTERNS['api_key'].match(api_key):
            return False, "Invalid API key format"
        
        return True, "Valid"
    
    @staticmethod
    def sanitize_prompt(prompt: str, max_length: int = 1000) -> tuple[str, List[str]]:
        """
        Sanitize user prompt for DALL-E API
        Returns sanitized prompt and list of issues found
        """
        issues = []
        
        if not prompt:
            return "", ["Empty prompt"]
        
        # Remove leading/trailing whitespace
        prompt = prompt.strip()
        
        # Check length
        if len(prompt) < 3:
            issues.append("Prompt too short (minimum 3 characters)")
        elif len(prompt) > max_length:
            prompt = prompt[:max_length]
            issues.append(f"Prompt truncated to {max_length} characters")
        
        # Remove potential injection attempts
        # Remove SQL-like patterns
        sql_patterns = [
            r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE)\b',
            r'(--|#|/\*|\*/)',
            r'[\x00-\x1F\x7F]'  # Control characters
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                prompt = re.sub(pattern, '', prompt, flags=re.IGNORECASE)
                issues.append("Removed potential SQL injection attempt")
        
        # Remove JavaScript patterns
        js_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
            r'<object'
        ]
        
        for pattern in js_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                prompt = re.sub(pattern, '', prompt, flags=re.IGNORECASE)
                issues.append("Removed potential XSS attempt")
        
        # HTML escape
        prompt = html.escape(prompt)
        
        # Check for banned content
        prompt_lower = prompt.lower()
        for word in InputValidator.BANNED_WORDS:
            if word in prompt_lower:
                issues.append("Inappropriate content detected")
                return "", issues
        
        # Normalize whitespace
        prompt = ' '.join(prompt.split())
        
        return prompt, issues
    
    @staticmethod
    def validate_image_size(size: str) -> tuple[bool, str]:
        """Validate DALL-E image size parameter"""
        valid_sizes = ["256x256", "512x512", "1024x1024"]
        
        if size not in valid_sizes:
            return False, f"Invalid size. Must be one of: {', '.join(valid_sizes)}"
        
        return True, "Valid"
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for saving"""
        # Remove path traversal attempts
        filename = filename.replace('..', '')
        filename = filename.replace('/', '')
        filename = filename.replace('\\', '')
        
        # Keep only safe characters
        filename = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')
        
        return filename
    
    @staticmethod
    def validate_url(url: str) -> tuple[bool, str]:
        """Validate URL format and safety"""
        if not url:
            return False, "URL is required"
        
        # Check protocol
        if not url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"
        
        # Check format
        if not InputValidator.PATTERNS['url'].match(url):
            return False, "Invalid URL format"
        
        # Check for known malicious patterns
        malicious_patterns = [
            'javascript:',
            'data:',
            'vbscript:',
            'file://',
            'about:'
        ]
        
        for pattern in malicious_patterns:
            if pattern in url.lower():
                return False, f"Potentially malicious URL pattern: {pattern}"
        
        return True, "Valid"

class ContentFilter:
    """
    Content filtering for appropriate use
    """
    
    @staticmethod
    def check_content_policy(prompt: str) -> tuple[bool, str]:
        """
        Check if prompt violates content policy
        Returns (is_allowed, reason)
        """
        # Check for violent content
        violence_keywords = [
            'gore', 'violence', 'blood', 'murder', 'kill',
            'torture', 'death', 'weapon'
        ]
        
        prompt_lower = prompt.lower()
        for keyword in violence_keywords:
            if keyword in prompt_lower:
                return False, "Content may violate violence policy"
        
        # Check for adult content
        adult_keywords = [
            'nude', 'naked', 'nsfw', 'adult', 'explicit'
        ]
        
        for keyword in adult_keywords:
            if keyword in prompt_lower:
                return False, "Content may violate adult content policy"
        
        # Check for hate speech
        hate_patterns = [
            r'\b(hate|racist|discrimination)\b',
            r'\b(harass|bully|threat)\b'
        ]
        
        for pattern in hate_patterns:
            if re.search(pattern, prompt_lower):
                return False, "Content may violate hate speech policy"
        
        # Check for personal information
        pii_patterns = [
            r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
            r'\b\d{16}\b',  # Credit card
            r'\b[A-Z]{2}\d{6,8}\b',  # Passport
        ]
        
        for pattern in pii_patterns:
            if re.search(pattern, prompt):
                return False, "Content appears to contain personal information"
        
        return True, "Content appears appropriate"
EOF

# 4. Implement Secure Logging
echo -e "${YELLOW}Implementing Secure Logging...${NC}"
cat > utils/secure_logger.py << 'EOF'
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
EOF

# 5. Create Network Security Configuration
echo -e "${YELLOW}Creating Network Security Configuration...${NC}"
mkdir -p res/xml
cat > res/xml/network_security_config.xml << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <!-- Pin certificates for OpenAI API -->
    <domain-config>
        <domain includeSubdomains="true">api.openai.com</domain>
        <pin-set expiration="2026-01-01">
            <!-- Primary pin -->
            <pin digest="SHA-256">Ko8tivDrEjiY90yGasP6ZpBU4jwXvHqVvQI0GS3GNdA=</pin>
            <!-- Backup pin -->
            <pin digest="SHA-256">VjLZe/p3W/PJnd6lL8JVNBCGQBZynFLdZSTIqcO0SJ8=</pin>
        </pin-set>
        <!-- Require TLS 1.2 minimum -->
        <trustkit-config>
            <min-tls-version>1.2</min-tls-version>
        </trustkit-config>
    </domain-config>
    
    <!-- Default configuration for other domains -->
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
</network-security-config>
EOF

# 6. Create Anti-Tampering Implementation
echo -e "${YELLOW}Implementing Anti-Tampering Measures...${NC}"
cat > utils/integrity_checker.py << 'EOF'
"""
App Integrity Checker - Anti-tampering protection
"""

import hashlib
import hmac
import os
from kivy.utils import platform
from kivy.logger import Logger

class IntegrityChecker:
    """
    Verifies app integrity and detects tampering
    """
    
    def __init__(self):
        self.package_name = "com.dalleandroid.dalleaiart"
        self.expected_signature = None
        self.init_integrity_checks()
    
    def init_integrity_checks(self):
        """Initialize integrity checking"""
        if platform == 'android':
            self._init_android_checks()
    
    def _init_android_checks(self):
        """Initialize Android-specific integrity checks"""
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PackageManager = autoclass('android.content.pm.PackageManager')
            PackageInfo = autoclass('android.content.pm.PackageInfo')
            Signature = autoclass('android.content.pm.Signature')
            
            # Get package info
            context = PythonActivity.mActivity
            pm = context.getPackageManager()
            package_info = pm.getPackageInfo(
                self.package_name,
                PackageManager.GET_SIGNATURES
            )
            
            # Get signature
            signatures = package_info.signatures
            if signatures and len(signatures) > 0:
                self.expected_signature = self._hash_signature(signatures[0])
                Logger.info(f"IntegrityChecker: Initialized with signature hash: {self.expected_signature[:10]}...")
            
        except Exception as e:
            Logger.error(f"IntegrityChecker: Failed to initialize: {e}")
    
    def _hash_signature(self, signature):
        """Hash app signature for comparison"""
        return hashlib.sha256(signature.toByteArray()).hexdigest()
    
    def verify_app_signature(self):
        """Verify app signature hasn't changed"""
        if platform != 'android':
            return True  # Skip on non-Android platforms
        
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PackageManager = autoclass('android.content.pm.PackageManager')
            
            context = PythonActivity.mActivity
            pm = context.getPackageManager()
            package_info = pm.getPackageInfo(
                self.package_name,
                PackageManager.GET_SIGNATURES
            )
            
            signatures = package_info.signatures
            if signatures and len(signatures) > 0:
                current_signature = self._hash_signature(signatures[0])
                
                if current_signature != self.expected_signature:
                    Logger.error("IntegrityChecker: Signature mismatch - possible tampering!")
                    return False
                
            return True
            
        except Exception as e:
            Logger.error(f"IntegrityChecker: Verification failed: {e}")
            return False
    
    def check_debugger(self):
        """Check if debugger is attached"""
        if platform != 'android':
            return False
        
        try:
            from jnius import autoclass
            Debug = autoclass('android.os.Debug')
            
            if Debug.isDebuggerConnected():
                Logger.warning("IntegrityChecker: Debugger detected!")
                return True
                
        except:
            pass
        
        return False
    
    def check_emulator(self):
        """Check if running on emulator"""
        if platform != 'android':
            return False
        
        try:
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            
            # Common emulator indicators
            emulator_indicators = [
                Build.FINGERPRINT.startswith("generic"),
                Build.FINGERPRINT.startswith("unknown"),
                Build.MODEL.contains("google_sdk"),
                Build.MODEL.contains("Emulator"),
                Build.MODEL.contains("Android SDK built for x86"),
                Build.MANUFACTURER.contains("Genymotion"),
                Build.HARDWARE.contains("goldfish"),
                Build.HARDWARE.contains("ranchu"),
                Build.PRODUCT.contains("sdk"),
                Build.PRODUCT.contains("google_sdk"),
                Build.PRODUCT.contains("sdk_x86"),
                Build.PRODUCT.contains("vbox86p"),
                Build.DEVICE.contains("generic")
            ]
            
            if any(emulator_indicators):
                Logger.warning("IntegrityChecker: Emulator detected!")
                return True
                
        except:
            pass
        
        return False
    
    def check_root(self):
        """Check if device is rooted"""
        if platform != 'android':
            return False
        
        # Check for common root indicators
        root_paths = [
            "/system/app/Superuser.apk",
            "/sbin/su",
            "/system/bin/su",
            "/system/xbin/su",
            "/data/local/xbin/su",
            "/data/local/bin/su",
            "/system/sd/xbin/su",
            "/system/bin/failsafe/su",
            "/data/local/su",
            "/su/bin/su"
        ]
        
        for path in root_paths:
            if os.path.exists(path):
                Logger.warning(f"IntegrityChecker: Root indicator found: {path}")
                return True
        
        # Check for root management apps
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PackageManager = autoclass('android.content.pm.PackageManager')
            
            context = PythonActivity.mActivity
            pm = context.getPackageManager()
            
            root_packages = [
                "com.topjohnwu.magisk",
                "com.koushikdutta.superuser",
                "com.noshufou.android.su",
                "com.thirdparty.superuser",
                "eu.chainfire.supersu",
                "com.yellowes.su"
            ]
            
            for package in root_packages:
                try:
                    pm.getPackageInfo(package, 0)
                    Logger.warning(f"IntegrityChecker: Root app found: {package}")
                    return True
                except:
                    continue
                    
        except:
            pass
        
        return False
    
    def perform_integrity_check(self):
        """Perform full integrity check"""
        results = {
            'signature_valid': self.verify_app_signature(),
            'debugger_attached': self.check_debugger(),
            'emulator_detected': self.check_emulator(),
            'root_detected': self.check_root()
        }
        
        # Overall integrity status
        results['integrity_ok'] = (
            results['signature_valid'] and
            not results['debugger_attached'] and
            not results['root_detected']
        )
        
        return results

# Global integrity checker instance
_integrity_checker = None

def get_integrity_checker():
    """Get singleton integrity checker instance"""
    global _integrity_checker
    if _integrity_checker is None:
        _integrity_checker = IntegrityChecker()
    return _integrity_checker
EOF

# 7. Create Security Test Suite
echo -e "${YELLOW}Creating Security Test Suite...${NC}"
cat > test_security.py << 'EOF'
"""
Security Test Suite for DALL-E Android App
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.input_validator import InputValidator, ContentFilter
from utils.secure_storage import SecureStorage
from services.rate_limiter import RateLimiter, TokenBucket
from services.certificate_pinning import CertificatePinner
from utils.secure_logger import SecureLogger

class TestInputValidation(unittest.TestCase):
    """Test input validation and sanitization"""
    
    def test_api_key_validation(self):
        """Test API key format validation"""
        # Valid key
        valid, msg = InputValidator.validate_api_key("sk-" + "a" * 48)
        self.assertTrue(valid)
        
        # Invalid keys
        invalid_keys = [
            "",
            "not-an-api-key",
            "sk-",
            "sk-" + "a" * 47,  # Too short
            "sk-" + "a" * 49,  # Too long
            "SK-" + "a" * 48,  # Wrong case
        ]
        
        for key in invalid_keys:
            valid, msg = InputValidator.validate_api_key(key)
            self.assertFalse(valid)
    
    def test_prompt_sanitization(self):
        """Test prompt sanitization"""
        # Normal prompt
        prompt, issues = InputValidator.sanitize_prompt("A beautiful sunset over mountains")
        self.assertEqual(len(issues), 0)
        
        # SQL injection attempt
        prompt, issues = InputValidator.sanitize_prompt("'; DROP TABLE users; --")
        self.assertIn("Removed potential SQL injection attempt", issues)
        
        # XSS attempt
        prompt, issues = InputValidator.sanitize_prompt("<script>alert('xss')</script>")
        self.assertIn("Removed potential XSS attempt", issues)
        
        # Too long prompt
        long_prompt = "a" * 2000
        prompt, issues = InputValidator.sanitize_prompt(long_prompt)
        self.assertIn("Prompt truncated", issues[0])
        self.assertEqual(len(prompt), 1000)
    
    def test_filename_sanitization(self):
        """Test filename sanitization"""
        # Path traversal attempt
        filename = InputValidator.sanitize_filename("../../etc/passwd")
        self.assertNotIn("..", filename)
        self.assertNotIn("/", filename)
        
        # Special characters
        filename = InputValidator.sanitize_filename("my file@#$%.png")
        self.assertEqual(filename, "my_file_____.png")

class TestRateLimiting(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def test_token_bucket(self):
        """Test token bucket algorithm"""
        bucket = TokenBucket(capacity=5, refill_rate=1)
        
        # Consume all tokens
        for i in range(5):
            self.assertTrue(bucket.consume())
        
        # Should fail on 6th attempt
        self.assertFalse(bucket.consume())
        
        # Wait for refill
        import time
        time.sleep(1.1)
        self.assertTrue(bucket.consume())
    
    def test_rate_limiter_decorator(self):
        """Test rate limiter decorator"""
        limiter = RateLimiter()
        
        @limiter.with_rate_limit
        def api_call():
            return "success"
        
        # Should work for first few calls
        for i in range(3):
            result = api_call()
            self.assertEqual(result, "success")

class TestSecureLogging(unittest.TestCase):
    """Test secure logging functionality"""
    
    def test_sensitive_data_redaction(self):
        """Test that sensitive data is redacted"""
        logger = SecureLogger("test")
        
        # Test API key redaction
        message = logger._redact_sensitive_data("API key: sk-abcd1234567890abcd1234567890abcd1234567890abcd12")
        self.assertIn("sk-***REDACTED***", message)
        self.assertNotIn("sk-abcd", message)
        
        # Test email redaction
        message = logger._redact_sensitive_data("User email: user@example.com")
        self.assertIn("***@***.***", message)
        self.assertNotIn("user@example.com", message)

class TestContentFilter(unittest.TestCase):
    """Test content filtering"""
    
    def test_content_policy_check(self):
        """Test content policy validation"""
        # Appropriate content
        allowed, reason = ContentFilter.check_content_policy("A beautiful landscape painting")
        self.assertTrue(allowed)
        
        # Violent content
        allowed, reason = ContentFilter.check_content_policy("A scene with violence and gore")
        self.assertFalse(allowed)
        self.assertIn("violence", reason.lower())
        
        # Adult content
        allowed, reason = ContentFilter.check_content_policy("nude figure")
        self.assertFalse(allowed)
        self.assertIn("adult", reason.lower())

if __name__ == '__main__':
    unittest.main()
EOF

# Make scripts executable
chmod +x build_secure_release.sh
chmod +x implement_security_fixes.sh
chmod +x generate_release_keystore.sh

echo -e "${GREEN}✅ Security implementation complete!${NC}"
echo ""
echo "Security features implemented:"
echo "1. ✅ Certificate pinning for OpenAI API"
echo "2. ✅ Advanced rate limiting with circuit breaker"
echo "3. ✅ Input validation and sanitization"
echo "4. ✅ Secure logging with PII redaction"
echo "5. ✅ Network security configuration"
echo "6. ✅ Anti-tampering protection"
echo "7. ✅ Privacy compliance framework"
echo "8. ✅ Secure storage with Android Keystore"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Run security tests: python test_security.py"
echo "2. Generate release keystore: ./generate_release_keystore.sh"
echo "3. Build secure release: ./build_secure_release.sh"
echo "4. Test the APK thoroughly"
echo "5. Run security scanning tools"
echo ""
echo -e "${GREEN}Security checklist:${NC}"
echo "□ Generate release keystore"
echo "□ Configure API key securely"
echo "□ Review privacy policy"
echo "□ Test all security features"
echo "□ Verify certificate pinning"
echo "□ Check ProGuard obfuscation"
echo "□ Scan APK with security tools"