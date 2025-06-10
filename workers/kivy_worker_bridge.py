"""
Kivy Worker Bridge - Thread-safe communication between workers and Kivy UI
Based on Kivy's Clock for proper main thread execution
"""

from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from typing import Callable, Any, Dict, Optional
import threading
import queue
import logging
from functools import partial


class KivyWorkerBridge(EventDispatcher):
    """
    Bridge between background workers and Kivy UI.
    Ensures all UI updates happen on the main thread using Clock.
    """
    
    # Properties that can be observed by UI
    worker_state = StringProperty('idle')
    progress_value = NumericProperty(0)
    progress_text = StringProperty('')
    is_busy = BooleanProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = logging.getLogger("KivyWorkerBridge")
        
        # Thread-safe queue for UI updates
        self.ui_update_queue = queue.Queue()
        
        # Schedule periodic processing of UI updates
        Clock.schedule_interval(self._process_ui_updates, 1/60.0)  # 60 FPS
        
        # Callback storage
        self.callbacks: Dict[str, Callable] = {}
        
    def _process_ui_updates(self, dt):
        """Process pending UI updates on main thread"""
        processed = 0
        max_updates_per_frame = 10  # Prevent blocking
        
        while not self.ui_update_queue.empty() and processed < max_updates_per_frame:
            try:
                update = self.ui_update_queue.get_nowait()
                self._execute_update(update)
                processed += 1
            except queue.Empty:
                break
            except Exception as e:
                self.logger.error(f"Error processing UI update: {e}")
                
    def _execute_update(self, update: Dict[str, Any]):
        """Execute a UI update on the main thread"""
        update_type = update.get('type')
        
        if update_type == 'property':
            # Update a property
            prop_name = update.get('property')
            value = update.get('value')
            if hasattr(self, prop_name):
                setattr(self, prop_name, value)
                
        elif update_type == 'callback':
            # Execute a callback
            callback_id = update.get('callback_id')
            args = update.get('args', ())
            kwargs = update.get('kwargs', {})
            
            if callback_id in self.callbacks:
                try:
                    self.callbacks[callback_id](*args, **kwargs)
                except Exception as e:
                    self.logger.error(f"Callback error: {e}")
                    
        elif update_type == 'event':
            # Dispatch an event
            event_name = update.get('event')
            args = update.get('args', ())
            self.dispatch(event_name, *args)
            
    def schedule_ui_update(self, update_type: str, **kwargs):
        """
        Schedule a UI update from any thread.
        
        Args:
            update_type: Type of update ('property', 'callback', 'event')
            **kwargs: Update parameters
        """
        update = {'type': update_type, **kwargs}
        self.ui_update_queue.put(update)
        
    def register_callback(self, callback_id: str, callback: Callable):
        """Register a callback that can be called from workers"""
        self.callbacks[callback_id] = callback
        
    def unregister_callback(self, callback_id: str):
        """Unregister a callback"""
        self.callbacks.pop(callback_id, None)
        
    def update_progress(self, value: float, text: str = ''):
        """Update progress from worker thread"""
        self.schedule_ui_update(
            'property',
            property='progress_value',
            value=value
        )
        if text:
            self.schedule_ui_update(
                'property',
                property='progress_text',
                value=text
            )
            
    def set_busy(self, busy: bool):
        """Set busy state from worker thread"""
        self.schedule_ui_update(
            'property',
            property='is_busy',
            value=busy
        )
        
    def call_on_main_thread(self, func: Callable, *args, **kwargs):
        """
        Execute a function on the main thread.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        # Use Clock.schedule_once for immediate execution
        Clock.schedule_once(lambda dt: func(*args, **kwargs), 0)
        
    def call_later(self, func: Callable, delay: float, *args, **kwargs):
        """
        Execute a function on the main thread after a delay.
        
        Args:
            func: Function to execute
            delay: Delay in seconds
            *args: Positional arguments
            **kwargs: Keyword arguments
        """
        Clock.schedule_once(lambda dt: func(*args, **kwargs), delay)


class WorkerTaskWrapper:
    """
    Wrapper for worker tasks that provides Kivy-safe callbacks.
    """
    
    def __init__(self, bridge: KivyWorkerBridge, task_id: str):
        self.bridge = bridge
        self.task_id = task_id
        self.logger = logging.getLogger(f"WorkerTask-{task_id}")
        
    def update_progress(self, progress: float, message: str = ''):
        """Update task progress (thread-safe)"""
        self.bridge.update_progress(progress, message)
        
    def complete(self, result: Any):
        """Mark task as complete with result (thread-safe)"""
        self.bridge.schedule_ui_update(
            'callback',
            callback_id=f'task_complete_{self.task_id}',
            args=(result,)
        )
        self.bridge.set_busy(False)
        
    def error(self, error: Exception):
        """Mark task as failed with error (thread-safe)"""
        self.bridge.schedule_ui_update(
            'callback',
            callback_id=f'task_error_{self.task_id}',
            args=(str(error),)
        )
        self.bridge.set_busy(False)
        
    def log(self, message: str, level: str = 'info'):
        """Log a message (thread-safe)"""
        log_func = getattr(self.logger, level, self.logger.info)
        log_func(message)
        
        # Optionally update UI
        if level in ['error', 'warning']:
            self.bridge.schedule_ui_update(
                'event',
                event='on_worker_log',
                args=(message, level)
            )


class KivyWorkerMixin:
    """
    Mixin for workers to integrate with Kivy UI.
    Add this to your worker classes for Kivy-safe operations.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kivy_bridge = None
        
    def set_kivy_bridge(self, bridge: KivyWorkerBridge):
        """Set the Kivy bridge for UI updates"""
        self.kivy_bridge = bridge
        
    def create_task_wrapper(self, task_id: str) -> WorkerTaskWrapper:
        """Create a task wrapper for Kivy-safe callbacks"""
        if not self.kivy_bridge:
            raise RuntimeError("Kivy bridge not set")
        return WorkerTaskWrapper(self.kivy_bridge, task_id)
        
    def schedule_ui_callback(self, callback: Callable, *args, **kwargs):
        """Schedule a callback on the main thread"""
        if self.kivy_bridge:
            self.kivy_bridge.call_on_main_thread(callback, *args, **kwargs)
        else:
            # Fallback to direct call if no bridge
            callback(*args, **kwargs)


