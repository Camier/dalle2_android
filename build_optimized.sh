#!/bin/bash
# Optimized build script for DALL-E Android app
# This script uses a progressive approach to handle build issues

set -e

echo "=========================================="
echo "DALL-E Android App - Optimized Build"
echo "=========================================="

cd /home/mik/dalle_android
source venv/bin/activate

# Install/update buildozer
pip install --upgrade buildozer cython==0.29.33

# Set Java 11 (most compatible)
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

echo "Using Java version:"
java -version

# Clean build environment
echo "Cleaning build environment..."
rm -rf ~/.gradle/daemon
pkill -f gradle 2>/dev/null || true

# Create minimal buildozer spec first
cat > buildozer_minimal_new.spec << 'EOF'
[app]
title = DALL-E AI Art
package.name = dalleai
package.domain = com.camier
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

# Use full version with all features
source.main = main_full.py

# Minimal requirements first
requirements = python3,kivy==2.2.1,kivymd==1.1.1,requests,pillow

# Resources
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png

# Basic Android config
orientation = portrait
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.arch = arm64-v8a
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 1
EOF

# Use the new minimal spec
cp buildozer_minimal_new.spec buildozer.spec
cp main_full.py main.py

# First build attempt
echo "Starting build (attempt 1/2)..."
if buildozer android debug; then
    echo "Build successful on first attempt!"
    mv bin/*.apk bin/dalleai-debug.apk 2>/dev/null || true
else
    echo "First attempt failed, applying fixes..."
    
    # Apply gradle fixes
    ./fix_gradle.sh
    
    # Try manual gradle build
    echo "Attempting manual gradle build..."
    BUILD_DIR=$(find .buildozer -name "gradlew" -type f | head -1 | xargs dirname)
    
    if [ -n "$BUILD_DIR" ]; then
        cd "$BUILD_DIR"
        
        # Additional fixes for common issues
        # Fix: Add missing dependencies
        if [ -f "build.gradle" ]; then
            # Ensure Material Design dependency
            if ! grep -q "material:" build.gradle; then
                sed -i '/dependencies {/a \    implementation "com.google.android.material:material:1.6.1"' build.gradle
            fi
        fi
        
        # Clean and build
        ./gradlew clean
        ./gradlew assembleDebug --stacktrace
        
        # Copy APK
        cd /home/mik/dalle_android
        find .buildozer -name "*-debug.apk" -type f -exec cp {} bin/dalleai-debug.apk \;
    fi
fi

# Final check
echo ""
echo "=========================================="
if [ -f "bin/dalleai-debug.apk" ]; then
    APK_SIZE=$(ls -lh bin/dalleai-debug.apk | awk '{print $5}')
    echo "✅ BUILD SUCCESSFUL!"
    echo ""
    echo "📱 APK Details:"
    echo "   File: bin/dalleai-debug.apk"
    echo "   Size: $APK_SIZE"
    echo ""
    echo "📲 Installation methods:"
    echo ""
    echo "1. Using ADB (USB debugging enabled):"
    echo "   adb install -r bin/dalleai-debug.apk"
    echo ""
    echo "2. Direct transfer:"
    echo "   - Copy APK to device via USB/cloud"
    echo "   - Enable 'Install from unknown sources'"
    echo "   - Open APK file on device to install"
    echo ""
    echo "3. Using Python HTTP server:"
    echo "   python3 -m http.server 8000"
    echo "   Then visit http://[your-ip]:8000 on device"
else
    echo "❌ BUILD FAILED"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check Java version (should be 11):"
    echo "   java -version"
    echo ""
    echo "2. Clear all caches:"
    echo "   rm -rf ~/.gradle/"
    echo "   rm -rf .buildozer/"
    echo ""
    echo "3. Check logs in:"
    echo "   .buildozer/logs/"
fi
echo "=========================================="
