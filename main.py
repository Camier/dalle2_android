#!/usr/bin/env python3
"""
DALL-E 2 Complete Android App
Features: Text-to-Image, Variations, Inpainting, Outpainting, Multi-Resolution
"""

import os
import sys
from pathlib import Path

# Android imports
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    ANDROID = True
except:
    ANDROID = False

# Kivy configuration
from kivy.config import Config
if not ANDROID:
    Config.set('graphics', 'width', '400')
    Config.set('graphics', 'height', '800')

# Main imports
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.utils import platform
from kivymd.uix.snackbar import Snackbar

# Import screens
from screens.main_screen import MainScreen
from screens.gallery_screen import GalleryScreen
from screens.history_screen import HistoryScreen
from screens.settings_screen import SettingsScreen

# Import services
from services.dalle_api import DalleAPIService
from utils.storage import SecureStorage

# Import workers
from workers import WorkerManager


class DALLE2CompleteApp(MDApp):
    """DALL-E 2 Complete - All features in your pocket"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "DALL-E 2 Complete"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.primary_hue = "500"
        self.theme_cls.theme_style = "Dark"
        
        # Services
        self.dalle_service = DalleAPIService()
        self.storage = SecureStorage()
        self.worker_manager = None
        
        # Data directory
        if ANDROID:
            from android.storage import app_storage_path
            self.data_dir = app_storage_path()
        else:
            self.data_dir = Path.home() / '.dalle2complete'
        
        self.data_dir = Path(self.data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
    def build(self):
        """Build the app UI"""
        # Initialize worker manager
        api_key = self.storage.get_api_key()
        self.worker_manager = WorkerManager(
            app_data_dir=str(self.data_dir),
            api_key=api_key or ""
        )
        self.worker_manager.start_all()
        
        # Create screen manager
        self.screen_manager = ScreenManager()
        
        # Add screens
        self.screen_manager.add_widget(MainScreen(name='main'))
        self.screen_manager.add_widget(GalleryScreen(name='gallery'))
        self.screen_manager.add_widget(HistoryScreen(name='history'))
        self.screen_manager.add_widget(SettingsScreen(name='settings'))
        
        # Request permissions on Android
        if ANDROID:
            self.request_android_permissions()
        
        return self.screen_manager
    
    def request_android_permissions(self):
        """Request necessary Android permissions"""
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.ACCESS_NETWORK_STATE
            ])
        except:
            pass
    
    def switch_screen(self, screen_name):
        """Switch to a different screen"""
        self.screen_manager.current = screen_name
    
    def toggle_nav_drawer(self):
        """Toggle navigation drawer (placeholder)"""
        Snackbar(text="Navigation drawer coming soon!").open()
    
    def on_stop(self):
        """Clean up when app stops"""
        if self.worker_manager:
            # Auto-backup if enabled
            if self.storage.get_setting('auto_backup', True):
                self.worker_manager.create_backup(reason="app_close")
            
            self.worker_manager.stop_all()


if __name__ == '__main__':
    DALLE2CompleteApp().run()
