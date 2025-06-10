"""
Enhanced settings screen with export/import functionality
"""

from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.progressindicator import MDCircularProgressIndicator
from kivymd.uix.list import OneLineListItem, TwoLineListItem
from kivymd.app import MDApp
from kivy.metrics import dp
from kivy.clock import Clock
from pathlib import Path
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any

from utils.storage import SecureStorage
from utils.dialogs import ConfirmDialog


class SettingsScreenEnhanced(Screen):
    """Enhanced settings screen with export/import and backup functionality"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.storage = SecureStorage()
        self.size_options = ['256x256', '512x512', '1024x1024']
        self.current_size = '512x512'
        self.export_in_progress = False
        self.import_in_progress = False
        
        # Add backup section to the UI
        Clock.schedule_once(self._add_backup_section, 0.5)
    
    def on_enter(self):
        """Called when screen is entered"""
        # Load current API key (masked)
        api_key = self.storage.get_api_key()
        if api_key:
            self.ids.api_key_input.text = '*' * 20
            
        # Update the API key in worker manager if needed
        app = MDApp.get_running_app()
        if hasattr(app, 'worker_manager'):
            app.update_api_key(api_key)
    
    def _add_backup_section(self, dt):
        """Add backup/restore section to settings"""
        if not hasattr(self.ids, 'settings_container'):
            # If using the default KV, find the main container
            for child in self.children:
                if hasattr(child, 'children'):
                    for subchild in child.children:
                        if isinstance(subchild, MDBoxLayout) and subchild.orientation == 'vertical':
                            self._create_backup_card(subchild)
                            break
        else:
            # If using custom KV with settings_container id
            self._create_backup_card(self.ids.settings_container)
    
    def _create_backup_card(self, parent_container):
        """Create the backup/restore card"""
        # Create backup card
        backup_card = MDCard(
            orientation='vertical',
            padding=dp(20),
            size_hint_y=None,
            height=dp(320),
            elevation=5,
            radius=[15,]
        )
        
        # Title
        backup_card.add_widget(MDLabel(
            text='Backup & Restore',
            font_style='H6',
            size_hint_y=None,
            height=dp(30)
        ))
        
        # Description
        backup_card.add_widget(MDLabel(
            text='Export your settings, API key, and history or import from a backup',
            theme_text_color='Secondary',
            font_style='Caption',
            size_hint_y=None,
            height=dp(40)
        ))
        
        # Export section
        export_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(10),
            padding=[0, dp(10), 0, 0]
        )
        
        export_btn = MDRaisedButton(
            text='Export Settings',
            on_release=lambda x: self._show_export_options(),
            size_hint_x=0.6
        )
        export_box.add_widget(export_btn)
        
        # Include images checkbox
        from kivymd.uix.selectioncontrol import MDCheckbox
        self.include_images_check = MDCheckbox(
            size_hint=(None, None),
            size=(dp(48), dp(48))
        )
        export_box.add_widget(self.include_images_check)
        
        export_box.add_widget(MDLabel(
            text='Include images',
            size_hint_x=0.3
        ))
        
        backup_card.add_widget(export_box)
        
        # Import section
        import_btn = MDRaisedButton(
            text='Import Settings',
            on_release=lambda x: self._show_import_dialog(),
            size_hint_y=None,
            height=dp(50)
        )
        backup_card.add_widget(import_btn)
        
        # Auto-backup section
        auto_backup_box = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(10),
            padding=[0, dp(10), 0, 0]
        )
        
        auto_backup_box.add_widget(MDLabel(
            text='Auto-backup on app close',
            size_hint_x=0.7
        ))
        
        from kivymd.uix.selectioncontrol import MDSwitch
        self.auto_backup_switch = MDSwitch(
            size_hint_x=0.3,
            active=self._load_auto_backup_preference()
        )
        self.auto_backup_switch.bind(active=self._on_auto_backup_toggle)
        auto_backup_box.add_widget(self.auto_backup_switch)
        
        backup_card.add_widget(auto_backup_box)
        
        # Progress indicator
        self.backup_progress = MDCircularProgressIndicator(
            size_hint=(None, None),
            size=(dp(48), dp(48)),
            pos_hint={'center_x': 0.5}
        )
        self.backup_progress.opacity = 0
        backup_card.add_widget(self.backup_progress)
        
        # Add to parent container
        parent_container.add_widget(backup_card)
        
        # Store reference
        self.backup_card = backup_card
    
    def save_api_key(self):
        """Save new API key"""
        api_key = self.ids.api_key_input.text.strip()
        
        # Only save if it's not the masked version
        if api_key and not api_key.startswith('*'):
            self.storage.save_api_key(api_key)
            
            # Update in main app
            app = MDApp.get_running_app()
            if hasattr(app.main_screen, 'api_service'):
                app.main_screen.api_service.set_api_key(api_key)
            
            # Update in worker manager
            if hasattr(app, 'worker_manager'):
                app.update_api_key(api_key)
            
            Snackbar(text="API Key saved successfully!").open()
            self.ids.api_key_input.text = '*' * 20
    
    def _show_export_options(self):
        """Show export options"""
        if self.export_in_progress:
            Snackbar(text="Export already in progress").open()
            return
        
        # Get file name from user
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.textfield import MDTextField
        
        # Create filename field
        filename_field = MDTextField(
            hint_text="Backup filename",
            text=f"dalle_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            helper_text="Will be saved as .zip file",
            helper_text_mode="persistent"
        )
        
        dialog = MDDialog(
            title="Export Settings",
            type="custom",
            content_cls=filename_field,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="EXPORT",
                    on_release=lambda x: self._perform_export(filename_field.text, dialog)
                ),
            ],
        )
        dialog.open()
    
    def _perform_export(self, filename: str, dialog):
        """Perform the actual export"""
        dialog.dismiss()
        
        if not filename:
            Snackbar(text="Please enter a filename").open()
            return
        
        # Show progress
        self.export_in_progress = True
        self.backup_progress.opacity = 1
        self.backup_progress.active = True
        
        app = MDApp.get_running_app()
        if not hasattr(app, 'worker_manager'):
            Snackbar(text="Worker system not available").open()
            self._hide_progress()
            return
        
        # Prepare destination
        if not filename.endswith('.zip'):
            filename += '.zip'
        
        destination = Path(app.data_dir) / 'exports' / filename
        
        # Export callback with thread safety
        def on_export_complete(result):
            from kivy.clock import Clock
            
            def update_ui(dt):
                self.export_in_progress = False
                self._hide_progress()
                
                if result.get('success'):
                    export_path = result.get('export_path', destination)
                    Snackbar(text=f"Exported to {export_path.name}").open()
                    
                    # Offer to share on Android
                    from kivy.utils import platform
                    if platform == 'android':
                        self._offer_share_export(export_path)
                else:
                    error = result.get('error', 'Unknown error')
                    Snackbar(text=f"Export failed: {error}").open()
            
            # Schedule UI update on main thread
            Clock.schedule_once(update_ui, 0)
        
        # Perform export
        include_images = self.include_images_check.active if hasattr(self, 'include_images_check') else False
        app.worker_manager.export_settings(
            destination=str(destination),
            include_images=include_images,
            callback=on_export_complete
        )
    
    def _offer_share_export(self, export_path):
        """Offer to share the exported file on Android"""
        dialog = ConfirmDialog(
            title="Share Export?",
            text=f"Would you like to share {export_path.name}?",
            on_confirm=lambda: self._share_export_file(export_path),
            confirm_text="Share",
            cancel_text="Later"
        )
        dialog.open()
    
    def _share_export_file(self, export_path):
        """Share the export file"""
        try:
            from utils.android_utils import share_file
            success = share_file(
                str(export_path),
                "application/zip",
                f"DALL-E App Backup - {export_path.name}"
            )
            if not success:
                Snackbar(text="Failed to open share dialog").open()
        except Exception as e:
            Snackbar(text=f"Share error: {str(e)}").open()
    
    def _show_import_dialog(self):
        """Show import dialog"""
        if self.import_in_progress:
            Snackbar(text="Import already in progress").open()
            return
        
        # For Android, use file picker
        from kivy.utils import platform
        if platform == 'android':
            self._show_android_file_picker()
        else:
            # For desktop, show text input
            self._show_desktop_import_dialog()
    
    def _show_desktop_import_dialog(self):
        """Show import dialog for desktop"""
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.textfield import MDTextField
        
        # Create filename field
        filename_field = MDTextField(
            hint_text="Path to backup file",
            helper_text="Enter full path to .zip backup file",
            helper_text_mode="persistent"
        )
        
        dialog = MDDialog(
            title="Import Settings",
            type="custom",
            content_cls=filename_field,
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="IMPORT",
                    on_release=lambda x: self._perform_import(filename_field.text, dialog)
                ),
            ],
        )
        dialog.open()
    
    def _show_android_file_picker(self):
        """Show file picker on Android"""
        try:
            from plyer import filechooser
            filechooser.open_file(
                on_selection=self._on_file_selected,
                filters=["*.zip"]
            )
        except:
            # Fallback to text input
            self._show_desktop_import_dialog()
    
    def _on_file_selected(self, selection):
        """Handle file selection"""
        if selection:
            self._perform_import(selection[0], None)
    
    def _perform_import(self, filepath: str, dialog):
        """Perform the actual import"""
        if dialog:
            dialog.dismiss()
        
        if not filepath:
            Snackbar(text="Please select a file").open()
            return
        
        source_path = Path(filepath)
        if not source_path.exists():
            Snackbar(text="File not found").open()
            return
        
        # Confirm import
        confirm_dialog = ConfirmDialog(
            title="Import Settings?",
            text="This will replace your current settings with the imported ones. Continue?",
            on_confirm=lambda: self._do_import(str(source_path))
        )
        confirm_dialog.open()
    
    def _do_import(self, source_path: str):
        """Actually perform the import"""
        # Show progress
        self.import_in_progress = True
        self.backup_progress.opacity = 1
        self.backup_progress.active = True
        
        app = MDApp.get_running_app()
        if not hasattr(app, 'worker_manager'):
            Snackbar(text="Worker system not available").open()
            self._hide_progress()
            return
        
        # Import callback with thread safety
        def on_import_complete(result):
            from kivy.clock import Clock
            
            def update_ui(dt):
                self.import_in_progress = False
                self._hide_progress()
                
                if result.get('success'):
                    Snackbar(text="Settings imported successfully!").open()
                    
                    # Reload settings
                    self.on_enter()
                    
                    # Refresh other screens if needed
                    if hasattr(app, 'gallery_screen'):
                        app.gallery_screen.refresh_gallery()
                else:
                    error = result.get('error', 'Unknown error')
                    Snackbar(text=f"Import failed: {error}").open()
            
            # Schedule UI update on main thread
            Clock.schedule_once(update_ui, 0)
        
        # Perform import
        app.worker_manager.import_settings(
            source=source_path,
            callback=on_import_complete
        )
    
    def _on_auto_backup_toggle(self, switch, value):
        """Handle auto-backup toggle"""
        self._save_auto_backup_preference(value)
        status = "enabled" if value else "disabled"
        Snackbar(text=f"Auto-backup {status}").open()
    
    def _load_auto_backup_preference(self) -> bool:
        """Load auto-backup preference"""
        try:
            prefs_file = Path(self.storage.storage_dir) / '.preferences'
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    prefs = json.load(f)
                    return prefs.get('auto_backup', False)
        except:
            pass
        return False
    
    def _save_auto_backup_preference(self, enabled: bool):
        """Save auto-backup preference"""
        try:
            prefs_file = Path(self.storage.storage_dir) / '.preferences'
            prefs = {}
            
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    prefs = json.load(f)
            
            prefs['auto_backup'] = enabled
            
            with open(prefs_file, 'w') as f:
                json.dump(prefs, f)
        except Exception as e:
            print(f"Error saving auto-backup preference: {e}")
    
    def _hide_progress(self):
        """Hide progress indicator"""
        self.backup_progress.opacity = 0
        self.backup_progress.active = False
    
    # Keep all existing methods from original SettingsScreen
    def show_size_menu(self):
        """Show image size selection menu"""
        menu_items = [
            {
                "text": size,
                "on_release": lambda x=size: self.set_image_size(x),
            }
            for size in self.size_options
        ]
        
        self.menu = MDDropdownMenu(
            caller=self.ids.size_dropdown,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()
    
    def set_image_size(self, size):
        """Set selected image size"""
        self.current_size = size
        self.ids.size_dropdown.text = size
        self.menu.dismiss()
        
        # Save size preference
        self._save_size_preference(size)
        Snackbar(text=f"Default size set to {size}").open()
    
    def get_image_size(self):
        """Get current image size setting"""
        # Try to load saved preference
        size = self._load_size_preference()
        if size and size in self.size_options:
            self.current_size = size
        return self.current_size
    
    def is_auto_save_enabled(self):
        """Check if auto-save is enabled"""
        return self.ids.auto_save_switch.active
    
    def _save_size_preference(self, size):
        """Save size preference to storage"""
        try:
            prefs_file = Path(self.storage.storage_dir) / '.preferences'
            prefs = {}
            
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    prefs = json.load(f)
            
            prefs['image_size'] = size
            
            with open(prefs_file, 'w') as f:
                json.dump(prefs, f)
        except Exception as e:
            print(f"Error saving size preference: {e}")
    
    def _load_size_preference(self):
        """Load size preference from storage"""
        try:
            prefs_file = Path(self.storage.storage_dir) / '.preferences'
            
            if prefs_file.exists():
                with open(prefs_file, 'r') as f:
                    prefs = json.load(f)
                    return prefs.get('image_size')
        except Exception as e:
            print(f"Error loading size preference: {e}")
        
        return None