"""
Enhanced image viewer with zoom, pan, and filter support
"""

from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDIconButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.slider import MDSlider
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.core.window import Window
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from pathlib import Path
import os
import shutil
from typing import Optional, Callable

from utils.android_utils import share_image


class ImageViewerWithFilters(MDDialog):
    """Enhanced image viewer with zoom, pan, share, delete, and filter functionality"""
    
    def __init__(self, image_path, on_delete_callback=None, **kwargs):
        self.image_path = Path(image_path)
        self.on_delete_callback = on_delete_callback
        self.original_image_path = None
        self.temp_image_path = None
        self.processing = False
        
        # Filter values
        self.current_brightness = 0
        self.current_contrast = 1.0
        self.current_saturation = 1.0
        
        # Create content
        content = self._create_content()
        
        # Initialize dialog
        super().__init__(
            type="custom",
            content_cls=content,
            size_hint=(0.95, 0.95),
            **kwargs
        )
        
        # Bind keyboard
        Window.bind(on_keyboard=self._on_keyboard)
        
        # Create temporary copy of original image
        self._create_temp_copy()
    
    def _create_temp_copy(self):
        """Create a temporary copy of the original image"""
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        
        if hasattr(app, 'worker_manager'):
            temp_dir = Path(app.data_dir) / 'temp'
            temp_dir.mkdir(exist_ok=True)
            
            self.original_image_path = self.image_path
            self.temp_image_path = temp_dir / f"temp_{self.image_path.name}"
            shutil.copy2(self.image_path, self.temp_image_path)
    
    def _create_content(self):
        """Create the viewer content with filter controls"""
        # Main container
        layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            padding=dp(10)
        )
        
        # Top toolbar
        toolbar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(56),
            spacing=dp(10)
        )
        
        # Title
        title = MDLabel(
            text=self.image_path.name,
            theme_text_color="Primary",
            font_style="H6",
            size_hint_x=0.6
        )
        toolbar.add_widget(title)
        
        # Action buttons
        filter_btn = MDIconButton(
            icon="tune",
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 1, 1),
            on_release=lambda x: self._toggle_filter_panel()
        )
        toolbar.add_widget(filter_btn)
        
        share_btn = MDIconButton(
            icon="share-variant",
            theme_text_color="Custom",
            text_color=(0, 0.7, 1, 1),
            on_release=lambda x: self._share_image()
        )
        toolbar.add_widget(share_btn)
        
        delete_btn = MDIconButton(
            icon="delete",
            theme_text_color="Custom",
            text_color=(1, 0, 0, 1),
            on_release=lambda x: self._delete_image()
        )
        toolbar.add_widget(delete_btn)
        
        close_btn = MDIconButton(
            icon="close",
            on_release=lambda x: self.dismiss()
        )
        toolbar.add_widget(close_btn)
        
        layout.add_widget(toolbar)
        
        # Image container with scatter for zoom/pan
        scatter = Scatter(
            do_rotation=False,
            do_translation=True,
            scale_min=0.5,
            scale_max=4.0,
            size_hint=(1, 1)
        )
        
        # Image
        image = Image(
            source=str(self.image_path),
            allow_stretch=True,
            keep_ratio=True
        )
        
        # Bind double tap to reset zoom
        image.bind(on_touch_down=self._on_image_touch)
        self.last_touch_time = 0
        
        scatter.add_widget(image)
        layout.add_widget(scatter)
        
        # Store references
        self.scatter = scatter
        self.image = image
        
        # Filter panel (initially hidden)
        filter_panel = self._create_filter_panel()
        filter_panel.opacity = 0
        filter_panel.disabled = True
        layout.add_widget(filter_panel)
        self.filter_panel = filter_panel
        
        # Progress indicator
        progress = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        progress.opacity = 0
        layout.add_widget(progress)
        self.progress = progress
        
        # Instructions
        instructions = MDLabel(
            text="Pinch to zoom • Double tap to reset • Swipe to pan • Tap filter icon for adjustments",
            theme_text_color="Secondary",
            font_style="Caption",
            halign="center",
            size_hint_y=None,
            height=dp(30)
        )
        layout.add_widget(instructions)
        
        return layout
    
    def _create_filter_panel(self):
        """Create the filter control panel"""
        panel = MDCard(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(10),
            size_hint_y=None,
            height=dp(280),
            elevation=5
        )
        
        # Panel title
        panel.add_widget(MDLabel(
            text="Image Filters",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(30)
        ))
        
        # Brightness control
        brightness_box = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(5)
        )
        
        brightness_label = MDLabel(
            text=f"Brightness: {self.current_brightness}",
            size_hint_y=None,
            height=dp(20)
        )
        brightness_box.add_widget(brightness_label)
        
        brightness_slider = MDSlider(
            min=-100,
            max=100,
            value=0,
            size_hint_y=None,
            height=dp(40)
        )
        brightness_slider.bind(value=lambda x, v: self._update_brightness(v, brightness_label))
        brightness_box.add_widget(brightness_slider)
        
        panel.add_widget(brightness_box)
        self.brightness_slider = brightness_slider
        
        # Contrast control
        contrast_box = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(5)
        )
        
        contrast_label = MDLabel(
            text=f"Contrast: {self.current_contrast:.1f}x",
            size_hint_y=None,
            height=dp(20)
        )
        contrast_box.add_widget(contrast_label)
        
        contrast_slider = MDSlider(
            min=0.5,
            max=2.0,
            value=1.0,
            size_hint_y=None,
            height=dp(40)
        )
        contrast_slider.bind(value=lambda x, v: self._update_contrast(v, contrast_label))
        contrast_box.add_widget(contrast_slider)
        
        panel.add_widget(contrast_box)
        self.contrast_slider = contrast_slider
        
        # Saturation control
        saturation_box = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(5)
        )
        
        saturation_label = MDLabel(
            text=f"Saturation: {self.current_saturation:.1f}x",
            size_hint_y=None,
            height=dp(20)
        )
        saturation_box.add_widget(saturation_label)
        
        saturation_slider = MDSlider(
            min=0,
            max=2.0,
            value=1.0,
            size_hint_y=None,
            height=dp(40)
        )
        saturation_slider.bind(value=lambda x, v: self._update_saturation(v, saturation_label))
        saturation_box.add_widget(saturation_slider)
        
        panel.add_widget(saturation_box)
        self.saturation_slider = saturation_slider
        
        # Action buttons
        button_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        reset_btn = MDFlatButton(
            text="Reset",
            on_release=lambda x: self._reset_filters()
        )
        button_box.add_widget(reset_btn)
        
        apply_btn = MDRaisedButton(
            text="Apply Filters",
            on_release=lambda x: self._apply_filters()
        )
        button_box.add_widget(apply_btn)
        
        save_btn = MDRaisedButton(
            text="Save Copy",
            md_bg_color=(0, 0.7, 0, 1),
            on_release=lambda x: self._save_filtered_copy()
        )
        button_box.add_widget(save_btn)
        
        panel.add_widget(button_box)
        
        return panel
    
    def _toggle_filter_panel(self):
        """Toggle the filter panel visibility"""
        if self.filter_panel.opacity == 0:
            self.filter_panel.opacity = 1
            self.filter_panel.disabled = False
        else:
            self.filter_panel.opacity = 0
            self.filter_panel.disabled = True
    
    def _update_brightness(self, value, label):
        """Update brightness value"""
        self.current_brightness = int(value)
        label.text = f"Brightness: {self.current_brightness}"
    
    def _update_contrast(self, value, label):
        """Update contrast value"""
        self.current_contrast = round(value, 1)
        label.text = f"Contrast: {self.current_contrast}x"
    
    def _update_saturation(self, value, label):
        """Update saturation value"""
        self.current_saturation = round(value, 1)
        label.text = f"Saturation: {self.current_saturation}x"
    
    def _reset_filters(self):
        """Reset all filters to default values"""
        self.brightness_slider.value = 0
        self.contrast_slider.value = 1.0
        self.saturation_slider.value = 1.0
        
        # Reset the image to original
        if self.original_image_path:
            self.image.source = str(self.original_image_path)
            self.image.reload()
    
    def _apply_filters(self):
        """Apply filters to the image using WorkerManager with proper thread safety"""
        if self.processing:
            Snackbar(text="Already processing...").open()
            return
            
        from kivymd.app import MDApp
        from kivy.clock import Clock
        
        app = MDApp.get_running_app()
        
        if not hasattr(app, 'worker_manager'):
            Snackbar(text="Worker system not available").open()
            return
        
        # Show progress
        self.processing = True
        self.progress.opacity = 1
        self.progress.active = True
        
        # Define callback that will run on main thread
        def on_filter_complete(result):
            # This callback might be called from worker thread
            # Schedule UI updates on main thread
            def update_ui(dt):
                self.processing = False
                self.progress.opacity = 0
                self.progress.active = False
                
                if result.get('success'):
                    # Update displayed image
                    self.image.source = str(self.temp_image_path)
                    self.image.reload()
                    Snackbar(text="Filters applied successfully").open()
                else:
                    error = result.get('error', 'Unknown error')
                    Snackbar(text=f"Filter error: {error}").open()
            
            # Schedule on main thread
            Clock.schedule_once(update_ui, 0)
        
        # Apply filters using worker
        app.worker_manager.process_image_filters(
            image_path=str(self.original_image_path),
            output_path=str(self.temp_image_path),
            brightness=self.current_brightness if self.current_brightness != 0 else None,
            contrast=self.current_contrast if self.current_contrast != 1.0 else None,
            saturation=self.current_saturation if self.current_saturation != 1.0 else None,
            callback=on_filter_complete
        )
    
    def _save_filtered_copy(self):
        """Save a copy of the filtered image"""
        if not self.temp_image_path or not self.temp_image_path.exists():
            Snackbar(text="No filters applied yet").open()
            return
        
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        
        if hasattr(app, 'data_dir'):
            gallery_dir = Path(app.data_dir) / 'gallery'
            gallery_dir.mkdir(exist_ok=True)
            
            # Generate unique filename
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"filtered_{timestamp}_{self.image_path.name}"
            save_path = gallery_dir / filename
            
            try:
                shutil.copy2(self.temp_image_path, save_path)
                Snackbar(text=f"Saved as {filename}").open()
            except Exception as e:
                Snackbar(text=f"Save error: {str(e)}").open()
    
    def _on_image_touch(self, widget, touch):
        """Handle double tap to reset zoom"""
        if widget.collide_point(*touch.pos):
            import time
            current_time = time.time()
            
            # Check for double tap
            if current_time - self.last_touch_time < 0.3:
                # Reset zoom and position
                self.scatter.scale = 1
                self.scatter.pos = (0, 0)
            
            self.last_touch_time = current_time
    
    def _share_image(self):
        """Share the image (filtered or original)"""
        try:
            # Share the currently displayed image
            current_source = self.temp_image_path if self.temp_image_path and self.temp_image_path.exists() else self.image_path
            success = share_image(str(current_source), "Check out this image!")
            if success:
                Snackbar(text="Opening share dialog...").open()
            else:
                Snackbar(text="Failed to share image").open()
        except Exception as e:
            Snackbar(text=f"Share error: {str(e)}").open()
    
    def _delete_image(self):
        """Delete the original image with confirmation"""
        from utils.dialogs import ConfirmDialog
        
        dialog = ConfirmDialog(
            title="Delete Image?",
            text=f"Are you sure you want to delete {self.image_path.name}?",
            on_confirm=self._confirm_delete
        )
        dialog.open()
    
    def _confirm_delete(self):
        """Actually delete the image"""
        try:
            os.remove(self.image_path)
            Snackbar(text="Image deleted").open()
            self.dismiss()
            
            # Call callback if provided
            if self.on_delete_callback:
                self.on_delete_callback()
        except Exception as e:
            Snackbar(text=f"Delete failed: {str(e)}").open()
    
    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        """Handle keyboard events"""
        if key == 27:  # ESC or Back button
            self.dismiss()
            return True
        return False
    
    def on_dismiss(self):
        """Clean up when dialog is dismissed"""
        Window.unbind(on_keyboard=self._on_keyboard)
        
        # Clean up temporary file
        if self.temp_image_path and self.temp_image_path.exists():
            try:
                os.remove(self.temp_image_path)
            except:
                pass