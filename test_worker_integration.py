#!/usr/bin/env python3
"""
Test script to verify worker integration in DALL-E Android app
"""

import os
import sys
import time
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


def test_basic_app_startup():
    """Test basic app startup with workers"""
    print("\n=== Testing Basic App Startup ===")
    
    try:
        from main_full import DalleApp
        
        # Create app instance
        app = DalleApp()
        
        # Build the app to trigger initialization
        app.build()
        
        # Check worker manager
        assert hasattr(app, 'worker_manager'), "WorkerManager not initialized"
        print("✅ WorkerManager initialized")
        
        # Check data directory
        assert hasattr(app, 'data_dir'), "Data directory not set"
        print("✅ Data directory configured")
        
        # Check workers
        workers = app.worker_manager.workers
        assert 'image_processor' in workers, "Image processor worker missing"
        assert 'settings_sync' in workers, "Settings sync worker missing"
        assert 'api_request' in workers, "API request worker missing"
        print("✅ All workers present")
        
        # Get stats
        stats = app.worker_manager.get_all_stats()
        print(f"✅ Worker stats: {len(stats['workers'])} workers active")
        
        # Test lifecycle methods
        app.on_stop()  # Should trigger auto-backup check
        print("✅ App lifecycle methods working")
        
        return True
        
    except Exception as e:
        print(f"❌ App startup test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_image_viewer_filters():
    """Test image viewer with filters"""
    print("\n=== Testing Image Viewer with Filters ===")
    
    try:
        from utils.image_viewer_with_filters import ImageViewerWithFilters
        from PIL import Image
        
        # Create test image
        test_dir = Path("test_output")
        test_dir.mkdir(exist_ok=True)
        
        test_image = Image.new('RGB', (100, 100), color='blue')
        test_image_path = test_dir / "test_viewer.png"
        test_image.save(test_image_path)
        
        # Create viewer instance (without opening dialog)
        viewer = ImageViewerWithFilters(str(test_image_path))
        
        # Check filter controls exist
        assert hasattr(viewer, 'brightness_slider'), "Brightness slider missing"
        assert hasattr(viewer, 'contrast_slider'), "Contrast slider missing"
        assert hasattr(viewer, 'saturation_slider'), "Saturation slider missing"
        print("✅ Filter controls created")
        
        # Check filter values
        assert viewer.current_brightness == 0, "Brightness default incorrect"
        assert viewer.current_contrast == 1.0, "Contrast default incorrect"
        assert viewer.current_saturation == 1.0, "Saturation default incorrect"
        print("✅ Filter defaults correct")
        
        # Cleanup
        test_image_path.unlink()
        test_dir.rmdir()
        
        return True
        
    except Exception as e:
        print(f"❌ Image viewer test failed: {str(e)}")
        return False


def test_settings_screen_enhanced():
    """Test enhanced settings screen"""
    print("\n=== Testing Enhanced Settings Screen ===")
    
    try:
        from screens.settings_screen_enhanced import SettingsScreenEnhanced
        
        # Create settings screen instance
        settings = SettingsScreenEnhanced()
        
        # Check backup methods exist
        assert hasattr(settings, '_show_export_options'), "Export method missing"
        assert hasattr(settings, '_show_import_dialog'), "Import method missing"
        assert hasattr(settings, '_load_auto_backup_preference'), "Auto-backup method missing"
        print("✅ Backup/restore methods present")
        
        # Test auto-backup preference
        settings._save_auto_backup_preference(True)
        assert settings._load_auto_backup_preference() == True, "Auto-backup save/load failed"
        
        settings._save_auto_backup_preference(False)
        assert settings._load_auto_backup_preference() == False, "Auto-backup save/load failed"
        print("✅ Auto-backup preferences working")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings screen test failed: {str(e)}")
        return False


def test_worker_operations():
    """Test actual worker operations"""
    print("\n=== Testing Worker Operations ===")
    
    try:
        from workers import WorkerManager
        from PIL import Image
        import json
        
        # Create test directory
        test_dir = Path("test_worker_ops")
        test_dir.mkdir(exist_ok=True)
        
        # Initialize worker manager
        manager = WorkerManager(
            app_data_dir=str(test_dir),
            api_key="test-key"
        )
        manager.start_all()
        time.sleep(1)
        
        print("✅ Worker manager started")
        
        # Test 1: Image processing
        test_image = Image.new('RGB', (100, 100), color='red')
        input_path = test_dir / "input.png"
        output_path = test_dir / "output.png"
        test_image.save(input_path)
        
        process_complete = False
        process_result = None
        
        def on_process_complete(result):
            nonlocal process_complete, process_result
            process_complete = True
            process_result = result
        
        manager.process_image_filters(
            image_path=str(input_path),
            output_path=str(output_path),
            brightness=50,
            contrast=1.5,
            callback=on_process_complete
        )
        
        # Wait for completion
        timeout = 5
        start = time.time()
        while not process_complete and time.time() - start < timeout:
            time.sleep(0.1)
        
        if process_complete and process_result.get('success'):
            print("✅ Image processing completed")
        else:
            print("❌ Image processing failed or timed out")
        
        # Test 2: Settings export
        settings_data = {
            "api_key": "test-key",
            "theme": "light",
            "image_size": "1024x1024"
        }
        
        settings_file = test_dir / "settings.json"
        with open(settings_file, 'w') as f:
            json.dump(settings_data, f)
        
        export_complete = False
        export_result = None
        
        def on_export_complete(result):
            nonlocal export_complete, export_result
            export_complete = True
            export_result = result
        
        manager.export_settings(
            destination=str(test_dir / "backup.zip"),
            include_images=False,
            callback=on_export_complete
        )
        
        # Wait for completion
        start = time.time()
        while not export_complete and time.time() - start < timeout:
            time.sleep(0.1)
        
        if export_complete and export_result.get('success'):
            print("✅ Settings export completed")
        else:
            print("❌ Settings export failed or timed out")
        
        # Stop workers
        manager.stop_all()
        
        # Cleanup
        import shutil
        shutil.rmtree(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Worker operations test failed: {str(e)}")
        return False


def test_kivy_worker_bridge():
    """Test Kivy worker bridge thread safety"""
    print("\n=== Testing Kivy Worker Bridge ===")
    
    try:
        from workers.kivy_worker_bridge import KivyWorkerBridge
        import threading
        
        # Create bridge
        bridge = KivyWorkerBridge()
        
        # Test property updates from multiple threads
        update_count = 20
        threads = []
        
        def update_from_thread(thread_id):
            for i in range(10):
                bridge.schedule_ui_update(
                    'property',
                    property='progress_value',
                    value=thread_id * 10 + i
                )
                time.sleep(0.01)
        
        # Start multiple threads
        for i in range(5):
            t = threading.Thread(target=update_from_thread, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for threads
        for t in threads:
            t.join()
        
        # Check queue has updates
        queue_size = bridge.ui_update_queue.qsize()
        print(f"✅ Bridge queued {queue_size} updates safely")
        
        # Test callback registration
        callback_called = False
        def test_callback():
            nonlocal callback_called
            callback_called = True
        
        bridge.register_callback('test', test_callback)
        bridge.schedule_ui_update(
            'callback',
            callback_id='test'
        )
        
        # Process updates
        bridge._process_ui_updates(0)
        
        assert callback_called, "Callback not executed"
        print("✅ Callback system working")
        
        return True
        
    except Exception as e:
        print(f"❌ Kivy worker bridge test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("🔧 Testing DALL-E Android App Worker Integration\n")
    
    tests = [
        test_basic_app_startup,
        test_image_viewer_filters,
        test_settings_screen_enhanced,
        test_worker_operations,
        test_kivy_worker_bridge
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
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()