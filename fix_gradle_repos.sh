#!/bin/bash
echo "Fixing deprecated jcenter() repository..."

cd .buildozer/android/platform/build-arm64-v8a/dists/dallesimple

# Backup original
cp build.gradle build.gradle.bak

# Replace jcenter with mavenCentral
sed -i 's/jcenter()/mavenCentral()/g' build.gradle

echo "Updated build.gradle:"
cat build.gradle | head -20

echo ""
echo "Now retrying gradle build..."
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export ANDROID_HOME=/home/mik/.buildozer/android/platform/android-sdk

./gradlew --no-daemon clean assembleDebug
