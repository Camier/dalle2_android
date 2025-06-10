#!/bin/bash
# Final comprehensive build solution for DALL-E Android App

set -e

echo "================================================"
echo "DALL-E AI Art - Final Build Solution"
echo "================================================"

# 1. Clean everything
echo "Step 1: Complete cleanup..."
rm -rf .buildozer/android/platform/build-*
rm -rf .buildozer/android/app
rm -rf build
rm -rf bin
rm -rf __pycache__
rm -rf .buildozer/android/platform/build-*/packages
rm -rf .buildozer/android/platform/build-*/build

# 2. Ensure Java 11 is being used
echo "Step 2: Checking Java version..."
java -version
echo "Note: Java 11 is recommended. If you have Java 21+, it may cause issues."

# 3. Activate virtual environment
echo "Step 3: Setting up Python environment..."
source venv/bin/activate

# Ensure Cython is at the right version
pip install --force-reinstall cython==0.29.37

# 4. Create minimal buildozer.spec for initial test
echo "Step 4: Creating optimized buildozer.spec..."
cat > buildozer.spec << 'EOF'
[app]
title = DALL-E AI Art
package.name = dalleaiart
package.domain = com.aiart
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,ttf,otf,xml
version = 1.0.0

# Minimal requirements first
requirements = python3,kivy==2.3.0,kivymd,pillow,requests,certifi,urllib3,pyjnius,android

# Orientation
orientation = portrait

# Android configuration
android.permissions = INTERNET,VIBRATE,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True
android.archs = arm64-v8a

# Build settings
android.release = False
log_level = 2
warn_on_root = 1

# Local recipes
p4a.local_recipes = ./recipes

# Optimization
android.optimize_python = 1

# Enable AndroidX
android.enable_androidx = True
android.gradle_dependencies = androidx.appcompat:appcompat:1.4.1,com.google.android.material:material:1.5.0
android.add_gradle_repositories = google(),mavenCentral()

# Assets
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png

[buildozer]
android.skip_update = False
EOF

# 5. Update pyjnius recipe for Python 3
echo "Step 5: Updating pyjnius recipe..."
mkdir -p recipes/pyjnius
cat > recipes/pyjnius/__init__.py << 'EOF'
from pythonforandroid.recipe import CythonRecipe
from pythonforandroid import logger
import sh
import os
from os.path import join

class PyjniusRecipe(CythonRecipe):
    version = '1.4.2'
    url = 'https://github.com/kivy/pyjnius/archive/{version}.tar.gz'
    name = 'pyjnius'
    depends = ['setuptools', 'six']
    site_packages_name = 'jnius'
    
    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['PYTHON'] = self.ctx.hostpython
        return env
    
    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        # Fix for Python 3
        build_dir = self.get_build_dir(arch.arch)
        
        # Patch setup.py to force language_level=3
        setup_py = join(build_dir, 'setup.py')
        if os.path.exists(setup_py):
            with open(setup_py, 'r') as f:
                content = f.read()
            
            # Add Cython directive
            if 'from Cython.Build import cythonize' in content:
                content = content.replace(
                    'from Cython.Build import cythonize',
                    'from Cython.Build import cythonize\nimport Cython\nCython.Compiler.Options.language_level = 3'
                )
                
            with open(setup_py, 'w') as f:
                f.write(content)

recipe = PyjniusRecipe()
EOF

# 6. Create pre-build patch script
echo "Step 6: Creating pre-build patches..."
cat > patch_builds.sh << 'EOF'
#!/bin/bash
# Fix any Python 2/3 compatibility issues
find .buildozer -name "*.pyx" -o -name "*.pxi" | while read file; do
    if grep -q '\blong\b' "$file" 2>/dev/null; then
        echo "Patching $file..."
        sed -i 's/\blong\b/int/g' "$file"
    fi
done
EOF
chmod +x patch_builds.sh

# 7. Set environment variables
echo "Step 7: Setting environment variables..."
export CYTHON_DIRECTIVE="language_level=3str"
export ANDROID_HOME=$HOME/.buildozer/android/platform/android-sdk
export ANDROID_NDK_HOME=$HOME/.buildozer/android/platform/android-ndk-r25b

# 8. Build the APK
echo "================================================"
echo "Starting build process..."
echo "================================================"

# Run with increased timeout and verbose output
timeout 30m buildozer -v android debug 2>&1 | tee build_final.log

# 9. Check results
if [ -f bin/*.apk ]; then
    echo "================================================"
    echo "BUILD SUCCESSFUL!"
    echo "================================================"
    ls -la bin/*.apk
    echo ""
    echo "APK built successfully!"
    echo "Install with: adb install -r bin/*.apk"
else
    echo "================================================"
    echo "BUILD FAILED - Analyzing..."
    echo "================================================"
    
    # Check for common issues
    if grep -q "404: Not Found" build_final.log; then
        echo "ERROR: Some dependencies could not be downloaded."
        echo "This might be a temporary network issue or version mismatch."
    fi
    
    if grep -q "error: Microsoft Visual C++ 14.0" build_final.log; then
        echo "ERROR: Missing compiler dependencies."
    fi
    
    if grep -q "No module named" build_final.log; then
        echo "ERROR: Missing Python modules."
    fi
    
    echo ""
    echo "Check build_final.log for detailed error information."
    echo ""
    echo "Common fixes:"
    echo "1. Run: rm -rf .buildozer && ./build_final_solution.sh"
    echo "2. Check network connection"
    echo "3. Try with a single architecture: android.archs = arm64-v8a"
fi