#!/bin/bash
# DALL-E Android Working Build Script
# This script has all the fixes that made the build successful

cd /home/mik/dalle_android
source venv/bin/activate

# Use Java 11 (not 8, not 17)
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/usr/lib/wsl/lib
export ANDROID_HOME=/home/mik/.buildozer/android/platform/android-sdk

echo "Building DALL-E Android App..."
echo "Java version: openjdk version "21.0.7" 2025-04-15"

# Clean gradle
pkill -f gradle 2>/dev/null
rm -rf ~/.gradle/daemon

# Ensure we're using simplified version
cp main_simple.py main.py
cp buildozer_simple.spec buildozer.spec

# Build with buildozer
buildozer android debug

# If buildozer fails with gradle, apply fixes and build directly
if [ ! -f bin/*.apk ]; then
    echo "Applying gradle fixes..."
    cd .buildozer/android/platform/build-arm64-v8a/dists/dallesimple
    
    # Fix repositories
    sed -i 's/jcenter()/mavenCentral()/g' build.gradle
    
    # Use compatible gradle plugin version
    sed -i 's/com.android.tools.build:gradle:.*/com.android.tools.build:gradle:7.2.2/g' build.gradle
    
    # Use compatible gradle wrapper
    sed -i 's/gradle-.*-all.zip/gradle-7.4.2-all.zip/g' gradle/wrapper/gradle-wrapper.properties
    
    # Build directly with gradle
    ./gradlew --no-daemon clean assembleDebug
    
    # Copy APK to bin
    cd /home/mik/dalle_android
    mkdir -p bin
    cp .buildozer/android/platform/build-arm64-v8a/dists/dallesimple/build/outputs/apk/debug/dallesimple-debug.apk bin/
fi

echo ""
echo "Build complete! Check bin/ for APK"
ls -la bin/*.apk
EOF && chmod +x working_build_script.sh
