#!/bin/bash

echo "=== Offline Build Script ==="

# Set Java environment
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Python 3 environment
export PYJNIUS_PYTHON_VERSION=3
export ANDROID_PYJNIUS_PYTHON_VERSION=3

# Increase timeouts
export P4A_CONN_TIMEOUT=300
export P4A_RETRY_COUNT=10

# Force offline mode if packages exist
export P4A_OFFLINE_MODE=1

echo "=== Starting build ==="
buildozer android debug 2>&1 | tee build_offline.log

if [ -f "bin/dalleaiart-1.0.0-debug.apk" ]; then
    echo "=== SUCCESS: APK created! ==="
    ls -lh bin/*.apk
else
    echo "=== Build failed ==="
fi