#!/bin/bash
# Quick APK status check

echo "=== APK Build Status ==="
echo

# Check for APK
if [ -f bin/dalleimages-1.0.0-arm64-v8a_armeabi-v7a-debug.apk ]; then
    echo "✅ APK FOUND!"
    echo
    ls -lh bin/*.apk
    echo
    echo "To install:"
    echo "1. Run: ./INSTALL_WITHOUT_ADB.sh"
    echo "2. Transfer APK to phone"
    echo "3. Install and enjoy!"
else
    echo "❌ No APK yet"
    
    # Check if building
    if pgrep -f buildozer > /dev/null; then
        echo "🔄 Build is running..."
        echo
        echo "Build directory size: $(du -sh .buildozer 2>/dev/null | cut -f1)"
        echo "Log size: $(wc -l < build2.log 2>/dev/null || echo 0) lines"
        echo
        echo "Latest activity:"
        tail -3 build2.log 2>/dev/null | grep -v "^$" | head -3
    else
        echo "❌ Build not running"
        echo
        echo "To start build:"
        echo "  source venv/bin/activate"
        echo "  buildozer android debug"
    fi
fi