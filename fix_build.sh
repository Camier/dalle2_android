#!/bin/bash
cd /home/mik/dalle_android

# Activate virtual environment
source venv/bin/activate

# Set Java 8 specifically for this build
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/usr/lib/wsl/lib

# Verify Java version
echo "Using Java version:"
/bin/java -version

# Clean previous build artifacts
echo "Cleaning build artifacts..."
rm -rf .buildozer/android/platform/build-arm64-v8a_armeabi-v7a/dists
rm -rf .buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/gradle_cache

# Fix gradle permissions if needed
if [ -f .buildozer/android/platform/build-arm64-v8a_armeabi-v7a/dists/dalleimages/gradlew ]; then
    chmod +x .buildozer/android/platform/build-arm64-v8a_armeabi-v7a/dists/dalleimages/gradlew
fi

# Build with verbose output
echo "Starting build..."
buildozer -v android debug

