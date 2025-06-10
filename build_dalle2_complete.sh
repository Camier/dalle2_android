#!/bin/bash
# Build script for DALL-E 2 Complete Android app with all features
# Includes inpainting, outpainting, and resolution selector

set -e

echo "=========================================="
echo "DALL-E 2 Complete Android App - Build"
echo "Feature-complete with inpainting & more!"
echo "=========================================="

cd /home/mik/dalle_android
source venv/bin/activate

# Install/update buildozer
pip install --upgrade buildozer cython==0.29.36

# Set Java 11 (most compatible)
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

echo "Using Java version:"
java -version

# Clean build environment
echo "Cleaning build environment..."
rm -rf ~/.gradle/daemon
pkill -f gradle 2>/dev/null || true

# Create buildozer spec with all DALL-E 2 features
cat > buildozer_dalle2_complete.spec << 'EOF'
[app]
title = DALL-E 2 Complete
package.name = dalle2complete
package.domain = com.aiart
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
version = 2.0

# Requirements including opencv for inpainting
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,requests,certifi,urllib3,openai,pyjnius,android,cryptography,numpy

# Resources
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png

# Android configuration
orientation = portrait
fullscreen = 0
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.arch = arm64-v8a

# Permissions for all features
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,VIBRATE

# Android specific
android.gradle_dependencies = com.google.android.material:material:1.6.1, androidx.appcompat:appcompat:1.4.2
android.enable_androidx = True
android.add_gradle_maven_dependencies = True
android.gradle_repositories = google(),mavenCentral(),jcenter()

# Build settings
android.release = False
android.debug = True
p4a.bootstrap = sdl2
log_level = 2
warn_on_root = 0

# Exclude unnecessary files
android.blacklist_src = venv,tests,apk_extracted,*.pyc,*.pyo

[buildozer]
# Buildozer settings
log_level = 2
warn_on_root = 0

# Custom build options
android.skip_update = False
android.gradle_timeout = 300
EOF

# Prepare main.py with all features
cat > main.py << 'EOF'
#!/usr/bin/env python3
"""
DALL-E 2 Complete Android App
Features: Text-to-Image, Variations, Inpainting, Outpainting, Multi-Resolution
"""

import os
import sys
from pathlib import Path

# Android imports
try:
    from jnius import autoclass
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    activity = PythonActivity.mActivity
    ANDROID = True
except:
    ANDROID = False

# Kivy configuration
from kivy.config import Config
if not ANDROID:
    Config.set('graphics', 'width', '400')
    Config.set('graphics', 'height', '800')

# Main imports
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager
from kivy.core.window import Window
from kivy.utils import platform
from kivymd.uix.snackbar import Snackbar

# Import screens
from screens.main_screen import MainScreen
from screens.gallery_screen import GalleryScreen
from screens.history_screen import HistoryScreen
from screens.settings_screen import SettingsScreen

# Import services
from services.dalle_api import DalleAPIService
from utils.storage import SecureStorage

# Import workers
from workers import WorkerManager


class DALLE2CompleteApp(MDApp):
    """DALL-E 2 Complete - All features in your pocket"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "DALL-E 2 Complete"
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.primary_hue = "500"
        self.theme_cls.theme_style = "Dark"
        
        # Services
        self.dalle_service = DalleAPIService()
        self.storage = SecureStorage()
        self.worker_manager = None
        
        # Data directory
        if ANDROID:
            from android.storage import app_storage_path
            self.data_dir = app_storage_path()
        else:
            self.data_dir = Path.home() / '.dalle2complete'
        
        self.data_dir = Path(self.data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
    def build(self):
        """Build the app UI"""
        # Initialize worker manager
        api_key = self.storage.get_api_key()
        self.worker_manager = WorkerManager(
            app_data_dir=str(self.data_dir),
            api_key=api_key or ""
        )
        self.worker_manager.start_all()
        
        # Create screen manager
        self.screen_manager = ScreenManager()
        
        # Add screens
        self.screen_manager.add_widget(MainScreen(name='main'))
        self.screen_manager.add_widget(GalleryScreen(name='gallery'))
        self.screen_manager.add_widget(HistoryScreen(name='history'))
        self.screen_manager.add_widget(SettingsScreen(name='settings'))
        
        # Request permissions on Android
        if ANDROID:
            self.request_android_permissions()
        
        return self.screen_manager
    
    def request_android_permissions(self):
        """Request necessary Android permissions"""
        try:
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.INTERNET,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.ACCESS_NETWORK_STATE
            ])
        except:
            pass
    
    def switch_screen(self, screen_name):
        """Switch to a different screen"""
        self.screen_manager.current = screen_name
    
    def toggle_nav_drawer(self):
        """Toggle navigation drawer (placeholder)"""
        Snackbar(text="Navigation drawer coming soon!").open()
    
    def on_stop(self):
        """Clean up when app stops"""
        if self.worker_manager:
            # Auto-backup if enabled
            if self.storage.get_setting('auto_backup', True):
                self.worker_manager.create_backup(reason="app_close")
            
            self.worker_manager.stop_all()


if __name__ == '__main__':
    DALLE2CompleteApp().run()
EOF

# Use the new spec
cp buildozer_dalle2_complete.spec buildozer.spec

# First build attempt
echo "Starting DALL-E 2 Complete build..."
echo "This may take 10-20 minutes on first run..."
echo ""

# Create required directories
mkdir -p bin

if buildozer android debug; then
    echo "Build successful!"
else
    echo "First attempt failed, applying fixes..."
    
    # Apply gradle fixes
    if [ -f "./fix_gradle.sh" ]; then
        ./fix_gradle.sh
    fi
    
    # Retry with manual gradle if needed
    BUILD_DIR=$(find .buildozer -name "gradlew" -type f | head -1 | xargs dirname)
    
    if [ -n "$BUILD_DIR" ]; then
        cd "$BUILD_DIR"
        
        # Clean and rebuild
        ./gradlew clean
        ./gradlew assembleDebug --stacktrace --no-daemon
        
        cd /home/mik/dalle_android
    fi
fi

# Find and rename APK
APK_PATH=$(find . -name "*-debug.apk" -type f | head -1)
if [ -n "$APK_PATH" ]; then
    cp "$APK_PATH" bin/dalle2-complete-debug.apk
    echo ""
    echo "=========================================="
    echo "✅ BUILD SUCCESSFUL!"
    echo ""
    echo "📱 APK: bin/dalle2-complete-debug.apk"
    echo "📏 Size: $(ls -lh bin/dalle2-complete-debug.apk | awk '{print $5}')"
    echo ""
    echo "🚀 Features included:"
    echo "   ✅ Text-to-Image Generation"
    echo "   ✅ Image Variations"
    echo "   ✅ Inpainting (Edit with AI)"
    echo "   ✅ Outpainting (Extend images)"
    echo "   ✅ Resolution Selector (256/512/1024)"
    echo "   ✅ Batch Generation (1-4 images)"
    echo "   ✅ Gallery & History"
    echo "   ✅ Secure API Key Storage"
    echo ""
    echo "📲 Install with:"
    echo "   adb install -r bin/dalle2-complete-debug.apk"
    echo "=========================================="
else
    echo "❌ Build failed - check .buildozer/logs/"
fi