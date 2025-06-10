# DALL-E Android App - Worker Integration Guide

## Overview
This guide shows how to integrate the new worker system with your existing Kivy/KivyMD DALL-E Android app.

## Quick Start

### 1. Initialize Workers in Main App

```python
# main_full.py - Add to your main app class

from workers import WorkerManager

class DalleApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.worker_manager = None
        
    def build(self):
        # Existing code...
        
        # Initialize worker manager
        self.worker_manager = WorkerManager(
            app_data_dir=self.user_data_dir,
            api_key=self.api_key
        )
        
        # Set up callbacks
        self.worker_manager.on_task_complete = self.on_worker_task_complete
        self.worker_manager.on_task_error = self.on_worker_task_error
        
        # Start all workers
        self.worker_manager.start_all()
        
        return self.root
        
    def on_stop(self):
        # Stop all workers on app exit
        if self.worker_manager:
            self.worker_manager.stop_all()
```

### 2. Implement Image Filters (Task 3)

```python
# utils/image_viewer.py - Add filter controls

from kivymd.uix.slider import MDSlider
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout

class ImageViewer(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.filter_controls = None
        self.current_filters = {
            'brightness': 0,
            'contrast': 1.0,
            'saturation': 1.0
        }
        
    def setup_filter_controls(self):
        """Add filter UI controls"""
        filter_layout = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(200),
            padding=dp(10)
        )
        
        # Brightness slider (-100 to +100)
        brightness_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        brightness_box.add_widget(MDLabel(text="Brightness", size_hint_x=0.3))
        self.brightness_slider = MDSlider(
            min=-100, max=100, value=0,
            size_hint_x=0.7
        )
        self.brightness_slider.bind(value=self.on_brightness_change)
        brightness_box.add_widget(self.brightness_slider)
        filter_layout.add_widget(brightness_box)
        
        # Contrast slider (0.5x to 2x)
        contrast_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        contrast_box.add_widget(MDLabel(text="Contrast", size_hint_x=0.3))
        self.contrast_slider = MDSlider(
            min=0.5, max=2.0, value=1.0,
            size_hint_x=0.7
        )
        self.contrast_slider.bind(value=self.on_contrast_change)
        contrast_box.add_widget(self.contrast_slider)
        filter_layout.add_widget(contrast_box)
        
        # Saturation slider (0 to 2x)
        saturation_box = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(50))
        saturation_box.add_widget(MDLabel(text="Saturation", size_hint_x=0.3))
        self.saturation_slider = MDSlider(
            min=0, max=2.0, value=1.0,
            size_hint_x=0.7
        )
        self.saturation_slider.bind(value=self.on_saturation_change)
        saturation_box.add_widget(self.saturation_slider)
        filter_layout.add_widget(saturation_box)
        
        # Apply button
        apply_btn = MDRaisedButton(
            text="Apply Filters",
            size_hint_x=1,
            on_release=self.apply_filters
        )
        filter_layout.add_widget(apply_btn)
        
        return filter_layout
        
    def apply_filters(self, *args):
        """Apply filters using worker"""
        if not self.current_image_path:
            return
            
        # Generate output path
        timestamp = int(time.time())
        output_path = os.path.join(
            MDApp.get_running_app().user_data_dir,
            'gallery',
            f'filtered_{timestamp}.png'
        )
        
        # Show progress
        self.show_progress("Applying filters...")
        
        # Process with worker
        app = MDApp.get_running_app()
        success = app.worker_manager.process_image_filters(
            image_path=self.current_image_path,
            output_path=output_path,
            brightness=self.current_filters['brightness'],
            contrast=self.current_filters['contrast'],
            saturation=self.current_filters['saturation'],
            callback=self.on_filter_complete
        )
        
        if not success:
            self.show_error("Failed to queue filter task")
            
    def on_filter_complete(self, result):
        """Handle filter completion"""
        Clock.schedule_once(lambda dt: self._handle_filter_result(result))
        
    def _handle_filter_result(self, result):
        """Update UI with filtered image"""
        self.hide_progress()
        
        if result.get('success'):
            # Update displayed image
            self.current_image_path = result['output_path']
            self.image_widget.source = result['output_path']
            self.image_widget.reload()
            
            # Show success message
            self.show_snackbar(f"Filters applied in {result['processing_time']:.1f}s")
            
            # Update history
            self.add_to_history(result['output_path'], "Filtered Image")
        else:
            self.show_error(f"Filter error: {result.get('error', 'Unknown error')}")
```

