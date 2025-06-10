"""
Enhanced UI Components with animations, progress indicators, and better UX
"""

from kivy.uix.progressbar import ProgressBar
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.properties import NumericProperty, StringProperty
from typing import Optional, Callable

class AnimatedProgressBar(ProgressBar):
    """Progress bar with smooth animations"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.animation_duration = 0.3
        
    def set_progress(self, value: float, animate: bool = True):
        """Set progress with optional animation"""
        if animate:
            anim = Animation(value=value, duration=self.animation_duration)
            anim.start(self)
        else:
            self.value = value

class LoadingModal(ModalView):
    """Beautiful loading modal with progress tracking"""
    
    def __init__(self, title: str = "Processing...", **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.8, 0.3)
        self.auto_dismiss = False
        
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Title
        self.title_label = Label(
            text=title,
            size_hint_y=0.3,
            font_size='20sp'
        )
        layout.add_widget(self.title_label)
        
        # Progress bar
        self.progress_bar = AnimatedProgressBar(
            max=100,
            value=0,
            size_hint_y=0.2
        )
        layout.add_widget(self.progress_bar)
        
        # Status label
        self.status_label = Label(
            text="Initializing...",
            size_hint_y=0.3,
            font_size='16sp'
        )
        layout.add_widget(self.status_label)
        
        # Step counter
        self.step_label = Label(
            text="Step 0 of 0",
            size_hint_y=0.2,
            font_size='14sp'
        )
        layout.add_widget(self.step_label)
        
        self.add_widget(layout)
        
    def update_progress(self, value: float, status: str = "", 
                       current_step: int = 0, total_steps: int = 0):
        """Update loading modal progress"""
        self.progress_bar.set_progress(value)
        
        if status:
            self.status_label.text = status
        
        if total_steps > 0:
            self.step_label.text = f"Step {current_step} of {total_steps}"

class ErrorRecoveryDialog(ModalView):
    """User-friendly error recovery dialog"""
    
    def __init__(self, error_message: str, retry_callback: Optional[Callable] = None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9, 0.4)
        self.retry_callback = retry_callback
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Error icon and title
        title_layout = BoxLayout(size_hint_y=0.2)
        title_label = Label(
            text="⚠️ Oops! Something went wrong",
            font_size='22sp',
            bold=True
        )
        title_layout.add_widget(title_label)
        layout.add_widget(title_layout)
        
        # Error message
        error_label = Label(
            text=error_message,
            size_hint_y=0.4,
            font_size='16sp',
            text_size=(self.width * 0.8, None),
            halign='center'
        )
        layout.add_widget(error_label)
        
        # Buttons
        button_layout = BoxLayout(size_hint_y=0.3, spacing=10)
        
        # Retry button
        from kivy.uix.button import Button
        retry_btn = Button(
            text="🔄 Try Again",
            size_hint_x=0.5,
            font_size='18sp'
        )
        retry_btn.bind(on_press=self._on_retry)
        button_layout.add_widget(retry_btn)
        
        # Cancel button
        cancel_btn = Button(
            text="✖ Cancel",
            size_hint_x=0.5,
            font_size='18sp'
        )
        cancel_btn.bind(on_press=self.dismiss)
        button_layout.add_widget(cancel_btn)
        
        layout.add_widget(button_layout)
        self.add_widget(layout)
    
    def _on_retry(self, instance):
        """Handle retry button press"""
        self.dismiss()
        if self.retry_callback:
            self.retry_callback()

class OfflineModeIndicator(BoxLayout):
    """Indicator for offline mode status"""
    
    is_offline = NumericProperty(False)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint = (None, None)
        self.size = (200, 40)
        self.padding = 10
        
        # Status icon
        self.icon_label = Label(
            text="📡",
            size_hint_x=0.3,
            font_size='20sp'
        )
        self.add_widget(self.icon_label)
        
        # Status text
        self.status_label = Label(
            text="Online",
            size_hint_x=0.7,
            font_size='16sp',
            color=(0, 1, 0, 1)  # Green
        )
        self.add_widget(self.status_label)
        
        # Bind to offline property
        self.bind(is_offline=self._update_status)
        
        # Pulse animation for offline mode
        self.pulse_animation = None
        
    def _update_status(self, instance, value):
        """Update UI based on offline status"""
        if value:
            self.icon_label.text = "📵"
            self.status_label.text = "Offline Mode"
            self.status_label.color = (1, 0.5, 0, 1)  # Orange
            
            # Start pulse animation
            self.pulse_animation = Animation(opacity=0.5, duration=1) + \
                                 Animation(opacity=1, duration=1)
            self.pulse_animation.repeat = True
            self.pulse_animation.start(self.status_label)
        else:
            self.icon_label.text = "📡"
            self.status_label.text = "Online"
            self.status_label.color = (0, 1, 0, 1)  # Green
            
            # Stop pulse animation
            if self.pulse_animation:
                self.pulse_animation.stop(self.status_label)
                self.status_label.opacity = 1

class ImagePreviewCarousel(BoxLayout):
    """Carousel for previewing generated images with swipe gestures"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from kivy.uix.carousel import Carousel
        
        self.carousel = Carousel(direction='right')
        self.add_widget(self.carousel)
        
        # Add navigation buttons
        self._add_navigation_buttons()
        
    def add_image(self, image_path: str, metadata: dict):
        """Add image to carousel with metadata"""
        from kivy.uix.image import Image
        from kivy.uix.floatlayout import FloatLayout
        
        # Create slide layout
        slide = FloatLayout()
        
        # Add image
        img = Image(source=image_path, allow_stretch=True, keep_ratio=True)
        slide.add_widget(img)
        
        # Add metadata overlay
        metadata_label = Label(
            text=f"Prompt: {metadata.get('prompt', 'Unknown')[:50]}...",
            size_hint=(1, 0.1),
            pos_hint={'x': 0, 'y': 0},
            font_size='14sp',
            color=(1, 1, 1, 0.8)
        )
        slide.add_widget(metadata_label)
        
        self.carousel.add_widget(slide)
    
    def _add_navigation_buttons(self):
        """Add previous/next navigation buttons"""
        from kivy.uix.button import Button
        
        # Previous button
        prev_btn = Button(
            text="◀",
            size_hint=(0.1, 1),
            pos_hint={'x': 0, 'center_y': 0.5},
            font_size='30sp',
            background_color=(0, 0, 0, 0.5)
        )
        prev_btn.bind(on_press=lambda x: self.carousel.load_previous())
        
        # Next button
        next_btn = Button(
            text="▶",
            size_hint=(0.1, 1),
            pos_hint={'right': 1, 'center_y': 0.5},
            font_size='30sp',
            background_color=(0, 0, 0, 0.5)
        )
        next_btn.bind(on_press=lambda x: self.carousel.load_next())
