"""
Image utility functions for saving images to device gallery
"""

import os
from datetime import datetime
from PIL import Image as PILImage
from kivy.utils import platform

def save_image_to_gallery(pil_image, filename=None):
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dalle_image_{timestamp}.png"
    
    if platform == 'android':
        # Android-specific gallery saving
        from android.storage import primary_external_storage_path
        from android import mActivity
        from jnius import autoclass, cast
        
        # Get the Pictures directory
        Environment = autoclass('android.os.Environment')
        pictures_dir = os.path.join(
            primary_external_storage_path(),
            Environment.DIRECTORY_PICTURES,
            'DALLE'
        )
        os.makedirs(pictures_dir, exist_ok=True)
        
        # Save the image
        filepath = os.path.join(pictures_dir, filename)
        pil_image.save(filepath, 'PNG')
        
        # Notify the media scanner so it appears in gallery
        MediaScannerConnection = autoclass('android.media.MediaScannerConnection')
        MediaStore = autoclass('android.provider.MediaStore')
        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')
        
        # Create media scan intent
        intent = Intent(Intent.ACTION_MEDIA_SCANNER_SCAN_FILE)
        intent.setData(Uri.parse(f"file://{filepath}"))
        mActivity.sendBroadcast(intent)
        
        return filepath
    else:
        # Desktop fallback for testing
        home = os.path.expanduser('~')
        pictures_dir = os.path.join(home, 'Pictures', 'DALLE')
        os.makedirs(pictures_dir, exist_ok=True)
        
        filepath = os.path.join(pictures_dir, filename)
        pil_image.save(filepath, 'PNG')
        
        return filepath