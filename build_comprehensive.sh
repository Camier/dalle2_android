#!/bin/bash
# Comprehensive build script for DALL-E Android App
# This applies all fixes and builds a complete, fully functional APK

set -e

echo "================================================"
echo "DALL-E AI Art - Comprehensive APK Build"
echo "================================================"

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Set Python 3 environment variables
export CYTHON_DIRECTIVE="language_level=3"
export CYTHON_LANGUAGE_LEVEL=3
export PYTHONIOENCODING=utf-8

# Create prebuild hook
echo "Creating prebuild hook..."
cat > prebuild.sh << 'EOF'
#!/bin/bash
# Prebuild hook to fix Python 3 compatibility issues
echo "Running prebuild fixes..."

# Find and patch pyjnius files
find .buildozer/android/platform/build-* -name "*.pyx" -o -name "*.pxi" | while read file; do
    if grep -q '\blong\b' "$file" 2>/dev/null; then
        echo "Patching $file for Python 3 compatibility..."
        sed -i 's/\blong\b/int/g' "$file"
        sed -i 's/basestring/str/g' "$file"
    fi
done

# Create setup.cfg for Cython directives
find .buildozer/android/platform/build-* -name "setup.py" | while read setup; do
    dir=$(dirname "$setup")
    if [[ "$dir" == *"pyjnius"* ]]; then
        echo "[build_ext]" > "$dir/setup.cfg"
        echo "cython-directives=language_level=3" >> "$dir/setup.cfg"
    fi
done
EOF
chmod +x prebuild.sh

# Update buildozer to include prebuild hook
echo "Updating buildozer.spec with prebuild hook..."
if ! grep -q "p4a.prebuild_cmd" buildozer.spec; then
    sed -i '/p4a.local_recipes/a p4a.prebuild_cmd = ./prebuild.sh' buildozer.spec
fi

# Create network security config
echo "Creating network security configuration..."
mkdir -p res/xml
cat > res/xml/network_security_config.xml << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">api.openai.com</domain>
        <pin-set expiration="2025-01-01">
            <pin digest="SHA-256">++MBgDH5hZVr4KvMBMb3e/GSh+KhOPdWE9hQJ9KXw=</pin>
            <pin digest="SHA-256">f0HkCwl4ByDC+M8piHfRsoSqGK/7cH8OTpVAQ9DH3HQ=</pin>
        </pin-set>
    </domain-config>
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </base-config>
</network-security-config>
EOF

# Add network security config to buildozer.spec
if ! grep -q "android.add_src" buildozer.spec; then
    echo "android.add_src = ./res" >> buildozer.spec
fi

# Create app icons if they don't exist
echo "Checking app assets..."
if [ ! -f assets/icon.png ]; then
    echo "Creating placeholder icon..."
    python3 << 'EOF'
from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs('assets', exist_ok=True)

# Create icon
icon = Image.new('RGBA', (512, 512), (33, 150, 243, 255))
draw = ImageDraw.Draw(icon)
# Add text
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
except:
    font = None
draw.text((256, 256), "DALL-E", fill=(255, 255, 255), anchor="mm", font=font)
icon.save('assets/icon.png')

# Create presplash
presplash = Image.new('RGBA', (512, 512), (255, 255, 255, 255))
draw = ImageDraw.Draw(presplash)
draw.text((256, 256), "DALL-E AI Art", fill=(33, 150, 243), anchor="mm", font=font)
presplash.save('assets/presplash.png')
EOF
fi

# Final buildozer.spec check
echo "Finalizing buildozer.spec..."
python3 << 'EOF'
import re

with open('buildozer.spec', 'r') as f:
    content = f.read()

# Ensure all required settings are present
updates = []

# Add keystore configuration if missing
if 'android.release' in content and 'android.keystore' not in content:
    updates.append(('android.release = True', 
                   'android.release = True\nandroid.keystore = dalle-ai-art-release.keystore\nandroid.keystore_alias = dalleaiart'))

# Add gradle settings if missing
if 'android.gradle_dependencies' in content and 'android.add_gradle_maven_dependencies' not in content:
    updates.append(('android.gradle_dependencies', 
                   'android.add_gradle_maven_dependencies = com.google.crypto.tink:tink-android:1.7.0\nandroid.gradle_dependencies'))

# Apply updates
for old, new in updates:
    content = content.replace(old, new)

with open('buildozer.spec', 'w') as f:
    f.write(content)
EOF

# Build the APK
echo "================================================"
echo "Starting APK build..."
echo "================================================"

# Clean any partial builds
rm -rf .buildozer/android/platform/build-*/build/other_builds/pyjnius*

# Run buildozer with verbose output
buildozer -v android debug

# Check if build succeeded
if [ -f bin/*.apk ]; then
    echo "================================================"
    echo "BUILD SUCCESSFUL!"
    echo "================================================"
    echo "APK location: $(ls bin/*.apk)"
    echo ""
    echo "Next steps:"
    echo "1. Install on device: adb install -r bin/*.apk"
    echo "2. Or transfer manually to your Android device"
    echo ""
    echo "For production release:"
    echo "1. Update keystore passwords in buildozer.spec"
    echo "2. Run: buildozer android release"
else
    echo "================================================"
    echo "BUILD FAILED"
    echo "================================================"
    echo "Check the logs above for errors"
    echo "Common fixes:"
    echo "1. Run ./fix_build_issues.sh again"
    echo "2. Check Java version: java -version (should be 11)"
    echo "3. Clean and retry: rm -rf .buildozer && ./build_comprehensive.sh"
fi