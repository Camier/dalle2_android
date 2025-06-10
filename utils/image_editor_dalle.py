"""
DALL-E 2 style image editor with mask drawing for inpainting
"""

from kivymd.uix.dialog import MDDialog
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.slider import MDSlider
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivy.uix.widget import Widget
from kivy.graphics import Line, Color, Rectangle, Ellipse
from kivy.uix.image import Image
from kivy.core.window import Window
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivy.metrics import dp
from PIL import Image as PILImage, ImageDraw
import io
import os
from pathlib import Path
import numpy as np

class MaskCanvas(Widget):
    """Canvas for drawing masks with advanced features"""
    
    def __init__(self, image_path, **kwargs):
        super().__init__(**kwargs)
        self.image_path = image_path
        self.mask_lines = []
        self.brush_size = 20
        self.drawing = False
        self.eraser_mode = False
        
        # Load image to get dimensions
        self.pil_image = PILImage.open(image_path)
        self.image_width, self.image_height = self.pil_image.size
        
        # Create transparent mask
        self.mask_image = PILImage.new('RGBA', (self.image_width, self.image_height), (0, 0, 0, 0))
        self.mask_draw = ImageDraw.Draw(self.mask_image)
        
        # Store points for undo
        self.stroke_history = []
        self.current_stroke = []
        
        # Bind touch events
        self.bind(on_touch_down=self.start_drawing)
        self.bind(on_touch_move=self.draw_line)
        self.bind(on_touch_up=self.stop_drawing)
        
    def start_drawing(self, widget, touch):
        if self.collide_point(*touch.pos):
            self.drawing = True
            self.current_stroke = []
            
            with self.canvas:
                # Red for mask, blue for eraser
                color = (0, 0, 1, 0.5) if self.eraser_mode else (1, 0, 0, 0.5)
                Color(*color)
                
                # Draw circle at touch point
                d = self.brush_size
                Ellipse(pos=(touch.x - d/2, touch.y - d/2), size=(d, d))
                
                touch.ud['line'] = Line(
                    points=[touch.x, touch.y],
                    width=self.brush_size/2
                )
            
            self.current_stroke.append((touch.x, touch.y))
            self.mask_lines.append(touch.ud['line'])
            return True
            
    def draw_line(self, widget, touch):
        if self.drawing and 'line' in touch.ud:
            touch.ud['line'].points += [touch.x, touch.y]
            
            # Draw circle at each point for smooth line
            with self.canvas:
                d = self.brush_size
                Ellipse(pos=(touch.x - d/2, touch.y - d/2), size=(d, d))
            
            # Convert widget coordinates to image coordinates
            x = int((touch.x - self.x) / self.width * self.image_width)
            y = int((1 - (touch.y - self.y) / self.height) * self.image_height)
            
            # Update PIL mask
            brush_radius = int(self.brush_size * self.image_width / self.width / 2)
            
            if self.eraser_mode:
                # Erase (make transparent)
                for i in range(-brush_radius, brush_radius + 1):
                    for j in range(-brush_radius, brush_radius + 1):
                        if i*i + j*j <= brush_radius*brush_radius:
                            px, py = x + i, y + j
                            if 0 <= px < self.image_width and 0 <= py < self.image_height:
                                self.mask_image.putpixel((px, py), (0, 0, 0, 0))
            else:
                # Draw mask
                self.mask_draw.ellipse(
                    [x - brush_radius, y - brush_radius,
                     x + brush_radius, y + brush_radius],
                    fill=(255, 255, 255, 255)
                )
            
            self.current_stroke.append((touch.x, touch.y))
            return True
            
    def stop_drawing(self, widget, touch):
        if self.drawing:
            self.drawing = False
            if self.current_stroke:
                self.stroke_history.append({
                    'points': self.current_stroke.copy(),
                    'brush_size': self.brush_size,
                    'eraser_mode': self.eraser_mode
                })
            self.current_stroke = []
        
    def clear_mask(self):
        """Clear all mask drawings"""
        self.canvas.clear()
        self.mask_lines = []
        self.stroke_history = []
        self.mask_image = PILImage.new('RGBA', (self.image_width, self.image_height), (0, 0, 0, 0))
        self.mask_draw = ImageDraw.Draw(self.mask_image)
        
    def undo_last_stroke(self):
        """Undo the last stroke"""
        if self.stroke_history:
            self.stroke_history.pop()
            self.redraw_from_history()
            
    def redraw_from_history(self):
        """Redraw mask from stroke history"""
        self.canvas.clear()
        self.mask_lines = []
        self.mask_image = PILImage.new('RGBA', (self.image_width, self.image_height), (0, 0, 0, 0))
        self.mask_draw = ImageDraw.Draw(self.mask_image)
        
        # Replay all strokes
        for stroke in self.stroke_history:
            # Implement stroke replay logic here
            pass
        
    def get_mask_bytes(self):
        """Get mask as PNG bytes for API"""
        # Convert RGBA to grayscale mask
        mask_array = np.array(self.mask_image)
        mask_gray = mask_array[:, :, 3]  # Use alpha channel
        
        # Create PIL image from grayscale
        mask_final = PILImage.fromarray(mask_gray, mode='L')
        
        # Save to bytes
        buffer = io.BytesIO()
        mask_final.save(buffer, format='PNG')
        return buffer.getvalue()
        
    def has_mask(self):
        """Check if any mask has been drawn"""
        return len(self.stroke_history) > 0


