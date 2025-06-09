# Building DALL-E Android APK

## Overview
This guide covers building the DALL-E AI Art Generator Android app with all features including the new batch generation functionality.

## Prerequisites

### System Requirements
- Ubuntu/WSL2 (tested on Ubuntu 22.04)
- Python 3.8+ (tested with 3.10)
- At least 4GB RAM
- 10GB free disk space

### Required Software
```bash
# Install Java (OpenJDK 11 recommended)
sudo apt update
sudo apt install openjdk-11-jdk

# Install build dependencies
sudo apt install python3-pip python3-venv git
sudo apt install autoconf libtool pkg-config
sudo apt install libssl-dev libffi-dev python3-dev
```

## Quick Start

### Option 1: Optimized Build (Recommended)
```bash
cd ~/dalle_android
./build_optimized.sh
```

### Option 2: Full Feature Build
```bash
cd ~/dalle_android
./build_full_app.sh
```

### Option 3: Manual Build
```bash
cd ~/dalle_android
source venv/bin/activate

# Set Java environment
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# Clean and build
buildozer android clean
buildozer android debug
```

## Build Scripts

### 1. `build_optimized.sh`
- Uses minimal configuration first
- Automatically applies gradle fixes
- Progressive build approach
- Best success rate

### 2. `build_full_app.sh`
- Builds with all features enabled
- Comprehensive error handling
- Detailed logging

### 3. `fix_gradle.sh`
- Standalone gradle fix script
- Can be run if build fails
- Fixes common repository and version issues

## Common Issues and Solutions

### Issue 1: Java Version Mismatch
**Error**: `Unsupported class file major version`

**Solution**:
```bash
# Use Java 11 (most compatible)
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
```

### Issue 2: Gradle Build Failures
**Error**: `Could not resolve dependencies`

**Solution**:
```bash
# Run the gradle fix script
./fix_gradle.sh

# Clear gradle cache
rm -rf ~/.gradle/caches/
rm -rf ~/.gradle/daemon/
```

### Issue 3: JCenter Repository Deprecated
**Error**: `Could not resolve all artifacts`

**Solution**: Automatically handled by build scripts, or manually:
```bash
find .buildozer -name "build.gradle" -exec sed -i 's/jcenter()/mavenCentral()/g' {} \;
```

### Issue 4: SDK License Not Accepted
**Error**: `You have not accepted the license agreements`

**Solution**: Set in buildozer.spec:
```ini
android.accept_sdk_license = True
```

## Build Configuration

### Buildozer Spec Overview
```ini
[app]
title = DALL-E AI Art Generator
package.name = dalleaiart
package.domain = com.camier
version = 1.0

# Features included:
# - Single image generation
# - Batch generation (1-4 images)
# - Gallery with zoom/pan
# - History tracking
# - Share functionality
# - Settings management

requirements = python3,kivy==2.2.1,kivymd==1.1.1,requests,pillow

android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 21
android.arch = arm64-v8a
```

## APK Installation

### Method 1: USB Debugging
1. Enable Developer Options on Android device
2. Enable USB Debugging
3. Connect device via USB
4. Install APK:
```bash
adb install -r bin/dalleai-debug.apk
```

### Method 2: Direct Transfer
1. Copy APK to device (USB, email, cloud storage)
2. Enable "Install from unknown sources" in Settings
3. Open APK file on device
4. Follow installation prompts

### Method 3: Local Web Server
```bash
# Start server in project directory
cd ~/dalle_android
python3 -m http.server 8000

# On device browser, visit:
# http://[your-computer-ip]:8000/bin/
# Download and install APK
```

## Build Output
- Debug APK: `bin/dalleai-debug.apk`
- Size: ~40-50MB
- Architecture: ARM64-v8a
- Min Android: 5.0 (API 21)
- Target Android: 12 (API 31)

## Troubleshooting

### Check Build Logs
```bash
# Buildozer logs
cat .buildozer/logs/last_build.log

# Gradle logs
find .buildozer -name "*.log" -type f
```

### Clean Build
```bash
# Full clean
rm -rf .buildozer/
rm -rf bin/
rm -rf ~/.gradle/

# Then rebuild
./build_optimized.sh
```

### Verify Environment
```bash
# Check Java
java -version  # Should show 11.x.x

# Check Python
python3 --version  # Should be 3.8+

# Check buildozer
buildozer --version
```

## Next Steps
After successful build:
1. Test all features on device
2. Generate signed APK for release
3. Consider ProGuard for optimization
4. Test on multiple devices/Android versions

## Support
For issues specific to this app:
- Check `docs/` folder for feature documentation
- Review build logs carefully
- Ensure all prerequisites are installed
