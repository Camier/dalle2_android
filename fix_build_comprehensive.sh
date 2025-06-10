#!/bin/bash

echo "=== Comprehensive Build Fix for DALL-E Android App ==="
echo "This script addresses HTTP 404 errors and dependency issues"

# Function to display errors and solutions
show_error_solution() {
    echo -e "\n❌ ERROR IDENTIFIED: $1"
    echo -e "✅ SOLUTION: $2\n"
}

# 1. Fix SDL2 version issues
show_error_solution \
    "SDL2_image-2.0.5 returns HTTP 404 error" \
    "Removing specific SDL2 version requirements to use buildozer defaults"

# 2. Clean build environment
echo "🧹 Step 1: Cleaning build environment..."
buildozer android clean
rm -rf .buildozer/android/platform/build-*/packages/sdl2_*
rm -rf .buildozer/android/platform/build-*/build/other_builds/sdl2_*
rm -rf ~/.gradle/daemon/
pkill -f gradle || true

# 3. Fix Java version if needed
echo "☕ Step 2: Checking Java version..."
java_version=$(java -version 2>&1 | head -n 1)
echo "Current Java: $java_version"
if [[ $java_version == *"21"* ]]; then
    show_error_solution \
        "Java 21 may cause Gradle issues" \
        "Consider using Java 11 with: sudo update-alternatives --config java"
fi

# 4. Update buildozer and p4a
echo "📦 Step 3: Updating build tools..."
pip install --upgrade buildozer
pip install --upgrade python-for-android

# 5. Use the fixed buildozer.spec
echo "📝 Step 4: Using fixed buildozer.spec..."
cp buildozer.spec buildozer.spec.original
cp buildozer_fixed.spec buildozer.spec

# 6. Alternative: Try with python-for-android directly
echo "🔧 Step 5: Alternative build method available..."
cat > build_with_p4a.sh << 'EOF'
#!/bin/bash
# Direct p4a build without specific SDL2 versions
p4a create --dist_name=dalleaiart \
    --bootstrap=sdl2 \
    --requirements=python3,kivy==2.3.0,kivymd,pillow,requests,certifi,urllib3,cryptography,pycryptodome,openai,pyjnius,android \
    --arch=arm64-v8a \
    --arch=armeabi-v7a \
    --permission=INTERNET \
    --permission=VIBRATE \
    --permission=ACCESS_NETWORK_STATE \
    --package=com.aiart.dalleaiart \
    --name="DALL-E AI Art" \
    --version=1.0.0 \
    --orientation=portrait
EOF
chmod +x build_with_p4a.sh

# 7. Create a minimal test build
echo "🧪 Step 6: Creating minimal test configuration..."
cat > buildozer_minimal_test.spec << 'EOF'
[app]
title = DALL-E Test
package.name = dalletest
package.domain = com.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# Absolute minimal requirements
requirements = python3,kivy

android.permissions = INTERNET
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

[buildozer]
log_level = 2
warn_on_root = 1
EOF

# 8. Show build options
echo -e "\n📋 BUILD OPTIONS:"
echo "1. Run: ./fix_sdl2_build.sh          # Uses updated main buildozer.spec"
echo "2. Run: buildozer android debug      # Uses the fixed spec we just created"
echo "3. Run: ./build_with_p4a.sh          # Direct p4a build (alternative)"
echo "4. Test: buildozer -v android debug  # Verbose output for debugging"
echo ""
echo "For minimal test build:"
echo "   cp buildozer_minimal_test.spec buildozer.spec && buildozer android debug"

# 9. Additional troubleshooting
echo -e "\n🔍 TROUBLESHOOTING TIPS:"
echo "- If gradle daemon fails: rm -rf ~/.gradle && pkill -f gradle"
echo "- If download fails: Check your internet connection and proxy settings"
echo "- If Java issues: Use Java 11 instead of newer versions"
echo "- For clean slate: rm -rf .buildozer && buildozer android debug"

echo -e "\n✨ Fix script completed! Choose a build option above to proceed."