"""
Smart Request Queue Manager with priority handling and batch processing
"""

import queue
import threading
import time
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum
import json

class Priority(Enum):
    LOW = 3
    NORMAL = 2
    HIGH = 1
    URGENT = 0

@dataclass(order=True)
class QueuedRequest:
    priority: int
    request_id: str = field(compare=False)
    prompt: str = field(compare=False)
    params: Dict[str, Any] = field(compare=False)
    callback: Optional[Callable] = field(compare=False)
    timestamp: float = field(default_factory=time.time, compare=False)
    retry_count: int = field(default=0, compare=False)

class RequestQueueManager:
    def __init__(self, max_concurrent: int = 3, max_retries: int = 3):
        self.request_queue = queue.PriorityQueue()
        self.active_requests = {}
        self.completed_requests = {}
        self.failed_requests = {}
        
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.is_running = False
        
        self.workers = []
        self.lock = threading.Lock()
        
        # Batch processing
        self.batch_queue = []
        self.batch_size = 5
        self.batch_timeout = 2.0  # seconds
        
    def start(self):
        """Start queue processing"""
        self.is_running = True
        
        # Start worker threads
        for i in range(self.max_concurrent):
            worker = threading.Thread(target=self._process_queue, daemon=True)
            worker.start()
            self.workers.append(worker)
        
        # Start batch processor
        batch_worker = threading.Thread(target=self._process_batches, daemon=True)
        batch_worker.start()
        self.workers.append(batch_worker)
    
    def stop(self):
        """Stop queue processing"""
        self.is_running = False
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5.0)
    
    def add_request(self, prompt: str, params: Dict[str, Any], 
                   priority: Priority = Priority.NORMAL, 
                   callback: Optional[Callable] = None) -> str:
        """Add request to queue"""
        import uuid
        request_id = str(uuid.uuid4())
        
        request = QueuedRequest(
            priority=priority.value,
            request_id=request_id,
            prompt=prompt,
            params=params,
            callback=callback
        )
        
        self.request_queue.put(request)
        return request_id
    
    def add_batch_request(self, prompts: List[str], params: Dict[str, Any],
                         priority: Priority = Priority.NORMAL) -> List[str]:
        """Add batch request for multiple prompts"""
        request_ids = []
        
        with self.lock:
            for prompt in prompts:
                request_id = self.add_request(prompt, params, priority)
                request_ids.append(request_id)
                self.batch_queue.append(request_id)
        
        return request_ids
    
    def _process_queue(self):
        """Worker thread to process requests"""
        while self.is_running:
            try:
                # Get request with timeout
                request = self.request_queue.get(timeout=1.0)
                
                with self.lock:
                    self.active_requests[request.request_id] = request
                
                # Process request
                success = self._process_request(request)
                
                with self.lock:
                    del self.active_requests[request.request_id]
                    
                    if success:
                        self.completed_requests[request.request_id] = request
                    else:
                        # Retry logic
                        if request.retry_count < self.max_retries:
                            request.retry_count += 1
                            self.request_queue.put(request)
                        else:
                            self.failed_requests[request.request_id] = request
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Queue processing error: {e}")
    
    def _process_request(self, request: QueuedRequest) -> bool:
        """Process individual request (placeholder)"""
        try:
            # Simulate API call
            time.sleep(0.5)
            
            # Call callback if provided
            if request.callback:
                request.callback(request.request_id, True, None)
            
            return True
        except Exception as e:
            if request.callback:
                request.callback(request.request_id, False, str(e))
            return False
    
    def _process_batches(self):
        """Process batched requests efficiently"""
        while self.is_running:
            try:
                time.sleep(self.batch_timeout)
                
                with self.lock:
                    if len(self.batch_queue) >= self.batch_size:
                        # Process batch
                        batch = self.batch_queue[:self.batch_size]
                        self.batch_queue = self.batch_queue[self.batch_size:]
                        
                        # Batch processing logic here
                        print(f"Processing batch of {len(batch)} requests")
                        
            except Exception as e:
                print(f"Batch processing error: {e}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        with self.lock:
            return {
                'queued': self.request_queue.qsize(),
                'active': len(self.active_requests),
                'completed': len(self.completed_requests),
                'failed': len(self.failed_requests),
                'batch_pending': len(self.batch_queue)
            }
    
    def cancel_request(self, request_id: str) -> bool:
        """Cancel a queued request"""
        # Implementation would remove from queue
        return False
    
    def get_request_status(self, request_id: str) -> Dict[str, Any]:
        """Get status of specific request"""
        with self.lock:
            if request_id in self.active_requests:
                return {'status': 'active', 'request': self.active_requests[request_id]}
            elif request_id in self.completed_requests:
                return {'status': 'completed', 'request': self.completed_requests[request_id]}
            elif request_id in self.failed_requests:
                return {'status': 'failed', 'request': self.failed_requests[request_id]}
            else:
                return {'status': 'queued'}
