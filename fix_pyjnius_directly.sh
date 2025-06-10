#!/bin/bash
# Direct fix for pyjnius Python 3 compatibility

set -e

echo "=== Direct pyjnius Fix for WSL Ubuntu 22.04 ==="

# 1. Stop current build
pkill -f buildozer 2>/dev/null || true
pkill -f python 2>/dev/null || true

# 2. Create pre-patched pyjnius
echo "Creating pre-patched pyjnius..."
mkdir -p pyjnius_fix
cd pyjnius_fix

# Download pyjnius 1.4.2
wget -q https://github.com/kivy/pyjnius/archive/1.4.2.tar.gz
tar xzf 1.4.2.tar.gz
cd pyjnius-1.4.2

# Patch all files for Python 3
echo "Patching pyjnius for Python 3..."
find . -name "*.pyx" -o -name "*.pxi" | while read file; do
    echo "Patching $file..."
    sed -i 's/\blong\b/int/g' "$file"
    sed -i 's/basestring/str/g' "$file"
done

# Create setup.cfg
cat > setup.cfg << 'EOF'
[build_ext]
cython-directives=language_level=3
EOF

# Create patched tarball
cd ..
tar czf pyjnius-1.4.2-patched.tar.gz pyjnius-1.4.2
cd ..

# 3. Update recipe to use local file
echo "Updating pyjnius recipe..."
cat > recipes/pyjnius/__init__.py << 'EOF'
from pythonforandroid.recipe import CythonRecipe
import os
from os.path import join, dirname, exists

class PyjniusRecipe(CythonRecipe):
    version = '1.4.2'
    # Use local patched version
    url = 'file://' + join(dirname(dirname(dirname(__file__))), 'pyjnius_fix', 'pyjnius-{version}-patched.tar.gz')
    name = 'pyjnius'
    depends = ['setuptools', 'six']
    site_packages_name = 'jnius'
    
    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['CYTHON_DIRECTIVE'] = 'language_level=3'
        return env

recipe = PyjniusRecipe()
EOF

# 4. Clean and restart build
echo "Cleaning build cache..."
rm -rf .buildozer/android/platform/build-arm64-v8a/build/other_builds/pyjnius*
rm -rf .buildozer/android/platform/build-arm64-v8a/packages/pyjnius*

echo "================================================"
echo "Direct fix applied!"
echo "Now run: ./build_wsl.sh"
echo "================================================"