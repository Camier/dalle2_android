"""
Secure storage for API keys and generation history using encryption
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from cryptography.fernet import Fernet
from kivy.utils import platform

class SecureStorage:
    def __init__(self):
        self.storage_dir = self._get_storage_dir()
        self.key_file = os.path.join(self.storage_dir, '.key')
        self.data_file = os.path.join(self.storage_dir, '.data')
        self.history_file = os.path.join(self.storage_dir, '.history')
        self.cipher = self._get_cipher()
    
    def _get_storage_dir(self):
        if platform == 'android':
            from android.storage import app_storage_path
            return app_storage_path()
        else:
            # For desktop testing
            home = os.path.expanduser('~')
            storage_dir = os.path.join(home, '.dalle_app')
            os.makedirs(storage_dir, exist_ok=True)
            return storage_dir
    
    def _get_cipher(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        return Fernet(key)
    
    def save_api_key(self, api_key):
        encrypted_key = self.cipher.encrypt(api_key.encode())
        data = {'api_key': encrypted_key.decode()}
        with open(self.data_file, 'w') as f:
            json.dump(data, f)
    
    def get_api_key(self):
        if not os.path.exists(self.data_file):
            return None
        
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            encrypted_key = data.get('api_key', '').encode()
            if encrypted_key:
                return self.cipher.decrypt(encrypted_key).decode()
        except Exception:
            return None
        return None
    
    def clear_api_key(self):
        if os.path.exists(self.data_file):
            os.remove(self.data_file)
    
    # History methods
    def save_to_history(self, prompt: str, image_url: str = None, image_path: str = None, 
                       settings: Dict[str, Any] = None) -> bool:
        """
        Save a generation to history
        
        Args:
            prompt: The prompt used for generation
            image_url: URL of the generated image (optional)
            image_path: Local path where image was saved (optional)
            settings: Dictionary of settings used (size, model, etc.)
            
        Returns:
            True if saved successfully
        """
        try:
            # Load existing history
            history = self._load_history()
            
            # Create new entry
            entry = {
                'id': datetime.now().strftime('%Y%m%d_%H%M%S_%f'),
                'timestamp': datetime.now().isoformat(),
                'prompt': prompt,
                'image_url': image_url,
                'image_path': image_path,
                'settings': settings or {},
                'size': settings.get('size', '512x512') if settings else '512x512',
                'model': settings.get('model', 'dall-e-2') if settings else 'dall-e-2'
            }
            
            # Add to history (newest first)
            history.insert(0, entry)
            
            # Limit history size to prevent unbounded growth
            history = history[:100]
            
            # Save history
            self._save_history(history)
            
            return True
            
        except Exception as e:
            print(f"Error saving to history: {e}")
            return False
    
    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get generation history
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of history entries (newest first)
        """
        history = self._load_history()
        return history[:limit]
    
    def search_history(self, query: str) -> List[Dict[str, Any]]:
        """
        Search history by prompt text
        
        Args:
            query: Search query (case-insensitive)
            
        Returns:
            List of matching history entries
        """
        query_lower = query.lower()
        history = self._load_history()
        
        # Filter by prompt containing query
        results = [
            entry for entry in history
            if query_lower in entry.get('prompt', '').lower()
        ]
        
        return results
    
    def clear_history(self) -> bool:
        """
        Clear all history entries
        
        Returns:
            True if cleared successfully
        """
        try:
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
            return True
        except Exception as e:
            print(f"Error clearing history: {e}")
            return False
    
    def get_history_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific history entry by ID
        
        Args:
            entry_id: The ID of the history entry
            
        Returns:
            History entry or None if not found
        """
        history = self._load_history()
        for entry in history:
            if entry.get('id') == entry_id:
                return entry
        return None
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """Load history from file"""
        if not os.path.exists(self.history_file):
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                # Handle both encrypted and unencrypted history
                if isinstance(data, str):
                    # Encrypted history
                    decrypted = self.cipher.decrypt(data.encode()).decode()
                    return json.loads(decrypted)
                else:
                    # Unencrypted history (for compatibility)
                    return data
        except Exception as e:
            print(f"Error loading history: {e}")
            return []
    
    def _save_history(self, history: List[Dict[str, Any]]) -> None:
        """Save history to file (encrypted)"""
        try:
            # Convert to JSON
            history_json = json.dumps(history)
            
            # Encrypt
            encrypted = self.cipher.encrypt(history_json.encode()).decode()
            
            # Save
            with open(self.history_file, 'w') as f:
                json.dump(encrypted, f)
                
        except Exception as e:
            print(f"Error saving history: {e}")
            # Fallback to unencrypted save
            try:
                with open(self.history_file, 'w') as f:
                    json.dump(history, f)
            except:
                pass