### 3. Implement Settings Export/Import (Task 4)

```python
# screens/settings_screen.py - Add export/import UI

class SettingsScreen(MDScreen):
    def add_backup_section(self):
        """Add backup/restore UI section"""
        backup_card = MDCard(
            orientation='vertical',
            padding=dp(10),
            spacing=dp(10),
            size_hint_y=None,
            height=dp(200)
        )
        
        backup_card.add_widget(MDLabel(
            text="Backup & Restore",
            font_style="H6"
        ))
        
        # Export button
        export_btn = MDRaisedButton(
            text="Export Settings",
            size_hint_x=1,
            on_release=self.export_settings
        )
        backup_card.add_widget(export_btn)
        
        # Export with images checkbox
        self.include_images_check = MDCheckbox(size_hint_x=None, width=dp(48))
        images_box = MDBoxLayout(orientation='horizontal')
        images_box.add_widget(self.include_images_check)
        images_box.add_widget(MDLabel(text="Include generated images"))
        backup_card.add_widget(images_box)
        
        # Import button
        import_btn = MDRaisedButton(
            text="Import Settings",
            size_hint_x=1,
            on_release=self.import_settings
        )
        backup_card.add_widget(import_btn)
        
        # Auto-backup switch
        auto_backup_box = MDBoxLayout(orientation='horizontal')
        auto_backup_box.add_widget(MDLabel(text="Auto-backup"))
        self.auto_backup_switch = MDSwitch(active=True)
        auto_backup_box.add_widget(self.auto_backup_switch)
        backup_card.add_widget(auto_backup_box)
        
        return backup_card
        
    def export_settings(self, *args):
        """Export settings to file"""
        from plyer import filechooser
        
        # Choose save location
        path = filechooser.save_file(
            title="Export Settings",
            filters=[("JSON files", "*.json"), ("ZIP files", "*.zip")]
        )
        
        if path:
            if isinstance(path, list):
                path = path[0]
                
            # Show progress
            self.show_progress("Exporting settings...")
            
            # Export with worker
            app = MDApp.get_running_app()
            success = app.worker_manager.export_settings(
                destination=path,
                include_images=self.include_images_check.active,
                callback=self.on_export_complete
            )
            
            if not success:
                self.show_error("Failed to queue export task")
                
    def import_settings(self, *args):
        """Import settings from file"""
        from plyer import filechooser
        
        # Choose file
        selection = filechooser.open_file(
            title="Import Settings",
            filters=[("Settings files", "*.json", "*.zip")]
        )
        
        if selection:
            path = selection[0]
            
            # Confirm import
            dialog = MDDialog(
                title="Import Settings",
                text="This will replace your current settings. Continue?",
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        on_release=lambda x: dialog.dismiss()
                    ),
                    MDRaisedButton(
                        text="IMPORT",
                        on_release=lambda x: self.do_import(path, dialog)
                    )
                ]
            )
            dialog.open()
            
    def do_import(self, path, dialog):
        """Perform settings import"""
        dialog.dismiss()
        
        # Show progress
        self.show_progress("Importing settings...")
        
        # Import with worker
        app = MDApp.get_running_app()
        success = app.worker_manager.import_settings(
            source=path,
            callback=self.on_import_complete
        )
        
        if not success:
            self.show_error("Failed to queue import task")
            
    def on_export_complete(self, result):
        """Handle export completion"""
        Clock.schedule_once(lambda dt: self._handle_export_result(result))
        
    def _handle_export_result(self, result):
        """Update UI after export"""
        self.hide_progress()
        
        if result.get('success'):
            size_mb = result['size'] / (1024 * 1024)
            msg = f"Settings exported ({size_mb:.1f} MB)"
            if result.get('includes_images'):
                msg += " with images"
            self.show_snackbar(msg)
        else:
            self.show_error(f"Export failed: {result.get('error', 'Unknown error')}")
```

