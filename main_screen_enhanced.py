"""
Enhanced main screen with resolution selector and all DALL-E 2 features
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
from utils.resolution_selector import CompactResolutionSelector

# Create enhanced KV layout with resolution selector
KV = '''
<MainScreenEnhanced>:
    MDBoxLayout:
        orientation: 'vertical'
        
        # Top App Bar
        MDTopAppBar:
            title: "DALL-E 2 Complete"
            elevation: 4
            md_bg_color: app.theme_cls.primary_color
            left_action_items: [["menu", lambda x: app.toggle_nav_drawer()]]
            right_action_items: [["history", lambda x: app.switch_screen('history')], ["image-multiple", lambda x: app.switch_screen('gallery')]]
        
        # Main content scroll view
        MDScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                spacing: dp(20)
                padding: dp(20)
                adaptive_height: True
                
                # Welcome card
                MDCard:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: dp(120)
                    elevation: 8
                    radius: [dp(20)]
                    md_bg_color: app.theme_cls.primary_light
                    
                    MDBoxLayout:
                        orientation: 'vertical'
                        padding: dp(20)
                        spacing: dp(10)
                        
                        MDLabel:
                            text: "DALL-E 2 Complete Features"
                            font_style: "H5"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 1
                            
                        MDLabel:
                            text: "Generate • Edit • Extend • Create Variations"
                            font_style: "Body1"
                            theme_text_color: "Custom"
                            text_color: 1, 1, 1, 0.8
                
                # Prompt input card
                MDCard:
                    orientation: 'vertical'
                    size_hint_y: None
                    height: dp(280)
                    elevation: 3
                    radius: [dp(15)]
                    padding: dp(20)
                    spacing: dp(10)
                    
                    MDTextField:
                        id: prompt_input
                        hint_text: "Enter your creative prompt..."
                        mode: "rectangle"
                        multiline: True
                        max_height: dp(100)
                        font_size: dp(16)
                        helper_text: "Be descriptive! E.g., 'A majestic lion in a neon-lit cyberpunk city'"
                        helper_text_mode: "on_focus"
                        icon_right: "lightbulb-outline"
                    
                    # Resolution selector container
                    MDBoxLayout:
                        id: resolution_container
                        size_hint_y: None
                        height: dp(40)
                        spacing: dp(10)
                    
                    # Batch generation section
                    MDBoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: dp(40)
                        spacing: dp(10)
                        
                        MDLabel:
                            text: "Batch:"
                            size_hint_x: None
                            width: dp(50)
                        
                        MDSlider:
                            id: batch_slider
                            min: 1
                            max: 4
                            value: 1
                            size_hint_x: 0.6
                            on_value: batch_label.text = f"{int(self.value)} image{'s' if int(self.value) > 1 else ''}"
                        
                        MDLabel:
                            id: batch_label
                            text: "1 image"
                            size_hint_x: 0.3
                
                # Action buttons
                MDBoxLayout:
                    orientation: 'horizontal'
                    size_hint_y: None
                    height: dp(60)
                    spacing: dp(20)
                    padding: [dp(40), 0, dp(40), 0]
                    
                    MDRaisedButton:
                        text: "Generate"
                        icon: "creation"
                        pos_hint: {"center_x": 0.5}
                        md_bg_color: app.theme_cls.accent_color
                        on_release: root.generate_images()
                        size_hint_x: 1
                    
                    MDRaisedButton:
                        text: "Gallery"
                        icon: "image-multiple"
                        pos_hint: {"center_x": 0.5}
                        on_release: app.switch_screen('gallery')
                        size_hint_x: 0.5
                
                # Loading spinner (hidden by default)
                MDSpinner:
                    id: spinner
                    size_hint: None, None
                    size: dp(48), dp(48)
                    pos_hint: {"center_x": 0.5}
                    active: False
                    opacity: 0 if not self.active else 1
                
                # Generated image display
                MDCard:
                    id: image_card
                    orientation: 'vertical'
                    size_hint_y: None
                    height: dp(400)
                    elevation: 5
                    radius: [dp(15)]
                    opacity: 0 if not generated_image.texture else 1
                    
                    Image:
                        id: generated_image
                        allow_stretch: True
                        keep_ratio: True
                        opacity: 0
                    
                    # Image action buttons
                    MDBoxLayout:
                        orientation: 'horizontal'
                        size_hint_y: None
                        height: dp(60)
                        padding: dp(10)
                        spacing: dp(10)
                        opacity: 1 if generated_image.texture else 0
                        
                        MDIconButton:
                            icon: "content-save"
                            theme_icon_color: "Custom"
                            icon_color: app.theme_cls.primary_color
                            on_release: root.save_image()
                        
                        MDIconButton:
                            icon: "share-variant"
                            theme_icon_color: "Custom"
                            icon_color: app.theme_cls.primary_color
                            on_release: root.share_image()
                        
                        MDIconButton:
                            icon: "brush"
                            theme_icon_color: "Custom"
                            icon_color: (0.7, 0, 0.7, 1)
                            on_release: root.edit_image()
                            tooltip_text: "Edit with AI"
                        
                        MDIconButton:
                            icon: "arrow-expand-all"
                            theme_icon_color: "Custom"
                            icon_color: (0, 0.7, 0, 1)
                            on_release: root.outpaint_image()
                            tooltip_text: "Extend image"
'''

Builder.load_string(KV)


class MainScreenEnhanced(Screen):
    """Enhanced main screen with all DALL-E 2 features"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api_service = DalleAPIService()
        self.storage = SecureStorage()
        self.image_processor = ImageProcessor()
        self.current_image_url = None
        self.current_image_data = None
        self.current_image_path = None
        self.resolution_selector = None
        
        # Load API key on startup
        Clock.schedule_once(self.load_api_key, 0.5)
        Clock.schedule_once(self.setup_resolution_selector, 0.1)
    
    def setup_resolution_selector(self, dt):
        """Add resolution selector to the UI"""
        self.resolution_selector = CompactResolutionSelector()
        self.resolution_selector.on_size_change = self.on_resolution_change
        self.ids.resolution_container.add_widget(self.resolution_selector)
    
    def on_resolution_change(self, size):
        """Handle resolution change"""
        print(f"Selected resolution: {size}")
    
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
        api_key_field = MDTextField(
            hint_text="Enter your OpenAI API key",
            helper_text="Get your API key from platform.openai.com",
            helper_text_mode="on_focus",
            password=True,
            size_hint_y=None,
            height=dp(80)
        )
        
        dialog = MDDialog(
            title="API Key Required",
            type="custom",
            content_cls=api_key_field,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDFlatButton(
                    text="SAVE",
                    on_release=lambda x: self.save_api_key(api_key_field.text, dialog)
                ),
            ],
        )
        dialog.open()
    
    def save_api_key(self, api_key, dialog):
        """Save the API key"""
        if api_key.strip():
            self.storage.save_api_key(api_key.strip())
            self.api_service.set_api_key(api_key.strip())
            dialog.dismiss()
            Snackbar(text="API key saved successfully").open()
        else:
            Snackbar(text="Please enter a valid API key").open()
    
    def generate_images(self):
        """Generate images with selected resolution and batch size"""
        prompt = self.ids.prompt_input.text.strip()
        
        if not prompt:
            Snackbar(text="Please enter a prompt").open()
            return
        
        if not self.api_service.api_key:
            self.show_api_key_dialog()
            return
        
        # Get settings
        size = self.resolution_selector.selected_size
        batch_size = int(self.ids.batch_slider.value)
        
        # Show loading spinner
        self.ids.spinner.active = True
        self.ids.generated_image.opacity = 0
        
        # Generate in background thread
        threading.Thread(
            target=self._generate_images_thread,
            args=(prompt, size, batch_size)
        ).start()
    
    def _generate_images_thread(self, prompt, size, batch_size):
        """Background thread for image generation"""
        try:
            # For batch generation, we'll generate one at a time
            # (DALL-E 2 API supports n parameter, but for demo we'll do sequential)
            
            for i in range(batch_size):
                # Generate image
                image, image_url = self.api_service.generate_image(
                    prompt=prompt,
                    size=size,
                    n=1
                )
                
                # Save the first image for display
                if i == 0:
                    self.current_image_data = image
                    self.current_image_url = image_url
                
                # Save to gallery
                filename = self.image_processor.save_to_gallery(image, prompt)
                
                # Update UI on main thread
                if i == 0:
                    Clock.schedule_once(
                        lambda dt: self._update_ui_success(filename),
                        0
                    )
            
            # Show completion message for batch
            if batch_size > 1:
                Clock.schedule_once(
                    lambda dt: Snackbar(text=f"Generated {batch_size} images!").open(),
                    0
                )
                    
        except DalleAPIError as e:
            Clock.schedule_once(
                lambda dt: self._update_ui_error(str(e)),
                0
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._update_ui_error(f"Unexpected error: {str(e)}"),
                0
            )
    
    def _update_ui_success(self, filename):
        """Update UI after successful generation"""
        self.ids.spinner.active = False
        
        # Display the generated image
        gallery_path = self.image_processor.get_gallery_path()
        image_path = os.path.join(gallery_path, filename)
        self.current_image_path = image_path
        
        self.ids.generated_image.source = image_path
        self.ids.generated_image.opacity = 1
        
        Snackbar(text=f"Image saved as {filename}").open()
    
    def _update_ui_error(self, error_message):
        """Update UI after generation error"""
        self.ids.spinner.active = False
        Snackbar(text=error_message).open()
    
    def save_image(self):
        """Save current image (already saved to gallery)"""
        if self.current_image_path:
            Snackbar(text="Image already saved to gallery!").open()
    
    def share_image(self):
        """Share the current image"""
        if self.current_image_path:
            from utils.android_utils import share_image
            share_image(self.current_image_path, "Check out this DALL-E 2 creation!")
    
    def edit_image(self):
        """Open inpainting editor"""
        if self.current_image_path:
            from utils.image_editor_dalle import ImageEditorDALLE
            
            editor = ImageEditorDALLE(
                image_path=self.current_image_path,
                on_complete_callback=self.on_edit_complete
            )
            editor.open()
    
    def outpaint_image(self):
        """Open outpainting editor"""
        if self.current_image_path:
            from utils.image_outpainter_dalle import ImageOutpainterDALLE
            
            outpainter = ImageOutpainterDALLE(
                image_path=self.current_image_path,
                on_complete_callback=self.on_outpaint_complete
            )
            outpainter.open()
    
    def on_edit_complete(self, edited_path):
        """Handle edit completion"""
        # Update displayed image
        self.current_image_path = edited_path
        self.ids.generated_image.source = edited_path
        Snackbar(text="Edit completed!").open()
    
    def on_outpaint_complete(self, extended_path):
        """Handle outpainting completion"""
        # Update displayed image
        self.current_image_path = extended_path
        self.ids.generated_image.source = extended_path
        Snackbar(text="Image extended!").open()