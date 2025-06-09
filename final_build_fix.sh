#!/bin/bash
cd /home/mik/dalle_android

echo "=== DALL-E Android Final Build Fix ==="
echo "Fixing all known issues..."
echo ""

# Activate venv
source venv/bin/activate

# Set correct Java
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/usr/lib/wsl/lib

# Set Android paths
export ANDROID_HOME=/home/mik/.buildozer/android/platform/android-sdk
export ANDROID_SDK_ROOT=

# Kill any stuck gradle processes
pkill -f gradle 2>/dev/null
rm -rf ~/.gradle/daemon

# Fix the gradle build file
echo "1. Fixing Gradle repositories..."
if [ -f .buildozer/android/platform/build-arm64-v8a/dists/dallesimple/build.gradle ]; then
    cd .buildozer/android/platform/build-arm64-v8a/dists/dallesimple
    
    # Replace deprecated jcenter with mavenCentral
    sed -i 's/jcenter()/mavenCentral()/g' build.gradle
    
    # Also fix gradle version if needed - use compatible version
    sed -i "s/com.android.tools.build:gradle:8.1.1/com.android.tools.build:gradle:7.4.2/g" build.gradle
    
    echo "   ✅ Fixed repositories and gradle version"
    
    # Try gradle build directly
    echo ""
    echo "2. Testing Gradle build directly..."
    ./gradlew --no-daemon --offline clean 2>&1 | head -20
    
    cd /home/mik/dalle_android
fi

# Alternative: Skip gradle and build with older method
echo ""
echo "3. Building with p4a directly (bypassing buildozer gradle issues)..."

# Ensure we have the simplified files
cp main_simple.py main.py
cp buildozer_simple.spec buildozer.spec

# Try building with explicit options
echo ""
echo "Starting build..."
python -m buildozer -v android debug

echo ""
echo "Build attempt complete. Checking for APK..."
ls -la bin/*.apk 2>/dev/null || echo "No APK found"
