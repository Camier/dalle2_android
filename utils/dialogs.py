"""
Custom dialogs for the app
"""

from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivy.metrics import dp


class ConfirmDialog(MDDialog):
    """Confirmation dialog with customizable actions"""
    
    def __init__(self, title="Confirm", text="Are you sure?", 
                 on_confirm=None, on_cancel=None,
                 confirm_text="Confirm", cancel_text="Cancel",
                 confirm_color=None, **kwargs):
        
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        
        # Default confirm color is error color for destructive actions
        if confirm_color is None:
            confirm_color = (1, 0, 0, 1)  # Red
        
        # Create buttons
        buttons = [
            MDFlatButton(
                text=cancel_text,
                on_release=self._handle_cancel
            ),
            MDRaisedButton(
                text=confirm_text,
                md_bg_color=confirm_color,
                on_release=self._handle_confirm
            ),
        ]
        
        super().__init__(
            title=title,
            text=text,
            buttons=buttons,
            **kwargs
        )
    
    def _handle_confirm(self, *args):
        """Handle confirm button press"""
        self.dismiss()
        if self.on_confirm:
            self.on_confirm()
    
    def _handle_cancel(self, *args):
        """Handle cancel button press"""
        self.dismiss()
        if self.on_cancel:
            self.on_cancel()


class InfoDialog(MDDialog):
    """Information dialog with single OK button"""
    
    def __init__(self, title="Info", text="", button_text="OK", **kwargs):
        buttons = [
            MDRaisedButton(
                text=button_text,
                on_release=lambda x: self.dismiss()
            ),
        ]
        
        super().__init__(
            title=title,
            text=text,
            buttons=buttons,
            **kwargs
        )


class LoadingDialog(MDDialog):
    """Loading dialog with spinner"""
    
    def __init__(self, title="Loading", text="Please wait...", **kwargs):
        # Create content with spinner
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(20),
            size_hint_y=None,
            height=dp(120)
        )
        
        # Add loading spinner
        from kivymd.uix.spinner import MDSpinner
        spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(46), dp(46)),
            pos_hint={'center_x': 0.5},
            active=True
        )
        content.add_widget(spinner)
        
        # Add text
        label = MDLabel(
            text=text,
            theme_text_color="Secondary",
            halign="center"
        )
        content.add_widget(label)
        
        super().__init__(
            title=title,
            type="custom",
            content_cls=content,
            auto_dismiss=False,
            **kwargs
        )
