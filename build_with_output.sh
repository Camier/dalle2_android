#!/bin/bash
# Build script with better output

echo "Starting DALL-E Android APK build..."
echo "This will take 15-30 minutes for first build"
echo "================================================"

# Activate virtual environment
source venv/bin/activate

# Ensure PATH includes Android tools
export PATH=$PATH:$HOME/.buildozer/android/platform/android-sdk/platform-tools

# Start build with output to both screen and log
buildozer android debug 2>&1 | tee build.log

# Check if APK was created
echo
echo "================================================"
if [ -f "bin/*.apk" ]; then
    echo "✅ BUILD SUCCESSFUL!"
    echo "APK location:"
    ls -la bin/*.apk
else
    echo "❌ Build failed or in progress"
    echo "Check build.log for details"
    echo
    echo "Last 20 lines of log:"
    tail -20 build.log
fi