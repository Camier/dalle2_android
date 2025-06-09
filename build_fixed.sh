#!/bin/bash
cd /home/mik/dalle_android

echo "=== DALL-E Android Fixed Build ==="
echo "This will build the simplified version properly"
echo ""

# Clean previous attempts
echo "1. Cleaning previous build..."
rm -rf .buildozer/android/platform/build-arm64-v8a/dists/dallesimple
rm -rf bin/*.apk

# Set up simplified version
echo "2. Setting up simplified version..."
cp main_simple.py main.py
cp buildozer_simple.spec buildozer.spec

# Set Java 8
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/usr/lib/wsl/lib

# Activate venv
source venv/bin/activate

# Build
echo "3. Starting build (this will take ~5-10 minutes)..."
echo "   DO NOT interrupt or modify files during build!"
echo ""
buildozer android debug 2>&1 | tee build_fixed.log

# Check result
echo ""
echo "4. Build complete. Checking for APK..."
if [ -f bin/*.apk ]; then
    echo "✅ SUCCESS! APK built:"
    ls -la bin/*.apk
    echo ""
    echo "To install: adb install bin/*.apk"
else
    echo "❌ Build failed. Check build_fixed.log for errors"
fi

# DO NOT restore files here - keep simplified version for now
echo ""
echo "Note: main.py and buildozer.spec are still the simplified versions"
echo "To restore originals later: cp main_original.py main.py"
