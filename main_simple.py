#!/usr/bin/env python
"""
DALL-E 2 Android App - Simplified Version
"""

from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivy.network.urlrequest import UrlRequest
import json

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        
        # Title
        title = MDLabel(
            text='DALL-E Image Generator',
            font_style='H4',
            halign='center',
            size_hint_y=None,
            height=50
        )
        layout.add_widget(title)
        
        # API Key input
        self.api_key_input = MDTextField(
            hint_text='Enter OpenAI API Key',
            password=True,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.api_key_input)
        
        # Prompt input
        self.prompt_input = MDTextField(
            hint_text='Enter image prompt',
            multiline=True,
            size_hint_y=None,
            height=100
        )
        layout.add_widget(self.prompt_input)
        
        # Generate button
        generate_btn = MDRaisedButton(
            text='Generate Image',
            size_hint=(1, None),
            height=50,
            on_release=self.generate_image
        )
        layout.add_widget(generate_btn)
        
        # Status label
        self.status_label = MDLabel(
            text='Ready',
            halign='center',
            size_hint_y=None,
            height=30
        )
        layout.add_widget(self.status_label)
        
        # Spacer
        layout.add_widget(BoxLayout())
        
        self.add_widget(layout)
    
    def generate_image(self, instance):
        api_key = self.api_key_input.text.strip()
        prompt = self.prompt_input.text.strip()
        
        if not api_key:
            self.status_label.text = 'Please enter API key'
            return
            
        if not prompt:
            self.status_label.text = 'Please enter a prompt'
            return
        
        self.status_label.text = 'Generating...'
        
        # API call
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = json.dumps({
            'prompt': prompt,
            'n': 1,
            'size': '512x512'
        })
        
        req = UrlRequest(
            'https://api.openai.com/v1/images/generations',
            req_body=data,
            req_headers=headers,
            on_success=self.on_success,
            on_error=self.on_error,
            on_failure=self.on_error
        )
    
    def on_success(self, req, result):
        self.status_label.text = 'Image generated successfully!'
        # In a full app, we'd display the image here
        
    def on_error(self, req, error):
        self.status_label.text = f'Error: {str(error)}'

class DalleSimpleApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = 'Blue'
        self.theme_cls.theme_style = 'Light'
        
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm

if __name__ == '__main__':
    DalleSimpleApp().run()
