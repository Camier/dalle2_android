"""
Secure Storage Module for DALL-E AI Art App
Implements encrypted storage for sensitive data like API keys
"""

import os
import json
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from kivy.logger import Logger
from kivy.utils import platform

class SecureStorage:
    """Secure storage for sensitive application data"""
    
    def __init__(self, app_name="dalle_ai_art"):
        self.app_name = app_name
        self.storage_dir = self._get_secure_storage_path()
        self.key_file = self.storage_dir / "app.key"
        self.data_file = self.storage_dir / "secure_data.enc"
        self.cipher = self._initialize_cipher()
        Logger.info(f"SecureStorage: Initialized for {app_name}")
    
    def _get_secure_storage_path(self):
        """Get platform-specific secure storage path"""
        if platform == 'android':
            from android.storage import app_storage_path
            path = Path(app_storage_path()) / '.secure'
        else:
            # For desktop testing
            path = Path.home() / f'.{self.app_name}' / '.secure'
        
        # Create directory with restricted permissions
        path.mkdir(parents=True, exist_ok=True)
        if platform != 'android':
            os.chmod(path, 0o700)  # Owner read/write/execute only
        
        return path
    
    def _initialize_cipher(self):
        """Initialize or load encryption cipher"""
        if self.key_file.exists():
            # Load existing key
            try:
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                return Fernet(key)
            except Exception as e:
                Logger.error(f"SecureStorage: Failed to load key: {e}")
                # Generate new key if loading fails
        
        # Generate new key
        return self._generate_new_key()
    
    def _generate_new_key(self):
        """Generate a new encryption key"""
        # Use device-specific salt if available
        salt = self._get_device_salt()
        
        # Generate key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        # Use a combination of app name and random data
        password = f"{self.app_name}_{os.urandom(16).hex()}".encode()
        key = base64.urlsafe_b64encode(kdf.derive(password))
        
        # Store key securely
        with open(self.key_file, 'wb') as f:
            f.write(key)
        
        if platform != 'android':
            os.chmod(self.key_file, 0o600)  # Owner read/write only
        
        return Fernet(key)
    
    def _get_device_salt(self):
        """Get device-specific salt for key generation"""
        if platform == 'android':
            try:
                from jnius import autoclass
                Build = autoclass('android.os.Build')
                # Use Android ID as part of salt
                device_id = f"{Build.SERIAL}_{Build.FINGERPRINT}"
                return device_id.encode()[:16]  # Use first 16 bytes
            except:
                pass
        
        # Fallback to random salt
        salt = os.urandom(16)
        salt_file = self.storage_dir / "device.salt"
        
        if salt_file.exists():
            with open(salt_file, 'rb') as f:
                salt = f.read()
        else:
            with open(salt_file, 'wb') as f:
                f.write(salt)
            if platform != 'android':
                os.chmod(salt_file, 0o600)
        
        return salt
    
    def store_api_key(self, api_key):
        """Securely store the API key"""
        try:
            self.store_data('api_key', api_key)
            Logger.info("SecureStorage: API key stored securely")
            return True
        except Exception as e:
            Logger.error(f"SecureStorage: Failed to store API key: {e}")
            return False
    
    def get_api_key(self):
        """Retrieve the stored API key"""
        try:
            return self.get_data('api_key')
        except Exception as e:
            Logger.error(f"SecureStorage: Failed to retrieve API key: {e}")
            return None
    
    def store_data(self, key, value):
        """Store encrypted data"""
        # Load existing data
        data = self._load_all_data()
        
        # Update with new value
        data[key] = value
        
        # Encrypt and save
        encrypted_data = self.cipher.encrypt(json.dumps(data).encode())
        
        with open(self.data_file, 'wb') as f:
            f.write(encrypted_data)
        
        if platform != 'android':
            os.chmod(self.data_file, 0o600)
    
    def get_data(self, key, default=None):
        """Retrieve decrypted data"""
        data = self._load_all_data()
        return data.get(key, default)
    
    def _load_all_data(self):
        """Load and decrypt all stored data"""
        if not self.data_file.exists():
            return {}
        
        try:
            with open(self.data_file, 'rb') as f:
                encrypted_data = f.read()
            
            if not encrypted_data:
                return {}
            
            decrypted_data = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            Logger.error(f"SecureStorage: Failed to load data: {e}")
            return {}
    
    def remove_api_key(self):
        """Remove stored API key"""
        self.remove_data('api_key')
        Logger.info("SecureStorage: API key removed")
    
    def remove_data(self, key):
        """Remove specific data"""
        data = self._load_all_data()
        data.pop(key, None)
        
        if data:
            # Re-encrypt remaining data
            encrypted_data = self.cipher.encrypt(json.dumps(data).encode())
            with open(self.data_file, 'wb') as f:
                f.write(encrypted_data)
        else:
            # Remove file if no data left
            if self.data_file.exists():
                self.data_file.unlink()
    
    def clear_all_data(self):
        """Clear all stored data (for privacy/GDPR compliance)"""
        try:
            if self.data_file.exists():
                self.data_file.unlink()
            if self.key_file.exists():
                self.key_file.unlink()
            Logger.info("SecureStorage: All data cleared")
            return True
        except Exception as e:
            Logger.error(f"SecureStorage: Failed to clear data: {e}")
            return False
    
    def rotate_encryption_key(self):
        """Rotate encryption key (security best practice)"""
        try:
            # Load all data with current key
            data = self._load_all_data()
            
            # Generate new key
            self.cipher = self._generate_new_key()
            
            # Re-encrypt with new key
            if data:
                encrypted_data = self.cipher.encrypt(json.dumps(data).encode())
                with open(self.data_file, 'wb') as f:
                    f.write(encrypted_data)
            
            Logger.info("SecureStorage: Encryption key rotated successfully")
            return True
        except Exception as e:
            Logger.error(f"SecureStorage: Failed to rotate key: {e}")
            return False

# Singleton instance
_secure_storage = None

def get_secure_storage():
    """Get singleton instance of SecureStorage"""
    global _secure_storage
    if _secure_storage is None:
        _secure_storage = SecureStorage()
    return _secure_storage