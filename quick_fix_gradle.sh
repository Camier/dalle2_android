#!/bin/bash
cd /home/mik/dalle_android

# Kill any existing gradle processes
echo "Stopping gradle daemons..."
pkill -f gradle || true

# Clean gradle cache
echo "Cleaning gradle cache..."
rm -rf ~/.gradle/daemon
rm -rf ~/.gradle/caches

# Clean buildozer gradle cache
rm -rf .buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/gradle_cache

# Set memory limits for gradle
export GRADLE_OPTS="-Xmx2048m -XX:MaxPermSize=512m"

# Use Java 8
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

# Activate venv
source venv/bin/activate

# Try building again with gradle in offline mode to avoid network issues
echo "Starting build with fixed gradle settings..."
buildozer android debug

