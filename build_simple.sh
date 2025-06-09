#!/bin/bash
cd /home/mik/dalle_android

# Backup original files
cp main.py main_original.py
cp buildozer.spec buildozer_original.spec

# Use simplified versions
cp main_simple.py main.py
cp buildozer_simple.spec buildozer.spec

# Clean everything
rm -rf .buildozer
rm -rf bin

# Kill gradle daemons
pkill -f gradle || true
rm -rf ~/.gradle/daemon

# Set Java 8
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/usr/lib/wsl/lib

# Activate venv
source venv/bin/activate

# Build
echo "Building simplified APK..."
buildozer android debug

# Restore original files
cp main_original.py main.py
cp buildozer_original.spec buildozer.spec

echo "Build complete! Check bin/ directory for APK"
