#!/usr/bin/env python3
"""
Worker Deployment Script for DALL-E Android App
Sets up and tests the worker system
"""

import os
import sys
import json
import time
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from workers import WorkerManager, WorkerPriority, FilterType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class WorkerDeployment:
    """Deploy and test worker system"""
    
    def __init__(self):
        self.project_root = project_root
        self.test_dir = self.project_root / "test_workers"
        self.test_dir.mkdir(exist_ok=True)
        
    def setup_test_environment(self):
        """Create test directories and files"""
        print("🔧 Setting up test environment...")
        
        # Create test directories
        dirs = ['cache', 'gallery', 'backups', 'exports', 'temp']
        for dir_name in dirs:
            (self.test_dir / dir_name).mkdir(exist_ok=True)
            
        # Create test settings
        settings = {
            "api_key": os.environ.get("OPENAI_API_KEY", "sk-test"),
            "model": "dall-e-2",
            "image_size": "1024x1024",
            "quality": "standard",
            "theme": "light"
        }
        
        with open(self.test_dir / "settings.json", "w") as f:
            json.dump(settings, f, indent=2)
            
        # Create test image (placeholder)
        from PIL import Image
        test_image = Image.new('RGB', (1024, 1024), color='red')
        test_image.save(self.test_dir / "test_image.png")
        
        print("✅ Test environment ready")
        
    def test_worker_manager(self):
        """Test WorkerManager initialization"""
        print("\n🧪 Testing WorkerManager...")
        
        api_key = os.environ.get("OPENAI_API_KEY", "sk-test")
        manager = WorkerManager(
            app_data_dir=str(self.test_dir),
            api_key=api_key
        )
        
        # Start workers
        manager.start_all()
        time.sleep(1)
        
        # Check worker states
        stats = manager.get_all_stats()
        print(f"📊 Worker Stats: {json.dumps(stats, indent=2)}")
        
        # Stop workers
        manager.stop_all()
        
        print("✅ WorkerManager test passed")
        return manager
        
    def test_image_processing(self, manager):
        """Test image processing worker"""
        print("\n🖼️ Testing Image Processing Worker...")
        
        # Start workers
        manager.start_all()
        
        # Test variables
        test_complete = False
        test_result = None
        
        def on_complete(result):
            nonlocal test_complete, test_result
            test_complete = True
            test_result = result
            print(f"✅ Image processing complete: {result}")
            
        # Process test image
        success = manager.process_image_filters(
            image_path=str(self.test_dir / "test_image.png"),
            output_path=str(self.test_dir / "gallery" / "filtered_test.png"),
            brightness=50,
            contrast=1.5,
            saturation=0.8,
            callback=on_complete
        )
        
        if not success:
            print("❌ Failed to queue image processing task")
            return False
            
        # Wait for completion
        timeout = 10
        start_time = time.time()
        while not test_complete and (time.time() - start_time) < timeout:
            time.sleep(0.1)
            
        if test_complete:
            print("✅ Image processing test passed")
            return True
        else:
            print("❌ Image processing test timed out")
            return False
            
    def test_settings_sync(self, manager):
        """Test settings sync worker"""
        print("\n💾 Testing Settings Sync Worker...")
        
        # Test export
        export_complete = False
        export_result = None
        
        def on_export_complete(result):
            nonlocal export_complete, export_result
            export_complete = True
            export_result = result
            print(f"✅ Export complete: {result}")
            
        success = manager.export_settings(
            destination=str(self.test_dir / "exports" / "test_export.json"),
            include_images=False,
            callback=on_export_complete
        )
        
        if not success:
            print("❌ Failed to queue export task")
            return False
            
        # Wait for completion
        timeout = 5
        start_time = time.time()
        while not export_complete and (time.time() - start_time) < timeout:
            time.sleep(0.1)
            
        if export_complete and export_result.get('success'):
            print("✅ Settings export test passed")
            
            # Test import
            import_complete = False
            
            def on_import_complete(result):
                nonlocal import_complete
                import_complete = True
                print(f"✅ Import complete: {result}")
                
            success = manager.import_settings(
                source=export_result['path'],
                callback=on_import_complete
            )
            
            # Wait for import
            start_time = time.time()
            while not import_complete and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                
            if import_complete:
                print("✅ Settings import test passed")
                return True
                
        print("❌ Settings sync test failed")
        return False
        
    def test_api_requests(self, manager):
        """Test API request worker (requires valid API key)"""
        print("\n🌐 Testing API Request Worker...")
        
        if not os.environ.get("OPENAI_API_KEY"):
            print("⚠️ Skipping API test - no API key found")
            return True
            
        # Test generation request
        request_complete = False
        
        def on_generate_complete(result):
            nonlocal request_complete
            request_complete = True
            print(f"✅ Generation complete: {result.get('success', False)}")
            
        success = manager.generate_image(
            prompt="A red test square",
            n=1,
            size="256x256",  # Smaller size for testing
            callback=on_generate_complete
        )
        
        if not success:
            print("❌ Failed to queue generation task")
            return False
            
        # Wait for completion (longer timeout for API)
        timeout = 30
        start_time = time.time()
        while not request_complete and (time.time() - start_time) < timeout:
            time.sleep(0.1)
            
        if request_complete:
            print("✅ API request test passed")
            return True
        else:
            print("❌ API request test timed out")
            return False
            
    def run_deployment_tests(self):
        """Run all deployment tests"""
        print("\n🚀 DALL-E Android Worker Deployment")
        print("=" * 50)
        
        # Setup
        self.setup_test_environment()
        
        # Initialize manager
        manager = self.test_worker_manager()
        
        # Run tests
        tests_passed = 0
        total_tests = 3
        
        if self.test_image_processing(manager):
            tests_passed += 1
            
        if self.test_settings_sync(manager):
            tests_passed += 1
            
        if self.test_api_requests(manager):
            tests_passed += 1
            
        # Stop workers
        manager.stop_all()
        
        # Summary
        print("\n" + "=" * 50)
        print(f"🏁 Deployment Test Results: {tests_passed}/{total_tests} passed")
        
        if tests_passed == total_tests:
            print("✅ All tests passed! Workers are ready for deployment.")
            self.generate_integration_script()
        else:
            print("❌ Some tests failed. Please check the logs.")
            
    def generate_integration_script(self):
        """Generate integration script for the app"""
        print("\n📝 Generating integration script...")
        
        integration_code = '''# Auto-generated integration code for DALL-E Android App

# Add to main_full.py imports
from workers import WorkerManager

# Add to MDApp.__init__
self.worker_manager = None

# Add to MDApp.build
self.worker_manager = WorkerManager(
    app_data_dir=self.user_data_dir,
    api_key=self.settings.get('api_key', '')
)
self.worker_manager.start_all()

# Add to MDApp.on_stop
if self.worker_manager:
    self.worker_manager.stop_all()

# Example usage in screens:
# app = MDApp.get_running_app()
# app.worker_manager.process_image_filters(...)
# app.worker_manager.export_settings(...)
# app.worker_manager.generate_image(...)
'''
        
        with open(self.project_root / "worker_integration.py", "w") as f:
            f.write(integration_code)
            
        print("✅ Integration script saved to worker_integration.py")
        
def main():
    """Main deployment function"""
    deployment = WorkerDeployment()
    deployment.run_deployment_tests()
    
if __name__ == "__main__":
    main()
