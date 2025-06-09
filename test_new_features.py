#!/usr/bin/env python3
"""Test new features imports"""

try:
    print("Testing imports...")
    from utils.image_viewer import ImageViewer
    print("✓ ImageViewer imported successfully")
    
    from utils.dialogs import ConfirmDialog, InfoDialog, LoadingDialog
    print("✓ Dialogs imported successfully")
    
    from screens.gallery_screen import GalleryScreen
    print("✓ Updated GalleryScreen imported successfully")
    
    from screens.history_screen import HistoryScreen
    print("✓ Updated HistoryScreen imported successfully")
    
    print("\nAll imports successful! New features are ready.")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
