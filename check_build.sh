#!/bin/bash
# Script to check build progress

echo "=== DALL-E Android Build Status ==="
echo

# Check if buildozer is running
if pgrep -f "buildozer" > /dev/null; then
    echo "✅ Build is running..."
    echo
    
    # Show what's being downloaded/built
    echo "Recent activity:"
    tail -n 20 ~/.buildozer/logs/*.log 2>/dev/null || echo "No log files yet"
    
    echo
    echo "Disk usage:"
    du -sh ~/.buildozer/ 2>/dev/null || echo "Buildozer directory not found"
else
    echo "❌ Build is not running"
    
    # Check if APK exists
    if ls bin/*.apk 1> /dev/null 2>&1; then
        echo "✅ APK found:"
        ls -lh bin/*.apk
    else
        echo "❌ No APK found yet"
    fi
fi

echo
echo "To start/resume build:"
echo "  source venv/bin/activate"
echo "  buildozer android debug"