#\!/bin/bash

echo "=== Monitoring Build Progress ==="
echo "Build started at: $(date)"
echo ""

while true; do
    # Check if buildozer is still running
    if \! pgrep -f "buildozer android debug" > /dev/null; then
        echo ""
        echo "Build process completed at: $(date)"
        
        # Check if APK was created
        if [ -f "bin/dalleaiart-1.0.0-debug.apk" ]; then
            echo "SUCCESS: APK created successfully\!"
            ls -lh bin/*.apk
        else
            echo "Build completed but no APK found in bin/"
            echo "Checking for errors in log..."
            tail -n 50 build_complete.log  < /dev/null |  grep -E "(ERROR|error|Failed|failed)"
        fi
        break
    fi
    
    # Show current stage
    echo -n "."
    
    # Check for specific build stages
    if tail -n 5 build_complete.log | grep -q "Building"; then
        echo -n " [Building]"
    elif tail -n 5 build_complete.log | grep -q "Downloading"; then
        echo -n " [Downloading]"
    elif tail -n 5 build_complete.log | grep -q "Compiling"; then
        echo -n " [Compiling]"
    elif tail -n 5 build_complete.log | grep -q "Packaging"; then
        echo -n " [Packaging]"
    fi
    
    sleep 10
done
