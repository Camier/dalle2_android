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
