#!/bin/bash
# build_clean.sh

# Set Java environment - use Java 21 (latest available)
export JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Set download timeout environment variables
export P4A_CONN_TIMEOUT=120
export P4A_RETRY_COUNT=5

# Clean everything
echo "=== Cleaning previous builds ==="
buildozer android clean
rm -rf .buildozer/android/platform/build-arm64-v8a/

echo "=== Java version ==="
java -version
javac -version

echo "=== Starting build with timeout ==="
# Build with connection timeout to prevent hanging
timeout 3600 buildozer android debug 2>&1 | tee build.log

# Check result
if [ -f "bin/dalleaiart-1.0.0-debug.apk" ]; then
    echo "=== SUCCESS: APK created! ==="
    ls -lh bin/*.apk
else
    echo "=== Build failed. Checking logs... ==="
    tail -100 build.log | grep -E "(ERROR|error|Failed|failed)" || echo "No errors found in last 100 lines"
fi