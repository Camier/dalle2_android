"""
Full screen image viewer with zoom and pan support
"""

from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDIconButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.core.window import Window
from kivymd.uix.snackbar import Snackbar
from pathlib import Path
import os

from utils.android_utils import share_image


class ImageViewer(MDDialog):
    """Full screen image viewer with zoom, pan, share, and delete functionality"""
    
    def __init__(self, image_path, on_delete_callback=None, **kwargs):
        self.image_path = Path(image_path)
        self.on_delete_callback = on_delete_callback
        
        # Create content
        content = self._create_content()
        
        # Initialize dialog
        super().__init__(
            type="custom",
            content_cls=content,
            size_hint=(0.95, 0.9),
            **kwargs
        )
        
        # Bind keyboard
        Window.bind(on_keyboard=self._on_keyboard)
    
    def _create_content(self):
        """Create the viewer content"""
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
        from kivymd.uix.label import MDLabel
        title = MDLabel(
            text=self.image_path.name,
            theme_text_color="Primary",
            font_style="H6",
            size_hint_x=0.7
        )
        toolbar.add_widget(title)
        
        # Action buttons
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
        
        # Instructions
        instructions = MDLabel(
            text="Pinch to zoom • Double tap to reset • Swipe to pan",
            theme_text_color="Secondary",
            font_style="Caption",
            halign="center",
            size_hint_y=None,
            height=dp(30)
        )
        layout.add_widget(instructions)
        
        return layout
    
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
        """Share the image"""
        try:
            success = share_image(str(self.image_path), "Check out this image!")
            if success:
                Snackbar(text="Opening share dialog...").open()
            else:
                Snackbar(text="Failed to share image").open()
        except Exception as e:
            Snackbar(text=f"Share error: {str(e)}").open()
    
    def _delete_image(self):
        """Delete the image with confirmation"""
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
