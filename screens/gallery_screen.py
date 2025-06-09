"""
Gallery screen to view saved images
"""

from kivy.uix.screenmanager import Screen
from kivy.utils import platform
from kivy.lang import Builder
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.card import MDCard
from kivy.uix.image import Image
from pathlib import Path
import os

from utils.image_utils import ImageProcessor
from utils.image_viewer import ImageViewer
from utils.dialogs import ConfirmDialog

# Load KV file
Builder.load_file(os.path.join(os.path.dirname(__file__), '../ui/gallery_screen.kv'))


class GalleryScreen(Screen):
    """Gallery screen to view saved images"""
    
    def on_enter(self):
        """Called when screen is entered"""
        self.refresh_gallery()
    
    def refresh_gallery(self):
        """Refresh gallery with saved images"""
        self.ids.gallery_grid.clear_widgets()
        
        # Get gallery path
        gallery_path = Path(ImageProcessor().get_gallery_path())
        
        # Load all images
        images = list(gallery_path.glob("*.png"))
        
        # Update count
        if hasattr(self.ids, 'gallery_count'):
            count_text = f"{len(images)} {'image' if len(images) == 1 else 'images'}"
            self.ids.gallery_count.text = count_text
        
        # Add images to grid
        for image_file in sorted(images, reverse=True):
            self._add_gallery_image(image_file)
    
    def _add_gallery_image(self, image_path):
        """Add image to gallery grid"""
        card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height=200,
            elevation=5,
            radius=[15,]
        )
        
        img = Image(
            source=str(image_path),
            allow_stretch=True,
            keep_ratio=True
        )
        card.add_widget(img)
        
        # Add tap to view full
        card.bind(on_release=lambda x: self._view_full_image(image_path))
        
        self.ids.gallery_grid.add_widget(card)
    
    def _view_full_image(self, image_path):
        """View full size image"""
        viewer = ImageViewer(image_path, on_delete_callback=self.refresh_gallery)
        viewer.open()
    
    def clear_gallery(self):
        """Clear all gallery images"""
        # Get image count
        gallery_path = Path(ImageProcessor().get_gallery_path())
        images = list(gallery_path.glob("*.png"))
        
        if not images:
            Snackbar(text="Gallery is already empty").open()
            return
        
        dialog = ConfirmDialog(
            title="Clear Gallery?",
            text=f"This will delete all {len(images)} images from the gallery. This action cannot be undone.",
            on_confirm=self._confirm_clear_gallery,
            confirm_text="Delete All",
            cancel_text="Cancel"
        )
        dialog.open()
    
    def _confirm_clear_gallery(self):
        """Actually clear the gallery"""
        try:
            gallery_path = Path(ImageProcessor().get_gallery_path())
            images = list(gallery_path.glob("*.png"))
            
            for image in images:
                os.remove(image)
            
            self.refresh_gallery()
            Snackbar(text=f"Deleted {len(images)} images").open()
        except Exception as e:
            Snackbar(text=f"Error clearing gallery: {str(e)}").open()
