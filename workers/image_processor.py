"""
Image Processing Worker for DALL-E Android App
Handles image filters and transformations asynchronously
"""

import io
import time
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
from dataclasses import dataclass
from enum import Enum

from .base_worker import BaseWorker, WorkerPriority

class FilterType(Enum):
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    SATURATION = "saturation"
    BLUR = "blur"
    SHARPEN = "sharpen"
    EDGE_ENHANCE = "edge_enhance"
    GRAYSCALE = "grayscale"
    SEPIA = "sepia"
    INVERT = "invert"

@dataclass
class ImageTask:
    """Represents an image processing task"""
    image_path: str
    output_path: str
    filters: Dict[FilterType, float]
    callback: Optional[callable] = None
    metadata: Dict[str, Any] = None

class ImageProcessingWorker(BaseWorker):
    """
    Worker for processing image filters and transformations.
    Handles brightness, contrast, saturation, and other effects.
    """
    
    def __init__(self, cache_dir: str = None):
        super().__init__("ImageProcessor", max_queue_size=50)
        self.cache_dir = cache_dir
        self.processing_times = []
        
    def process_task(self, task: ImageTask) -> Dict[str, Any]:
        """Process image with specified filters"""
        start_time = time.time()
        
        try:
            # Load image
            self.logger.info(f"Processing image: {task.image_path}")
            image = Image.open(task.image_path)
            
            # Convert to RGB if necessary
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
                
            # Apply filters in order
            processed_image = self._apply_filters(image, task.filters)
            
            # Save processed image
            processed_image.save(task.output_path, quality=95, optimize=True)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            self.processing_times.append(processing_time)
            
            # Prepare result
            result = {
                "success": True,
                "input_path": task.image_path,
                "output_path": task.output_path,
                "filters_applied": {k.value: v for k, v in task.filters.items()},
                "processing_time": processing_time,
                "image_size": processed_image.size,
                "file_size": self._get_file_size(task.output_path)
            }
            
            # Call task callback if provided
            if task.callback:
                task.callback(result)
                
            self.logger.info(f"Image processed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing image: {str(e)}")
            error_result = {
                "success": False,
                "error": str(e),
                "input_path": task.image_path
            }
            
            if task.callback:
                task.callback(error_result)
                
            return None
            
    def _apply_filters(self, image: Image.Image, filters: Dict[FilterType, float]) -> Image.Image:
        """Apply multiple filters to an image"""
        result = image.copy()
        
        for filter_type, value in filters.items():
            if filter_type == FilterType.BRIGHTNESS:
                result = self._adjust_brightness(result, value)
            elif filter_type == FilterType.CONTRAST:
                result = self._adjust_contrast(result, value)
            elif filter_type == FilterType.SATURATION:
                result = self._adjust_saturation(result, value)
            elif filter_type == FilterType.BLUR:
                result = self._apply_blur(result, value)
            elif filter_type == FilterType.SHARPEN:
                result = self._apply_sharpen(result, value)
            elif filter_type == FilterType.EDGE_ENHANCE:
                result = result.filter(ImageFilter.EDGE_ENHANCE)
            elif filter_type == FilterType.GRAYSCALE:
                result = result.convert('L').convert('RGB')
            elif filter_type == FilterType.SEPIA:
                result = self._apply_sepia(result, value)
            elif filter_type == FilterType.INVERT:
                result = self._invert_colors(result)
                
        return result
        
    def _adjust_brightness(self, image: Image.Image, factor: float) -> Image.Image:
        """Adjust brightness: -100 to +100 mapped to 0.0 to 2.0"""
        # Convert from -100 to +100 range to 0.0 to 2.0 range
        brightness_factor = (factor + 100) / 100
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(brightness_factor)
        
    def _adjust_contrast(self, image: Image.Image, factor: float) -> Image.Image:
        """Adjust contrast: 0.5x to 2x"""
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(factor)
        
    def _adjust_saturation(self, image: Image.Image, factor: float) -> Image.Image:
        """Adjust saturation: 0 to 2x"""
        enhancer = ImageEnhance.Color(image)
        return enhancer.enhance(factor)
        
    def _apply_blur(self, image: Image.Image, radius: float) -> Image.Image:
        """Apply Gaussian blur with specified radius"""
        return image.filter(ImageFilter.GaussianBlur(radius=radius))
        
    def _apply_sharpen(self, image: Image.Image, factor: float) -> Image.Image:
        """Apply sharpening filter"""
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(factor)
        
    def _apply_sepia(self, image: Image.Image, intensity: float = 1.0) -> Image.Image:
        """Apply sepia tone effect"""
        # Convert to RGB
        img = image.convert('RGB')
        pixels = img.load()
        
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = pixels[x, y]
                
                # Sepia formula
                tr = int(0.393 * r + 0.769 * g + 0.189 * b)
                tg = int(0.349 * r + 0.686 * g + 0.168 * b)
                tb = int(0.272 * r + 0.534 * g + 0.131 * b)
                
                # Blend with original based on intensity
                nr = int(r * (1 - intensity) + tr * intensity)
                ng = int(g * (1 - intensity) + tg * intensity)
                nb = int(b * (1 - intensity) + tb * intensity)
                
                # Clamp values
                pixels[x, y] = (
                    min(255, max(0, nr)),
                    min(255, max(0, ng)),
                    min(255, max(0, nb))
                )
                
        return img
        
    def _invert_colors(self, image: Image.Image) -> Image.Image:
        """Invert image colors"""
        if image.mode == 'RGBA':
            r, g, b, a = image.split()
            rgb_image = Image.merge('RGB', (r, g, b))
            inverted = Image.eval(rgb_image, lambda x: 255 - x)
            r2, g2, b2 = inverted.split()
            return Image.merge('RGBA', (r2, g2, b2, a))
        else:
            return Image.eval(image, lambda x: 255 - x)
            
    def _get_file_size(self, path: str) -> int:
        """Get file size in bytes"""
        import os
        try:
            return os.path.getsize(path)
        except:
            return 0
            
    def add_filter_task(self, image_path: str, output_path: str, 
                       brightness: Optional[float] = None,
                       contrast: Optional[float] = None,
                       saturation: Optional[float] = None,
                       additional_filters: Dict[FilterType, float] = None,
                       priority: WorkerPriority = WorkerPriority.NORMAL,
                       callback: Optional[callable] = None) -> bool:
        """Convenience method to add a filter task"""
        
        filters = {}
        
        if brightness is not None:
            filters[FilterType.BRIGHTNESS] = brightness
        if contrast is not None:
            filters[FilterType.CONTRAST] = contrast
        if saturation is not None:
            filters[FilterType.SATURATION] = saturation
            
        if additional_filters:
            filters.update(additional_filters)
            
        task = ImageTask(
            image_path=image_path,
            output_path=output_path,
            filters=filters,
            callback=callback
        )
        
        return self.add_task(task, priority)
        
    def get_average_processing_time(self) -> float:
        """Get average processing time for performance monitoring"""
        if not self.processing_times:
            return 0.0
        return sum(self.processing_times) / len(self.processing_times)
        
    def clear_stats(self):
        """Clear processing statistics"""
        self.processing_times.clear()
        self.completed_tasks = 0
        self.failed_tasks = 0
