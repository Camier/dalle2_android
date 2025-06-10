#!/bin/bash

# Exit on error
set -e

echo "=== Setting up environment ==="
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
export PYJNIUS_PYTHON_VERSION=3
export ANDROID_PYJNIUS_PYTHON_VERSION=3

# Additional environment variables to help with builds
export P4A_RELEASE=true
export P4A_BUILD_CACHE_DIR=/home/mik/.buildozer/android/platform/build-arm64-v8a
export ANDROID_HOME=/home/mik/.buildozer/android/platform/android-sdk
export ANDROID_SDK_ROOT=$ANDROID_HOME

echo "=== Cleaning problematic directories ==="
# Clean the external directory that causes SDL2_image prebuild to fail
rm -rf .buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds/sdl2/jni/SDL2_image/external

# Clean any partial downloads
find .buildozer/android/platform/build-arm64-v8a/packages -name "*.part" -delete 2>/dev/null || true

echo "=== Activating virtual environment ==="
source venv/bin/activate

# Create a marker file to help track SDL2_image prebuild
echo "=== Creating SDL2_image external directory pre-emptively ==="
mkdir -p .buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds/sdl2/jni/SDL2_image/external
mkdir -p .buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds/sdl2/jni/SDL2_image/external/jpeg
touch .buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds/sdl2/jni/SDL2_image/external/jpeg/.gitkeep

echo "=== Starting build ==="
buildozer android debug 2>&1 | tee build_final_output.log