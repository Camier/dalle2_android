"""
DALL-E enhanced image viewer with AI features
Supports image variations and future inpainting/outpainting
"""

from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDIconButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox
from kivy.uix.scatter import Scatter
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.core.window import Window
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.gridlayout import MDGridLayout
from pathlib import Path
import os
from typing import Optional, Callable, List
from kivy.clock import Clock

from utils.android_utils import share_image


class ImageViewerDALLE(MDDialog):
    """DALL-E enhanced image viewer with AI features"""
    
    def __init__(self, image_path, on_delete_callback=None, **kwargs):
        self.image_path = Path(image_path)
        self.on_delete_callback = on_delete_callback
        self.processing = False
        self.variation_paths: List[Path] = []
        
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
    
    def _create_content(self):
        """Create the viewer content with DALL-E features"""
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
        ai_btn = MDIconButton(
            icon="creation",
            theme_text_color="Custom",
            text_color=(0.5, 0.5, 1, 1),
            on_release=lambda x: self._toggle_ai_panel()
        )
        toolbar.add_widget(ai_btn)
        
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
        
        # AI panel (initially hidden)
        ai_panel = self._create_ai_panel()
        ai_panel.opacity = 0
        ai_panel.disabled = True
        layout.add_widget(ai_panel)
        self.ai_panel = ai_panel
        
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
            text="Pinch to zoom • Double tap to reset • Tap AI icon for DALL-E features",
            theme_text_color="Secondary",
            font_style="Caption",
            halign="center",
            size_hint_y=None,
            height=dp(30)
        )
        layout.add_widget(instructions)
        
        return layout
    
    def _create_ai_panel(self):
        """Create the DALL-E AI features panel"""
        panel = MDCard(
            orientation='vertical',
            padding=dp(15),
            spacing=dp(10),
            size_hint_y=None,
            height=dp(320),
            elevation=5
        )
        
        # Panel title
        panel.add_widget(MDLabel(
            text="DALL-E AI Features",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height=dp(30)
        ))
        
        # Variations section
        variations_label = MDLabel(
            text="Image Variations",
            theme_text_color="Primary",
            font_style="Subtitle2",
            size_hint_y=None,
            height=dp(25)
        )
        panel.add_widget(variations_label)
        
        variations_desc = MDLabel(
            text="Generate AI variations of this image",
            theme_text_color="Secondary",
            font_style="Caption",
            size_hint_y=None,
            height=dp(20)
        )
        panel.add_widget(variations_desc)
        
        # Variations options
        var_options = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40),
            spacing=dp(10)
        )
        
        var_count_label = MDLabel(
            text="Count:",
            size_hint_x=None,
            width=dp(50)
        )
        var_options.add_widget(var_count_label)
        
        # Count selector (1-4 variations)
        count_box = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(5)
        )
        
        self.variation_count_btns = []
        for i in range(1, 5):
            btn = MDFlatButton(
                text=str(i),
                on_release=lambda x, count=i: self._set_variation_count(count)
            )
            if i == 2:  # Default to 2 variations
                btn.md_bg_color = (0.5, 0.5, 1, 0.3)
            count_box.add_widget(btn)
            self.variation_count_btns.append(btn)
        
        var_options.add_widget(count_box)
        panel.add_widget(var_options)
        
        self.selected_count = 2  # Default
        
        # Generate variations button
        generate_var_btn = MDRaisedButton(
            text="Generate Variations",
            pos_hint={'center_x': 0.5},
            on_release=lambda x: self._generate_variations()
        )
        panel.add_widget(generate_var_btn)
        
        # Divider
        panel.add_widget(MDLabel(
            text="",
            size_hint_y=None,
            height=dp(10)
        ))
        
        # Inpainting section
        inpainting_label = MDLabel(
            text="AI Image Editing",
            theme_text_color="Primary",
            font_style="Subtitle2",
            size_hint_y=None,
            height=dp(25)
        )
        panel.add_widget(inpainting_label)
        
        # Inpainting button
        inpainting_btn = MDRaisedButton(
            text="Edit with AI (Inpainting)",
            pos_hint={'center_x': 0.5},
            md_bg_color=(0.7, 0, 0.7, 1),
            on_release=lambda x: self._open_inpainting_editor()
        )
        panel.add_widget(inpainting_btn)
        
        # Coming soon features
        coming_soon_box = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(40),
            padding=[dp(10), 0, 0, 0]
        )
        
        coming_soon_desc = MDLabel(
            text="Coming Soon:\n• Outpainting: Extend image beyond borders",
            theme_text_color="Secondary",
            font_style="Caption"
        )
        coming_soon_box.add_widget(coming_soon_desc)
        
        panel.add_widget(coming_soon_box)
        
        # Results preview area (for variations)
        self.results_preview = MDGridLayout(
            cols=2,
            spacing=dp(5),
            size_hint_y=None,
            height=dp(100),
            opacity=0
        )
        panel.add_widget(self.results_preview)
        
        return panel
    
    def _toggle_ai_panel(self):
        """Toggle the AI features panel visibility"""
        if self.ai_panel.opacity == 0:
            self.ai_panel.opacity = 1
            self.ai_panel.disabled = False
        else:
            self.ai_panel.opacity = 0
            self.ai_panel.disabled = True
    
    def _set_variation_count(self, count):
        """Set the number of variations to generate"""
        self.selected_count = count
        # Update button colors
        for i, btn in enumerate(self.variation_count_btns):
            if i + 1 == count:
                btn.md_bg_color = (0.5, 0.5, 1, 0.3)
            else:
                btn.md_bg_color = (0, 0, 0, 0)
    
    def _generate_variations(self):
        """Generate image variations using DALL-E API"""
        if self.processing:
            Snackbar(text="Already processing...").open()
            return
        
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        
        if not hasattr(app, 'worker_manager'):
            Snackbar(text="Worker system not available").open()
            return
        
        # Show progress
        self.processing = True
        self.progress.opacity = 1
        self.progress.active = True
        Snackbar(text=f"Generating {self.selected_count} variations...").open()
        
        def on_variations_complete(result):
            """Handle variations completion on main thread"""
            def update_ui(dt):
                self.processing = False
                self.progress.opacity = 0
                self.progress.active = False
                
                if result.get('success'):
                    variations = result.get('variations', [])
                    if variations:
                        self.variation_paths = [Path(v) for v in variations]
                        self._show_variations_preview()
                        Snackbar(text=f"Generated {len(variations)} variations!").open()
                    else:
                        Snackbar(text="No variations generated").open()
                else:
                    error = result.get('error', 'Unknown error')
                    Snackbar(text=f"Error: {error}").open()
            
            Clock.schedule_once(update_ui, 0)
        
        # Request variations through worker
        app.worker_manager.generate_image_variations(
            image_path=str(self.image_path),
            count=self.selected_count,
            callback=on_variations_complete
        )
    
    def _show_variations_preview(self):
        """Show preview of generated variations"""
        self.results_preview.clear_widgets()
        self.results_preview.opacity = 1
        
        for i, var_path in enumerate(self.variation_paths[:4]):  # Show max 4 previews
            if var_path.exists():
                # Create clickable preview
                preview_btn = MDIconButton(
                    size_hint=(None, None),
                    size=(dp(48), dp(48))
                )
                
                preview_img = Image(
                    source=str(var_path),
                    allow_stretch=True,
                    keep_ratio=True
                )
                preview_btn.add_widget(preview_img)
                
                # Open variation in new viewer on click
                preview_btn.bind(
                    on_release=lambda x, path=var_path: self._open_variation(path)
                )
                
                self.results_preview.add_widget(preview_btn)
    
    def _open_variation(self, var_path):
        """Open a variation in a new viewer"""
        # Create new viewer for the variation
        viewer = ImageViewerDALLE(
            image_path=var_path,
            on_delete_callback=self.on_delete_callback
        )
        viewer.open()
    
    def _open_inpainting_editor(self):
        """Open the inpainting editor for this image"""
        from utils.image_editor_dalle import ImageEditorDALLE
        
        # Close this viewer first
        self.dismiss()
        
        # Open the editor
        editor = ImageEditorDALLE(
            image_path=self.image_path,
            on_complete_callback=self._on_edit_complete
        )
        editor.open()
    
    def _on_edit_complete(self, edited_image_path):
        """Handle completion of image editing"""
        # Refresh gallery if callback exists
        if self.on_delete_callback:
            self.on_delete_callback()
    
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
        """Share the current image"""
        try:
            success = share_image(str(self.image_path), "Check out this DALL-E image!")
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
            
            # Also delete any variations in the same directory
            for var_path in self.variation_paths:
                if var_path.exists():
                    try:
                        os.remove(var_path)
                    except:
                        pass
            
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