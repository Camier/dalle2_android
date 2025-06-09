#!/usr/bin/env python3
"""
Test script for batch generation feature
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.app import App
from kivy.lang import Builder
from kivymd.app import MDApp
from screens.main_screen import MainScreen
from screens.settings_screen import SettingsScreen
from screens.gallery_screen import GalleryScreen
from screens.history_screen import HistoryScreen

# Simple test app
class TestBatchApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.accent_palette = "Pink"
        
        # Create screens
        self.main_screen = MainScreen(name='main')
        self.settings_screen = SettingsScreen(name='settings')
        self.gallery_screen = GalleryScreen(name='gallery')
        self.history_screen = HistoryScreen(name='history')
        
        return self.main_screen
    
    def switch_screen(self, screen_name):
        print(f"Switch to {screen_name} screen requested")
    
    def toggle_nav_drawer(self):
        print("Nav drawer toggle requested")

if __name__ == "__main__":
    print("Testing batch generation feature...")
    print("1. Check if batch UI elements are loaded")
    print("2. Enter API key when prompted")
    print("3. Enter a prompt in the batch generation field")
    print("4. Use the slider to select number of images")
    print("5. Click 'Generate Batch' button")
    print("-" * 50)
    
    TestBatchApp().run()
