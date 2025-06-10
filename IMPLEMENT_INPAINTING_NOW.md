# Implement Inpainting Feature - Quick Start Guide

## Overview
The API support for image editing (inpainting) already exists in `workers/api_request.py`. We just need to build the UI and connect it.

## Step 1: Create Mask Drawing UI

Create `utils/image_editor_dalle.py`:

```python
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
from kivy.graphics import Line, Color, Rectangle
from kivy.uix.image import Image
from kivy.core.window import Window
from kivymd.uix.snackbar import Snackbar
from kivy.metrics import dp
from PIL import Image as PILImage, ImageDraw
import io
import os
from pathlib import Path

class MaskCanvas(Widget):
    """Canvas for drawing masks"""
    
    def __init__(self, image_path, **kwargs):
        super().__init__(**kwargs)
        self.image_path = image_path
        self.mask_lines = []
        self.brush_size = 20
        self.drawing = False
        
        # Create transparent mask
        img = PILImage.open(image_path)
        self.mask_image = PILImage.new('RGBA', img.size, (0, 0, 0, 0))
        self.mask_draw = ImageDraw.Draw(self.mask_image)
        
        # Bind touch events
        self.bind(on_touch_down=self.start_drawing)
        self.bind(on_touch_move=self.draw_line)
        self.bind(on_touch_up=self.stop_drawing)
        
    def start_drawing(self, widget, touch):
        if self.collide_point(*touch.pos):
            self.drawing = True
            with self.canvas:
                Color(1, 0, 0, 0.5)  # Red mask color
                touch.ud['line'] = Line(
                    points=[touch.x, touch.y],
                    width=self.brush_size
                )
            self.mask_lines.append(touch.ud['line'])
            return True
            
    def draw_line(self, widget, touch):
        if self.drawing and 'line' in touch.ud:
            touch.ud['line'].points += [touch.x, touch.y]
            
            # Update PIL mask
            x = int(touch.x - self.x)
            y = int(self.height - (touch.y - self.y))
            self.mask_draw.ellipse(
                [x - self.brush_size//2, y - self.brush_size//2,
                 x + self.brush_size//2, y + self.brush_size//2],
                fill=(255, 255, 255, 255)
            )
            return True
            
    def stop_drawing(self, widget, touch):
        self.drawing = False
        
    def clear_mask(self):
        self.canvas.clear()
        self.mask_lines = []
        self.mask_image = PILImage.new('RGBA', self.mask_image.size, (0, 0, 0, 0))
        self.mask_draw = ImageDraw.Draw(self.mask_image)
        
    def get_mask_bytes(self):
        """Get mask as PNG bytes"""
        # Convert to grayscale
        mask_gray = self.mask_image.convert('L')
        buffer = io.BytesIO()
        mask_gray.save(buffer, format='PNG')
        return buffer.getvalue()


class ImageEditorDALLE(MDDialog):
    """DALL-E 2 style image editor with inpainting"""
    
    def __init__(self, image_path, **kwargs):
        self.image_path = Path(image_path)
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
        
        # Image with mask overlay
        image_container = MDBoxLayout(size_hint_y=0.6)
        
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
        
        # Action buttons
        actions = self._create_actions()
        layout.add_widget(actions)
        
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
        
        close_btn = MDIconButton(
            icon="close",
            on_release=lambda x: self.dismiss()
        )
        toolbar.add_widget(close_btn)
        
        return toolbar
        
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
            text="Brush Size:",
            size_hint_x=0.3
        ))
        
        self.brush_slider = MDSlider(
            min=5,
            max=50,
            value=20,
            size_hint_x=0.5
        )
        self.brush_slider.bind(value=self._on_brush_size_change)
        controls.add_widget(self.brush_slider)
        
        # Clear button
        clear_btn = MDIconButton(
            icon="eraser",
            on_release=lambda x: self.mask_canvas.clear_mask()
        )
        controls.add_widget(clear_btn)
        
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
        
        generate_btn = MDRaisedButton(
            text="Generate Edit",
            md_bg_color=(0, 0.7, 0, 1),
            on_release=lambda x: self._generate_edit()
        )
        actions.add_widget(generate_btn)
        
        return actions
        
    def _on_brush_size_change(self, slider, value):
        """Update brush size"""
        self.mask_canvas.brush_size = int(value)
        
    def _generate_edit(self):
        """Generate the edit using DALL-E API"""
        if self.processing:
            return
            
        prompt = self.prompt_field.text.strip()
        if not prompt:
            Snackbar(text="Please enter a description").open()
            return
            
        from kivymd.app import MDApp
        from kivy.clock import Clock
        
        app = MDApp.get_running_app()
        
        if not hasattr(app, 'worker_manager'):
            Snackbar(text="Worker system not available").open()
            return
            
        # Save mask to temporary file
        mask_path = app.user_data_dir / 'temp' / 'edit_mask.png'
        mask_path.parent.mkdir(exist_ok=True)
        
        mask_bytes = self.mask_canvas.get_mask_bytes()
        with open(mask_path, 'wb') as f:
            f.write(mask_bytes)
            
        self.processing = True
        Snackbar(text="Generating edit...").open()
        
        # Call API through worker
        from workers.api_request import APIRequest, APIRequestType
        
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
        
        app.worker_manager.api_worker.add_task(request)
        
    def _on_edit_complete(self, result):
        """Handle edit completion"""
        self.processing = False
        
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
                    self.dismiss()
                    
                    # Refresh gallery if possible
                    if hasattr(app.root, 'refresh_gallery'):
                        app.root.refresh_gallery()
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
```

