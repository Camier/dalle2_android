#!/bin/bash

# Fix Python 2 vs Python 3 compatibility issues in buildozer build
echo "Fixing Python 2 vs Python 3 compatibility issues..."

# Create a custom recipe for pyjnius with Python 3 language level
mkdir -p recipes
mkdir -p recipes/pyjnius

# Create a custom pyjnius recipe that forces Python 3 language level
cat > recipes/pyjnius/__init__.py << 'EOF'
from pythonforandroid.recipe import CythonRecipe
from pythonforandroid.util import current_directory
from os.path import join
import sh


class PyjniusRecipe(CythonRecipe):
    version = '1.6.1'
    url = 'https://github.com/kivy/pyjnius/archive/{version}.tar.gz'
    name = 'pyjnius'
    depends = [('genericndkbuild', 'sdl2'), 'six']
    site_packages_name = 'jnius'
    
    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        # Force Cython to use Python 3 language level
        env['CYTHON_DIRECTIVE'] = 'language_level=3'
        return env
    
    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        # Create setup.cfg to force Python 3 language level
        with current_directory(self.get_build_dir(arch.arch)):
            with open('setup.cfg', 'w') as f:
                f.write('[build_ext]\n')
                f.write('cython_directives = language_level=3\n')


recipe = PyjniusRecipe()
EOF

# Update buildozer.spec to use custom recipes
echo "Updating buildozer.spec to use custom recipes..."
cp buildozer.spec buildozer.spec.backup

# Create a new buildozer.spec with p4a.local_recipes
cat > buildozer_python3_fix.spec << 'EOF'
[app]
# App name
title = DALL-E AI Art Generator

# Package name
package.name = dalleaiart

# Package domain
package.domain = com.aiart

# Source code where the main.py lives
source.dir = .

# Source files to include
source.include_exts = py,png,jpg,kv,atlas,json,xml

# Source files to exclude
source.exclude_exts = spec

# List of directory to exclude
source.exclude_dirs = tests, bin, build, dist, __pycache__, .git, venv

# Application versioning
version = 1.0.0

# Application requirements - Updated with specific versions
requirements = python3,kivy==2.3.0,pillow,requests,certifi,urllib3,pyjnius==1.6.1,cython==3.0.0

# Supported orientations
orientation = portrait

# Android specific
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE

# Android API target
android.api = 33
android.minapi = 26
android.ndk = 25b

# Android specific features
android.features = android.hardware.touchscreen

# Android arch
android.archs = arm64-v8a,armeabi-v7a

# Release configuration
android.release = True

# Gradle dependencies for security
android.gradle_dependencies = androidx.security:security-crypto:1.1.0-alpha06

# Use local recipes directory
p4a.local_recipes = ./recipes

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
build_dir = ./build

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
bin_dir = ./bin
EOF

# Create a setup.cfg file for the project to ensure Python 3 language level
cat > setup.cfg << 'EOF'
[build_ext]
cython_directives = language_level=3
EOF

# Update requirements.txt to use Cython 3.0.0
cat > requirements_python3.txt << 'EOF'
cython==3.0.0
kivy==2.3.0
kivymd==1.2.0
openai
requests
pillow
cryptography
pyjnius==1.6.1
buildozer
EOF

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf .buildozer/android/platform/build-*
rm -rf .buildozer/android/app
rm -rf build/
rm -rf bin/

echo "Fix applied! To build with Python 3 compatibility:"
echo "1. Run: pip install -r requirements_python3.txt"
echo "2. Run: buildozer -v android clean"
echo "3. Run: buildozer -v android debug -s buildozer_python3_fix.spec"
echo ""
echo "The fix includes:"
echo "- Custom pyjnius recipe with Python 3 language level"
echo "- Updated Cython to version 3.0.0"
echo "- setup.cfg to force Python 3 language level"
echo "- Local recipes directory for custom recipes"