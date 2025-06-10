#!/bin/bash

echo "=== Complete Python 3 Compatibility Build Script ==="
echo "This script applies all necessary fixes for Python 2 vs Python 3 compatibility"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[STATUS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Step 1: Clean previous builds
print_status "Cleaning previous builds..."
rm -rf .buildozer/android/platform/build-*
rm -rf .buildozer/android/app
rm -rf build/
rm -rf bin/
rm -rf __pycache__

# Step 2: Create Python 3 compatible requirements
print_status "Creating Python 3 compatible requirements..."
cat > requirements_python3_complete.txt << 'EOF'
cython==3.0.10
kivy==2.3.0
kivymd==1.2.0
openai
requests
pillow
cryptography
pyjnius==1.6.1
buildozer
certifi
urllib3
EOF

# Step 3: Create setup.cfg for Cython
print_status "Creating setup.cfg for Cython language level..."
cat > setup.cfg << 'EOF'
[build_ext]
cython_directives = language_level=3
EOF

# Step 4: Create custom recipes directory
print_status "Creating custom recipes for pyjnius..."
mkdir -p recipes/pyjnius

cat > recipes/pyjnius/__init__.py << 'EOF'
from pythonforandroid.recipe import CythonRecipe
from pythonforandroid.util import current_directory
from os.path import join
import os


class PyjniusRecipe(CythonRecipe):
    version = '1.6.1'
    url = 'https://github.com/kivy/pyjnius/archive/{version}.tar.gz'
    name = 'pyjnius'
    depends = [('genericndkbuild', 'sdl2'), 'six']
    site_packages_name = 'jnius'
    
    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        # Force Python 3 language level
        env['CYTHON_DIRECTIVE'] = 'language_level=3'
        env['CYTHON_LANGUAGE_LEVEL'] = '3'
        return env
    
    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        # Patch source files for Python 3 compatibility
        build_dir = self.get_build_dir(arch.arch)
        
        # Create setup.cfg
        with current_directory(build_dir):
            with open('setup.cfg', 'w') as f:
                f.write('[build_ext]\n')
                f.write('cython_directives = language_level=3\n')
            
            # Patch jnius.pyx to add language level
            jnius_pyx = join('jnius', 'jnius.pyx')
            if os.path.exists(jnius_pyx):
                with open(jnius_pyx, 'r') as f:
                    content = f.read()
                
                if '# cython: language_level=' not in content:
                    content = '# cython: language_level=3\n' + content
                    with open(jnius_pyx, 'w') as f:
                        f.write(content)


recipe = PyjniusRecipe()
EOF

# Step 5: Create optimized buildozer spec
print_status "Creating optimized buildozer.spec..."
cat > buildozer_python3_complete.spec << 'EOF'
[app]
# App name and package info
title = DALL-E AI Art Generator
package.name = dalleaiart
package.domain = com.aiart
version = 1.0.0

# Source configuration
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,xml,txt
source.exclude_exts = spec
source.exclude_dirs = tests, bin, build, dist, __pycache__, .git, venv, .buildozer

# Application requirements - Python 3 compatible versions
requirements = python3==3.11,kivy==2.3.0,pillow,requests,certifi,urllib3,pyjnius==1.6.1,cython==3.0.10,six

# Orientation and permissions
orientation = portrait
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE

# Android configuration
android.api = 33
android.minapi = 26
android.ndk = 25b
android.accept_sdk_license = True
android.features = android.hardware.touchscreen
android.archs = arm64-v8a,armeabi-v7a

# Build configuration
android.release = True
android.gradle_dependencies = androidx.security:security-crypto:1.1.0-alpha06

# Use local recipes
p4a.local_recipes = ./recipes

# Python for Android configuration
p4a.bootstrap = sdl2

# Presplash and icon
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png

[buildozer]
# Build configuration
log_level = 2
warn_on_root = 1
build_dir = ./build
bin_dir = ./bin

# Specify python3 explicitly
android.python_executable = python3
EOF

# Step 6: Create environment setup script
print_status "Creating environment setup script..."
cat > setup_build_env.sh << 'EOF'
#!/bin/bash
# Set up environment for Python 3 compatibility
export CYTHON_DIRECTIVE="language_level=3"
export CYTHON_LANGUAGE_LEVEL="3"
export KIVY_WINDOW=""
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Use Python 3 explicitly
export PYTHON_FOR_ANDROID_PY3=1

echo "Build environment configured for Python 3"
EOF
chmod +x setup_build_env.sh

# Step 7: Update virtual environment
print_status "Checking virtual environment..."
if [ ! -d "venv" ]; then
    print_warning "Creating new virtual environment..."
    python3 -m venv venv
fi

print_status "Activating virtual environment and installing requirements..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements_python3_complete.txt

# Step 8: Set environment and build
print_status "Setting up build environment..."
source setup_build_env.sh

# Step 9: Run buildozer
print_status "Starting buildozer build process..."
print_warning "This may take 15-30 minutes on first run..."

buildozer -v android clean
buildozer -v android debug -s buildozer_python3_complete.spec

# Check if build was successful
if [ -f "bin/*.apk" ]; then
    print_status "Build completed successfully!"
    print_status "APK file(s) created in bin/ directory:"
    ls -la bin/*.apk
else
    print_error "Build failed. Check the output above for errors."
    print_warning "Common issues:"
    print_warning "1. Missing dependencies - check requirements"
    print_warning "2. Network issues - check internet connection"
    print_warning "3. SDK/NDK issues - check Android SDK installation"
fi

echo ""
print_status "Build process completed!"