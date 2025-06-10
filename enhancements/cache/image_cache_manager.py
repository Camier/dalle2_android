"""
Advanced Image Cache Manager with LRU eviction and disk persistence
"""

import os
import json
import time
import hashlib
from typing import Optional, Dict, Any
from collections import OrderedDict
import threading
from pathlib import Path

class ImageCacheManager:
    def __init__(self, cache_dir: str, max_memory_mb: int = 100, max_disk_mb: int = 500):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.max_disk_bytes = max_disk_mb * 1024 * 1024
        
        self.memory_cache = OrderedDict()
        self.cache_lock = threading.RLock()
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        
        self._load_metadata()
        
    def _get_cache_key(self, prompt: str, params: Dict[str, Any]) -> str:
        """Generate unique cache key from prompt and parameters"""
        cache_data = f"{prompt}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(cache_data.encode()).hexdigest()
    
    def get(self, prompt: str, params: Dict[str, Any]) -> Optional[bytes]:
        """Retrieve image from cache"""
        cache_key = self._get_cache_key(prompt, params)
        
        with self.cache_lock:
            # Check memory cache first
            if cache_key in self.memory_cache:
                # Move to end (LRU)
                self.memory_cache.move_to_end(cache_key)
                return self.memory_cache[cache_key]['data']
            
            # Check disk cache
            cache_file = self.cache_dir / f"{cache_key}.jpg"
            if cache_file.exists():
                try:
                    with open(cache_file, 'rb') as f:
                        image_data = f.read()
                    
                    # Add to memory cache
                    self._add_to_memory_cache(cache_key, image_data)
                    return image_data
                except Exception:
                    # Remove corrupted cache file
                    cache_file.unlink(missing_ok=True)
        
        return None
    
    def put(self, prompt: str, params: Dict[str, Any], image_data: bytes):
        """Store image in cache"""
        cache_key = self._get_cache_key(prompt, params)
        
        with self.cache_lock:
            # Add to memory cache
            self._add_to_memory_cache(cache_key, image_data)
            
            # Save to disk
            cache_file = self.cache_dir / f"{cache_key}.jpg"
            try:
                with open(cache_file, 'wb') as f:
                    f.write(image_data)
                
                # Update metadata
                self._update_metadata(cache_key, prompt, params, len(image_data))
            except Exception as e:
                print(f"Failed to save cache to disk: {e}")
    
    def _add_to_memory_cache(self, cache_key: str, image_data: bytes):
        """Add image to memory cache with LRU eviction"""
        size = len(image_data)
        
        # Remove items if necessary
        current_size = sum(item['size'] for item in self.memory_cache.values())
        while current_size + size > self.max_memory_bytes and self.memory_cache:
            # Remove least recently used
            self.memory_cache.popitem(last=False)
            current_size = sum(item['size'] for item in self.memory_cache.values())
        
        self.memory_cache[cache_key] = {
            'data': image_data,
            'size': size,
            'timestamp': time.time()
        }
    
    def _load_metadata(self):
        """Load cache metadata from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except:
                self.metadata = {}
        else:
            self.metadata = {}
    
    def _update_metadata(self, cache_key: str, prompt: str, params: Dict[str, Any], size: int):
        """Update cache metadata"""
        self.metadata[cache_key] = {
            'prompt': prompt,
            'params': params,
            'size': size,
            'timestamp': time.time()
        }
        
        # Enforce disk cache size limit
        self._evict_disk_cache()
        
        # Save metadata
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Failed to save metadata: {e}")
    
    def _evict_disk_cache(self):
        """Evict old items from disk cache if size limit exceeded"""
        total_size = sum(item['size'] for item in self.metadata.values())
        
        if total_size > self.max_disk_bytes:
            # Sort by timestamp (oldest first)
            sorted_items = sorted(
                self.metadata.items(),
                key=lambda x: x[1]['timestamp']
            )
            
            # Remove oldest items until under limit
            for cache_key, _ in sorted_items:
                if total_size <= self.max_disk_bytes:
                    break
                
                cache_file = self.cache_dir / f"{cache_key}.jpg"
                if cache_file.exists():
                    size = self.metadata[cache_key]['size']
                    cache_file.unlink()
                    del self.metadata[cache_key]
                    total_size -= size
    
    def clear_cache(self):
        """Clear all caches"""
        with self.cache_lock:
            self.memory_cache.clear()
            
            # Clear disk cache
            for cache_file in self.cache_dir.glob("*.jpg"):
                cache_file.unlink()
            
            self.metadata = {}
            if self.metadata_file.exists():
                self.metadata_file.unlink()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.cache_lock:
            memory_size = sum(item['size'] for item in self.memory_cache.values())
            disk_size = sum(item['size'] for item in self.metadata.values())
            
            return {
                'memory_items': len(self.memory_cache),
                'memory_size_mb': memory_size / (1024 * 1024),
                'disk_items': len(self.metadata),
                'disk_size_mb': disk_size / (1024 * 1024),
                'hit_rate': self._calculate_hit_rate()
            }
    
    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate (placeholder - implement with actual metrics)"""
        # In production, track hits and misses
        return 0.0
