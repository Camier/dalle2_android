#!/bin/bash

# Production Release Build Script for DALL-E AI Art Generator
# This script builds a production-ready APK with all optimizations

set -e  # Exit on error

echo "=========================================="
echo "DALL-E AI Art Generator - Production Build"
echo "=========================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check prerequisites
echo "Checking prerequisites..."

# Check if buildozer is installed
if ! command -v buildozer &> /dev/null; then
    print_error "Buildozer is not installed. Please install it first."
    exit 1
fi

# Check if keystore exists
if [ ! -f "dalle-ai-art-release.keystore" ]; then
    print_warning "Release keystore not found. Generating new keystore..."
    keytool -genkey -v -keystore dalle-ai-art-release.keystore \
        -alias dalleaiart -keyalg RSA -keysize 2048 -validity 10000 \
        -storepass changeme -keypass changeme \
        -dname "CN=DALL-E AI Art Generator, OU=Mobile Apps, O=AI Art, L=City, ST=State, C=US"
    print_warning "IMPORTANT: Change the keystore passwords in buildozer.spec!"
fi

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf .buildozer build dist bin
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Verify required files
print_status "Verifying required files..."
required_files=(
    "main.py"
    "buildozer.spec"
    "requirements.txt"
    "assets/icon.png"
    "assets/presplash.png"
    "res/xml/network_security_config.xml"
    "proguard-rules.pro"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file missing: $file"
        exit 1
    fi
done

# Update buildozer.spec with current date in version
print_status "Updating build metadata..."
BUILD_DATE=$(date +%Y%m%d)
sed -i.bak "s/# Build date.*/# Build date: $BUILD_DATE/" buildozer.spec || true

# Create build info
cat > build_info.json << EOF
{
    "build_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "build_type": "production",
    "version": "1.0.0",
    "api_level": "33",
    "min_api": "26",
    "architectures": ["arm64-v8a", "armeabi-v7a"]
}
EOF

# Set production environment variables
export ANDROID_HOME=${ANDROID_HOME:-$HOME/.buildozer/android/platform/android-sdk}
export ANDROID_NDK_HOME=${ANDROID_NDK_HOME:-$HOME/.buildozer/android/platform/android-ndk-r25b}
export BUILDOZER_LOG_LEVEL=2
export P4A_RELEASE=1

# Build the APK
print_status "Building production APK..."
print_warning "This may take 10-30 minutes on first run..."

# Run buildozer with error handling
if buildozer android release 2>&1 | tee build_production.log; then
    print_status "Build completed successfully!"
else
    print_error "Build failed. Check build_production.log for details."
    exit 1
fi

# Find the generated APK
APK_PATH=$(find bin -name "*-release.apk" -o -name "*-release-unsigned.apk" | head -n 1)

if [ -z "$APK_PATH" ]; then
    print_error "No APK found in bin directory"
    exit 1
fi

print_status "APK generated: $APK_PATH"

# Verify APK
print_status "Verifying APK..."

# Check APK size
APK_SIZE=$(du -h "$APK_PATH" | cut -f1)
print_status "APK size: $APK_SIZE"

# Extract APK info
if command -v aapt &> /dev/null; then
    print_status "APK details:"
    aapt dump badging "$APK_PATH" | grep -E "package:|version|targetSdk|minSdk" || true
fi

# Check if APK is signed
if command -v jarsigner &> /dev/null; then
    if jarsigner -verify "$APK_PATH" &> /dev/null; then
        print_status "APK is signed correctly"
    else
        print_warning "APK signature verification failed"
    fi
fi

# Generate checksums
print_status "Generating checksums..."
sha256sum "$APK_PATH" > "$APK_PATH.sha256"
print_status "SHA-256: $(cat $APK_PATH.sha256)"

# Create release directory
RELEASE_DIR="releases/v1.0.0-$(date +%Y%m%d)"
mkdir -p "$RELEASE_DIR"

# Copy release files
cp "$APK_PATH" "$RELEASE_DIR/"
cp "$APK_PATH.sha256" "$RELEASE_DIR/"
cp build_info.json "$RELEASE_DIR/"
cp build_production.log "$RELEASE_DIR/"

# Create release notes
cat > "$RELEASE_DIR/RELEASE_NOTES.md" << EOF
# DALL-E AI Art Generator v1.0.0

## Release Date
$(date +"%B %d, %Y")

## Build Information
- Build Type: Production Release
- API Level: 33 (Android 13)
- Minimum API: 26 (Android 8.0)
- Architectures: arm64-v8a, armeabi-v7a
- APK Size: $APK_SIZE

## Features
- AI-powered image generation using DALL-E
- Secure API key storage
- Image history and gallery
- Multiple image size options
- Batch generation support
- Privacy-focused design

## Security Features
- Certificate pinning for API communications
- Encrypted storage for sensitive data
- ProGuard obfuscation
- Network security configuration
- Age verification

## Checksum
$(cat $APK_PATH.sha256)

## Installation
1. Enable "Install from unknown sources" in Android settings
2. Download the APK file
3. Verify the SHA-256 checksum
4. Tap the APK file to install

## Requirements
- Android 8.0 or higher
- Active internet connection
- OpenAI API key
EOF

print_status "Release package created in: $RELEASE_DIR"

# Final summary
echo
echo "=========================================="
echo "BUILD SUMMARY"
echo "=========================================="
print_status "APK Location: $APK_PATH"
print_status "APK Size: $APK_SIZE"
print_status "Release Directory: $RELEASE_DIR"
echo
print_warning "Next steps:"
echo "  1. Test the APK thoroughly on multiple devices"
echo "  2. Update keystore passwords if using default values"
echo "  3. Sign up for Google Play Console if distributing there"
echo "  4. Prepare store listing materials"
echo "  5. Consider generating an AAB for Play Store"
echo
print_status "Build completed successfully!"