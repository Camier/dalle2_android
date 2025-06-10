#!/usr/bin/env python3
"""
Test script for DALL-E 2 inpainting feature
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.config import Config
Config.set('graphics', 'width', '400')
Config.set('graphics', 'height', '800')

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.core.window import Window
from kivy.metrics import dp

# Import the image editor
from utils.image_editor_dalle import ImageEditorDALLE
from workers import WorkerManager


class TestInpaintingApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.worker_manager = None
        
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Purple"
        
        # Initialize worker manager (mock for testing)
        self.user_data_dir = "./test_data"
        Path(self.user_data_dir).mkdir(exist_ok=True)
        
        # Initialize worker with test API key
        test_api_key = os.environ.get('OPENAI_API_KEY', 'test_key')
        self.worker_manager = WorkerManager(
            app_data_dir=self.user_data_dir,
            api_key=test_api_key
        )
        self.worker_manager.start_all()
        
        # Create test screen
        screen = MDScreen()
        layout = MDBoxLayout(
            orientation='vertical',
            padding=dp(20),
            spacing=dp(20)
        )
        
        # Title
        layout.add_widget(MDLabel(
            text="DALL-E 2 Inpainting Test",
            font_style="H4",
            halign="center"
        ))
        
        # Instructions
        layout.add_widget(MDLabel(
            text="1. Place a test image named 'test_image.png' in this directory\n"
                 "2. Click 'Open Editor' to test inpainting\n"
                 "3. Draw a mask and describe what to generate",
            halign="center",
            size_hint_y=None,
            height=dp(100)
        ))
        
        # Test button
        test_btn = MDRaisedButton(
            text="Open Inpainting Editor",
            pos_hint={'center_x': 0.5},
            size_hint_x=0.8,
            on_release=self.open_test_editor
        )
        layout.add_widget(test_btn)
        
        # Test with sample image button
        sample_btn = MDRaisedButton(
            text="Create Sample Image First",
            pos_hint={'center_x': 0.5},
            size_hint_x=0.8,
            on_release=self.create_sample_image
        )
        layout.add_widget(sample_btn)
        
        screen.add_widget(layout)
        return screen
        
    def open_test_editor(self, *args):
        """Open the inpainting editor"""
        test_image = Path("test_image.png")
        
        if not test_image.exists():
            from kivymd.uix.snackbar import Snackbar
            Snackbar(text="Please create test_image.png first").open()
            return
            
        editor = ImageEditorDALLE(
            image_path=str(test_image),
            on_complete_callback=self.on_edit_complete
        )
        editor.open()
        
    def create_sample_image(self, *args):
        """Create a sample image for testing"""
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a test image
        img = Image.new('RGB', (1024, 1024), color='lightblue')
        draw = ImageDraw.Draw(img)
        
        # Draw some shapes
        draw.rectangle([100, 100, 400, 400], fill='red')
        draw.ellipse([600, 100, 900, 400], fill='green')
        draw.rectangle([100, 600, 900, 900], fill='yellow')
        
        # Add text
        try:
            # Try to use a nice font
            from PIL import ImageFont
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except:
            font = None
            
        draw.text((512, 512), "TEST IMAGE", fill='black', anchor='mm', font=font)
        draw.text((512, 450), "Draw mask to edit", fill='black', anchor='mm', font=font)
        
        # Save
        img.save('test_image.png')
        
        from kivymd.uix.snackbar import Snackbar
        Snackbar(text="Sample image created: test_image.png").open()
        
    def on_edit_complete(self, edited_path):
        """Handle edit completion"""
        from kivymd.uix.snackbar import Snackbar
        Snackbar(text=f"Edit saved: {edited_path}").open()
        
    def on_stop(self):
        """Clean up workers"""
        if self.worker_manager:
            self.worker_manager.stop_all()


if __name__ == "__main__":
    # Set window size for desktop testing
    if Window:
        Window.size = (400, 800)
    
    app = TestInpaintingApp()
    app.run()