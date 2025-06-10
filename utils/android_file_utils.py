"""
Android file utilities for sharing files
"""

from kivy.utils import platform


def share_file(file_path: str, mime_type: str = "application/octet-stream", title: str = "Share"):
    """
    Share a file on Android using intent
    
    Args:
        file_path: Path to the file to share
        mime_type: MIME type of the file (e.g., "application/zip", "image/png")
        title: Title for the share dialog
        
    Returns:
        bool: True if successful, False otherwise
    """
    if platform != 'android':
        print(f"File sharing not implemented for {platform}")
        return False
    
    try:
        from jnius import autoclass, cast
        from android import activity
        
        # Get required Java classes
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')
        Uri = autoclass('android.net.Uri')
        File = autoclass('java.io.File')
        FileProvider = autoclass('androidx.core.content.FileProvider')
        
        # Get current activity
        current_activity = cast('android.app.Activity', PythonActivity.mActivity)
        context = current_activity.getApplicationContext()
        
        # Create file object
        file_to_share = File(file_path)
        
        # Get package name
        package_name = context.getPackageName()
        authority = f"{package_name}.fileprovider"
        
        # Get content URI using FileProvider
        uri = FileProvider.getUriForFile(context, authority, file_to_share)
        
        # Create share intent
        share_intent = Intent(Intent.ACTION_SEND)
        share_intent.setType(mime_type)
        share_intent.putExtra(Intent.EXTRA_STREAM, uri)
        share_intent.putExtra(Intent.EXTRA_TEXT, title)
        share_intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        
        # Create chooser
        chooser = Intent.createChooser(share_intent, title)
        chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        
        # Start activity
        current_activity.startActivity(chooser)
        
        return True
        
    except Exception as e:
        print(f"Error sharing file: {e}")
        return False


def get_downloads_directory():
    """Get the Android downloads directory"""
    if platform != 'android':
        from pathlib import Path
        return str(Path.home() / 'Downloads')
    
    try:
        from jnius import autoclass
        Environment = autoclass('android.os.Environment')
        downloads_dir = Environment.getExternalStoragePublicDirectory(
            Environment.DIRECTORY_DOWNLOADS
        )
        return downloads_dir.getAbsolutePath()
    except Exception as e:
        print(f"Error getting downloads directory: {e}")
        return "/sdcard/Download"


def copy_to_downloads(source_path: str, filename: str = None):
    """
    Copy a file to the downloads directory
    
    Args:
        source_path: Path to the source file
        filename: Optional filename for the destination (uses source filename if not provided)
        
    Returns:
        str: Path to the copied file, or None if failed
    """
    try:
        import shutil
        from pathlib import Path
        
        source = Path(source_path)
        if not source.exists():
            return None
        
        downloads = Path(get_downloads_directory())
        downloads.mkdir(exist_ok=True)
        
        dest_filename = filename or source.name
        dest_path = downloads / dest_filename
        
        # Copy file
        shutil.copy2(source, dest_path)
        
        return str(dest_path)
        
    except Exception as e:
        print(f"Error copying to downloads: {e}")
        return None