#!/bin/bash

# Exit on error
set -e

echo "=== Setting up environment ==="
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
export PYJNIUS_PYTHON_VERSION=3
export ANDROID_PYJNIUS_PYTHON_VERSION=3

echo "=== Cleaning build directories ==="
rm -rf .buildozer/android/platform/build-arm64-v8a/dists
rm -rf .buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds
rm -rf .buildozer/android/platform/build-arm64-v8a/build/other_builds

echo "=== Activating virtual environment ==="
source venv/bin/activate

echo "=== Starting minimal build ==="
buildozer android debug 2>&1 | tee build_minimal.log

echo "=== Build complete ==="
if [ -f "bin/dalleaiart-1.0.0-debug.apk" ]; then
    echo "SUCCESS: APK created!"
    ls -lh bin/*.apk
else
    echo "Build failed. Checking logs..."
    tail -100 build_minimal.log | grep -E "(ERROR|error|Failed|failed)" || echo "No errors found in last 100 lines"
fi