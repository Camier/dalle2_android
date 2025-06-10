"""
Base Worker Class for DALL-E Android App
Provides foundation for all background workers
"""

import threading
import queue
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Callable
from enum import Enum

class WorkerState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

class WorkerPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class BaseWorker(ABC):
    """
    Abstract base class for all workers in the DALL-E Android app.
    Provides queue management, state handling, and error recovery.
    """
    
    def __init__(self, name: str, max_queue_size: int = 100):
        self.name = name
        self.state = WorkerState.IDLE
        self.queue = queue.PriorityQueue(maxsize=max_queue_size)
        self.thread = None
        self.logger = logging.getLogger(f"Worker.{name}")
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused by default
        self.error_count = 0
        self.max_errors = 5
        self.error_cooldown = 60  # seconds
        self.last_error_time = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        
        # Callbacks
        self.on_task_complete: Optional[Callable] = None
        self.on_task_error: Optional[Callable] = None
        self.on_state_change: Optional[Callable] = None
        
    def start(self):
        """Start the worker thread"""
        if self.state != WorkerState.IDLE:
            self.logger.warning(f"Cannot start worker in state: {self.state}")
            return False
            
        self.state = WorkerState.RUNNING
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run, name=f"Worker-{self.name}")
        self.thread.daemon = True
        self.thread.start()
        self.logger.info(f"Worker {self.name} started")
        self._notify_state_change()
        return True
        
    def stop(self, wait: bool = True, timeout: float = 5.0):
        """Stop the worker thread"""
        if self.state not in [WorkerState.RUNNING, WorkerState.PAUSED]:
            return False
            
        self.logger.info(f"Stopping worker {self.name}")
        self.state = WorkerState.STOPPED
        self._stop_event.set()
        self._pause_event.set()  # Unpause if paused
        
        if wait and self.thread and self.thread.is_alive():
            self.thread.join(timeout)
            
        self._notify_state_change()
        return True
        
    def pause(self):
        """Pause the worker"""
        if self.state == WorkerState.RUNNING:
            self.state = WorkerState.PAUSED
            self._pause_event.clear()
            self.logger.info(f"Worker {self.name} paused")
            self._notify_state_change()
            return True
        return False
        
    def resume(self):
        """Resume the worker"""
        if self.state == WorkerState.PAUSED:
            self.state = WorkerState.RUNNING
            self._pause_event.set()
            self.logger.info(f"Worker {self.name} resumed")
            self._notify_state_change()
            return True
        return False
        
    def add_task(self, task: Any, priority: WorkerPriority = WorkerPriority.NORMAL):
        """Add a task to the worker queue"""
        try:
            # Priority queue expects (priority, task) tuple
            # Lower number = higher priority, so we invert
            self.queue.put((priority.value * -1, time.time(), task), block=False)
            self.logger.debug(f"Task added to {self.name} queue with priority {priority.name}")
            return True
        except queue.Full:
            self.logger.error(f"Queue full for worker {self.name}")
            return False
            
    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics"""
        return {
            "name": self.name,
            "state": self.state.value,
            "queue_size": self.queue.qsize(),
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "error_count": self.error_count,
            "thread_alive": self.thread.is_alive() if self.thread else False
        }
        
    def _run(self):
        """Main worker loop - runs in separate thread"""
        self.logger.info(f"Worker {self.name} thread started")
        
        while not self._stop_event.is_set():
            # Check if paused
            self._pause_event.wait()
            
            # Check error cooldown
            if self.error_count >= self.max_errors:
                if time.time() - self.last_error_time < self.error_cooldown:
                    time.sleep(1)
                    continue
                else:
                    # Reset error count after cooldown
                    self.error_count = 0
                    
            try:
                # Get task from queue with timeout
                priority, timestamp, task = self.queue.get(timeout=1.0)
                
                # Process the task
                self.logger.debug(f"Processing task in {self.name}")
                result = self.process_task(task)
                
                # Handle result
                if result:
                    self.completed_tasks += 1
                    if self.on_task_complete:
                        self.on_task_complete(task, result)
                else:
                    self.failed_tasks += 1
                    if self.on_task_error:
                        self.on_task_error(task, None)
                        
                self.queue.task_done()
                
            except queue.Empty:
                # No tasks, continue loop
                continue
                
            except Exception as e:
                self.error_count += 1
                self.last_error_time = time.time()
                self.failed_tasks += 1
                self.logger.error(f"Error in worker {self.name}: {str(e)}", exc_info=True)
                
                if self.on_task_error:
                    self.on_task_error(None, e)
                    
                if self.error_count >= self.max_errors:
                    self.state = WorkerState.ERROR
                    self.logger.error(f"Worker {self.name} entering error state")
                    self._notify_state_change()
                    
        self.logger.info(f"Worker {self.name} thread stopped")
        
    @abstractmethod
    def process_task(self, task: Any) -> Any:
        """
        Process a single task. Must be implemented by subclasses.
        Returns result on success, None on failure.
        """
        pass
        
    def _notify_state_change(self):
        """Notify state change callback if registered"""
        if self.on_state_change:
            try:
                self.on_state_change(self.state)
            except Exception as e:
                self.logger.error(f"Error in state change callback: {str(e)}")
