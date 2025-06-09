from utils.dialogs import ConfirmDialog
"""
History screen to view generation history
"""

from kivy.uix.screenmanager import Screen
from kivy.lang import Builder
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.list import TwoLineListItem
from kivymd.app import MDApp
import os

from utils.storage import SecureStorage

# Load KV file
Builder.load_file(os.path.join(os.path.dirname(__file__), '../ui/history_screen.kv'))


class HistoryScreen(Screen):
    """History screen to view generation history"""
    
    def on_enter(self):
        """Called when screen is entered"""
        self.refresh_history()
    
    def refresh_history(self):
        """Refresh history list"""
        self.ids.history_list.clear_widgets()
        
        # Load history
        history = SecureStorage().get_history()
        
        for item in history:
            self._add_history_item(item)
    
    def _add_history_item(self, item):
        """Add item to history list"""
        list_item = TwoLineListItem(
            text=item.get('prompt', 'No prompt'),
            secondary_text=item.get('timestamp', 'Unknown time')
        )
        
        # Add tap to regenerate
        list_item.bind(on_release=lambda x: self._regenerate_from_history(item))
        
        self.ids.history_list.add_widget(list_item)
    
    def _regenerate_from_history(self, item):
        """Regenerate image from history item"""
        app = MDApp.get_running_app()
        app.switch_screen('main')
        app.main_screen.ids.prompt_input.text = item.get('prompt', '')
        Snackbar(text="Prompt loaded - tap Generate to create new image").open()
    
    def clear_history(self):
        """Clear all history"""
        history = SecureStorage().get_history()
        
        if not history:
            Snackbar(text="History is already empty").open()
            return
        
        dialog = ConfirmDialog(
            title="Clear History?",
            text=f"This will delete all {len(history)} entries from history. This action cannot be undone.",
            on_confirm=self._confirm_clear_history,
            confirm_text="Clear All",
            cancel_text="Cancel"
        )
        dialog.open()
        
    
    def filter_history(self, query):
        """Filter history based on search query"""
        if not query:
            self.refresh_history()
            return
        
        # Clear current list
        self.ids.history_list.clear_widgets()
        
        # Search history
        results = SecureStorage().search_history(query)
        
        for item in results:
            self._add_history_item(item)
    
    def _confirm_clear_history(self):
        """Actually clear the history"""
        try:
            storage = SecureStorage()
            count = len(storage.get_history())
            storage.clear_history()
            
            self.refresh_history()
            Snackbar(text=f"Cleared {count} history entries").open()
        except Exception as e:
            Snackbar(text=f"Error clearing history: {str(e)}").open()
