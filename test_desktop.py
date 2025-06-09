#!/usr/bin/env python
"""
Desktop test script for DALL-E app
Run this before building APK to test functionality
"""

import os
import sys

# Set environment for desktop testing
os.environ['KIVY_WINDOW'] = 'sdl2'

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the app
from main import DalleApp

if __name__ == '__main__':
    print("Starting DALL-E app in desktop mode...")
    print("Note: Some Android-specific features may not work")
    print("=" * 50)
    
    app = DalleApp()
    app.run()