#!/bin/bash

# Exit on error
set -e

echo "=== Setting up environment ==="
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
export PYJNIUS_PYTHON_VERSION=3
export ANDROID_PYJNIUS_PYTHON_VERSION=3

# Verify Java
echo "Java version:"
$JAVA_HOME/bin/java -version
$JAVA_HOME/bin/javac -version

echo "=== Cleaning previous builds ==="
rm -rf .buildozer
rm -rf recipes
rm -rf __pycache__
rm -f .buildozer.log

echo "=== Installing Cython in virtual environment ==="
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install cython==0.29.36
pip install buildozer

echo "=== Creating clean buildozer.spec ==="
cat > buildozer.spec << 'EOF'
[app]
title = DALL-E AI Art
package.name = dalleaiart
package.domain = com.aiart
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0

# Requirements - order matters!
requirements = python3,kivy==2.3.0,pyjnius,android,openai,pillow,requests,certifi,chardet,idna,urllib3

# Android configuration
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

# Build settings
android.release = False
android.debug = True
log_level = 2
warn_on_root = 0

# Gradle configuration
android.gradle_dependencies = androidx.appcompat:appcompat:1.4.1
android.enable_androidx = True
android.add_gradle_repositories = google(),mavenCentral()

[buildozer]
# Prevent re-downloading
android.skip_update = False
android.auto_update_sdk = False
EOF

echo "=== Starting build ==="
buildozer android debug

echo "=== Build complete ==="