from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

class DALLEApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20)
        
        # Title
        title = Label(text='DALL-E AI Art Generator', size_hint_y=0.2, font_size='24sp')
        layout.add_widget(title)
        
        # Input
        self.prompt_input = TextInput(
            hint_text='Enter your image description...',
            multiline=True,
            size_hint_y=0.4
        )
        layout.add_widget(self.prompt_input)
        
        # Button
        generate_btn = Button(
            text='Generate Image',
            size_hint_y=0.2,
            background_color=(0.2, 0.6, 1, 1)
        )
        generate_btn.bind(on_press=self.generate_image)
        layout.add_widget(generate_btn)
        
        # Status
        self.status_label = Label(
            text='Ready to generate!',
            size_hint_y=0.2
        )
        layout.add_widget(self.status_label)
        
        return layout
    
    def generate_image(self, instance):
        prompt = self.prompt_input.text
        if prompt:
            self.status_label.text = f'Generating: {prompt[:50]}...'
        else:
            self.status_label.text = 'Please enter a description!'

if __name__ == '__main__':
    DALLEApp().run()