def create_kivy_safe_callback(bridge: KivyWorkerBridge, callback: Callable) -> Callable:
    """
    Create a thread-safe callback that executes on Kivy main thread.
    
    Args:
        bridge: KivyWorkerBridge instance
        callback: Original callback function
        
    Returns:
        Thread-safe wrapper function
    """
    def safe_callback(*args, **kwargs):
        bridge.call_on_main_thread(callback, *args, **kwargs)
    
    return safe_callback


# Example usage in a screen
"""
from workers.kivy_worker_bridge import KivyWorkerBridge, create_kivy_safe_callback

class MyScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create bridge
        self.worker_bridge = KivyWorkerBridge()
        
        # Bind to bridge properties
        self.worker_bridge.bind(
            is_busy=self.on_worker_busy,
            progress_value=self.on_progress_update
        )
        
        # Register callbacks
        self.worker_bridge.register_callback(
            'filter_complete',
            self.on_filter_complete
        )
        
    def start_filter_task(self):
        app = MDApp.get_running_app()
        
        # Create safe callback
        safe_callback = create_kivy_safe_callback(
            self.worker_bridge,
            self.on_filter_result
        )
        
        # Start worker task
        app.worker_manager.process_image_filters(
            image_path="input.png",
            output_path="output.png",
            brightness=50,
            callback=safe_callback
        )
        
        # Update UI state
        self.worker_bridge.set_busy(True)
        
    def on_worker_busy(self, instance, value):
        # Update UI based on busy state
        self.ids.progress_spinner.active = value
        
    def on_progress_update(self, instance, value):
        # Update progress bar
        self.ids.progress_bar.value = value
"""