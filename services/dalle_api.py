"""
DALL-E 2 API Service
Handles all interactions with OpenAI's DALL-E API
"""

import requests
from openai import OpenAI
from io import BytesIO
from PIL import Image as PILImage
import time

class DalleAPIError(Exception):
    pass

class DalleAPIService:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.client = None
        if api_key:
            self.set_api_key(api_key)
    
    def set_api_key(self, api_key):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
    
    def generate_image(self, prompt, size="1024x1024", n=1):
        if not self.client:
            raise DalleAPIError("API key not set")
        
        try:
            response = self.client.images.generate(
                prompt=prompt,
                model="dall-e-2",
                size=size,
                n=n
            )
            
            # Get the image URL
            image_url = response.data[0].url
            
            # Download the image
            image_response = requests.get(image_url, timeout=30)
            image_response.raise_for_status()
            
            # Convert to PIL Image
            image = PILImage.open(BytesIO(image_response.content))
            
            return image, image_url
            
        except Exception as e:
            error_msg = str(e)
            
            # Handle specific errors
            if "api_key" in error_msg.lower():
                raise DalleAPIError("Invalid API key. Please check your OpenAI API key.")
            elif "rate_limit" in error_msg.lower():
                raise DalleAPIError("Rate limit exceeded. Please try again later.")
            elif "quota" in error_msg.lower():
                raise DalleAPIError("Quota exceeded. Please check your OpenAI account.")
            elif "timeout" in error_msg.lower():
                raise DalleAPIError("Request timed out. Please check your internet connection.")
            else:
                raise DalleAPIError(f"Error generating image: {error_msg}")
    
    def validate_api_key(self):
        if not self.client:
            return False
        
        try:
            # Make a minimal API call to validate the key
            self.client.models.list()
            return True
        except Exception:
            return False