"""
DALL-E 2 style outpainting - extend images beyond their borders
"""

from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.uix.widget import Widget
from kivy.graphics import Rectangle, Color, Line
from kivy.uix.image import Image as KivyImage
from kivy.core.window import Window
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivy.metrics import dp
from PIL import Image as PILImage, ImageDraw
import io
import os
from pathlib import Path
import numpy as np


class OutpaintCanvas(Widget):
    """Canvas showing image with extension areas"""
    
    def __init__(self, image_path, **kwargs):
        super().__init__(**kwargs)
        self.image_path = image_path
        self.pil_image = PILImage.open(image_path)
        self.original_width, self.original_height = self.pil_image.size
        
        # Extension settings
        self.extensions = {
            'top': False,
            'right': False,
            'bottom': False,
            'left': False
        }
        self.extension_size = 256  # pixels
        
        self.bind(size=self.update_display)
        self.bind(pos=self.update_display)
        
    def update_display(self, *args):
        """Update the canvas display"""
        self.canvas.clear()
        
        with self.canvas:
            # Calculate extended dimensions
            extended_width = self.original_width
            extended_height = self.original_height
            offset_x = 0
            offset_y = 0
            
            if self.extensions['left']:
                extended_width += self.extension_size
                offset_x = self.extension_size
            if self.extensions['right']:
                extended_width += self.extension_size
            if self.extensions['top']:
                extended_height += self.extension_size
                offset_y = self.extension_size
            if self.extensions['bottom']:
                extended_height += self.extension_size
            
            # Calculate scale to fit in widget
            scale_x = self.width / extended_width
            scale_y = self.height / extended_height
            scale = min(scale_x, scale_y) * 0.9  # 90% to leave margin
            
            # Calculate positions
            display_width = extended_width * scale
            display_height = extended_height * scale
            display_x = self.x + (self.width - display_width) / 2
            display_y = self.y + (self.height - display_height) / 2
            
            # Draw extension areas (semi-transparent)
            Color(0.5, 0.5, 0.5, 0.3)
            Rectangle(pos=(display_x, display_y), size=(display_width, display_height))
            
            # Draw original image area
            img_x = display_x + (offset_x * scale)
            img_y = display_y + (offset_y * scale)
            img_width = self.original_width * scale
            img_height = self.original_height * scale
            
            Color(1, 1, 1, 1)
            # Note: In real implementation, we'd draw the actual image here
            Rectangle(pos=(img_x, img_y), size=(img_width, img_height))
            
            # Draw extension indicators
            Color(1, 0, 0, 0.5)
            line_width = dp(3)
            
            if self.extensions['top']:
                Line(points=[display_x, img_y + img_height,
                           display_x + display_width, img_y + img_height],
                     width=line_width)
            if self.extensions['bottom']:
                Line(points=[display_x, img_y,
                           display_x + display_width, img_y],
                     width=line_width)
            if self.extensions['left']:
                Line(points=[img_x, display_y,
                           img_x, display_y + display_height],
                     width=line_width)
            if self.extensions['right']:
                Line(points=[img_x + img_width, display_y,
                           img_x + img_width, display_y + display_height],
                     width=line_width)
    
    def toggle_extension(self, side):
        """Toggle extension for a side"""
        self.extensions[side] = not self.extensions[side]
        self.update_display()
    
    def get_extended_image_and_mask(self):
        """Create extended image with mask for outpainting"""
        # Calculate new dimensions
        new_width = self.original_width
        new_height = self.original_height
        offset_x = 0
        offset_y = 0
        
        if self.extensions['left']:
            new_width += self.extension_size
            offset_x = self.extension_size
        if self.extensions['right']:
            new_width += self.extension_size
        if self.extensions['top']:
            new_height += self.extension_size
            offset_y = self.extension_size
        if self.extensions['bottom']:
            new_height += self.extension_size
        
        # Create extended image (transparent background)
        extended_image = PILImage.new('RGBA', (new_width, new_height), (0, 0, 0, 0))
        extended_image.paste(self.pil_image.convert('RGBA'), (offset_x, offset_y))
        
        # Create mask (white = generate, black = keep)
        mask = PILImage.new('L', (new_width, new_height), 0)  # Start all black
        mask_draw = ImageDraw.Draw(mask)
        
        # Mark extension areas as white (to generate)
        if self.extensions['top']:
            mask_draw.rectangle([0, 0, new_width, offset_y], fill=255)
        if self.extensions['bottom']:
            mask_draw.rectangle([0, offset_y + self.original_height, 
                               new_width, new_height], fill=255)
        if self.extensions['left']:
            mask_draw.rectangle([0, 0, offset_x, new_height], fill=255)
        if self.extensions['right']:
            mask_draw.rectangle([offset_x + self.original_width, 0, 
                               new_width, new_height], fill=255)
        
        return extended_image, mask
    
    def has_extensions(self):
        """Check if any extensions are selected"""
        return any(self.extensions.values())


