"""
Secure storage for API keys using encryption
"""

import os
import json
from cryptography.fernet import Fernet
from kivy.utils import platform

class SecureStorage:
    def __init__(self):
        self.storage_dir = self._get_storage_dir()
        self.key_file = os.path.join(self.storage_dir, '.key')
        self.data_file = os.path.join(self.storage_dir, '.data')
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