#!/bin/bash
# Build script for DALL-E Android app

echo "DALL-E Android App Build Script"
echo "==============================="

# Check if buildozer is installed
if ! command -v buildozer &> /dev/null; then
    echo "Error: buildozer is not installed"
    echo "Install with: pip install buildozer"
    exit 1
fi

# Clean previous builds
echo "Cleaning previous builds..."
buildozer android clean

# Build debug APK
echo "Building debug APK..."
buildozer android debug

# Check if build succeeded
if [ -f "bin/*.apk" ]; then
    echo ""
    echo "Build successful!"
    echo "APK location: $(ls bin/*.apk)"
    echo ""
    echo "To install on device:"
    echo "  adb install $(ls bin/*.apk)"
else
    echo ""
    echo "Build failed. Check the output above for errors."
    exit 1
fi