#!/usr/bin/env python
"""
DALL-E 2 Android App - Full Featured Version
Complete implementation with all features and improvements
"""

import os
import sys
from pathlib import Path

from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.utils import platform
from kivy.lang import Builder

# Import all screens
from screens.main_screen import MainScreen
from screens.gallery_screen import GalleryScreen
from screens.settings_screen import SettingsScreen
from screens.history_screen import HistoryScreen

# Request permissions on Android
if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([
        Permission.INTERNET,
        Permission.WRITE_EXTERNAL_STORAGE,
        Permission.READ_EXTERNAL_STORAGE,
        Permission.CAMERA  # For future feature: take photo and edit
    ])

# KV Design
KV = '''
ScreenManager:
    MainScreen:
        name: 'main'
    GalleryScreen:
        name: 'gallery'
    HistoryScreen:
        name: 'history'
    SettingsScreen:
        name: 'settings'

<MainScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        
        MDTopAppBar:
            title: 'DALL-E Image Generator'
            elevation: 10
            left_action_items: [['menu', lambda x: app.toggle_nav_drawer()]]
            right_action_items: [['cog', lambda x: app.switch_screen('settings')]]
        
        MDTabs:
            id: tabs
            on_tab_switch: app.on_tab_switch(*args)
            
            Tab:
                title: 'Generate'
                
                MDBoxLayout:
                    orientation: 'vertical'
                    padding: dp(20)
                    spacing: dp(20)
                    
                    MDTextField:
                        id: prompt_input
                        hint_text: 'Describe the image you want to create...'
                        mode: 'rectangle'
                        multiline: True
                        size_hint_y: None
                        height: dp(100)
                        helper_text: 'Be specific and descriptive for best results'
                        helper_text_mode: 'persistent'
                    
                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(60)
                        spacing: dp(10)
                        
                        MDRaisedButton:
                            text: 'Generate'
                            on_release: root.generate_image()
                            md_bg_color: app.theme_cls.primary_color
                            size_hint_x: 0.7
                        
                        MDIconButton:
                            icon: 'history'
                            on_release: app.switch_screen('history')
                            size_hint_x: 0.15
                        
                        MDIconButton:
                            icon: 'folder-image'
                            on_release: app.switch_screen('gallery')
                            size_hint_x: 0.15
                    
                    MDCard:
                        orientation: 'vertical'
                        size_hint_y: 1
                        elevation: 5
                        radius: [15,]
                        
                        MDBoxLayout:
                            id: image_container
                            orientation: 'vertical'
                            
                            MDSpinner:
                                id: spinner
                                size_hint: None, None
                                size: dp(48), dp(48)
                                pos_hint: {'center_x': 0.5, 'center_y': 0.5}
                                active: False
                            
                            Image:
                                id: generated_image
                                allow_stretch: True
                                keep_ratio: True
                                opacity: 0
            
            Tab:
                title: 'Batch'
                
                MDBoxLayout:
                    orientation: 'vertical'
                    padding: dp(20)
                    spacing: dp(10)
                    
                    MDTextField:
                        id: batch_prompt
                        hint_text: 'Base prompt for variations'
                        mode: 'rectangle'
                        multiline: True
                        size_hint_y: None
                        height: dp(80)
                    
                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(50)
                        spacing: dp(10)
                        
                        MDLabel:
                            text: 'Number of images:'
                            size_hint_x: 0.5
                        
                        MDSlider:
                            id: batch_slider
                            min: 1
                            max: 4
                            value: 2
                            size_hint_x: 0.4
                        
                        MDLabel:
                            text: str(int(batch_slider.value))
                            size_hint_x: 0.1
                    
                    MDRaisedButton:
                        text: 'Generate Batch'
                        on_release: root.generate_batch()
                        size_hint_y: None
                        height: dp(50)
                    
                    ScrollView:
                        MDGridLayout:
                            id: batch_grid
                            cols: 2
                            spacing: dp(10)
                            size_hint_y: None
                            height: self.minimum_height

<GalleryScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        
        MDTopAppBar:
            title: 'Image Gallery'
            elevation: 10
            left_action_items: [['arrow-left', lambda x: app.switch_screen('main')]]
            right_action_items: [['delete', lambda x: root.clear_gallery()]]
        
        ScrollView:
            MDGridLayout:
                id: gallery_grid
                cols: 2
                spacing: dp(10)
                padding: dp(10)
                size_hint_y: None
                height: self.minimum_height

<HistoryScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        
        MDTopAppBar:
            title: 'Generation History'
            elevation: 10
            left_action_items: [['arrow-left', lambda x: app.switch_screen('main')]]
            right_action_items: [['delete', lambda x: root.clear_history()]]
        
        ScrollView:
            MDList:
                id: history_list

<SettingsScreen>:
    MDBoxLayout:
        orientation: 'vertical'
        
        MDTopAppBar:
            title: 'Settings'
            elevation: 10
            left_action_items: [['arrow-left', lambda x: app.switch_screen('main')]]
        
        ScrollView:
            MDBoxLayout:
                orientation: 'vertical'
                padding: dp(20)
                spacing: dp(20)
                size_hint_y: None
                height: self.minimum_height
                
                MDCard:
                    orientation: 'vertical'
                    padding: dp(20)
                    size_hint_y: None
                    height: self.minimum_height
                    
                    MDLabel:
                        text: 'API Configuration'
                        font_style: 'H6'
                        size_hint_y: None
                        height: self.texture_size[1]
                    
                    MDTextField:
                        id: api_key_input
                        hint_text: 'OpenAI API Key'
                        helper_text: 'Your API key is encrypted and stored locally'
                        helper_text_mode: 'persistent'
                        password: True
                        size_hint_y: None
                        height: dp(80)
                    
                    MDRaisedButton:
                        text: 'Save API Key'
                        on_release: root.save_api_key()
                        size_hint_y: None
                        height: dp(50)
                
                MDCard:
                    orientation: 'vertical'
                    padding: dp(20)
                    size_hint_y: None
                    height: self.minimum_height
                    
                    MDLabel:
                        text: 'Image Settings'
                        font_style: 'H6'
                        size_hint_y: None
                        height: self.texture_size[1]
                    
                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(50)
                        
                        MDLabel:
                            text: 'Default Size:'
                            size_hint_x: 0.4
                        
                        MDDropDownItem:
                            id: size_dropdown
                            text: '1024x1024'
                            on_release: root.show_size_menu()
                            size_hint_x: 0.6
                
                MDCard:
                    orientation: 'vertical'
                    padding: dp(20)
                    size_hint_y: None
                    height: self.minimum_height
                    
                    MDLabel:
                        text: 'App Settings'
                        font_style: 'H6'
                        size_hint_y: None
                        height: self.texture_size[1]
                    
                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(50)
                        
                        MDLabel:
                            text: 'Dark Mode'
                            size_hint_x: 0.7
                        
                        MDSwitch:
                            id: dark_mode_switch
                            on_active: app.toggle_theme()
                            size_hint_x: 0.3
                    
                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(50)
                        
                        MDLabel:
                            text: 'Save to Gallery'
                            size_hint_x: 0.7
                        
                        MDSwitch:
                            id: auto_save_switch
                            active: True
                            size_hint_x: 0.3
'''

