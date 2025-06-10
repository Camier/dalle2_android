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
