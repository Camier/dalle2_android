"""
Worker Manager for DALL-E Android App
Orchestrates all background workers and provides unified interface
"""

import os
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import json

from .base_worker import BaseWorker, WorkerState, WorkerPriority
from .image_processor import ImageProcessingWorker, FilterType
from .settings_sync import SettingsSyncWorker
from .api_request import APIRequestWorker

class WorkerManager:
    """
    Central manager for all background workers in the DALL-E Android app.
    Provides unified interface and orchestration capabilities.
    """
    
    def __init__(self, app_data_dir: str, api_key: str):
        self.app_data_dir = app_data_dir
        self.api_key = api_key
        self.workers: Dict[str, BaseWorker] = {}
        self.logger = logging.getLogger("WorkerManager")
        
        # Initialize directories
        self._setup_directories()
        
        # Initialize workers
        self._initialize_workers()
        
        # Worker callbacks
        self.on_worker_state_change: Optional[Callable] = None
        self.on_task_complete: Optional[Callable] = None
        self.on_task_error: Optional[Callable] = None
        
    def _setup_directories(self):
        """Create necessary directories"""
        dirs = [
            self.app_data_dir,
            os.path.join(self.app_data_dir, "cache"),
            os.path.join(self.app_data_dir, "gallery"),
            os.path.join(self.app_data_dir, "temp"),
            os.path.join(self.app_data_dir, "backups"),
            os.path.join(self.app_data_dir, "exports")
        ]
        
        for directory in dirs:
            os.makedirs(directory, exist_ok=True)
            
    def _initialize_workers(self):
        """Initialize all workers"""
        try:
            # Image Processing Worker
            cache_dir = os.path.join(self.app_data_dir, "cache")
            self.workers['image_processor'] = ImageProcessingWorker(cache_dir)
            
            # Settings Sync Worker
            backup_dir = os.path.join(self.app_data_dir, "backups")
            self.workers['settings_sync'] = SettingsSyncWorker(self.app_data_dir, backup_dir)
            
            # API Request Worker
            self.workers['api_request'] = APIRequestWorker(self.api_key)
            
            # Set up callbacks for all workers
            for name, worker in self.workers.items():
                worker.on_state_change = lambda state, w=name: self._handle_state_change(w, state)
                worker.on_task_complete = lambda task, result, w=name: self._handle_task_complete(w, task, result)
                worker.on_task_error = lambda task, error, w=name: self._handle_task_error(w, task, error)
                
            self.logger.info(f"Initialized {len(self.workers)} workers")
            
        except Exception as e:
            self.logger.error(f"Error initializing workers: {str(e)}")
            raise
            
    def start_all(self):
        """Start all workers"""
        for name, worker in self.workers.items():
            if worker.start():
                self.logger.info(f"Started worker: {name}")
            else:
                self.logger.warning(f"Failed to start worker: {name}")
                
    def stop_all(self, wait: bool = True, timeout: float = 5.0):
        """Stop all workers"""
        for name, worker in self.workers.items():
            if worker.stop(wait, timeout):
                self.logger.info(f"Stopped worker: {name}")
            else:
                self.logger.warning(f"Failed to stop worker: {name}")
                
    def pause_worker(self, worker_name: str) -> bool:
        """Pause a specific worker"""
        if worker_name in self.workers:
            return self.workers[worker_name].pause()
        return False
        
    def resume_worker(self, worker_name: str) -> bool:
        """Resume a specific worker"""
        if worker_name in self.workers:
            return self.workers[worker_name].resume()
        return False
        
    def get_worker(self, worker_name: str) -> Optional[BaseWorker]:
        """Get a specific worker instance"""
        return self.workers.get(worker_name)
        
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all workers"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "workers": {}
        }
        
        for name, worker in self.workers.items():
            stats["workers"][name] = worker.get_stats()
            
        # Add specific worker stats
        if 'api_request' in self.workers:
            api_worker = self.workers['api_request']
            stats["api_stats"] = api_worker.get_request_stats()
            
        if 'image_processor' in self.workers:
            img_worker = self.workers['image_processor']
            stats["image_processing"] = {
                "average_time": img_worker.get_average_processing_time()
            }
            
        return stats
        
    # High-level task methods
    
    def resize_image(self, image_path: str, output_path: str,
                    width: int, height: int,
                    callback: Optional[Callable] = None) -> bool:
        """Resize image for variations or other processing"""
        if 'image_processor' not in self.workers:
            self.logger.error("Image processor worker not available")
            return False
            
        worker = self.workers['image_processor']
        return worker.add_resize_task(
            image_path=image_path,
            output_path=output_path,
            width=width,
            height=height,
            callback=callback
        )
        
    def export_settings(self, destination: str = None,
                       include_images: bool = False,
                       callback: Optional[Callable] = None) -> bool:
        """Export app settings"""
        if 'settings_sync' not in self.workers:
            self.logger.error("Settings sync worker not available")
            return False
            
        worker = self.workers['settings_sync']
        return worker.add_export_task(
            destination=destination,
            include_images=include_images,
            callback=callback
        )
        
    def import_settings(self, source: str,
                       callback: Optional[Callable] = None) -> bool:
        """Import app settings"""
        if 'settings_sync' not in self.workers:
            self.logger.error("Settings sync worker not available")
            return False
            
        worker = self.workers['settings_sync']
        return worker.add_import_task(
            source=source,
            callback=callback
        )
        
    def generate_image(self, prompt: str,
                      n: int = 1,
                      size: str = "1024x1024",
                      callback: Optional[Callable] = None) -> bool:
        """Generate image using DALL-E API"""
        if 'api_request' not in self.workers:
            self.logger.error("API request worker not available")
            return False
            
        worker = self.workers['api_request']
        return worker.add_generation_request(
            prompt=prompt,
            n=n,
            size=size,
            callback=callback
        )
        
    def generate_image_variations(self, image_path: str,
                                count: int = 2,
                                callback: Optional[Callable] = None) -> bool:
        """Generate variations of an image using DALL-E API"""
        if 'api_request' not in self.workers:
            self.logger.error("API request worker not available")
            return False
        
        # Process variations with image download and saving
        def on_variations_complete(api_result):
            if api_result.get('success'):
                variations = []
                gallery_dir = os.path.join(self.app_data_dir, "gallery")
                
                # Download and save each variation
                for i, image_data in enumerate(api_result.get('images', [])):
                    try:
                        import requests
                        from datetime import datetime
                        
                        # Download image
                        response = requests.get(image_data['url'], timeout=30)
                        if response.status_code == 200:
                            # Generate filename
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"variation_{timestamp}_{i}.png"
                            filepath = os.path.join(gallery_dir, filename)
                            
                            # Save image
                            with open(filepath, 'wb') as f:
                                f.write(response.content)
                            
                            variations.append(filepath)
                            self.logger.info(f"Saved variation: {filename}")
                    except Exception as e:
                        self.logger.error(f"Failed to save variation {i}: {str(e)}")
                
                # Update result with local paths
                result = {
                    'success': True,
                    'variations': variations,
                    'count': len(variations),
                    'source_image': image_path
                }
                
                if callback:
                    callback(result)
            else:
                if callback:
                    callback(api_result)
        
        worker = self.workers['api_request']
        return worker.add_variation_request(
            image_path=image_path,
            n=count,
            size="1024x1024",
            callback=on_variations_complete
        )
        
    def create_backup(self, reason: str = "manual",
                     callback: Optional[Callable] = None) -> bool:
        """Create settings backup"""
        if 'settings_sync' not in self.workers:
            self.logger.error("Settings sync worker not available")
            return False
            
        worker = self.workers['settings_sync']
        return worker.add_backup_task(
            reason=reason,
            callback=callback
        )
        
    # Orchestration methods
    
    def process_batch_generation(self, prompt: str, count: int,
                               size: str = "1024x1024",
                               apply_filters: Dict[FilterType, float] = None,
                               callback: Optional[Callable] = None):
        """
        Orchestrate batch image generation with optional filters.
        Combines API request and image processing workers.
        """
        
        def on_api_complete(result):
            if result.get('success') and apply_filters:
                # Process each generated image with filters
                for i, image_data in enumerate(result['images']):
                    # Download image first (would need implementation)
                    # Then apply filters
                    pass
                    
            if callback:
                callback(result)
                
        # Start API request
        self.generate_image(
            prompt=prompt,
            n=count,
            size=size,
            callback=on_api_complete
        )
        
    def backup_and_export(self, export_path: str,
                         include_images: bool = False,
                         callback: Optional[Callable] = None):
        """Create backup before exporting"""
        
        def on_backup_complete(result):
            if result.get('success'):
                # Now export
                self.export_settings(
                    destination=export_path,
                    include_images=include_images,
                    callback=callback
                )
            elif callback:
                callback(result)
                
        # First create backup
        self.create_backup(
            reason="pre-export",
            callback=on_backup_complete
        )
        
    # Callback handlers
    
    def _handle_state_change(self, worker_name: str, state: WorkerState):
        """Handle worker state change"""
        self.logger.info(f"Worker {worker_name} state changed to {state.value}")
        
        if self.on_worker_state_change:
            self.on_worker_state_change(worker_name, state)
            
        # Auto-restart on error
        if state == WorkerState.ERROR:
            self.logger.warning(f"Worker {worker_name} in error state, attempting restart")
            worker = self.workers.get(worker_name)
            if worker:
                worker.stop(wait=False)
                worker.error_count = 0
                worker.start()
                
    def _handle_task_complete(self, worker_name: str, task: Any, result: Any):
        """Handle task completion"""
        self.logger.debug(f"Task completed in {worker_name}")
        
        if self.on_task_complete:
            self.on_task_complete(worker_name, task, result)
            
    def _handle_task_error(self, worker_name: str, task: Any, error: Any):
        """Handle task error"""
        self.logger.error(f"Task error in {worker_name}: {str(error)}")
        
        if self.on_task_error:
            self.on_task_error(worker_name, task, error)
            
    # Utility methods
    
    def save_stats(self, filepath: str = None):
        """Save worker statistics to file"""
        if not filepath:
            filepath = os.path.join(self.app_data_dir, "worker_stats.json")
            
        stats = self.get_all_stats()
        
        with open(filepath, 'w') as f:
            json.dump(stats, f, indent=2)
            
        self.logger.info(f"Saved worker stats to {filepath}")
        
    def update_api_key(self, new_api_key: str):
        """Update API key for API worker"""
        self.api_key = new_api_key
        
        if 'api_request' in self.workers:
            api_worker = self.workers['api_request']
            api_worker.update_api_key(new_api_key)
            self.logger.info("API key updated")
