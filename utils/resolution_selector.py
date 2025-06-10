"""
Resolution selector component for DALL-E 2 image generation
Supports multiple sizes: 256x256, 512x512, 1024x1024
"""

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivy.metrics import dp
from kivy.properties import StringProperty, ObjectProperty


class ResolutionSelector(MDCard):
    """Resolution selector widget for DALL-E image generation"""
    
    selected_size = StringProperty("1024x1024")
    on_size_change = ObjectProperty(None)
    
    # DALL-E 2 supported sizes
    SIZES = {
        "256x256": {"label": "256×256", "cost": "$", "desc": "Quick & Cheap"},
        "512x512": {"label": "512×512", "cost": "$$", "desc": "Balanced"},
        "1024x1024": {"label": "1024×1024", "cost": "$$$", "desc": "High Quality"}
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(5)
        self.size_hint_y = None
        self.height = dp(140)
        self.elevation = 3
        
        self.size_buttons = {}
        self._create_ui()
    
    def _create_ui(self):
        """Create the resolution selector UI"""
        # Title
        title_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(30)
        )
        
        title_box.add_widget(MDLabel(
            text="Image Size",
            theme_text_color="Primary",
            font_style="Subtitle1"
        ))
        
        cost_label = MDLabel(
            text="Cost indicator",
            theme_text_color="Secondary",
            font_style="Caption",
            halign="right"
        )
        title_box.add_widget(cost_label)
        
        self.add_widget(title_box)
        
        # Size buttons
        button_box = MDBoxLayout(
            orientation='horizontal',
            spacing=dp(10),
            size_hint_y=None,
            height=dp(80)
        )
        
        for size, info in self.SIZES.items():
            # Create button container
            btn_container = MDBoxLayout(
                orientation='vertical',
                size_hint_x=1
            )
            
            # Size button
            btn = MDRaisedButton(
                text=info['label'],
                on_release=lambda x, s=size: self._select_size(s)
            )
            
            # Set default selection
            if size == self.selected_size:
                btn.md_bg_color = (0.5, 0.5, 1, 0.8)
            else:
                btn.md_bg_color = (0.5, 0.5, 0.5, 0.3)
            
            btn_container.add_widget(btn)
            self.size_buttons[size] = btn
            
            # Cost indicator
            cost_label = MDLabel(
                text=f"{info['cost']} {info['desc']}",
                theme_text_color="Secondary",
                font_style="Caption",
                halign="center",
                size_hint_y=None,
                height=dp(20)
            )
            btn_container.add_widget(cost_label)
            
            button_box.add_widget(btn_container)
        
        self.add_widget(button_box)
        
        # Info text
        self.info_label = MDLabel(
            text=self._get_size_info(self.selected_size),
            theme_text_color="Secondary",
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
            halign="center"
        )
        self.add_widget(self.info_label)
    
    def _select_size(self, size):
        """Handle size selection"""
        if size == self.selected_size:
            return
        
        # Update button appearances
        for s, btn in self.size_buttons.items():
            if s == size:
                btn.md_bg_color = (0.5, 0.5, 1, 0.8)
            else:
                btn.md_bg_color = (0.5, 0.5, 0.5, 0.3)
        
        self.selected_size = size
        self.info_label.text = self._get_size_info(size)
        
        # Call callback if provided
        if self.on_size_change:
            self.on_size_change(size)
    
    def _get_size_info(self, size):
        """Get informational text for selected size"""
        if size == "256x256":
            return "Fast generation • Lower cost • Good for testing"
        elif size == "512x512":
            return "Good quality • Moderate cost • Recommended"
        else:  # 1024x1024
            return "Best quality • Higher cost • Professional results"
    
    def get_selected_size(self):
        """Get the currently selected size"""
        return self.selected_size
    
    def set_size(self, size):
        """Programmatically set the size"""
        if size in self.SIZES:
            self._select_size(size)


class CompactResolutionSelector(MDBoxLayout):
    """Compact horizontal resolution selector"""
    
    selected_size = StringProperty("1024x1024")
    on_size_change = ObjectProperty(None)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.spacing = dp(5)
        self.size_hint_y = None
        self.height = dp(40)
        
        self._create_ui()
    
    def _create_ui(self):
        """Create compact UI"""
        # Label
        self.add_widget(MDLabel(
            text="Size:",
            size_hint_x=None,
            width=dp(40)
        ))
        
        # Size buttons
        self.size_buttons = {}
        sizes = ["256", "512", "1024"]
        
        for size in sizes:
            full_size = f"{size}x{size}"
            btn = MDFlatButton(
                text=size,
                on_release=lambda x, s=full_size: self._select_size(s)
            )
            
            if full_size == self.selected_size:
                btn.md_bg_color = (0.5, 0.5, 1, 0.3)
            
            self.add_widget(btn)
            self.size_buttons[full_size] = btn
    
    def _select_size(self, size):
        """Handle size selection"""
        if size == self.selected_size:
            return
        
        # Update buttons
        for s, btn in self.size_buttons.items():
            if s == size:
                btn.md_bg_color = (0.5, 0.5, 1, 0.3)
            else:
                btn.md_bg_color = (0, 0, 0, 0)
        
        self.selected_size = size
        
        if self.on_size_change:
            self.on_size_change(size)