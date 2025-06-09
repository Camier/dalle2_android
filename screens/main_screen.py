"""
Main screen for DALL-E image generation app
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.card import MDCard
from kivymd.app import MDApp

import threading
from io import BytesIO
from PIL import Image as PILImage

from services.dalle_api import DalleAPIService, DalleAPIError
from utils.storage import SecureStorage
from utils.image_utils import save_image_to_gallery

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = SecureStorage()
        self.dalle_service = DalleAPIService()
        self.current_image = None
        self.api_key_dialog = None
        
        # Build UI
        self.build_ui()
        
        # Check for saved API key
        Clock.schedule_once(self.check_api_key, 0.5)
    
    def build_ui(self):
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Header
        header = Label(
            text='DALL-E Image Generator',
            size_hint_y=None,
            height=50,
            font_size='24sp',
            bold=True
        )
        main_layout.add_widget(header)
        
        # Prompt input
        self.prompt_input = MDTextField(
            hint_text='Describe your image...',
            mode='rectangle',
            size_hint_y=None,
            height=100,
            multiline=True,
            max_text_length=1000
        )
        main_layout.add_widget(self.prompt_input)
        
        # Generate button
        self.generate_button = MDRaisedButton(
            text='Generate Image',
            size_hint=(1, None),
            height=50,
            md_bg_color=(0.2, 0.6, 1, 1),
            on_release=self.generate_image
        )
        main_layout.add_widget(self.generate_button)
        
        # Image display card
        self.image_card = MDCard(
            size_hint=(1, 1),
            elevation=5,
            padding=10
        )
        
        # Image display
        self.image_display = Image(
            source='',
            allow_stretch=True,
            keep_ratio=True
        )
        self.image_card.add_widget(self.image_display)
        
        # Loading spinner (hidden by default)
        self.loading_spinner = MDSpinner(
            size_hint=(None, None),
            size=(48, 48),
            pos_hint={'center_x': .5, 'center_y': .5},
            active=False
        )
        self.image_card.add_widget(self.loading_spinner)
        
        main_layout.add_widget(self.image_card)
        
        # Save button (hidden by default)
        self.save_button = MDRaisedButton(
            text='Save to Gallery',
            size_hint=(1, None),
            height=50,
            md_bg_color=(0.2, 0.8, 0.2, 1),
            on_release=self.save_image,
            disabled=True
        )
        main_layout.add_widget(self.save_button)
        
        # Settings button
        settings_button = MDFlatButton(
            text='API Settings',
            size_hint=(1, None),
            height=40,
            on_release=self.show_api_key_dialog
        )
        main_layout.add_widget(settings_button)
        
        self.add_widget(main_layout)
    
    def check_api_key(self, dt):
        api_key = self.storage.get_api_key()
        if api_key:
            self.dalle_service.set_api_key(api_key)
        else:
            self.show_api_key_dialog(None)
    
    def show_api_key_dialog(self, instance):
        if not self.api_key_dialog:
            self.api_key_input = MDTextField(
                hint_text='Enter your OpenAI API key',
                mode='rectangle',
                password=True
            )
            
            self.api_key_dialog = MDDialog(
                title='API Key Setup',
                text='Enter your OpenAI API key to use DALL-E 2',
                type='custom',
                content_cls=self.api_key_input,
                buttons=[
                    MDFlatButton(
                        text='CANCEL',
                        on_release=lambda x: self.api_key_dialog.dismiss()
                    ),
                    MDRaisedButton(
                        text='SAVE',
                        on_release=self.save_api_key
                    )
                ]
            )
        
        # Pre-fill with existing key if available
        existing_key = self.storage.get_api_key()
        if existing_key:
            self.api_key_input.text = existing_key
        
        self.api_key_dialog.open()
    
    def save_api_key(self, instance):
        api_key = self.api_key_input.text.strip()
        if api_key:
            self.dalle_service.set_api_key(api_key)
            if self.dalle_service.validate_api_key():
                self.storage.save_api_key(api_key)
                self.api_key_dialog.dismiss()
                Snackbar(text='API key saved successfully').open()
            else:
                Snackbar(text='Invalid API key. Please check and try again.').open()
        else:
            Snackbar(text='Please enter an API key').open()
    
    def generate_image(self, instance):
        prompt = self.prompt_input.text.strip()
        if not prompt:
            Snackbar(text='Please enter a prompt').open()
            return
        
        if not self.dalle_service.api_key:
            Snackbar(text='Please set your API key first').open()
            self.show_api_key_dialog(None)
            return
        
        # Disable UI during generation
        self.generate_button.disabled = True
        self.save_button.disabled = True
        self.loading_spinner.active = True
        self.image_display.opacity = 0.3
        
        # Generate in background thread
        threading.Thread(target=self._generate_image_thread, args=(prompt,)).start()
    
    def _generate_image_thread(self, prompt):
        try:
            pil_image, image_url = self.dalle_service.generate_image(prompt)
            self.current_image = pil_image
            
            # Convert PIL image to Kivy texture
            buf = BytesIO()
            pil_image.save(buf, format='PNG')
            buf.seek(0)
            
            Clock.schedule_once(lambda dt: self._update_image_display(buf.getvalue()))
            
        except DalleAPIError as e:
            Clock.schedule_once(lambda dt: self._show_error(str(e)))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._show_error(f'Unexpected error: {str(e)}'))
    
    def _update_image_display(self, image_data):
        # Create texture from image data
        try:
            from kivy.core.image import Image as CoreImage
            img = CoreImage(BytesIO(image_data), ext='png')
            self.image_display.texture = img.texture
            self.image_display.opacity = 1
            
            # Enable save button
            self.save_button.disabled = False
            
            Snackbar(text='Image generated successfully!').open()
        except Exception as e:
            self._show_error(f'Error displaying image: {str(e)}')
        finally:
            # Re-enable UI
            self.generate_button.disabled = False
            self.loading_spinner.active = False
    
    def _show_error(self, error_message):
        Snackbar(text=error_message, duration=5).open()
        self.generate_button.disabled = False
        self.loading_spinner.active = False
        self.image_display.opacity = 1
    
    def save_image(self, instance):
        if not self.current_image:
            Snackbar(text='No image to save').open()
            return
        
        try:
            filepath = save_image_to_gallery(self.current_image)
            Snackbar(text=f'Image saved to gallery!').open()
        except Exception as e:
            Snackbar(text=f'Error saving image: {str(e)}').open()