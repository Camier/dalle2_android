#!/usr/bin/env python
"""
DALL-E 2 Android App
Main entry point for the Kivy application
"""

from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.utils import platform
from screens.main_screen import MainScreen

if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.INTERNET, Permission.WRITE_EXTERNAL_STORAGE])

class DalleApp(MDApp):
    def build(self):
        self.title = 'DALL-E Image Generator'
        self.icon = 'assets/icon.png'
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "600"
        self.theme_cls.theme_style = "Light"
        
        # Set window size for desktop testing
        if platform != 'android':
            Window.size = (400, 700)
        
        # Create screen manager
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        
        return sm

if __name__ == '__main__':
    DalleApp().run()