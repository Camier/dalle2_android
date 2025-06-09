"""
Image utility functions for saving images to device gallery
Enhanced with proper MediaStore integration
"""

import os
import io
from datetime import datetime
from typing import Optional, Callable, Tuple
from PIL import Image as PILImage
from kivy.utils import platform
from kivy.graphics.texture import Texture

# Import our new Android utilities
try:
    from utils.android_utils import media_store_helper, permission_handler
except ImportError:
    # Fallback if module not available
    media_store_helper = None
    permission_handler = None


class ImageProcessor:
    """Enhanced image processing with gallery integration"""
    
    def __init__(self):
        self.gallery_path = self._get_gallery_path()
    
    def _get_gallery_path(self):
        """Get the gallery directory path"""
        if platform == 'android':
            from android.storage import primary_external_storage_path
            base_dir = primary_external_storage_path()
            gallery_dir = os.path.join(base_dir, "Pictures", "DALLE")
        else:
            home = os.path.expanduser('~')
            gallery_dir = os.path.join(home, "Pictures", "DALLE")
        
        os.makedirs(gallery_dir, exist_ok=True)
        return gallery_dir
    
    def get_gallery_path(self):
        """Public method to get gallery path"""
        return self.gallery_path
    
    def save_to_gallery(self, image_data: bytes, prompt: str = None, 
                       filename: str = None) -> Optional[str]:
        """
        Save image to gallery with proper MediaStore integration
        
        Args:
            image_data: Image bytes data
            prompt: Optional prompt for filename generation
            filename: Optional specific filename
            
        Returns:
            Path to saved file or None if failed
        """
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if prompt:
                # Clean prompt for filename
                clean_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_'))
                clean_prompt = clean_prompt.strip().replace(' ', '_')
                filename = f"dalle_{clean_prompt}_{timestamp}.png"
            else:
                filename = f"dalle_{timestamp}.png"
        
        # Use MediaStoreHelper if available (Android)
        if media_store_helper and platform == 'android':
            return media_store_helper.save_to_gallery(
                image_data=image_data,
                filename=filename,
                mime_type="image/png"
            )
        else:
            # Fallback method for desktop or if MediaStore not available
            return self._fallback_save(image_data, filename)
    
    def _fallback_save(self, image_data: bytes, filename: str) -> Optional[str]:
        """Fallback save method"""
        try:
            filepath = os.path.join(self.gallery_path, filename)
            
            # Convert bytes to PIL Image if needed
            if isinstance(image_data, bytes):
                image = PILImage.open(io.BytesIO(image_data))
            else:
                image = image_data
            
            # Save image
            image.save(filepath, 'PNG')
            
            return filepath
        except Exception as e:
            print(f"Error in fallback save: {e}")
            return None
    
    def download_image(self, image_url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            import requests
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error downloading image: {e}")
            return None
    
    def create_texture_from_data(self, image_data: bytes) -> Optional[Texture]:
        """Create Kivy texture from image data"""
        try:
            # Convert bytes to PIL Image
            image = PILImage.open(io.BytesIO(image_data))
            
            # Convert to RGBA
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # Create texture
            texture = Texture.create(size=image.size, colorfmt='rgba')
            texture.blit_buffer(image.tobytes(), colorfmt='rgba', bufferfmt='ubyte')
            texture.flip_vertical()
            
            return texture
        except Exception as e:
            print(f"Error creating texture: {e}")
            return None


# Legacy function for compatibility
def save_image_to_gallery(pil_image, filename=None):
    """
    Legacy function - maintained for compatibility
    Uses new ImageProcessor internally
    """
    processor = ImageProcessor()
    
    # Convert PIL image to bytes
    buffer = io.BytesIO()
    pil_image.save(buffer, format='PNG')
    image_data = buffer.getvalue()
    
    # Use new save method
    return processor.save_to_gallery(image_data, filename=filename)