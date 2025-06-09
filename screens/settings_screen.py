"""
Settings screen for app configuration
"""

from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.menu import MDDropdownMenu
from kivymd.app import MDApp
import os

from utils.storage import SecureStorage

# Load KV file
Builder.load_file(os.path.join(os.path.dirname(__file__), '../ui/settings_screen.kv'))


class SettingsScreen(Screen):
    """Settings screen"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = SecureStorage()
        self.size_options = ['256x256', '512x512', '1024x1024']
        self.current_size = '512x512'  # Default to 512x512 for faster generation
    
    def on_enter(self):
        """Called when screen is entered"""
        # Load current API key (masked)
        api_key = self.storage.get_api_key()
        if api_key:
            self.ids.api_key_input.text = '*' * 20
    
    def save_api_key(self):
        """Save new API key"""
        api_key = self.ids.api_key_input.text.strip()
        
        # Only save if it's not the masked version
        if api_key and not api_key.startswith('*'):
            self.storage.save_api_key(api_key)
            MDApp.get_running_app().main_screen.api_service.set_api_key(api_key)
            Snackbar(text="API Key saved successfully!").open()
            self.ids.api_key_input.text = '*' * 20
    
    def show_size_menu(self):
        """Show image size selection menu"""
        menu_items = [
            {
                "text": size,
                "on_release": lambda x=size: self.set_image_size(x),
            }
            for size in self.size_options
        ]
        
        self.menu = MDDropdownMenu(
            caller=self.ids.size_dropdown,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()
    
    def set_image_size(self, size):
        """Set selected image size"""
        self.current_size = size
        self.ids.size_dropdown.text = size
        self.menu.dismiss()
        
        # Save size preference
        self._save_size_preference(size)
        Snackbar(text=f"Default size set to {size}").open()
    
    def get_image_size(self):
        """Get current image size setting"""
        # Try to load saved preference
        size = self._load_size_preference()
        if size and size in self.size_options:
            self.current_size = size
        return self.current_size
    
    def is_auto_save_enabled(self):
        """Check if auto-save is enabled"""
        return self.ids.auto_save_switch.active
    
    def _save_size_preference(self, size):
        """Save size preference to storage"""
        try:
            # Use a simple file for now (can be enhanced later)
            import json
            import os
            
            prefs_file = os.path.join(self.storage.storage_dir, '.preferences')
            prefs = {}
            
            if os.path.exists(prefs_file):
                with open(prefs_file, 'r') as f:
                    prefs = json.load(f)
            
            prefs['image_size'] = size
            
            with open(prefs_file, 'w') as f:
                json.dump(prefs, f)
        except Exception as e:
            print(f"Error saving size preference: {e}")
    
    def _load_size_preference(self):
        """Load size preference from storage"""
        try:
            import json
            import os
            
            prefs_file = os.path.join(self.storage.storage_dir, '.preferences')
            
            if os.path.exists(prefs_file):
                with open(prefs_file, 'r') as f:
                    prefs = json.load(f)
                    return prefs.get('image_size')
        except Exception as e:
            print(f"Error loading size preference: {e}")
        
        return None
    
    def show_color_menu(self):
        """Show color palette selection menu"""
        colors = ['Blue', 'Red', 'Green', 'Purple', 'Orange', 'Teal', 'Pink']
        menu_items = [
            {
                "text": color,
                "on_release": lambda x=color: self.set_primary_color(x),
            }
            for color in colors
        ]
        
        self.color_menu = MDDropdownMenu(
            caller=self.ids.get('color_button', None) or self.ids.size_dropdown,
            items=menu_items,
            width_mult=4,
        )
        self.color_menu.open()
    
    def set_primary_color(self, color):
        """Set primary color theme"""
        app = MDApp.get_running_app()
        app.theme_cls.primary_palette = color
        self.color_menu.dismiss()
        Snackbar(text=f"Primary color set to {color}").open()
