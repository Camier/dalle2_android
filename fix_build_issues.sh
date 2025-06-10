#!/bin/bash
# Comprehensive Build Fix Script for DALL-E Android App
# This script fixes all known build issues including Python 3 compatibility

set -e

echo "=== DALL-E Android Build Fix Script ==="
echo "Fixing all build issues comprehensively..."

# 1. Setup environment
echo "Setting up environment..."
export ANDROID_HOME=$HOME/.buildozer/android/platform/android-sdk
export ANDROID_NDK_HOME=$HOME/.buildozer/android/platform/android-ndk-r25b
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# 2. Clean all caches
echo "Cleaning build caches..."
rm -rf .buildozer/android/platform/build-*
rm -rf .buildozer/android/app
rm -rf build
rm -rf __pycache__
rm -rf *.pyc

# 3. Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 4. Install correct Cython version (3.0.10 for Python 3 support)
echo "Installing Cython 3.0.10..."
pip install --upgrade pip
pip install cython==3.0.10

# 5. Install buildozer and dependencies
echo "Installing buildozer..."
pip install buildozer
pip install python-for-android

# 6. Create custom pyjnius recipe for Python 3
echo "Creating custom pyjnius recipe..."
mkdir -p recipes/pyjnius
cat > recipes/pyjnius/__init__.py << 'EOF'
from pythonforandroid.recipe import CythonRecipe
from pythonforandroid.util import current_directory
from os.path import join
import sh

class PyjniusRecipe(CythonRecipe):
    version = '1.5.0'
    url = 'https://github.com/kivy/pyjnius/archive/{version}.zip'
    name = 'pyjnius'
    depends = ['setuptools', 'six']
    site_packages_name = 'jnius'
    
    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        # Force Python 3 language level
        env['CYTHON_DIRECTIVE'] = 'language_level=3'
        return env
    
    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        # Create setup.cfg to force Python 3
        setup_cfg = join(self.get_build_dir(arch.arch), 'setup.cfg')
        with open(setup_cfg, 'w') as f:
            f.write('[build_ext]\n')
            f.write('cython-directives=language_level=3\n')

recipe = PyjniusRecipe()
EOF

# 7. Create optimized buildozer.spec
echo "Creating optimized buildozer.spec..."
cat > buildozer.spec << 'EOF'
[app]
title = DALL-E AI Art
package.name = dalleaiart
package.domain = com.aiart
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,ttf,otf,xml
version = 1.0.0
android.numeric_version = 1

# Requirements - all with compatible versions
requirements = python3==3.11,kivy==2.3.0,kivymd==1.2.0,pillow==10.2.0,requests==2.31.0,certifi==2024.2.2,urllib3==2.2.0,cryptography==42.0.5,pycryptodome==3.20.0,openai==1.12.0,pyjnius,android,sdl2_ttf,sdl2_image,sdl2_mixer,libffi,openssl

# Orientation
orientation = portrait

# Android configuration
android.permissions = INTERNET,VIBRATE,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True
android.archs = arm64-v8a,armeabi-v7a

# Build optimizations
android.release = True
android.minify_code = 1
android.optimize_python = 1
android.strip_python = 1

# Local recipes
p4a.local_recipes = ./recipes

# Enable features
android.add_gradle_maven_dependencies = com.google.crypto.tink:tink-android:1.7.0
android.gradle_dependencies = com.android.support:support-v4:28.0.0,com.google.android.material:material:1.5.0
android.enable_androidx = True
android.add_gradle_repositories = google(),mavenCentral()

# App assets
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png
android.splash_color = #FFFFFF

# Build settings
log_level = 2
warn_on_root = 1

[buildozer]
android.skip_update = False
android.skip_p4a_build = False
EOF

# 8. Create build wrapper script
echo "Creating build wrapper script..."
cat > build_apk.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
export CYTHON_DIRECTIVE="language_level=3"
export CYTHON_LANGUAGE_LEVEL=3
buildozer android debug
EOF
chmod +x build_apk.sh

# 9. Create Python 3 compatibility patch
echo "Creating Python 3 compatibility patches..."
cat > patch_python3.py << 'EOF'
import os
import re

def patch_pyjnius_files():
    """Patch pyjnius files for Python 3 compatibility"""
    build_dirs = []
    for root, dirs, files in os.walk('.buildozer/android/platform/build-'):
        if 'pyjnius' in root and any(f.endswith('.pyx') for f in files):
            build_dirs.append(root)
    
    for build_dir in build_dirs:
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                if file.endswith(('.pyx', '.pxi')):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Replace Python 2 constructs
                    content = re.sub(r'\blong\b', 'int', content)
                    content = re.sub(r'basestring', 'str', content)
                    
                    with open(filepath, 'w') as f:
                        f.write(content)

if __name__ == '__main__':
    patch_pyjnius_files()
EOF

echo "=== Build Fix Script Complete ==="
echo "To build your APK:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Run the build: ./build_apk.sh"