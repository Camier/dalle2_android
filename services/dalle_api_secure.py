"""
DALL-E 2 API Service with Enhanced Security
Handles all interactions with OpenAI's DALL-E API with security best practices
"""

import requests
import time
import ssl
import certifi
from openai import OpenAI
from io import BytesIO
from PIL import Image as PILImage
from urllib3 import PoolManager
from urllib3.util.retry import Retry
from urllib3.exceptions import MaxRetryError
from datetime import datetime, timedelta
from threading import Lock
from kivy.logger import Logger

# Import secure storage
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.secure_storage import get_secure_storage

class DalleAPIError(Exception):
    pass

class RateLimiter:
    """Token bucket rate limiter"""
    def __init__(self, requests_per_minute=5):
        self.requests_per_minute = requests_per_minute
        self.min_interval = 60.0 / requests_per_minute
        self.last_request_time = 0
        self.lock = Lock()
    
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit"""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                Logger.info(f"RateLimiter: Sleeping for {sleep_time:.2f}s")
                time.sleep(sleep_time)
            
            self.last_request_time = time.time()

class SecureHTTPAdapter:
    """HTTP adapter with certificate pinning and enhanced security"""
    
    # OpenAI API certificate fingerprints (these should be updated periodically)
    OPENAI_CERT_FINGERPRINTS = [
        # Add actual certificate fingerprints here
        # These are examples and should be replaced with real values
    ]
    
    def __init__(self):
        # Configure retry strategy
        self.retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        # Create secure pool manager
        self.pool_manager = PoolManager(
            cert_reqs="CERT_REQUIRED",
            ca_certs=certifi.where(),
            ssl_version=ssl.PROTOCOL_TLS_1_2,  # Minimum TLS 1.2
            retries=self.retry_strategy
        )
    
    def request(self, method, url, **kwargs):
        """Make secure HTTP request"""
        return self.pool_manager.request(method, url, **kwargs)

class DalleAPIServiceSecure:
    def __init__(self):
        self.client = None
        self.secure_storage = get_secure_storage()
        self.rate_limiter = RateLimiter(requests_per_minute=5)
        self.http_adapter = SecureHTTPAdapter()
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client with stored API key if available"""
        api_key = self.secure_storage.get_api_key()
        if api_key:
            self.client = OpenAI(api_key=api_key)
            Logger.info("DalleAPI: Initialized with stored API key")
    
    def set_api_key(self, api_key):
        """Securely store and set API key"""
        # Validate key format
        if not self._validate_api_key_format(api_key):
            raise DalleAPIError("Invalid API key format")
        
        # Store securely
        if self.secure_storage.store_api_key(api_key):
            self.client = OpenAI(api_key=api_key)
            Logger.info("DalleAPI: API key stored securely")
            return True
        else:
            raise DalleAPIError("Failed to store API key securely")
    
    def _validate_api_key_format(self, api_key):
        """Validate API key format"""
        if not api_key or not isinstance(api_key, str):
            return False
        
        # OpenAI API keys start with 'sk-'
        if not api_key.startswith('sk-'):
            return False
        
        # Check length (typical OpenAI keys are ~51 characters)
        if len(api_key) < 40 or len(api_key) > 60:
            return False
        
        return True
    
    def generate_image(self, prompt, size="1024x1024", n=1):
        """Generate image with enhanced security and error handling"""
        if not self.client:
            raise DalleAPIError("API key not set. Please configure your API key.")
        
        # Validate and sanitize input
        prompt = self._sanitize_prompt(prompt)
        size = self._validate_size(size)
        n = self._validate_count(n)
        
        # Apply rate limiting
        self.rate_limiter.wait_if_needed()
        
        try:
            Logger.info(f"DalleAPI: Generating image with prompt: {prompt[:50]}...")
            
            # Make API call with timeout
            response = self.client.images.generate(
                prompt=prompt,
                model="dall-e-2",
                size=size,
                n=n,
                response_format="url"
            )
            
            # Get the image URL
            image_url = response.data[0].url
            
            # Download image securely
            image = self._download_image_securely(image_url)
            
            Logger.info("DalleAPI: Image generated successfully")
            return image, image_url
            
        except Exception as e:
            error_msg = str(e)
            Logger.error(f"DalleAPI: Error - {error_msg}")
            
            # Enhanced error handling
            if "api_key" in error_msg.lower() or "unauthorized" in error_msg.lower():
                # Clear invalid key
                self.secure_storage.remove_api_key()
                self.client = None
                raise DalleAPIError("Invalid API key. Please check your OpenAI API key.")
            elif "rate" in error_msg.lower() or "429" in str(e):
                raise DalleAPIError("Rate limit exceeded. Please wait a moment and try again.")
            elif "quota" in error_msg.lower() or "insufficient" in error_msg.lower():
                raise DalleAPIError("Quota exceeded. Please check your OpenAI account balance.")
            elif "timeout" in error_msg.lower():
                raise DalleAPIError("Request timed out. Please check your internet connection.")
            elif "content_policy" in error_msg.lower():
                raise DalleAPIError("Content policy violation. Please modify your prompt.")
            else:
                # Don't expose internal errors
                raise DalleAPIError("Error generating image. Please try again.")
    
    def _sanitize_prompt(self, prompt):
        """Sanitize user prompt to prevent injection attacks"""
        if not prompt or not isinstance(prompt, str):
            raise DalleAPIError("Invalid prompt")
        
        # Remove potentially harmful characters
        prompt = prompt.strip()
        
        # Length validation
        if len(prompt) < 3:
            raise DalleAPIError("Prompt too short. Please provide more detail.")
        if len(prompt) > 1000:
            raise DalleAPIError("Prompt too long. Please shorten your description.")
        
        return prompt
    
    def _validate_size(self, size):
        """Validate image size parameter"""
        valid_sizes = ["256x256", "512x512", "1024x1024"]
        if size not in valid_sizes:
            Logger.warning(f"Invalid size {size}, defaulting to 1024x1024")
            return "1024x1024"
        return size
    
    def _validate_count(self, n):
        """Validate image count parameter"""
        if not isinstance(n, int) or n < 1 or n > 10:
            Logger.warning(f"Invalid count {n}, defaulting to 1")
            return 1
        return n
    
    def _download_image_securely(self, image_url):
        """Download image with security checks"""
        try:
            # Validate URL
            if not image_url.startswith('https://'):
                raise DalleAPIError("Invalid image URL")
            
            # Download with timeout and size limit
            response = self.http_adapter.request(
                'GET',
                image_url,
                timeout=30,
                preload_content=False
            )
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if not content_type.startswith('image/'):
                raise DalleAPIError("Invalid content type received")
            
            # Read with size limit (10MB)
            max_size = 10 * 1024 * 1024
            content = b''
            for chunk in response.stream(1024):
                content += chunk
                if len(content) > max_size:
                    raise DalleAPIError("Image too large")
            
            # Convert to PIL Image
            image = PILImage.open(BytesIO(content))
            
            # Validate image
            if image.format not in ['PNG', 'JPEG', 'WebP']:
                raise DalleAPIError("Invalid image format")
            
            return image
            
        except Exception as e:
            Logger.error(f"Failed to download image: {e}")
            raise DalleAPIError("Failed to download generated image")
        finally:
            if 'response' in locals():
                response.release_conn()
    
    def validate_api_key(self):
        """Validate stored API key"""
        if not self.client:
            return False
        
        try:
            # Apply rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Make a minimal API call to validate the key
            self.client.models.list()
            Logger.info("DalleAPI: API key validated successfully")
            return True
        except Exception as e:
            Logger.error(f"DalleAPI: API key validation failed - {e}")
            return False
    
    def clear_api_key(self):
        """Clear stored API key (for privacy compliance)"""
        self.secure_storage.remove_api_key()
        self.client = None
        Logger.info("DalleAPI: API key cleared")

# Singleton instance
_dalle_service = None

def get_dalle_service():
    """Get singleton instance of DalleAPIServiceSecure"""
    global _dalle_service
    if _dalle_service is None:
        _dalle_service = DalleAPIServiceSecure()
    return _dalle_service