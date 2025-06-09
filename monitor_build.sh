#!/bin/bash
# Monitor build progress

echo "=== DALL-E Android Build Monitor ==="
echo "Press Ctrl+C to stop monitoring"
echo

while true; do
    clear
    echo "=== DALL-E Android Build Monitor ==="
    echo "Time: $(date)"
    echo
    
    # Check if buildozer is running
    if pgrep -f "buildozer" > /dev/null; then
        echo "✅ Build is RUNNING"
        
        # Show current activity
        echo
        echo "Current activity:"
        tail -5 build.log | grep -v "^$"
        
        # Check build directory size
        echo
        echo "Build size: $(du -sh .buildozer 2>/dev/null | cut -f1)"
        
    else
        echo "❌ Build is NOT running"
        
        # Check if APK exists
        if [ -f bin/dalleimages-1.0.0-arm64-v8a_armeabi-v7a-debug.apk ]; then
            echo
            echo "✅ APK FOUND!"
            echo "Location: bin/dalleimages-1.0.0-arm64-v8a_armeabi-v7a-debug.apk"
            echo "Size: $(ls -lh bin/*.apk | awk '{print $5}')"
            echo
            echo "Run ./INSTALL_WITHOUT_ADB.sh for installation instructions"
            exit 0
        else
            echo
            echo "No APK found yet. Last build activity:"
            tail -10 build.log | grep -v "^$"
        fi
    fi
    
    echo
    echo "Refreshing in 5 seconds..."
    sleep 5
done