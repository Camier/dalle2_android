#!/bin/bash
# Direct build approach using p4a

set -e

echo "=== Direct APK Build using p4a ==="

# Activate venv
source venv/bin/activate

# Set environment
export ANDROID_HOME=$HOME/.buildozer/android/platform/android-sdk
export ANDROID_NDK_HOME=$HOME/.buildozer/android/platform/android-ndk-r25b
export ANDROIDAPI=31
export ANDROIDNDK=$ANDROID_NDK_HOME
export ANDROIDSDK=$ANDROID_HOME

# Clean previous attempts
echo "Cleaning previous builds..."
rm -rf .buildozer/android/platform/build-arm64-v8a/dists/dalleaiart
rm -rf bin/*

# Use buildozer one more time with minimal config
echo "Creating minimal buildozer.spec..."
cat > buildozer.spec << 'EOF'
[app]
title = DALL-E AI Art
package.name = dalleaiart
package.domain = com.aiart
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# Minimal requirements
requirements = python3,kivy

# Android configuration
android.permissions = INTERNET
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

# Build settings
android.release = False
log_level = 2

[buildozer]
android.skip_update = False
EOF

# Build
echo "Building APK..."
buildozer android debug

# Check if APK was created
if ls bin/*.apk 1> /dev/null 2>&1; then
    echo "================================================"
    echo "BUILD SUCCESSFUL!"
    echo "================================================"
    ls -la bin/*.apk
    echo ""
    echo "Your minimal APK is ready!"
    echo "You can now:"
    echo "1. Test it: adb install -r bin/*.apk"
    echo "2. Add features incrementally"
else
    echo "================================================"
    echo "Buildozer failed. Trying direct p4a command..."
    echo "================================================"
    
    # Try direct p4a command
    cd .buildozer/android/platform/python-for-android
    
    p4a apk \
        --name "DALLEApp" \
        --package "com.aiart.dalleaiart" \
        --version "1.0" \
        --bootstrap "sdl2" \
        --requirements "python3,kivy" \
        --permission "INTERNET" \
        --arch "arm64-v8a" \
        --private "/home/mik/dalle_android" \
        --output-dir "/home/mik/dalle_android/bin"
    
    cd /home/mik/dalle_android
    
    if ls bin/*.apk 1> /dev/null 2>&1; then
        echo "================================================"
        echo "P4A BUILD SUCCESSFUL!"
        echo "================================================"
        ls -la bin/*.apk
    else
        echo "Build failed. Check logs for details."
    fi
fi