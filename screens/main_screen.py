"""
Main screen for DALL-E image generation app - Full Featured Version
"""

from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
from kivy.utils import platform
from kivy.lang import Builder
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.app import MDApp

import threading
import os
from datetime import datetime
from pathlib import Path

from services.dalle_api import DalleAPIService, DalleAPIError
from utils.storage import SecureStorage
from utils.image_utils import ImageProcessor

# Load KV file
Builder.load_file(os.path.join(os.path.dirname(__file__), '../ui/main_screen.kv'))

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_service = DalleAPIService()
        self.storage = SecureStorage()
        self.image_processor = ImageProcessor()
        self.current_image_url = None
        self.current_image_data = None
        
        # Load API key on startup
        Clock.schedule_once(self.load_api_key, 0.5)
    
    def load_api_key(self, dt):
        """Load saved API key"""
        api_key = self.storage.get_api_key()
        if api_key:
            self.api_service.set_api_key(api_key)
        else:
            self.show_api_key_dialog()
    
    def show_api_key_dialog(self):
        """Show dialog to enter API key"""
        from kivymd.uix.textfield import MDTextField
        
        # Create text field for API key
        self.api_key_field = MDTextField(
            hint_text="Enter your OpenAI API Key",
            password=True,
            helper_text="Get your API key from platform.openai.com",
            helper_text_mode="on_focus"
        )
        
        self.dialog = MDDialog(
            title="API Key Required",
            type="custom",
            content_cls=self.api_key_field,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: self.dialog.dismiss()
                ),
                MDFlatButton(
                    text="SAVE",
                    on_release=self.save_api_key_from_dialog
                ),
            ],
        )
        self.dialog.open()
    
    def save_api_key_from_dialog(self, instance):
        """Save API key from dialog"""
        api_key = self.api_key_field.text.strip()
        if api_key:
            self.storage.save_api_key(api_key)
            self.api_service.set_api_key(api_key)
            self.dialog.dismiss()
            Snackbar(text="API Key saved successfully!").open()
        else:
            Snackbar(text="Please enter a valid API key").open()
    
    def generate_image(self):
        """Generate image from prompt"""
        prompt = self.ids.prompt_input.text.strip()
        
        if not prompt:
            Snackbar(text="Please enter a prompt").open()
            return
        
        if not self.api_service.api_key:
            self.show_api_key_dialog()
            return
        
        # Show loading spinner
        self.ids.spinner.active = True
        self.ids.generated_image.opacity = 0
        
        # Generate in background thread
        threading.Thread(
            target=self._generate_image_thread,
            args=(prompt,)
        ).start()
    
    def _generate_image_thread(self, prompt):
        """Background thread for image generation"""
        try:
            # Get size from settings or use default
            size = MDApp.get_running_app().settings_screen.get_image_size()
            
            # Generate image
            response = self.api_service.generate_image(prompt, size=size)
            
            if response and 'data' in response and len(response['data']) > 0:
                image_url = response['data'][0]['url']
                
                # Download image
                image_data = self.image_processor.download_image(image_url)
                
                if image_data:
                    # Update UI on main thread
                    Clock.schedule_once(
                        lambda dt: self._display_image(image_data, prompt),
                        0
                    )
                    
                    # Save to history
                    self.storage.save_to_history(prompt, image_url)
                else:
                    Clock.schedule_once(
                        lambda dt: self._show_error("Failed to download image"),
                        0
                    )
            else:
                Clock.schedule_once(
                    lambda dt: self._show_error("No image generated"),
                    0
                )
                
        except DalleAPIError as e:
            Clock.schedule_once(
                lambda dt: self._show_error(f"API Error: {str(e)}"),
                0
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._show_error(f"Error: {str(e)}"),
                0
            )
    
    def _display_image(self, image_data, prompt):
        """Display generated image"""
        # Hide spinner
        self.ids.spinner.active = False
        
        # Display image
        texture = self.image_processor.create_texture_from_data(image_data)
        if texture:
            self.ids.generated_image.texture = texture
            self.ids.generated_image.opacity = 1
            
            # Store current image
            self.current_image_data = image_data
            
            # Auto-save if enabled
            app = MDApp.get_running_app()
            if app.settings_screen.is_auto_save_enabled():
                self.save_current_image(prompt)
            
            Snackbar(text="Image generated successfully!").open()
        else:
            self._show_error("Failed to display image")
    
    def _show_error(self, message):
        """Show error message"""
        self.ids.spinner.active = False
        Snackbar(text=message).open()
    
    def save_current_image(self, prompt=None):
        """Save current image to gallery"""
        if self.current_image_data:
            filename = self.image_processor.save_to_gallery(
                self.current_image_data,
                prompt or "dalle_image"
            )
            if filename:
                Snackbar(text=f"Image saved to gallery!").open()
                # Refresh gallery
                MDApp.get_running_app().gallery_screen.refresh_gallery()
            else:
                Snackbar(text="Failed to save image").open()
    
    def share_current_image(self):
        """Share current image via Android share intent"""
        if self.current_image_data:
            # First save the image temporarily
            filename = self.image_processor.save_to_gallery(
                self.current_image_data,
                "share_temp"
            )
            if filename:
                # Import share helper
                try:
                    from utils.android_utils import share_helper
                    success = share_helper.share_image(
                        filename, 
                        f"Check out this AI-generated image: {self.ids.prompt_input.text}"
                    )
                    if success:
                        Snackbar(text="Opening share dialog...").open()
                    else:
                        Snackbar(text="Failed to share image").open()
                except Exception as e:
                    Snackbar(text=f"Share error: {str(e)}").open()
            else:
                Snackbar(text="Failed to prepare image for sharing").open()
        else:
            Snackbar(text="No image to share").open()
    
    def generate_batch(self):
        """Generate multiple images"""
        prompt = self.ids.batch_prompt.text.strip()
        count = int(self.ids.batch_slider.value)
        
        if not prompt:
            Snackbar(text="Please enter a prompt").open()
            return
        
        if not self.api_service.api_key:
            self.show_api_key_dialog()
            return
        
        # Clear previous batch
        self.ids.batch_grid.clear_widgets()
        
        # Start batch generation
        Snackbar(text=f"Generating {count} images...").open()
        
        threading.Thread(
            target=self._generate_batch_thread,
            args=(prompt, count)
        ).start()
    
    def _generate_batch_thread(self, prompt, count):
        """Generate multiple images in background"""
        for i in range(count):
            try:
                # Add variation to prompt
                varied_prompt = f"{prompt}, variation {i+1}"
                
                # Generate image
                response = self.api_service.generate_image(varied_prompt)
                
                if response and 'data' in response:
                    image_url = response['data'][0]['url']
                    image_data = self.image_processor.download_image(image_url)
                    
                    if image_data:
                        Clock.schedule_once(
                            lambda dt, data=image_data, p=varied_prompt: 
                            self._add_batch_image(data, p),
                            0
                        )
                        
            except Exception as e:
                print(f"Batch generation error: {e}")
                continue
    
    def _add_batch_image(self, image_data, prompt):
        """Add image to batch grid"""
        from kivymd.uix.card import MDCard
        from kivy.uix.image import Image
        
        # Create card for image
        card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height=200,
            elevation=5,
            radius=[15,]
        )
        
        # Create image widget
        texture = self.image_processor.create_texture_from_data(image_data)
        if texture:
            img = Image(
                texture=texture,
                allow_stretch=True,
                keep_ratio=True
            )
            card.add_widget(img)
            
            # Add tap to save
            card.bind(on_release=lambda x: self._save_batch_image(image_data, prompt))
            
            self.ids.batch_grid.add_widget(card)
    
    def _save_batch_image(self, image_data, prompt):
        """Save batch image to gallery"""
        filename = self.image_processor.save_to_gallery(image_data, prompt)
        if filename:
            Snackbar(text="Image saved to gallery!").open()
            MDApp.get_running_app().gallery_screen.refresh_gallery()