class DalleApp(MDApp):
    def build(self):
        self.title = 'DALL-E Image Generator'
        self.icon = 'assets/icon.png'
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.primary_hue = '600'
        self.theme_cls.theme_style = 'Light'
        
        # Set window size for desktop testing
        if platform != 'android':
            Window.size = (400, 700)
        
        # Load KV
        Builder.load_string(KV)
        
        # Create screen manager
        self.sm = ScreenManager()
        
        # Create screens (these will be implemented in separate files)
        self.main_screen = MainScreen(name='main')
        self.gallery_screen = GalleryScreen(name='gallery')
        self.history_screen = HistoryScreen(name='history')
        self.settings_screen = SettingsScreen(name='settings')
        
        # Add screens
        self.sm.add_widget(self.main_screen)
        self.sm.add_widget(self.gallery_screen)
        self.sm.add_widget(self.history_screen)
        self.sm.add_widget(self.settings_screen)
        
        return self.sm
    
    def switch_screen(self, screen_name):
        self.sm.current = screen_name
    
    def toggle_theme(self):
        self.theme_cls.theme_style = (
            'Dark' if self.theme_cls.theme_style == 'Light' else 'Light'
        )
    
    def on_tab_switch(self, instance_tabs, instance_tab, instance_tab_label, tab_text):
        pass  # Handle tab switching if needed

if __name__ == '__main__':
    DalleApp().run()
