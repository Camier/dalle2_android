#!/bin/bash
# Fix dependencies and build with stable versions

set -e

echo "=== Fixing Dependencies and Building DALL-E Android App ==="

# Activate virtual environment
source venv/bin/activate

# Update buildozer.spec with more stable requirements
echo "Updating buildozer.spec with stable dependencies..."
cat > buildozer.spec << 'EOF'
[app]
title = DALL-E AI Art
package.name = dalleaiart
package.domain = com.aiart
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,ttf,otf,xml
version = 1.0.0

# Use more stable and compatible versions
requirements = python3,kivy==2.3.0,kivymd,pillow,requests,certifi,urllib3,cryptography,pycryptodome,openai,pyjnius,android,sdl2_ttf==2.0.15,sdl2_image==2.0.5,sdl2_mixer==2.0.4,libffi,openssl

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
android.release = False
android.minify_code = 0
android.optimize_python = 1

# Local recipes
p4a.local_recipes = ./recipes
p4a.prebuild_cmd = ./prebuild.sh

# Enable features
android.gradle_dependencies = com.google.android.material:material:1.5.0,androidx.appcompat:appcompat:1.4.1
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
EOF

# Create a more robust prebuild script
echo "Creating robust prebuild script..."
cat > prebuild.sh << 'EOF'
#!/bin/bash
echo "Running prebuild fixes..."

# Fix Cython language level globally
export CYTHON_DIRECTIVE="language_level=3"
export CYTHON_LANGUAGE_LEVEL=3

# Find all pyjnius files and fix them
find . -name "*.pyx" -o -name "*.pxi" | while read file; do
    if [[ "$file" == *"pyjnius"* ]] && grep -q '\blong\b' "$file" 2>/dev/null; then
        echo "Patching $file for Python 3..."
        sed -i.bak 's/\blong\b/int/g' "$file"
        sed -i.bak 's/basestring/str/g' "$file"
    fi
done

# Create Cython directives for all setup.py files
find . -name "setup.py" | while read setup; do
    dir=$(dirname "$setup")
    if [[ "$dir" == *"pyjnius"* ]] || [[ "$dir" == *"jnius"* ]]; then
        echo "[build_ext]" > "$dir/setup.cfg"
        echo "cython-directives=language_level=3" >> "$dir/setup.cfg"
    fi
done

echo "Prebuild fixes complete"
EOF
chmod +x prebuild.sh

# Clean previous failed builds
echo "Cleaning previous builds..."
rm -rf .buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/pyjnius*
rm -rf .buildozer/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/openai*
rm -rf .buildozer/android/platform/build-arm64-v8a_armeabi-v7a/packages

# Update pyjnius recipe to use a stable version
echo "Updating pyjnius recipe..."
cat > recipes/pyjnius/__init__.py << 'EOF'
from pythonforandroid.recipe import CythonRecipe
from pythonforandroid import logger
from os.path import join
import os

class PyjniusRecipe(CythonRecipe):
    version = '1.4.2'  # Stable version for Python 3
    url = 'https://github.com/kivy/pyjnius/archive/{version}.tar.gz'
    name = 'pyjnius'
    depends = ['setuptools', 'six']
    site_packages_name = 'jnius'
    
    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        # Force Python 3 language level
        env['CYTHON_DIRECTIVE'] = 'language_level=3'
        env['CYTHON_LANGUAGE_LEVEL'] = '3'
        return env
    
    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        build_dir = self.get_build_dir(arch.arch)
        
        # Create setup.cfg
        setup_cfg = join(build_dir, 'setup.cfg')
        with open(setup_cfg, 'w') as f:
            f.write('[build_ext]\n')
            f.write('cython-directives=language_level=3\n')
        
        # Fix any Python 2 syntax in source files
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                if file.endswith(('.pyx', '.pxi')):
                    filepath = join(root, file)
                    try:
                        with open(filepath, 'r') as f:
                            content = f.read()
                        
                        # Replace Python 2 constructs
                        content = content.replace('basestring', 'str')
                        if 'long' in content:
                            # Be careful not to replace 'long' in other contexts
                            import re
                            content = re.sub(r'\blong\b', 'int', content)
                        
                        with open(filepath, 'w') as f:
                            f.write(content)
                    except Exception as e:
                        logger.warning(f"Could not patch {filepath}: {e}")

recipe = PyjniusRecipe()
EOF

# Set environment variables
export CYTHON_DIRECTIVE="language_level=3"
export CYTHON_LANGUAGE_LEVEL=3
export PYTHONIOENCODING=utf-8

# Build the APK
echo "================================================"
echo "Starting build with fixed dependencies..."
echo "================================================"

buildozer -v android debug

# Check result
if [ -f bin/*.apk ]; then
    echo "================================================"
    echo "BUILD SUCCESSFUL!"
    echo "================================================"
    ls -la bin/*.apk
else
    echo "================================================"
    echo "BUILD FAILED - Checking logs..."
    echo "================================================"
    tail -n 50 .buildozer/logs/*.txt 2>/dev/null || echo "No log files found"
fi