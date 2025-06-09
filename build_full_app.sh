#!/bin/bash
# DALL-E Android App Build Script with Full Features
# This script builds the complete app with all features including batch generation

set -e  # Exit on error

echo "================================================"
echo "DALL-E AI Art Generator - Android Build Script"
echo "================================================"

# Navigate to project directory
cd /home/mik/dalle_android

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install buildozer cython==0.29.33
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf .buildozer/android/platform/build*
rm -rf bin/*
rm -f .buildozer/state.db

# Kill any lingering gradle processes
pkill -f gradle 2>/dev/null || true
rm -rf ~/.gradle/daemon

# Set up Java environment (prefer Java 11)
if [ -d "/usr/lib/jvm/java-11-openjdk-amd64" ]; then
    export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
    echo "Using Java 11"
elif [ -d "/usr/lib/jvm/java-8-openjdk-amd64" ]; then
    export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
    echo "Using Java 8"
else
    echo "Error: Java 8 or 11 not found. Please install OpenJDK 11"
    exit 1
fi

export PATH=$JAVA_HOME/bin:$PATH

# Show Java version
echo "Java version:"
java -version

# Ensure we're using the full version
echo "Setting up full version..."
cp main_full.py main.py
cp buildozer_full.spec buildozer.spec

# Create bin directory if it doesn't exist
mkdir -p bin

# Build the APK
echo "Starting build process..."
echo "This may take 10-20 minutes on first run..."

# Try to build with buildozer
if buildozer android debug; then
    echo "Build successful!"
else
    echo "Buildozer failed, attempting gradle fixes..."
    
    # Navigate to the gradle project
    BUILD_DIR=".buildozer/android/platform/build-arm64-v8a/dists/dalleaiart"
    
    if [ -d "$BUILD_DIR" ]; then
        cd "$BUILD_DIR"
        
        # Fix 1: Update repositories
        echo "Fixing repositories..."
        find . -name "build.gradle" -type f -exec sed -i 's/jcenter()/mavenCentral()/g' {} \;
        
        # Fix 2: Update Gradle plugin version for compatibility
        echo "Updating Gradle plugin version..."
        sed -i 's/com.android.tools.build:gradle:[0-9.]\+/com.android.tools.build:gradle:7.2.2/g' build.gradle
        
        # Fix 3: Update Gradle wrapper version
        echo "Updating Gradle wrapper..."
        if [ -f "gradle/wrapper/gradle-wrapper.properties" ]; then
            sed -i 's/gradle-[0-9.]\+-all.zip/gradle-7.4.2-all.zip/g' gradle/wrapper/gradle-wrapper.properties
        fi
        
        # Fix 4: Add Google repository
        echo "Adding Google repository..."
        sed -i '/repositories {/a \        google()' build.gradle
        
        # Try to build again with gradle directly
        echo "Building with Gradle..."
        ./gradlew --no-daemon --stacktrace clean assembleDebug
        
        # Copy the APK to bin directory
        cd /home/mik/dalle_android
        APK_PATH=$(find .buildozer -name "*-debug.apk" -type f | head -n 1)
        
        if [ -f "$APK_PATH" ]; then
            cp "$APK_PATH" "bin/dalleaiart-debug.apk"
            echo "APK copied to bin/"
        fi
    else
        echo "Build directory not found!"
        exit 1
    fi
fi

# Check for APK
echo ""
echo "================================================"
if [ -f "bin/dalleaiart-debug.apk" ]; then
    echo "BUILD SUCCESSFUL!"
    echo "APK location: bin/dalleaiart-debug.apk"
    echo ""
    echo "APK Details:"
    ls -lh bin/dalleaiart-debug.apk
    echo ""
    echo "To install on device:"
    echo "  adb install -r bin/dalleaiart-debug.apk"
    echo ""
    echo "Or transfer the APK file to your device and install manually."
else
    echo "BUILD FAILED!"
    echo "Check the logs above for errors."
    
    # Show recent gradle errors if any
    if [ -f ".buildozer/android/platform/build-arm64-v8a/dists/dalleaiart/gradlew.log" ]; then
        echo ""
        echo "Recent Gradle errors:"
        tail -20 .buildozer/android/platform/build-arm64-v8a/dists/dalleaiart/gradlew.log
    fi
fi
echo "================================================"