class ImageOutpainterDALLE(MDDialog):
    """DALL-E 2 style outpainting interface"""
    
    def __init__(self, image_path, on_complete_callback=None, **kwargs):
        self.image_path = Path(image_path)
        self.on_complete_callback = on_complete_callback
        self.canvas_widget = None
        self.processing = False
        
        content = self._create_content()
        
        super().__init__(
            type="custom",
            content_cls=content,
            size_hint=(0.95, 0.95),
            **kwargs
        )
        
        Window.bind(on_keyboard=self._on_keyboard)
    
    def _create_content(self):
        """Create the outpainting UI"""
        layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            padding=dp(10)
        )
        
        # Toolbar
        toolbar = self._create_toolbar()
        layout.add_widget(toolbar)
        
        # Canvas showing image with extensions
        self.canvas_widget = OutpaintCanvas(str(self.image_path))
        layout.add_widget(self.canvas_widget)
        
        # Direction controls
        controls = self._create_direction_controls()
        layout.add_widget(controls)
        
        # Extension size control
        size_control = self._create_size_control()
        layout.add_widget(size_control)
        
        # Prompt input
        self.prompt_field = MDTextField(
            hint_text="Describe what to generate in the extended areas...",
            multiline=True,
            size_hint_y=None,
            height=dp(80)
        )
        layout.add_widget(self.prompt_field)
        
        # Progress indicator
        self.progress = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={'center_x': 0.5}
        )
        self.progress.opacity = 0
        layout.add_widget(self.progress)
        
        # Action buttons
        actions = self._create_actions()
        layout.add_widget(actions)
        
        return layout
    
    def _create_toolbar(self):
        """Create toolbar"""
        toolbar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(56)
        )
        
        toolbar.add_widget(MDLabel(
            text="Extend Image (Outpainting)",
            theme_text_color="Primary",
            font_style="H6"
        ))
        
        close_btn = MDIconButton(
            icon="close",
            on_release=lambda x: self.dismiss()
        )
        toolbar.add_widget(close_btn)
        
        return toolbar
    
    def _create_direction_controls(self):
        """Create direction selection controls"""
        controls = MDCard(
            orientation='vertical',
            padding=dp(10),
            size_hint_y=None,
            height=dp(120),
            elevation=3
        )
        
        controls.add_widget(MDLabel(
            text="Select sides to extend:",
            theme_text_color="Primary",
            size_hint_y=None,
            height=dp(30)
        ))
        
        # Direction grid
        grid = MDBoxLayout(
            orientation='vertical',
            spacing=dp(5)
        )
        
        # Top row
        top_row = MDBoxLayout(orientation='horizontal')
        top_row.add_widget(Widget())  # Spacer
        self.top_btn = MDRaisedButton(
            text="Top",
            size_hint_x=0.3,
            on_release=lambda x: self._toggle_direction('top')
        )
        top_row.add_widget(self.top_btn)
        top_row.add_widget(Widget())  # Spacer
        grid.add_widget(top_row)
        
        # Middle row
        middle_row = MDBoxLayout(orientation='horizontal')
        self.left_btn = MDRaisedButton(
            text="Left",
            size_hint_x=0.3,
            on_release=lambda x: self._toggle_direction('left')
        )
        middle_row.add_widget(self.left_btn)
        middle_row.add_widget(Widget(size_hint_x=0.4))  # Center space
        self.right_btn = MDRaisedButton(
            text="Right",
            size_hint_x=0.3,
            on_release=lambda x: self._toggle_direction('right')
        )
        middle_row.add_widget(self.right_btn)
        grid.add_widget(middle_row)
        
        # Bottom row
        bottom_row = MDBoxLayout(orientation='horizontal')
        bottom_row.add_widget(Widget())  # Spacer
        self.bottom_btn = MDRaisedButton(
            text="Bottom",
            size_hint_x=0.3,
            on_release=lambda x: self._toggle_direction('bottom')
        )
        bottom_row.add_widget(self.bottom_btn)
        bottom_row.add_widget(Widget())  # Spacer
        grid.add_widget(bottom_row)
        
        controls.add_widget(grid)
        
        self.direction_buttons = {
            'top': self.top_btn,
            'right': self.right_btn,
            'bottom': self.bottom_btn,
            'left': self.left_btn
        }
        
        return controls
    
    def _create_size_control(self):
        """Create extension size control"""
        size_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10)
        )
        
        size_box.add_widget(MDLabel(
            text="Extension size:",
            size_hint_x=0.4
        ))
        
        # Size options
        for size in [128, 256, 512]:
            btn = MDFlatButton(
                text=f"{size}px",
                on_release=lambda x, s=size: self._set_extension_size(s)
            )
            if size == 256:  # Default
                btn.md_bg_color = (0.5, 0.5, 1, 0.3)
            size_box.add_widget(btn)
            
        return size_box
    
    def _create_actions(self):
        """Create action buttons"""
        actions = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )
        
        cancel_btn = MDRaisedButton(
            text="Cancel",
            on_release=lambda x: self.dismiss()
        )
        actions.add_widget(cancel_btn)
        
        self.generate_btn = MDRaisedButton(
            text="Generate Extension",
            md_bg_color=(0, 0.7, 0, 1),
            on_release=lambda x: self._generate_outpainting()
        )
        actions.add_widget(self.generate_btn)
        
        return actions
    
    def _toggle_direction(self, direction):
        """Toggle extension direction"""
        self.canvas_widget.toggle_extension(direction)
        
        # Update button appearance
        btn = self.direction_buttons[direction]
        if self.canvas_widget.extensions[direction]:
            btn.md_bg_color = (0.5, 0.5, 1, 0.5)
        else:
            btn.md_bg_color = (0.5, 0.5, 0.5, 0.2)
    
    def _set_extension_size(self, size):
        """Set extension size"""
        self.canvas_widget.extension_size = size
        self.canvas_widget.update_display()
    
    def _generate_outpainting(self):
        """Generate the outpainting using DALL-E API"""
        if self.processing:
            return
        
        if not self.canvas_widget.has_extensions():
            Snackbar(text="Please select at least one side to extend").open()
            return
        
        prompt = self.prompt_field.text.strip()
        if not prompt:
            Snackbar(text="Please describe what to generate").open()
            return
        
        from kivymd.app import MDApp
        from kivy.clock import Clock
        
        app = MDApp.get_running_app()
        
        if not hasattr(app, 'worker_manager'):
            Snackbar(text="Worker system not available").open()
            return
        
        # Create extended image and mask
        extended_image, mask = self.canvas_widget.get_extended_image_and_mask()
        
        # Save to temporary files
        temp_dir = Path(app.user_data_dir) / 'temp'
        temp_dir.mkdir(exist_ok=True)
        
        extended_path = temp_dir / 'outpaint_extended.png'
        mask_path = temp_dir / 'outpaint_mask.png'
        
        extended_image.save(extended_path)
        mask.save(mask_path)
        
        self.processing = True
        self.progress.opacity = 1
        self.progress.active = True
        self.generate_btn.disabled = True
        
        Snackbar(text="Generating extension...").open()
        
        # Call API through worker (using edit endpoint for outpainting)
        from workers.api_request import APIRequest, APIRequestType, WorkerPriority
        
        request = APIRequest(
            request_type=APIRequestType.EDIT_IMAGE,
            prompt=prompt,
            image_path=str(extended_path),
            mask_path=str(mask_path),
            size="1024x1024",  # Will need to handle different sizes
            model="dall-e-2",
            callback=lambda result: Clock.schedule_once(
                lambda dt: self._on_outpaint_complete(result), 0
            )
        )
        
        app.worker_manager.api_worker.add_task(request, WorkerPriority.HIGH)
    
    def _on_outpaint_complete(self, result):
        """Handle outpainting completion"""
        self.processing = False
        self.progress.opacity = 0
        self.progress.active = False
        self.generate_btn.disabled = False
        
        if result.get('success'):
            # Download and save the extended image
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            
            images = result.get('images', [])
            if images:
                image_url = images[0]['url']
                
                # Download and save
                import requests
                from datetime import datetime
                
                response = requests.get(image_url)
                if response.status_code == 200:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"outpainted_{timestamp}.png"
                    save_path = Path(app.user_data_dir) / 'gallery' / filename
                    save_path.parent.mkdir(exist_ok=True)
                    
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    
                    Snackbar(text=f"Extension saved as {filename}").open()
                    
                    # Call completion callback
                    if self.on_complete_callback:
                        self.on_complete_callback(str(save_path))
                    
                    self.dismiss()
        else:
            error = result.get('error', 'Unknown error')
            Snackbar(text=f"Extension failed: {error}").open()
    
    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:  # ESC
            self.dismiss()
            return True
        return False
    
    def on_dismiss(self):
        Window.unbind(on_keyboard=self._on_keyboard)