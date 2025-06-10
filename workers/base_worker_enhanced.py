"""
Enhanced Base Worker Class for DALL-E Android App
Provides foundation for all background workers with improved thread safety
and Kivy integration support
"""

import threading
import queue
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import weakref
from concurrent.futures import ThreadPoolExecutor, Future
import contextvars

# Import Kivy bridge if available
try:
    from .kivy_worker_bridge import KivyWorkerMixin, WorkerTaskWrapper
    KIVY_AVAILABLE = True
except ImportError:
    KIVY_AVAILABLE = False
    KivyWorkerMixin = object
    WorkerTaskWrapper = None


class WorkerState(Enum):
    """Worker states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"


class WorkerPriority(Enum):
    """Task priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class WorkerTask:
    """Enhanced task structure with metadata"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    data: Any = None
    priority: WorkerPriority = WorkerPriority.NORMAL
    created_at: float = field(default_factory=time.time)
    timeout: Optional[float] = None
    callback: Optional[Callable] = None
    error_callback: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """For priority queue sorting"""
        if not isinstance(other, WorkerTask):
            return NotImplemented
        # Higher priority = lower number for queue
        return (-self.priority.value, self.created_at) < (-other.priority.value, other.created_at)


class BaseWorkerEnhanced(ABC, KivyWorkerMixin):
    """
    Enhanced abstract base class for all workers.
    Features:
    - Better thread safety with locks
    - Task timeout support
    - Graceful shutdown
    - Kivy integration support
    - Task lifecycle callbacks
    - Performance metrics
    """
    
    def __init__(self, name: str, max_queue_size: int = 100, 
                 max_workers: int = 1, enable_metrics: bool = True):
        super().__init__()
        self.name = name
        self.state = WorkerState.IDLE
        self.state_lock = threading.RLock()
        
        # Enhanced queue with task wrapper
        self.task_queue = queue.PriorityQueue(maxsize=max_queue_size)
        
        # Thread pool for concurrent processing
        self.max_workers = max_workers
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.active_futures: weakref.WeakSet = weakref.WeakSet()
        
        # Control events
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused by default
        
        # Logging
        self.logger = logging.getLogger(f"Worker.{name}")
        
        # Error handling
        self.error_count = 0
        self.max_errors = 5
        self.error_cooldown = 60  # seconds
        self.last_error_time = 0
        
        # Metrics
        self.enable_metrics = enable_metrics
        self.metrics = {
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0,
            "current_queue_size": 0,
            "peak_queue_size": 0
        }
        self.metrics_lock = threading.Lock()
        
        # Callbacks
        self.on_task_complete: Optional[Callable] = None
        self.on_task_error: Optional[Callable] = None
        self.on_state_change: Optional[Callable] = None
        self.on_task_timeout: Optional[Callable] = None
        
        # Context for thread-local storage
        self.context = contextvars.ContextVar(f'{name}_context', default={})
        
    def start(self) -> bool:
        """Start the worker with thread pool"""
        with self.state_lock:
            if self.state != WorkerState.IDLE:
                self.logger.warning(f"Cannot start worker in state: {self.state}")
                return False
            
            self.state = WorkerState.RUNNING
            self._stop_event.clear()
            
            # Create thread pool
            self.thread_pool = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix=f"Worker-{self.name}"
            )
            
            # Start main processing thread
            self.main_thread = threading.Thread(
                target=self._run,
                name=f"Worker-{self.name}-Main"
            )
            self.main_thread.daemon = True
            self.main_thread.start()
            
            self.logger.info(f"Worker {self.name} started with {self.max_workers} workers")
            self._notify_state_change()
            return True
    
    def stop(self, wait: bool = True, timeout: float = 5.0) -> bool:
        """Stop the worker gracefully"""
        with self.state_lock:
            if self.state not in [WorkerState.RUNNING, WorkerState.PAUSED]:
                return False
            
            self.logger.info(f"Stopping worker {self.name}")
            self.state = WorkerState.SHUTTING_DOWN
            self._stop_event.set()
            self._pause_event.set()  # Unpause if paused
        
        # Cancel active tasks
        for future in list(self.active_futures):
            if not future.done():
                future.cancel()
        
        # Shutdown thread pool
        if self.thread_pool:
            self.thread_pool.shutdown(wait=wait, cancel_futures=True)
            self.thread_pool = None
        
        # Wait for main thread
        if wait and hasattr(self, 'main_thread') and self.main_thread.is_alive():
            self.main_thread.join(timeout)
        
        with self.state_lock:
            self.state = WorkerState.STOPPED
            
        self._notify_state_change()
        return True
    
    def pause(self) -> bool:
        """Pause the worker"""
        with self.state_lock:
            if self.state == WorkerState.RUNNING:
                self.state = WorkerState.PAUSED
                self._pause_event.clear()
                self.logger.info(f"Worker {self.name} paused")
                self._notify_state_change()
                return True
        return False
    
    def resume(self) -> bool:
        """Resume the worker"""
        with self.state_lock:
            if self.state == WorkerState.PAUSED:
                self.state = WorkerState.RUNNING
                self._pause_event.set()
                self.logger.info(f"Worker {self.name} resumed")
                self._notify_state_change()
                return True
        return False
    
    def add_task(self, task_data: Any, priority: WorkerPriority = WorkerPriority.NORMAL,
                 timeout: Optional[float] = None, callback: Optional[Callable] = None,
                 error_callback: Optional[Callable] = None, **metadata) -> Optional[str]:
        """
        Add a task to the worker queue with enhanced options.
        
        Returns:
            Task ID if successful, None if queue is full
        """
        task = WorkerTask(
            data=task_data,
            priority=priority,
            timeout=timeout,
            callback=callback,
            error_callback=error_callback,
            metadata=metadata
        )
        
        try:
            self.task_queue.put(task, block=False)
            self.logger.debug(f"Task {task.id} added to {self.name} queue")
            
            # Update metrics
            if self.enable_metrics:
                with self.metrics_lock:
                    current_size = self.task_queue.qsize()
                    self.metrics["current_queue_size"] = current_size
                    if current_size > self.metrics["peak_queue_size"]:
                        self.metrics["peak_queue_size"] = current_size
                        
            return task.id
            
        except queue.Full:
            self.logger.error(f"Queue full for worker {self.name}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive worker statistics"""
        with self.state_lock:
            state = self.state.value
            
        with self.metrics_lock:
            metrics = self.metrics.copy()
            
        return {
            "name": self.name,
            "state": state,
            "queue_size": self.task_queue.qsize(),
            "active_tasks": len(self.active_futures),
            "error_count": self.error_count,
            **metrics
        }
    
    def _run(self):
        """Enhanced main worker loop"""
        self.logger.info(f"Worker {self.name} main thread started")
        
        while not self._stop_event.is_set():
            # Check if paused
            self._pause_event.wait()
            
            # Check error cooldown
            if self._should_cooldown():
                time.sleep(1)
                continue
            
            try:
                # Get task with timeout
                task = self.task_queue.get(timeout=1.0)
                
                # Submit to thread pool
                future = self.thread_pool.submit(self._process_task_wrapper, task)
                self.active_futures.add(future)
                
                # Add completion callback
                future.add_done_callback(
                    lambda f: self._handle_task_completion(f, task)
                )
                
            except queue.Empty:
                continue
            except Exception as e:
                self._handle_error(e)
        
        self.logger.info(f"Worker {self.name} main thread stopped")
    
    def _process_task_wrapper(self, task: WorkerTask) -> Tuple[bool, Any]:
        """Wrapper for task processing with timeout and error handling"""
        start_time = time.time()
        
        # Create task wrapper if Kivy bridge is available
        task_wrapper = None
        if KIVY_AVAILABLE and self.kivy_bridge:
            task_wrapper = self.create_task_wrapper(task.id)
        
        try:
            # Set context
            self.context.set({"task_id": task.id, "task_wrapper": task_wrapper})
            
            # Process with timeout if specified
            if task.timeout:
                # Use threading timer for timeout
                timeout_event = threading.Event()
                
                def timeout_handler():
                    timeout_event.set()
                    raise TimeoutError(f"Task {task.id} timed out after {task.timeout}s")
                
                timer = threading.Timer(task.timeout, timeout_handler)
                timer.start()
                
                try:
                    result = self.process_task(task.data)
                    timer.cancel()
                    return True, result
                except TimeoutError:
                    if self.on_task_timeout:
                        self.on_task_timeout(task)
                    return False, None
            else:
                result = self.process_task(task.data)
                return True, result
                
        except Exception as e:
            self.logger.error(f"Error processing task {task.id}: {str(e)}", exc_info=True)
            return False, e
        finally:
            # Update metrics
            if self.enable_metrics:
                processing_time = time.time() - start_time
                self._update_metrics(processing_time)
    
    def _handle_task_completion(self, future: Future, task: WorkerTask):
        """Handle task completion from future"""
        try:
            success, result = future.result()
            
            if success:
                self.logger.debug(f"Task {task.id} completed successfully")
                
                # Call task-specific callback
                if task.callback:
                    self._safe_callback(task.callback, result)
                
                # Call global callback
                if self.on_task_complete:
                    self._safe_callback(self.on_task_complete, task, result)
                    
                # Update metrics
                with self.metrics_lock:
                    self.metrics["completed_tasks"] += 1
            else:
                self.logger.error(f"Task {task.id} failed")
                
                # Call error callbacks
                if task.error_callback:
                    self._safe_callback(task.error_callback, result)
                    
                if self.on_task_error:
                    self._safe_callback(self.on_task_error, task, result)
                
                # Update metrics
                with self.metrics_lock:
                    self.metrics["failed_tasks"] += 1
                    
                self._handle_error(result if isinstance(result, Exception) else None)
                
        except Exception as e:
            self.logger.error(f"Error in task completion handler: {str(e)}", exc_info=True)
        finally:
            # Ensure task is marked done
            self.task_queue.task_done()
    
    def _safe_callback(self, callback: Callable, *args, **kwargs):
        """Execute callback safely"""
        try:
            # If Kivy bridge is available, schedule on main thread
            if KIVY_AVAILABLE and self.kivy_bridge:
                self.schedule_ui_callback(callback, *args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Error in callback: {str(e)}", exc_info=True)
    
    def _should_cooldown(self) -> bool:
        """Check if worker should be in error cooldown"""
        if self.error_count >= self.max_errors:
            if time.time() - self.last_error_time < self.error_cooldown:
                return True
            else:
                # Reset error count after cooldown
                self.error_count = 0
        return False
    
    def _handle_error(self, error: Optional[Exception]):
        """Handle worker error"""
        self.error_count += 1
        self.last_error_time = time.time()
        
        if self.error_count >= self.max_errors:
            with self.state_lock:
                self.state = WorkerState.ERROR
            self.logger.error(f"Worker {self.name} entering error state")
            self._notify_state_change()
    
    def _update_metrics(self, processing_time: float):
        """Update performance metrics"""
        with self.metrics_lock:
            self.metrics["total_processing_time"] += processing_time
            total_tasks = self.metrics["completed_tasks"] + self.metrics["failed_tasks"]
            if total_tasks > 0:
                self.metrics["average_processing_time"] = (
                    self.metrics["total_processing_time"] / total_tasks
                )
            self.metrics["current_queue_size"] = self.task_queue.qsize()
    
    def _notify_state_change(self):
        """Notify state change callback if registered"""
        if self.on_state_change:
            self._safe_callback(self.on_state_change, self.state)
    
    @abstractmethod
    def process_task(self, task_data: Any) -> Any:
        """
        Process a single task. Must be implemented by subclasses.
        
        Args:
            task_data: The task data to process
            
        Returns:
            Result on success
            
        Raises:
            Exception on failure
        """
        pass
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current task context (thread-safe)"""
        return self.context.get({})
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop(wait=True)
        self.task_queue = None
        self.active_futures.clear()