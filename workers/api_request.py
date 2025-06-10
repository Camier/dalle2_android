"""
API Request Worker for DALL-E Android App
Handles DALL-E API calls with retry logic and rate limiting
"""

import time
import json
import requests
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import threading

from .base_worker import BaseWorker, WorkerPriority

class APIRequestType(Enum):
    GENERATE_IMAGE = "generate_image"
    CREATE_VARIATION = "create_variation"
    EDIT_IMAGE = "edit_image"

@dataclass
class APIRequest:
    """Represents an API request"""
    request_type: APIRequestType
    prompt: Optional[str] = None
    n: int = 1
    size: str = "1024x1024"
    quality: str = "standard"
    model: str = "dall-e-2"
    image_path: Optional[str] = None  # For variations/edits
    mask_path: Optional[str] = None   # For edits
    callback: Optional[callable] = None
    metadata: Dict[str, Any] = None
    retry_count: int = 0
    max_retries: int = 3

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: int, per: int):
        self.rate = rate  # Number of requests
        self.per = per    # Per seconds
        self.tokens = rate
        self.last_update = time.time()
        self.lock = threading.Lock()
        
    def acquire(self, tokens: int = 1) -> float:
        """Acquire tokens, returns wait time if rate limited"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_update
            
            # Add tokens based on elapsed time
            self.tokens = min(self.rate, self.tokens + elapsed * (self.rate / self.per))
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return 0.0  # No wait
            else:
                # Calculate wait time
                deficit = tokens - self.tokens
                wait_time = deficit * (self.per / self.rate)
                return wait_time

class APIRequestWorker(BaseWorker):
    """
    Worker for handling DALL-E API requests with rate limiting,
    retry logic, and request batching.
    """
    
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        super().__init__("APIRequest", max_queue_size=100)
        self.api_key = api_key
        self.base_url = base_url
        self.rate_limiter = RateLimiter(rate=50, per=60)  # 50 requests per minute
        self.request_history = []
        self.max_history = 1000
        
        # Retry configuration
        self.retry_delays = [1, 2, 5]  # Exponential backoff
        
        # Headers for API requests
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def process_task(self, request: APIRequest) -> Dict[str, Any]:
        """Process API request with retry logic"""
        
        # Wait for rate limit if needed
        wait_time = self.rate_limiter.acquire(request.n)
        if wait_time > 0:
            self.logger.info(f"Rate limited, waiting {wait_time:.2f}s")
            time.sleep(wait_time)
            
        try:
            if request.request_type == APIRequestType.GENERATE_IMAGE:
                result = self._generate_image(request)
            elif request.request_type == APIRequestType.CREATE_VARIATION:
                result = self._create_variation(request)
            elif request.request_type == APIRequestType.EDIT_IMAGE:
                result = self._edit_image(request)
            else:
                raise ValueError(f"Unknown request type: {request.request_type}")
                
            # Record successful request
            self._record_request(request, result, success=True)
            
            # Call callback if provided
            if request.callback:
                request.callback(result)
                
            return result
            
        except Exception as e:
            # Handle retry logic
            if request.retry_count < request.max_retries:
                delay = self.retry_delays[min(request.retry_count, len(self.retry_delays) - 1)]
                self.logger.warning(f"Request failed, retrying in {delay}s: {str(e)}")
                
                time.sleep(delay)
                request.retry_count += 1
                
                # Re-queue the request
                self.add_task(request, WorkerPriority.HIGH)
                return None
            else:
                # Max retries exceeded
                self.logger.error(f"Request failed after {request.max_retries} retries: {str(e)}")
                error_result = {
                    "success": False,
                    "error": str(e),
                    "request_type": request.request_type.value,
                    "retries": request.retry_count
                }
                
                self._record_request(request, error_result, success=False)
                
                if request.callback:
                    request.callback(error_result)
                    
                return None
                
    def _generate_image(self, request: APIRequest) -> Dict[str, Any]:
        """Generate image using DALL-E API"""
        endpoint = f"{self.base_url}/images/generations"
        
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "n": request.n,
            "size": request.size,
            "quality": request.quality,
            "response_format": "url"  # or "b64_json"
        }
        
        self.logger.info(f"Generating {request.n} image(s) with prompt: {request.prompt[:50]}...")
        
        response = requests.post(
            endpoint,
            headers=self.headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code != 200:
            error_data = response.json()
            raise Exception(f"API Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
        data = response.json()
        
        return {
            "success": True,
            "request_type": "generate_image",
            "images": data['data'],
            "prompt": request.prompt,
            "model": request.model,
            "size": request.size,
            "timestamp": datetime.now().isoformat()
        }
        
    def _create_variation(self, request: APIRequest) -> Dict[str, Any]:
        """Create image variation using DALL-E API"""
        endpoint = f"{self.base_url}/images/variations"
        
        with open(request.image_path, 'rb') as image_file:
            files = {
                'image': ('image.png', image_file, 'image/png')
            }
            
            data = {
                'model': request.model,
                'n': request.n,
                'size': request.size,
                'response_format': 'url'
            }
            
            # Remove Content-Type header for multipart/form-data
            headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
            
            response = requests.post(
                endpoint,
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
            
        if response.status_code != 200:
            error_data = response.json()
            raise Exception(f"API Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
        data = response.json()
        
        return {
            "success": True,
            "request_type": "create_variation",
            "images": data['data'],
            "source_image": request.image_path,
            "model": request.model,
            "size": request.size,
            "timestamp": datetime.now().isoformat()
        }
        
    def _edit_image(self, request: APIRequest) -> Dict[str, Any]:
        """Edit image using DALL-E API"""
        endpoint = f"{self.base_url}/images/edits"
        
        with open(request.image_path, 'rb') as image_file:
            files = {
                'image': ('image.png', image_file, 'image/png')
            }
            
            # Add mask if provided
            if request.mask_path:
                with open(request.mask_path, 'rb') as mask_file:
                    files['mask'] = ('mask.png', mask_file, 'image/png')
                    
            data = {
                'model': request.model,
                'prompt': request.prompt,
                'n': request.n,
                'size': request.size,
                'response_format': 'url'
            }
            
            # Remove Content-Type header for multipart/form-data
            headers = {k: v for k, v in self.headers.items() if k != "Content-Type"}
            
            response = requests.post(
                endpoint,
                headers=headers,
                files=files,
                data=data,
                timeout=60
            )
            
        if response.status_code != 200:
            error_data = response.json()
            raise Exception(f"API Error: {error_data.get('error', {}).get('message', 'Unknown error')}")
            
        data = response.json()
        
        return {
            "success": True,
            "request_type": "edit_image",
            "images": data['data'],
            "prompt": request.prompt,
            "source_image": request.image_path,
            "mask_image": request.mask_path,
            "model": request.model,
            "size": request.size,
            "timestamp": datetime.now().isoformat()
        }
        
    def _record_request(self, request: APIRequest, result: Dict[str, Any], success: bool):
        """Record request for history and analytics"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "request_type": request.request_type.value,
            "success": success,
            "model": request.model,
            "size": request.size,
            "n": request.n,
            "retry_count": request.retry_count
        }
        
        if success and 'images' in result:
            record['image_count'] = len(result['images'])
            
        self.request_history.append(record)
        
        # Maintain max history size
        if len(self.request_history) > self.max_history:
            self.request_history = self.request_history[-self.max_history:]
            
    def add_generation_request(self, prompt: str, 
                             n: int = 1,
                             size: str = "1024x1024",
                             quality: str = "standard",
                             model: str = "dall-e-2",
                             priority: WorkerPriority = WorkerPriority.NORMAL,
                             callback: Optional[callable] = None) -> bool:
        """Add image generation request"""
        request = APIRequest(
            request_type=APIRequestType.GENERATE_IMAGE,
            prompt=prompt,
            n=n,
            size=size,
            quality=quality,
            model=model,
            callback=callback
        )
        return self.add_task(request, priority)
        
    def add_variation_request(self, image_path: str,
                            n: int = 1,
                            size: str = "1024x1024",
                            model: str = "dall-e-2",
                            priority: WorkerPriority = WorkerPriority.NORMAL,
                            callback: Optional[callable] = None) -> bool:
        """Add image variation request"""
        request = APIRequest(
            request_type=APIRequestType.CREATE_VARIATION,
            image_path=image_path,
            n=n,
            size=size,
            model=model,
            callback=callback
        )
        return self.add_task(request, priority)
        
    def get_request_stats(self) -> Dict[str, Any]:
        """Get API request statistics"""
        if not self.request_history:
            return {
                "total_requests": 0,
                "success_rate": 0.0,
                "requests_by_type": {},
                "average_retry_count": 0.0
            }
            
        total = len(self.request_history)
        successful = sum(1 for r in self.request_history if r['success'])
        
        requests_by_type = {}
        total_retries = 0
        
        for record in self.request_history:
            req_type = record['request_type']
            requests_by_type[req_type] = requests_by_type.get(req_type, 0) + 1
            total_retries += record['retry_count']
            
        return {
            "total_requests": total,
            "success_rate": successful / total if total > 0 else 0.0,
            "requests_by_type": requests_by_type,
            "average_retry_count": total_retries / total if total > 0 else 0.0,
            "rate_limit_tokens": self.rate_limiter.tokens
        }
        
    def update_api_key(self, new_api_key: str):
        """Update API key"""
        self.api_key = new_api_key
        self.headers["Authorization"] = f"Bearer {new_api_key}"
        self.logger.info("API key updated")
