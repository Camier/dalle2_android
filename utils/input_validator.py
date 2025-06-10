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
