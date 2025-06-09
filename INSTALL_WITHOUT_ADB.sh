#!/bin/bash
# Quick install script without ADB

echo "=== DALL-E APK Installation Helper ==="
echo

# Check if APK exists
if [ -f bin/dalleimages-1.0.0-arm64-v8a_armeabi-v7a-debug.apk ]; then
    echo "✅ APK found!"
    echo
    
    # Copy to Windows Desktop if in WSL
    if grep -q Microsoft /proc/version; then
        echo "Detected WSL environment"
        
        # Try to find Windows user
        WIN_USER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r\n')
        if [ -z "$WIN_USER" ]; then
            echo "Enter your Windows username:"
            read WIN_USER
        fi
        
        # Copy to Desktop
        DEST="/mnt/c/Users/$WIN_USER/Desktop/dalle_app.apk"
        cp bin/*.apk "$DEST" 2>/dev/null && echo "✅ Copied to Windows Desktop: $DEST" || echo "❌ Could not copy to Desktop"
        
        # Copy to Downloads
        DEST2="/mnt/c/Users/$WIN_USER/Downloads/dalle_app.apk"
        cp bin/*.apk "$DEST2" 2>/dev/null && echo "✅ Copied to Downloads: $DEST2"
    fi
    
    echo
    echo "=== Installation Instructions ==="
    echo "1. Transfer the APK to your Android device using:"
    echo "   - Email (attach the APK)"
    echo "   - Google Drive"
    echo "   - USB cable"
    echo "   - Bluetooth"
    echo
    echo "2. On your Android device:"
    echo "   - Go to Settings → Security"
    echo "   - Enable 'Unknown Sources' or 'Install unknown apps'"
    echo "   - Open the APK file"
    echo "   - Tap 'Install'"
    echo
    echo "3. After installation:"
    echo "   - Open 'DALL-E Image Generator'"
    echo "   - Enter your OpenAI API key"
    echo "   - Start creating images!"
    
    # Show file info
    echo
    echo "=== APK Details ==="
    ls -lh bin/*.apk
    
else
    echo "❌ APK not found!"
    echo
    echo "Build status:"
    
    # Check if build is running
    if pgrep -f buildozer > /dev/null; then
        echo "🔄 Build is still running..."
        echo "Wait for it to complete, then run this script again"
    else
        echo "Build is not running. To build the APK:"
        echo "  source venv/bin/activate"
        echo "  buildozer android debug"
    fi
fi