## Step 2: Update Gallery Screen

Modify `screens/gallery_screen.py` to add edit option:

```python
# In GalleryScreen class, update _open_image method:

def _open_image(self, image_path):
    """Open image with editing options"""
    from utils.dialogs import MDListBottomSheet
    
    bottom_sheet = MDListBottomSheet()
    bottom_sheet.add_item(
        "View Full Screen",
        lambda x: self._view_fullscreen(image_path),
        icon="fullscreen"
    )
    bottom_sheet.add_item(
        "Edit with AI (Inpainting)",
        lambda x: self._edit_image(image_path),
        icon="brush"
    )
    bottom_sheet.add_item(
        "Generate Variations",
        lambda x: self._generate_variations(image_path),
        icon="content-copy"
    )
    bottom_sheet.add_item(
        "Share",
        lambda x: self._share_image(image_path),
        icon="share"
    )
    bottom_sheet.add_item(
        "Delete",
        lambda x: self._delete_image(image_path),
        icon="delete"
    )
    bottom_sheet.open()
    
def _edit_image(self, image_path):
    """Open image editor"""
    from utils.image_editor_dalle import ImageEditorDALLE
    
    editor = ImageEditorDALLE(image_path)
    editor.open()
```

## Step 3: Add to Requirements

Update `requirements.txt`:
```txt
# Add for mask processing
opencv-python==4.8.1.78
numpy==1.24.3
```

## Step 4: Test the Feature

Create `test_inpainting.py`:

```python
import os
from pathlib import Path
from kivymd.app import MDApp
from utils.image_editor_dalle import ImageEditorDALLE

def test_inpainting():
    """Test inpainting feature"""
    
    # Use a test image
    test_image = Path("test_image.png")
    
    if not test_image.exists():
        print("Please provide a test_image.png")
        return
        
    # Create mock app
    class TestApp(MDApp):
        def __init__(self):
            super().__init__()
            self.user_data_dir = Path("./test_data")
            self.user_data_dir.mkdir(exist_ok=True)
            
    app = TestApp()
    
    # Open editor
    editor = ImageEditorDALLE(str(test_image))
    editor.open()
    
    # Run app
    app.run()

if __name__ == "__main__":
    test_inpainting()
```

## Quick Implementation Checklist

- [ ] Create `utils/image_editor_dalle.py` with mask drawing UI
- [ ] Update `screens/gallery_screen.py` to add edit option
- [ ] Add opencv-python to requirements.txt
- [ ] Test mask drawing functionality
- [ ] Test API integration with worker
- [ ] Add to main app imports
- [ ] Build and test APK

## Next Features After Inpainting

1. **Outpainting** - Similar UI but extends canvas
2. **Size Selection** - Add dropdown for 256x256, 512x512
3. **Mask Presets** - Quick selection tools

This implementation reuses the existing worker system and API support, requiring only UI additions!