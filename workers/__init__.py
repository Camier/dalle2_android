"""
Workers Package for DALL-E Android App
Enhanced background task processing system with Kivy integration
"""

from .base_worker import BaseWorker, WorkerState, WorkerPriority
from .image_processor import ImageProcessingWorker, FilterType
from .settings_sync import SettingsSyncWorker, SyncOperation
from .api_request import APIRequestWorker, APIRequestType
from .worker_manager import WorkerManager

# Import enhanced components if available
try:
    from .base_worker_enhanced import BaseWorkerEnhanced, WorkerTask
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False
    BaseWorkerEnhanced = None
    WorkerTask = None

# Import Kivy integration if available
try:
    from .kivy_worker_bridge import (
        KivyWorkerBridge, 
        WorkerTaskWrapper, 
        KivyWorkerMixin,
        create_kivy_safe_callback
    )
    KIVY_INTEGRATION_AVAILABLE = True
except ImportError:
    KIVY_INTEGRATION_AVAILABLE = False
    KivyWorkerBridge = None
    WorkerTaskWrapper = None
    KivyWorkerMixin = None
    create_kivy_safe_callback = None

__all__ = [
    # Base classes
    'BaseWorker',
    'BaseWorkerEnhanced',
    'WorkerState', 
    'WorkerPriority',
    'WorkerTask',
    
    # Worker implementations
    'ImageProcessingWorker',
    'FilterType',
    'SettingsSyncWorker',
    'SyncOperation',
    'APIRequestWorker',
    'APIRequestType',
    'WorkerManager',
    
    # Kivy integration
    'KivyWorkerBridge',
    'WorkerTaskWrapper',
    'KivyWorkerMixin',
    'create_kivy_safe_callback',
    
    # Feature flags
    'ENHANCED_AVAILABLE',
    'KIVY_INTEGRATION_AVAILABLE'
]

__version__ = '2.0.0'
