#!/bin/bash
# Build with pre-fixed pyjnius to avoid patching conflicts

set -e

echo "=== Building with Fixed pyjnius ==="

# Activate environment
source venv/bin/activate

# 1. First, let's check what patch is failing
echo "Checking failing patch..."
if [ -f ".buildozer/android/platform/python-for-android/pythonforandroid/recipes/pyjnius/fix_python3_long.patch" ]; then
    echo "Found conflicting patch. Removing it..."
    rm -f .buildozer/android/platform/python-for-android/pythonforandroid/recipes/pyjnius/fix_python3_long.patch
fi

# 2. Create a recipe that skips patching
mkdir -p recipes/pyjnius
cat > recipes/pyjnius/__init__.py << 'EOF'
from pythonforandroid.recipe import CythonRecipe
from pythonforandroid.util import current_directory
from pythonforandroid import logger
import os
from os.path import join, exists

class PyjniusRecipe(CythonRecipe):
    version = '1.4.2'
    url = 'https://github.com/kivy/pyjnius/archive/{version}.tar.gz'
    name = 'pyjnius'
    depends = ['setuptools', 'six']
    site_packages_name = 'jnius'
    patches = []  # No patches!
    
    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        # Force Python 3
        env['CYTHON_DIRECTIVE'] = 'language_level=3'
        env['CYTHON_LANGUAGE_LEVEL'] = '3'
        return env
    
    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        build_dir = self.get_build_dir(arch.arch)
        
        # Fix Python 2/3 issues directly in source
        logger.info("Fixing Python 3 compatibility in pyjnius...")
        
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                if file.endswith(('.pyx', '.pxi')):
                    filepath = join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Fix Python 2 constructs
                        original = content
                        import re
                        content = re.sub(r'\blong\b', 'int', content)
                        content = re.sub(r'basestring', 'str', content)
                        
                        if content != original:
                            logger.info(f"Fixed Python 3 issues in {file}")
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(content)
                    except Exception as e:
                        logger.warning(f"Could not process {filepath}: {e}")
        
        # Create setup.cfg
        setup_cfg = join(build_dir, 'setup.cfg')
        with open(setup_cfg, 'w') as f:
            f.write('[build_ext]\n')
            f.write('cython-directives=language_level=3\n')
        logger.info("Created setup.cfg for Python 3")

recipe = PyjniusRecipe()
EOF

# 3. Clean previous build attempts
echo "Cleaning previous builds..."
rm -rf .buildozer/android/platform/build-arm64-v8a/build/other_builds/pyjnius*
rm -rf .buildozer/android/platform/build-arm64-v8a/packages/pyjnius*

# 4. Build with our fixed recipe
echo "Building APK..."
export GRADLE_OPTS="-Dorg.gradle.daemon=false"
buildozer -v android debug 2>&1 | tee build_fixed.log

# 5. Check results
if ls bin/*.apk 1> /dev/null 2>&1; then
    echo "================================================"
    echo "BUILD SUCCESSFUL!"
    echo "================================================"
    ls -la bin/*.apk
else
    echo "Build failed. Checking specific issues..."
    grep -i "error" build_fixed.log | tail -10
fi