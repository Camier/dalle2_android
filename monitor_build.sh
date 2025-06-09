#!/bin/bash
while true; do
    clear
    echo "=== DALL-E Android Build Monitor ==="
    echo "Time: Mon Jun  9 09:12:17 CEST 2025"
    echo ""
    
    # Check if buildozer is running
    if pgrep -f buildozer > /dev/null; then
        echo "✅ Build Status: RUNNING"
        
        # Show what's being compiled
        echo ""
        echo "Current Activity:"
        ps aux | grep -E "(gcc|clang|python|gradlew)" | grep -v grep | tail -3
        
        # Check for APK
        echo ""
        echo "APK Status:"
        if [ -f bin/*.apk ]; then
            echo "✅ APK FOUND: "
        else
            echo "⏳ APK not yet created"
        fi
    else
        echo "❌ Build Status: NOT RUNNING"
        
        # Check if APK exists
        if [ -f bin/*.apk ]; then
            echo ""
            echo "✅ BUILD COMPLETE!"
            echo "APK Location: "
            break
        else
            echo ""
            echo "⚠️ Build may have failed. Check logs."
            break
        fi
    fi
    
    sleep 5
done
EOF && chmod +x /home/mik/dalle_android/monitor_build.sh
