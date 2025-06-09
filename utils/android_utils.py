"""
Android utility module for permissions, media handling, and sharing
Provides unified interface for Android-specific functionality with desktop fallbacks
"""

import os
import sys
from typing import List, Optional, Callable, Dict, Any
from pathlib import Path
from datetime import datetime

# Check if we're on Android
from kivy.utils import platform

# Import pyjnius components only on Android
if platform == 'android':
    from jnius import autoclass, cast, PythonJavaClass, java_method
    from android import mActivity
    from android.permissions import Permission, request_permissions, check_permission
    from android.storage import primary_external_storage_path
else:
    # Desktop fallbacks
    class Permission:
        WRITE_EXTERNAL_STORAGE = "android.permission.WRITE_EXTERNAL_STORAGE"
        READ_EXTERNAL_STORAGE = "android.permission.READ_EXTERNAL_STORAGE"
        CAMERA = "android.permission.CAMERA"
        INTERNET = "android.permission.INTERNET"
    
    def request_permissions(permissions):
        print(f"[Desktop] Would request permissions: {permissions}")
        return True
    
    def check_permission(permission):
        print(f"[Desktop] Would check permission: {permission}")
        return True


class PermissionHandler:
    """Handles Android permission requests with callbacks"""
    
    def __init__(self):
        self.callbacks = {}
        
    def request_permissions(self, permissions: List[str], callback: Optional[Callable] = None):
        """
        Request Android permissions
        
        Args:
            permissions: List of permission strings
            callback: Optional callback function(granted: bool)
        """
        if platform == 'android':
            # Store callback for when permission result arrives
            if callback:
                self.callbacks['permission_request'] = callback
            
            # Request permissions
            request_permissions(permissions)
            
            # Check immediately (some might already be granted)
            all_granted = all(check_permission(p) for p in permissions)
            if callback:
                callback(all_granted)
        else:
            # Desktop fallback
            print(f"[Desktop] Permission request simulation: {permissions}")
            if callback:
                callback(True)
    
    def check_permissions(self, permissions: List[str]) -> bool:
        """Check if permissions are granted"""
        if platform == 'android':
            return all(check_permission(p) for p in permissions)
        else:
            print(f"[Desktop] Permission check simulation: {permissions}")
            return True
    
    def request_storage_permissions(self, callback: Optional[Callable] = None):
        """Convenience method for storage permissions"""
        storage_perms = [
            Permission.WRITE_EXTERNAL_STORAGE,
            Permission.READ_EXTERNAL_STORAGE
        ]
        self.request_permissions(storage_perms, callback)


