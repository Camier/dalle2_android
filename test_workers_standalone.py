#!/usr/bin/env python3
"""
Standalone test for worker components without Kivy dependencies
"""

import os
import sys
import time
import json
import threading
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_base_worker():
    """Test base worker functionality"""
    print("\n=== Testing Base Worker ===")
    
    try:
        from workers.base_worker import BaseWorker, WorkerState, WorkerPriority
        
        # Create a simple test worker
        class TestWorker(BaseWorker):
            def process_task(self, task):
                # Simple task processing
                return f"Processed: {task}"
        
        worker = TestWorker("test-worker")
        
        # Test state transitions
        assert worker.state == WorkerState.IDLE
        print("✅ Initial state correct")
        
        # Start worker
        worker.start()
        assert worker.state == WorkerState.RUNNING
        print("✅ Worker started")
        
        # Add tasks
        for i in range(5):
            success = worker.add_task(f"task-{i}", WorkerPriority.NORMAL)
            assert success, f"Failed to add task {i}"
        print("✅ Tasks added to queue")
        
        # Wait for processing
        time.sleep(1)
        
        # Check stats
        stats = worker.get_stats()
        print(f"✅ Worker stats: {stats}")
        
        # Stop worker
        worker.stop(wait=True)
        assert worker.state == WorkerState.STOPPED
        print("✅ Worker stopped")
        
        return True
        
    except Exception as e:
        print(f"❌ Base worker test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_worker_manager_basic():
    """Test WorkerManager basic functionality"""
    print("\n=== Testing Worker Manager Basic ===")
    
    try:
        from workers.worker_manager import WorkerManager
        import tempfile
        
        # Create temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize manager
            manager = WorkerManager(
                app_data_dir=temp_dir,
                api_key="test-key"
            )
            
            print("✅ WorkerManager created")
            
            # Check workers initialized
            assert len(manager.workers) == 3
            print("✅ All workers initialized")
            
            # Start workers
            manager.start_all()
            print("✅ Workers started")
            
            # Get stats
            stats = manager.get_all_stats()
            assert "workers" in stats
            print(f"✅ Stats retrieved: {len(stats['workers'])} workers")
            
            # Stop workers
            manager.stop_all(wait=True)
            print("✅ Workers stopped")
            
        return True
        
    except Exception as e:
        print(f"❌ Worker manager test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_enhanced_worker():
    """Test enhanced worker features"""
    print("\n=== Testing Enhanced Worker ===")
    
    try:
        from workers.base_worker_enhanced import BaseWorkerEnhanced, WorkerTask, WorkerPriority
        
        # Skip if MRO issue persists
        class TestEnhancedWorker(BaseWorkerEnhanced):
            def process_task(self, task_data):
                # Simulate processing
                time.sleep(0.1)
                return f"Enhanced: {task_data}"
        
        worker = TestEnhancedWorker("enhanced-test", max_workers=2)
        
        # Test task creation
        task = WorkerTask(
            data="test-data",
            priority=WorkerPriority.HIGH,
            timeout=1.0
        )
        
        assert task.id is not None
        assert task.priority == WorkerPriority.HIGH
        print("✅ WorkerTask created")
        
        # Start worker
        worker.start()
        print("✅ Enhanced worker started")
        
        # Add tasks with callbacks
        results = []
        
        def on_complete(task, result):
            results.append(result)
        
        worker.on_task_complete = on_complete
        
        # Add multiple tasks
        for i in range(5):
            task_id = worker.add_task(
                task_data=f"task-{i}",
                priority=WorkerPriority.NORMAL,
                timeout=2.0
            )
            assert task_id is not None
        
        print("✅ Tasks added with timeouts")
        
        # Wait for completion
        time.sleep(1)
        
        # Check metrics
        stats = worker.get_stats()
        print(f"✅ Enhanced stats: {stats}")
        
        # Stop worker
        worker.stop(wait=True)
        print("✅ Enhanced worker stopped")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced worker test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_thread_safety():
    """Test thread safety of worker components"""
    print("\n=== Testing Thread Safety ===")
    
    try:
        from workers.base_worker import BaseWorker, WorkerPriority
        import threading
        
        class ConcurrentTestWorker(BaseWorker):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.processed_tasks = []
                self.lock = threading.Lock()
                
            def process_task(self, task):
                with self.lock:
                    self.processed_tasks.append(task)
                time.sleep(0.01)  # Simulate work
                return f"Done: {task}"
        
        worker = ConcurrentTestWorker("concurrent-test")
        worker.start()
        
        # Add tasks from multiple threads
        threads = []
        tasks_per_thread = 10
        num_threads = 5
        
        def add_tasks(thread_id):
            for i in range(tasks_per_thread):
                worker.add_task(
                    f"thread-{thread_id}-task-{i}",
                    WorkerPriority.NORMAL
                )
        
        # Start threads
        for i in range(num_threads):
            t = threading.Thread(target=add_tasks, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for threads
        for t in threads:
            t.join()
        
        print(f"✅ Added {num_threads * tasks_per_thread} tasks from {num_threads} threads")
        
        # Wait for processing
        time.sleep(2)
        
        # Check results
        processed_count = len(worker.processed_tasks)
        print(f"✅ Processed {processed_count} tasks safely")
        
        # Stop worker
        worker.stop(wait=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Thread safety test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test worker error handling"""
    print("\n=== Testing Error Handling ===")
    
    try:
        from workers.base_worker import BaseWorker, WorkerState
        
        class ErrorTestWorker(BaseWorker):
            def process_task(self, task):
                if "error" in task:
                    raise ValueError(f"Simulated error for {task}")
                return f"Success: {task}"
        
        worker = ErrorTestWorker("error-test")
        worker.max_errors = 3  # Lower threshold for testing
        
        # Track errors
        errors = []
        def on_error(task, error):
            errors.append((task, str(error)))
        
        worker.on_task_error = on_error
        worker.start()
        
        # Add mix of good and bad tasks
        worker.add_task("good-task-1")
        worker.add_task("error-task-1")
        worker.add_task("good-task-2")
        worker.add_task("error-task-2")
        worker.add_task("error-task-3")
        
        # Wait for processing
        time.sleep(1)
        
        # Check error handling
        assert len(errors) >= 3, "Not all errors captured"
        print(f"✅ Captured {len(errors)} errors")
        
        # Worker should be in error state after max errors
        assert worker.state == WorkerState.ERROR
        print("✅ Worker entered error state after max errors")
        
        # Test recovery
        worker.error_count = 0
        worker.state = WorkerState.RUNNING
        worker.add_task("recovery-task")
        
        time.sleep(0.5)
        
        stats = worker.get_stats()
        print(f"✅ Worker recovered: {stats}")
        
        worker.stop(wait=True)
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all standalone tests"""
    print("🔧 Testing DALL-E Android Worker Components (Standalone)\n")
    
    tests = [
        test_base_worker,
        test_worker_manager_basic,
        test_enhanced_worker,
        test_thread_safety,
        test_error_handling
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
            results.append(False)
    
    # Summary
    print("\n=== Test Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All standalone tests passed!")
        print("\nNote: Full integration tests require Kivy/KivyMD installation")
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()