class ImageEditorDALLE(MDDialog):
    """DALL-E 2 style image editor with inpainting"""
    
    def __init__(self, image_path, on_complete_callback=None, **kwargs):
        self.image_path = Path(image_path)
        self.on_complete_callback = on_complete_callback
        self.mask_canvas = None
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
        """Create the editor UI"""
        layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            padding=dp(10)
        )
        
        # Toolbar
        toolbar = self._create_toolbar()
        layout.add_widget(toolbar)
        
        # Image with mask overlay container
        image_container = MDBoxLayout(
            size_hint_y=0.6,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        # Background image
        self.image_widget = Image(
            source=str(self.image_path),
            allow_stretch=True,
            keep_ratio=True
        )
        image_container.add_widget(self.image_widget)
        
        # Mask canvas overlay
        self.mask_canvas = MaskCanvas(str(self.image_path))
        image_container.add_widget(self.mask_canvas)
        
        layout.add_widget(image_container)
        
        # Controls
        controls = self._create_controls()
        layout.add_widget(controls)
        
        # Edit prompt
        self.prompt_field = MDTextField(
            hint_text="Describe what to generate in the masked area...",
            multiline=True,
            size_hint_y=None,
            height=dp(80)
        )
        layout.add_widget(self.prompt_field)
        
        # Progress indicator (hidden initially)
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
        
        # Instructions
        instructions = MDLabel(
            text="Draw on the image to select areas to edit • Use eraser to refine • Describe your changes",
            theme_text_color="Secondary",
            font_style="Caption",
            halign="center",
            size_hint_y=None,
            height=dp(30)
        )
        layout.add_widget(instructions)
        
        return layout
        
    def _create_toolbar(self):
        """Create toolbar with title and close button"""
        toolbar = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(56)
        )
        
        toolbar.add_widget(MDLabel(
            text="Edit Image with AI",
            theme_text_color="Primary",
            font_style="H6"
        ))
        
        # Tool buttons
        self.draw_btn = MDIconButton(
            icon="draw",
            theme_text_color="Custom",
            text_color=(1, 0, 0, 1),
            on_release=lambda x: self.set_draw_mode()
        )
        toolbar.add_widget(self.draw_btn)
        
        self.eraser_btn = MDIconButton(
            icon="eraser",
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 0.5, 1),
            on_release=lambda x: self.set_eraser_mode()
        )
        toolbar.add_widget(self.eraser_btn)
        
        undo_btn = MDIconButton(
            icon="undo",
            on_release=lambda x: self.mask_canvas.undo_last_stroke()
        )
        toolbar.add_widget(undo_btn)
        
        clear_btn = MDIconButton(
            icon="delete-sweep",
            on_release=lambda x: self.mask_canvas.clear_mask()
        )
        toolbar.add_widget(clear_btn)
        
        close_btn = MDIconButton(
            icon="close",
            on_release=lambda x: self.dismiss()
        )
        toolbar.add_widget(close_btn)
        
        return toolbar
        
    def set_draw_mode(self):
        """Switch to draw mode"""
        self.mask_canvas.eraser_mode = False
        self.draw_btn.text_color = (1, 0, 0, 1)
        self.eraser_btn.text_color = (0.5, 0.5, 0.5, 1)
        
    def set_eraser_mode(self):
        """Switch to eraser mode"""
        self.mask_canvas.eraser_mode = True
        self.draw_btn.text_color = (0.5, 0.5, 0.5, 1)
        self.eraser_btn.text_color = (0, 0, 1, 1)
        
    def _create_controls(self):
        """Create brush controls"""
        controls = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(10)
        )
        
        # Brush size
        controls.add_widget(MDLabel(
            text="Brush:",
            size_hint_x=0.2
        ))
        
        self.brush_slider = MDSlider(
            min=5,
            max=50,
            value=20,
            size_hint_x=0.6
        )
        self.brush_slider.bind(value=self._on_brush_size_change)
        controls.add_widget(self.brush_slider)
        
        self.brush_label = MDLabel(
            text="20px",
            size_hint_x=0.2
        )
        controls.add_widget(self.brush_label)
        
        return controls
        
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
            text="Generate Edit",
            md_bg_color=(0, 0.7, 0, 1),
            on_release=lambda x: self._generate_edit()
        )
        actions.add_widget(self.generate_btn)
        
        return actions
        
    def _on_brush_size_change(self, slider, value):
        """Update brush size"""
        self.mask_canvas.brush_size = int(value)
        self.brush_label.text = f"{int(value)}px"
        
    def _generate_edit(self):
        """Generate the edit using DALL-E API"""
        if self.processing:
            return
            
        prompt = self.prompt_field.text.strip()
        if not prompt:
            Snackbar(text="Please enter a description").open()
            return
            
        if not self.mask_canvas.has_mask():
            Snackbar(text="Please draw on the image to select areas to edit").open()
            return
            
        from kivymd.app import MDApp
        from kivy.clock import Clock
        
        app = MDApp.get_running_app()
        
        if not hasattr(app, 'worker_manager'):
            Snackbar(text="Worker system not available").open()
            return
            
        # Save mask to temporary file
        temp_dir = Path(app.user_data_dir) / 'temp'
        temp_dir.mkdir(exist_ok=True)
        mask_path = temp_dir / 'edit_mask.png'
        
        mask_bytes = self.mask_canvas.get_mask_bytes()
        with open(mask_path, 'wb') as f:
            f.write(mask_bytes)
            
        self.processing = True
        self.progress.opacity = 1
        self.progress.active = True
        self.generate_btn.disabled = True
        
        Snackbar(text="Generating edit...").open()
        
        # Call API through worker
        from workers.api_request import APIRequest, APIRequestType, WorkerPriority
        
        request = APIRequest(
            request_type=APIRequestType.EDIT_IMAGE,
            prompt=prompt,
            image_path=str(self.image_path),
            mask_path=str(mask_path),
            size="1024x1024",
            model="dall-e-2",
            callback=lambda result: Clock.schedule_once(
                lambda dt: self._on_edit_complete(result), 0
            )
        )
        
        app.worker_manager.api_worker.add_task(request, WorkerPriority.HIGH)
        
    def _on_edit_complete(self, result):
        """Handle edit completion"""
        self.processing = False
        self.progress.opacity = 0
        self.progress.active = False
        self.generate_btn.disabled = False
        
        if result.get('success'):
            # Download and save the edited image
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
                    filename = f"edited_{timestamp}.png"
                    save_path = Path(app.user_data_dir) / 'gallery' / filename
                    save_path.parent.mkdir(exist_ok=True)
                    
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                        
                    Snackbar(text=f"Edit saved as {filename}").open()
                    
                    # Call completion callback if provided
                    if self.on_complete_callback:
                        self.on_complete_callback(str(save_path))
                        
                    self.dismiss()
                    
                    # Refresh gallery if possible
                    if hasattr(app.root, 'current_screen'):
                        current = app.root.current_screen
                        if hasattr(current, 'refresh_gallery'):
                            current.refresh_gallery()
        else:
            error = result.get('error', 'Unknown error')
            Snackbar(text=f"Edit failed: {error}").open()
            
    def _on_keyboard(self, window, key, scancode, codepoint, modifier):
        if key == 27:  # ESC
            self.dismiss()
            return True
        return False
        
    def on_dismiss(self):
        Window.unbind(on_keyboard=self._on_keyboard)
        
        # Clean up temp mask file
        temp_mask = Path(MDApp.get_running_app().user_data_dir) / 'temp' / 'edit_mask.png'
        if temp_mask.exists():
            try:
                os.remove(temp_mask)
            except:
                pass