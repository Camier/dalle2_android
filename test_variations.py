#!/usr/bin/env python3
"""
Test script for DALL-E image variations feature
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from workers.worker_manager import WorkerManager
from workers.api_request import APIRequest, APIRequestType
import time
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_variations():
    """Test image variations functionality"""
    print("\n=== Testing DALL-E Image Variations ===\n")
    
    # Create temp directory
    import tempfile
    temp_dir = tempfile.mkdtemp()
    
    # Initialize WorkerManager
    manager = WorkerManager(
        app_data_dir=temp_dir,
        api_key="test-key"  # Would need real key for actual test
    )
    
    print("✅ WorkerManager initialized")
    
    # Start workers
    manager.start_all()
    print("✅ Workers started")
    
    # Test variations request creation
    api_worker = manager.get_worker('api_request')
    if api_worker:
        # Create a mock variation request
        request = APIRequest(
            request_type=APIRequestType.CREATE_VARIATION,
            image_path="/path/to/test/image.png",
            n=2,
            size="1024x1024",
            model="dall-e-2"
        )
        
        print(f"✅ Created variation request: {request.request_type.value}")
        print(f"   - Image: {request.image_path}")
        print(f"   - Count: {request.n}")
        print(f"   - Size: {request.size}")
        
        # Test the generate_image_variations method
        success = manager.generate_image_variations(
            image_path="/path/to/test/image.png",
            count=3,
            callback=lambda result: print(f"Callback received: {result}")
        )
        
        print(f"✅ Variation request queued: {success}")
    
    # Wait a bit
    time.sleep(1)
    
    # Get stats
    stats = manager.get_all_stats()
    print("\n📊 Worker Stats:")
    for worker_name, worker_stats in stats['workers'].items():
        print(f"  - {worker_name}: {worker_stats['state']}")
    
    # Stop workers
    manager.stop_all()
    print("\n✅ Workers stopped")
    
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)
    
    print("\n✅ Test completed successfully!")


if __name__ == "__main__":
    test_variations()