### 4. Integration with Batch Generation

```python
# screens/main_screen.py - Update batch generation to use workers

def generate_batch(self, prompts, count):
    """Generate multiple images using worker"""
    
    # Show progress
    self.show_progress(f"Generating {count} images...")
    
    # Queue generation request
    app = MDApp.get_running_app()
    success = app.worker_manager.generate_image(
        prompt=prompts[0],  # Use first prompt
        n=count,
        size=self.selected_size,
        callback=self.on_batch_complete
    )
    
    if not success:
        self.show_error("Failed to queue generation task")
        
def on_batch_complete(self, result):
    """Handle batch generation completion"""
    Clock.schedule_once(lambda dt: self._handle_batch_result(result))
    
def _handle_batch_result(self, result):
    """Process batch generation results"""
    self.hide_progress()
    
    if result.get('success'):
        images = result.get('images', [])
        
        # Download and save images
        for i, image_data in enumerate(images):
            self.download_and_save_image(
                image_data['url'],
                f"{result['prompt'][:30]}_{i+1}"
            )
            
        self.show_snackbar(f"Generated {len(images)} images successfully")
        
        # Auto-backup if enabled
        if self.auto_backup_enabled:
            app = MDApp.get_running_app()
            app.worker_manager.create_backup(reason="post-generation")
    else:
        self.show_error(f"Generation failed: {result.get('error', 'Unknown error')}")
```

## Worker Architecture Benefits

1. **Non-blocking Operations**: All heavy tasks run in background threads
2. **Queue Management**: Automatic task queuing with priorities
3. **Error Recovery**: Built-in retry logic and error handling
4. **Rate Limiting**: Automatic API rate limit management
5. **Progress Tracking**: Real-time task status updates
6. **State Persistence**: Workers can resume after app restart

## Performance Optimizations

1. **Image Processing**: 
   - Filters applied in separate thread
   - Memory-efficient processing
   - Automatic cache management

2. **Settings Sync**:
   - Incremental backups
   - Compressed exports
   - Validation before import

3. **API Requests**:
   - Request batching
   - Smart retry logic
   - Token bucket rate limiting

## Testing the Workers

```python
# test_workers.py - Standalone test script

import asyncio
from workers import WorkerManager

async def test_workers():
    # Initialize manager
    manager = WorkerManager(
        app_data_dir="./test_data",
        api_key="your-api-key"
    )
    
    # Start workers
    manager.start_all()
    
    # Test image processing
    success = manager.process_image_filters(
        image_path="test.png",
        output_path="filtered.png",
        brightness=50,
        contrast=1.5,
        saturation=1.2
    )
    
    # Test settings export
    success = manager.export_settings(
        destination="backup.json"
    )
    
    # Wait for completion
    await asyncio.sleep(5)
    
    # Get stats
    stats = manager.get_all_stats()
    print(json.dumps(stats, indent=2))
    
    # Stop workers
    manager.stop_all()

if __name__ == "__main__":
    asyncio.run(test_workers())
```

## Deployment Checklist

- [ ] Install dependencies: `pip install pillow requests`
- [ ] Update main_full.py with worker initialization
- [ ] Add filter UI to image viewer
- [ ] Add export/import UI to settings
- [ ] Update batch generation to use workers
- [ ] Test all worker operations
- [ ] Configure auto-backup schedule
- [ ] Set appropriate queue sizes
- [ ] Monitor worker performance
- [ ] Handle Android-specific permissions

## Next Steps

1. **Add More Filters**: Blur, sharpen, sepia, grayscale
2. **Cloud Sync**: Integrate with cloud storage
3. **Background Notifications**: Progress updates
4. **Advanced Queue Management**: Priority queues
5. **Performance Monitoring**: Analytics dashboard
