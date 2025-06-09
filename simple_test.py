#!/usr/bin/env python
"""
Simple test app to verify APK building works
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button

class TestApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20)
        
        label = Label(
            text='Hello from DALL-E App!\nAPK Build Test',
            font_size='20sp'
        )
        layout.add_widget(label)
        
        button = Button(
            text='Test Button',
            size_hint=(1, 0.3),
            on_press=self.on_button_press
        )
        layout.add_widget(button)
        
        self.status_label = Label(
            text='Status: Ready',
            size_hint=(1, 0.2)
        )
        layout.add_widget(self.status_label)
        
        return layout
    
    def on_button_press(self, instance):
        self.status_label.text = 'Button pressed! Build works!'

if __name__ == '__main__':
    TestApp().run()