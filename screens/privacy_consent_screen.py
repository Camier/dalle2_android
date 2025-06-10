"""
Privacy Consent Screen for DALL-E AI Art App
Provides user-friendly interface for privacy settings and consent management
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.switch import Switch
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy.properties import ObjectProperty, BooleanProperty
from kivy.clock import Clock
from kivy.logger import Logger

import datetime
from pathlib import Path

from utils.privacy_manager import get_privacy_manager
from utils.storage import get_storage_path


class ConsentItem(BoxLayout):
    """Individual consent toggle item"""
    
    def __init__(self, consent_type, config, callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(80)
        self.padding = dp(10)
        self.spacing = dp(10)
        
        self.consent_type = consent_type
        self.config = config
        self.callback = callback
        
        # Info section
        info_layout = BoxLayout(orientation='vertical', size_hint_x=0.8)
        
        # Title
        title = Label(
            text=config['name'],
            size_hint_y=None,
            height=dp(30),
            font_size='16sp',
            bold=True,
            halign='left',
            valign='middle'
        )
        title.bind(size=title.setter('text_size'))
        info_layout.add_widget(title)
        
        # Description
        desc = Label(
            text=config['description'],
            size_hint_y=None,
            height=dp(40),
            font_size='12sp',
            halign='left',
            valign='top',
            color=(0.7, 0.7, 0.7, 1)
        )
        desc.bind(size=desc.setter('text_size'))
        info_layout.add_widget(desc)
        
        self.add_widget(info_layout)
        
        # Switch
        switch_layout = BoxLayout(size_hint_x=0.2)
        self.switch = Switch(
            active=get_privacy_manager().get_consent_status(consent_type),
            disabled=config['required']
        )
        self.switch.bind(active=self.on_switch_active)
        switch_layout.add_widget(self.switch)
        
        self.add_widget(switch_layout)
    
    def on_switch_active(self, switch, value):
        """Handle consent toggle"""
        if self.callback:
            self.callback(self.consent_type, value)


class PrivacyConsentScreen(Screen):
    """Privacy consent management screen"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.privacy_manager = get_privacy_manager()
        self.consent_items = {}
        self.build_ui()
    
    def build_ui(self):
        """Build the privacy consent UI"""
        main_layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        # Header
        header = Label(
            text='Privacy Settings',
            size_hint_y=None,
            height=dp(50),
            font_size='24sp',
            bold=True
        )
        main_layout.add_widget(header)
        
        # Scrollable content
        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        content.bind(minimum_height=content.setter('height'))
        
        # Privacy Policy Section
        policy_section = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(120))
        
        policy_label = Label(
            text='Privacy Policy',
            size_hint_y=None,
            height=dp(30),
            font_size='18sp',
            bold=True
        )
        policy_section.add_widget(policy_label)
        
        policy_status = Label(
            text=self._get_policy_status_text(),
            size_hint_y=None,
            height=dp(30),
            font_size='14sp'
        )
        self.policy_status_label = policy_status
        policy_section.add_widget(policy_status)
        
        policy_buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        read_policy_btn = Button(
            text='Read Privacy Policy',
            size_hint_x=0.5
        )
        read_policy_btn.bind(on_release=self.show_privacy_policy)
        policy_buttons.add_widget(read_policy_btn)
        
        accept_policy_btn = Button(
            text='Accept Privacy Policy',
            size_hint_x=0.5,
            disabled=self.privacy_manager.is_privacy_policy_accepted()
        )
        accept_policy_btn.bind(on_release=self.accept_privacy_policy)
        self.accept_policy_btn = accept_policy_btn
        policy_buttons.add_widget(accept_policy_btn)
        
        policy_section.add_widget(policy_buttons)
        content.add_widget(policy_section)
        
        # Separator
        content.add_widget(Label(size_hint_y=None, height=dp(20)))
        
        # Consent Toggles
        consent_header = Label(
            text='Data Processing Consents',
            size_hint_y=None,
            height=dp(30),
            font_size='18sp',
            bold=True
        )
        content.add_widget(consent_header)
        
        for consent_type, config in self.privacy_manager.CONSENT_TYPES.items():
            consent_item = ConsentItem(
                consent_type, 
                config, 
                self.on_consent_changed
            )
            self.consent_items[consent_type] = consent_item
            content.add_widget(consent_item)
        
        # Data Management Section
        content.add_widget(Label(size_hint_y=None, height=dp(20)))
        
        data_header = Label(
            text='Your Data',
            size_hint_y=None,
            height=dp(30),
            font_size='18sp',
            bold=True
        )
        content.add_widget(data_header)
        
        # Export Data Button
        export_btn = Button(
            text='Export My Data',
            size_hint_y=None,
            height=dp(50)
        )
        export_btn.bind(on_release=self.export_user_data)
        content.add_widget(export_btn)
        
        # Delete Data Button
        delete_btn = Button(
            text='Delete All My Data',
            size_hint_y=None,
            height=dp(50),
            background_color=(0.8, 0.2, 0.2, 1)
        )
        delete_btn.bind(on_release=self.show_delete_confirmation)
        content.add_widget(delete_btn)
        
        # Anonymize Data Button
        anonymize_btn = Button(
            text='Anonymize My Data',
            size_hint_y=None,
            height=dp(50)
        )
        anonymize_btn.bind(on_release=self.anonymize_data)
        content.add_widget(anonymize_btn)
        
        # Data Retention Settings
        retention_layout = BoxLayout(
            orientation='horizontal', 
            size_hint_y=None, 
            height=dp(50),
            spacing=dp(10)
        )
        
        retention_label = Label(
            text='Data retention (days):',
            size_hint_x=0.6
        )
        retention_layout.add_widget(retention_label)
        
        self.retention_input = TextInput(
            text=str(self.privacy_manager.settings.get('data_retention_days', 365)),
            multiline=False,
            input_filter='int',
            size_hint_x=0.2
        )
        retention_layout.add_widget(self.retention_input)
        
        retention_update_btn = Button(
            text='Update',
            size_hint_x=0.2
        )
        retention_update_btn.bind(on_release=self.update_retention_period)
        retention_layout.add_widget(retention_update_btn)
        
        content.add_widget(retention_layout)
        
        scroll.add_widget(content)
        main_layout.add_widget(scroll)
        
        # Bottom buttons
        bottom_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        reset_btn = Button(
            text='Reset to Minimum',
            size_hint_x=0.5
        )
        reset_btn.bind(on_release=self.reset_consents)
        bottom_layout.add_widget(reset_btn)
        
        done_btn = Button(
            text='Done',
            size_hint_x=0.5
        )
        done_btn.bind(on_release=self.go_back)
        bottom_layout.add_widget(done_btn)
        
        main_layout.add_widget(bottom_layout)
        
        self.add_widget(main_layout)
    
    def _get_policy_status_text(self):
        """Get privacy policy acceptance status text"""
        if self.privacy_manager.is_privacy_policy_accepted():
            version = self.privacy_manager.get_privacy_policy_version()
            date = self.privacy_manager.settings.get('privacy_policy_accepted_date', '')
            return f'Accepted version {version} on {date[:10]}'
        else:
            return 'Not yet accepted'
    
    def on_consent_changed(self, consent_type, granted):
        """Handle consent toggle change"""
        self.privacy_manager.update_consent(consent_type, granted)
        Logger.info(f"PrivacyConsent: Updated {consent_type} to {granted}")
    
    def show_privacy_policy(self, instance):
        """Show privacy policy in a popup"""
        try:
            policy_path = Path(__file__).parent.parent / 'assets' / 'privacy_policy.txt'
            with open(policy_path, 'r') as f:
                policy_text = f.read()
            
            # Create scrollable popup
            scroll = ScrollView()
            content = Label(
                text=policy_text,
                size_hint_y=None,
                text_size=(dp(400), None),
                padding=(dp(10), dp(10))
            )
            content.bind(texture_size=content.setter('size'))
            scroll.add_widget(content)
            
            popup = Popup(
                title='Privacy Policy',
                content=scroll,
                size_hint=(0.9, 0.9)
            )
            popup.open()
            
        except Exception as e:
            Logger.error(f"PrivacyConsent: Failed to show policy: {e}")
            self.show_error_popup('Failed to load privacy policy')
    
    def accept_privacy_policy(self, instance):
        """Accept privacy policy"""
        self.privacy_manager.accept_privacy_policy()
        self.accept_policy_btn.disabled = True
        self.policy_status_label.text = self._get_policy_status_text()
        self.show_success_popup('Privacy policy accepted')
    
    def export_user_data(self, instance):
        """Export user data"""
        export_path = self.privacy_manager.export_user_data()
        if export_path:
            self.show_success_popup(f'Data exported to:\n{export_path}')
        else:
            self.show_error_popup('Failed to export data')
    
    def show_delete_confirmation(self, instance):
        """Show delete confirmation dialog"""
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        warning = Label(
            text='WARNING: This will permanently delete all your data.\n'
                 'This action cannot be undone.\n\n'
                 f'Enter confirmation code: {self.privacy_manager.get_deletion_token()}',
            size_hint_y=None,
            height=dp(100)
        )
        content.add_widget(warning)
        
        self.delete_confirm_input = TextInput(
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        content.add_widget(self.delete_confirm_input)
        
        buttons = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        
        cancel_btn = Button(text='Cancel')
        cancel_btn.bind(on_release=lambda x: self.delete_popup.dismiss())
        buttons.add_widget(cancel_btn)
        
        confirm_btn = Button(
            text='Delete Everything',
            background_color=(0.8, 0.2, 0.2, 1)
        )
        confirm_btn.bind(on_release=self.confirm_delete_data)
        buttons.add_widget(confirm_btn)
        
        content.add_widget(buttons)
        
        self.delete_popup = Popup(
            title='Confirm Data Deletion',
            content=content,
            size_hint=(0.8, None),
            height=dp(300)
        )
        self.delete_popup.open()
    
    def confirm_delete_data(self, instance):
        """Confirm and execute data deletion"""
        token = self.delete_confirm_input.text.strip()
        if self.privacy_manager.delete_all_user_data(token):
            self.delete_popup.dismiss()
            self.show_success_popup('All data deleted successfully')
            # Return to main screen after deletion
            Clock.schedule_once(lambda dt: self.manager.current = 'main', 2)
        else:
            self.show_error_popup('Invalid confirmation code')
    
    def anonymize_data(self, instance):
        """Anonymize user data"""
        if self.privacy_manager.anonymize_data():
            self.show_success_popup('Data anonymized successfully')
        else:
            self.show_error_popup('Failed to anonymize data')
    
    def update_retention_period(self, instance):
        """Update data retention period"""
        try:
            days = int(self.retention_input.text)
            if self.privacy_manager.set_data_retention_period(days):
                self.show_success_popup(f'Retention period set to {days} days')
            else:
                self.show_error_popup('Invalid retention period')
        except ValueError:
            self.show_error_popup('Please enter a valid number')
    
    def reset_consents(self, instance):
        """Reset all consents to minimum required"""
        self.privacy_manager.reset_consents_to_minimum()
        # Update UI switches
        for consent_type, item in self.consent_items.items():
            item.switch.active = self.privacy_manager.get_consent_status(consent_type)
        self.show_success_popup('Consents reset to minimum required')
    
    def show_success_popup(self, message):
        """Show success popup"""
        popup = Popup(
            title='Success',
            content=Label(text=message),
            size_hint=(0.8, 0.3)
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)
    
    def show_error_popup(self, message):
        """Show error popup"""
        popup = Popup(
            title='Error',
            content=Label(text=message),
            size_hint=(0.8, 0.3)
        )
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 3)
    
    def go_back(self, instance):
        """Return to previous screen"""
        if self.manager.previous():
            self.manager.current = self.manager.previous()
        else:
            self.manager.current = 'main'
    
    def on_enter(self):
        """Called when entering the screen"""
        # Check if consent review is needed
        if self.privacy_manager.should_review_consents():
            Clock.schedule_once(self.show_consent_review_reminder, 1)
    
    def show_consent_review_reminder(self, dt):
        """Show reminder to review consents"""
        popup = Popup(
            title='Privacy Review',
            content=Label(
                text='It has been over a year since you last reviewed\n'
                     'your privacy settings. Please take a moment to\n'
                     'review your consent choices.'
            ),
            size_hint=(0.8, 0.3)
        )
        popup.open()
        self.privacy_manager.mark_consent_reviewed()