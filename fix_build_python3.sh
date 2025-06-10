#!/bin/bash

# Alternative fix for Python 2 vs Python 3 compatibility
echo "Applying alternative Python 3 compatibility fix..."

# Create a patch for buildozer to set Cython language level
mkdir -p patches

# Create environment setup script
cat > set_cython_env.sh << 'EOF'
#!/bin/bash
# Set environment variables to force Cython to use Python 3
export CYTHON_DIRECTIVE="language_level=3"
export CYTHON_LANGUAGE_LEVEL=3
EOF

# Create a wrapper script for cython
cat > cython_wrapper.sh << 'EOF'
#!/bin/bash
# Wrapper script to force Cython to use Python 3 language level
exec cython --directive language_level=3 "$@"
EOF

chmod +x set_cython_env.sh cython_wrapper.sh

# Create a simpler buildozer.spec that explicitly uses Python 3 compatible versions
cat > buildozer_simple_fix.spec << 'EOF'
[app]
title = DALL-E AI Art Generator
package.name = dalleaiart
package.domain = com.aiart
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,xml
source.exclude_exts = spec
source.exclude_dirs = tests, bin, build, dist, __pycache__, .git, venv
version = 1.0.0

# Updated requirements with compatible versions
requirements = python3==3.11,kivy==2.3.0,pillow,requests,certifi,urllib3,pyjnius,cython

orientation = portrait
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE
android.api = 33
android.minapi = 26
android.ndk = 25b
android.features = android.hardware.touchscreen
android.archs = arm64-v8a,armeabi-v7a
android.release = True
android.gradle_dependencies = androidx.security:security-crypto:1.1.0-alpha06

# Force Python 3 environment
android.add_compile_options = cython_directive = language_level=3

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = ./build
bin_dir = ./bin

# Custom build command that sets environment
# android.p4a_build_cmd = source set_cython_env.sh && {default}
EOF

# Create a pre-build hook script
cat > prebuild_hook.py << 'EOF'
#!/usr/bin/env python3
"""
Pre-build hook to ensure Python 3 compatibility
"""
import os
import sys

def patch_cython_files():
    """Add language_level directive to all .pyx files"""
    for root, dirs, files in os.walk('.buildozer'):
        for file in files:
            if file.endswith('.pyx') or file.endswith('.pxd'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Check if language_level is already set
                    if '# cython: language_level=' not in content:
                        # Add language_level directive at the beginning
                        content = '# cython: language_level=3\n' + content
                        
                        with open(filepath, 'w') as f:
                            f.write(content)
                        print(f"Patched {filepath}")
                except Exception as e:
                    print(f"Could not patch {filepath}: {e}")

if __name__ == '__main__':
    patch_cython_files()
EOF

chmod +x prebuild_hook.py

# Create build script with environment setup
cat > build_with_python3.sh << 'EOF'
#!/bin/bash

echo "Building with Python 3 compatibility..."

# Set environment variables
export CYTHON_DIRECTIVE="language_level=3"
export CYTHON_LANGUAGE_LEVEL=3

# Clean previous builds
echo "Cleaning previous builds..."
buildozer android clean

# Apply prebuild patches
echo "Applying Python 3 patches..."
python3 prebuild_hook.py

# Build with modified spec
echo "Starting build..."
buildozer -v android debug -s buildozer_simple_fix.spec

echo "Build complete!"
EOF

chmod +x build_with_python3.sh

echo "Alternative fix applied!"
echo ""
echo "To build with this fix, run:"
echo "./build_with_python3.sh"
echo ""
echo "This fix:"
echo "- Sets environment variables to force Python 3 language level"
echo "- Creates a simpler buildozer.spec"
echo "- Includes a pre-build hook to patch Cython files"
echo "- Provides a build script that sets up the environment"