class MediaStoreHelper:
    """Handles saving images to Android MediaStore for gallery visibility"""
    
    def __init__(self):
        if platform == 'android':
            # Load Java classes
            self.Environment = autoclass('android.os.Environment')
            self.MediaStore = autoclass('android.provider.MediaStore')
            self.ContentValues = autoclass('android.content.ContentValues')
            self.Uri = autoclass('android.net.Uri')
            self.File = autoclass('java.io.File')
            self.FileOutputStream = autoclass('java.io.FileOutputStream')
            self.MediaScannerConnection = autoclass('android.media.MediaScannerConnection')
            self.Context = autoclass('android.content.Context')
            
    def save_to_gallery(self, image_data: bytes, filename: str = None, 
                       mime_type: str = "image/png") -> Optional[str]:
        """
        Save image to gallery using MediaStore
        
        Args:
            image_data: Image bytes data
            filename: Optional filename (will generate if not provided)
            mime_type: MIME type of the image
            
        Returns:
            Path to saved file or None if failed
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dalle_{timestamp}.png"
        
        if platform == 'android':
            try:
                # Get content resolver
                resolver = mActivity.getContentResolver()
                
                # Create content values
                values = self.ContentValues()
                values.put(self.MediaStore.Images.Media.DISPLAY_NAME, filename)
                values.put(self.MediaStore.Images.Media.MIME_TYPE, mime_type)
                values.put(self.MediaStore.Images.Media.RELATIVE_PATH, 
                          self.Environment.DIRECTORY_PICTURES + "/DALLE")
                
                # Insert to MediaStore
                uri = resolver.insert(self.MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
                
                if uri:
                    # Write image data
                    output_stream = resolver.openOutputStream(uri)
                    output_stream.write(image_data)
                    output_stream.close()
                    
                    # Get the actual file path
                    cursor = resolver.query(uri, [self.MediaStore.Images.Media.DATA], 
                                          None, None, None)
                    if cursor and cursor.moveToFirst():
                        path = cursor.getString(0)
                        cursor.close()
                        
                        # Notify media scanner
                        self._scan_file(path)
                        
                        return path
                
                return None
                
            except Exception as e:
                print(f"Error saving to MediaStore: {e}")
                return self._fallback_save(image_data, filename)
        else:
            # Desktop fallback
            return self._fallback_save(image_data, filename)
    
    def _scan_file(self, file_path: str):
        """Notify media scanner about new file"""
        if platform == 'android':
            try:
                # Create intent for media scanning
                Intent = autoclass('android.content.Intent')
                intent = Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE)
                intent.setData(self.Uri.parse(f"file://{file_path}"))
                mActivity.sendBroadcast(intent)
            except Exception as e:
                print(f"Error scanning file: {e}")
    
    def _fallback_save(self, image_data: bytes, filename: str) -> Optional[str]:
        """Fallback save method for desktop or when MediaStore fails"""
        try:
            # Determine save directory
            if platform == 'android':
                from android.storage import primary_external_storage_path
                base_dir = primary_external_storage_path()
                save_dir = os.path.join(base_dir, "Pictures", "DALLE")
            else:
                # Desktop fallback
                home = os.path.expanduser('~')
                save_dir = os.path.join(home, "Pictures", "DALLE")
            
            # Create directory if needed
            os.makedirs(save_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(save_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(image_data)
            
            return file_path
            
        except Exception as e:
            print(f"Error in fallback save: {e}")
            return None


class ShareHelper:
    """Handles sharing images via Android Intent system"""
    
    def __init__(self):
        if platform == 'android':
            # Load Java classes
            self.Intent = autoclass('android.content.Intent')
            self.Uri = autoclass('android.net.Uri')
            self.File = autoclass('java.io.File')
            self.FileProvider = None
            
            # Try to load FileProvider (might need androidx)
            try:
                self.FileProvider = autoclass('androidx.core.content.FileProvider')
            except:
                try:
                    self.FileProvider = autoclass('android.support.v4.content.FileProvider')
                except:
                    print("FileProvider not available")
    
    def share_image(self, image_path: str, text: str = None) -> bool:
        """
        Share image using Android share intent
        
        Args:
            image_path: Path to image file
            text: Optional text to share with image
            
        Returns:
            True if share intent launched successfully
        """
        if platform == 'android':
            try:
                # Create file object
                file = self.File(image_path)
                
                # Get URI for file
                if self.FileProvider:
                    # Use FileProvider for Android 7.0+
                    uri = self.FileProvider.getUriForFile(
                        mActivity,
                        mActivity.getPackageName() + ".fileprovider",
                        file
                    )
                else:
                    # Direct file URI for older Android
                    uri = self.Uri.fromFile(file)
                
                # Create share intent
                intent = self.Intent(self.Intent.ACTION_SEND)
                intent.setType("image/*")
                intent.putExtra(self.Intent.EXTRA_STREAM, uri)
                
                if text:
                    intent.putExtra(self.Intent.EXTRA_TEXT, text)
                
                # Grant read permission
                intent.addFlags(self.Intent.FLAG_GRANT_READ_URI_PERMISSION)
                
                # Create chooser
                chooser = self.Intent.createChooser(intent, "Share Image")
                
                # Start activity
                mActivity.startActivity(chooser)
                
                return True
                
            except Exception as e:
                print(f"Error sharing image: {e}")
                return False
        else:
            # Desktop fallback
            print(f"[Desktop] Would share image: {image_path}")
            if text:
                print(f"[Desktop] With text: {text}")
            return True
    
    def share_text(self, text: str, subject: str = None) -> bool:
        """
        Share text using Android share intent
        
        Args:
            text: Text to share
            subject: Optional subject line
            
        Returns:
            True if share intent launched successfully
        """
        if platform == 'android':
            try:
                # Create share intent
                intent = self.Intent(self.Intent.ACTION_SEND)
                intent.setType("text/plain")
                intent.putExtra(self.Intent.EXTRA_TEXT, text)
                
                if subject:
                    intent.putExtra(self.Intent.EXTRA_SUBJECT, subject)
                
                # Create chooser
                chooser = self.Intent.createChooser(intent, "Share")
                
                # Start activity
                mActivity.startActivity(chooser)
                
                return True
                
            except Exception as e:
                print(f"Error sharing text: {e}")
                return False
        else:
            # Desktop fallback
            print(f"[Desktop] Would share text: {text}")
            if subject:
                print(f"[Desktop] With subject: {subject}")
            return True


# Singleton instances for easy access
permission_handler = PermissionHandler()
media_store_helper = MediaStoreHelper()
share_helper = ShareHelper()


# Convenience functions
def request_storage_permissions(callback: Optional[Callable] = None):
    """Request storage permissions"""
    return permission_handler.request_storage_permissions(callback)


def save_image_to_gallery(image_data: bytes, filename: str = None) -> Optional[str]:
    """Save image to gallery"""
    return media_store_helper.save_to_gallery(image_data, filename)


def share_image(image_path: str, text: str = None) -> bool:
    """Share image via intent"""
    return share_helper.share_image(image_path, text)


def share_text(text: str, subject: str = None) -> bool:
    """Share text via intent"""
    return share_helper.share_text(text, subject)
