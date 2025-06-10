#!/bin/bash
# Fix build issues specific to WSL Ubuntu 22.04

set -e

echo "=== WSL Ubuntu 22.04 Build Fix for DALL-E Android ==="

# 1. Fix WSL-specific issues
echo "Fixing WSL-specific issues..."

# Fix line endings (WSL can have CRLF issues)
find . -name "*.py" -o -name "*.sh" | xargs dos2unix 2>/dev/null || true

# Ensure proper permissions
chmod -R 755 .buildozer 2>/dev/null || true
chmod +x *.sh 2>/dev/null || true

# 2. Clean everything
echo "Cleaning build directories..."
rm -rf .buildozer/android/platform/build-arm64-v8a
rm -rf .buildozer/android/app
rm -rf build
rm -rf bin
rm -rf __pycache__

# 3. Set up environment
source venv/bin/activate

# Install specific versions that work on Ubuntu 22.04
echo "Installing compatible dependencies..."
pip uninstall -y cython buildozer python-for-android 2>/dev/null || true
pip install --upgrade pip setuptools wheel
pip install cython==0.29.33
pip install buildozer==1.5.0
pip install python-for-android==2024.1.21

# 4. Create WSL-compatible buildozer.spec
echo "Creating WSL-compatible buildozer.spec..."
cat > buildozer.spec << 'EOF'
[app]
title = DALL-E AI Art
package.name = dalleaiart
package.domain = com.aiart
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0

# Core requirements
requirements = python3,kivy,pillow,requests,certifi,urllib3,pyjnius,android

# Android configuration
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

# Build settings
android.release = False
android.debug = True
log_level = 2
warn_on_root = 0

# WSL-specific settings
android.gradle_dependencies = androidx.appcompat:appcompat:1.4.1
android.enable_androidx = True
android.add_gradle_repositories = google(),mavenCentral()

# Build options
android.copy_libs = 1

[buildozer]
# Prevent re-downloading in WSL
android.skip_update = False
android.auto_update_sdk = False
EOF

# 5. Create custom pyjnius recipe that works in WSL
echo "Creating WSL-compatible pyjnius recipe..."
mkdir -p recipes/pyjnius
cat > recipes/pyjnius/__init__.py << 'EOF'
from pythonforandroid.recipe import CythonRecipe
from pythonforandroid.util import current_directory
from pythonforandroid import logger
import sh
import os
from os.path import join, exists

class PyjniusRecipe(CythonRecipe):
    version = '1.4.2'
    url = 'https://github.com/kivy/pyjnius/archive/{version}.tar.gz'
    name = 'pyjnius'
    depends = ['setuptools', 'six']
    site_packages_name = 'jnius'
    
    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        # Ensure Cython uses Python 3
        env['CYTHON_DIRECTIVE'] = 'language_level=3'
        return env
    
    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        build_dir = self.get_build_dir(arch.arch)
        
        # Fix permissions for WSL
        sh.chmod('-R', '755', build_dir)
        
        # Fix .pxi files for Python 3
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                if file.endswith(('.pyx', '.pxi')):
                    filepath = join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Replace Python 2 constructs
                        import re
                        content = re.sub(r'\blong\b', 'int', content)
                        content = re.sub(r'basestring', 'str', content)
                        
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                            
                        # Fix file permissions
                        os.chmod(filepath, 0o755)
                    except Exception as e:
                        logger.warning(f"Could not patch {filepath}: {e}")
        
        # Create setup.cfg to force Python 3
        setup_cfg = join(build_dir, 'setup.cfg')
        with open(setup_cfg, 'w') as f:
            f.write('[build_ext]\n')
            f.write('cython-directives=language_level=3\n')

recipe = PyjniusRecipe()
EOF

# 6. Fix Java version issues in WSL
echo "Checking Java version..."
java_version=$(java -version 2>&1 | head -n 1)
echo "Current Java: $java_version"

if [[ "$java_version" == *"21"* ]]; then
    echo "Warning: Java 21 detected. Java 11 is recommended."
    echo "To switch to Java 11:"
    echo "  sudo update-alternatives --config java"
    echo "  sudo update-alternatives --config javac"
fi

# 7. Create build wrapper with WSL fixes
cat > build_wsl.sh << 'EOF'
#!/bin/bash
source venv/bin/activate

# WSL-specific environment
export ANDROID_HOME=$HOME/.buildozer/android/platform/android-sdk
export ANDROID_NDK_HOME=$HOME/.buildozer/android/platform/android-ndk-r25b
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# Disable some problematic gradle features in WSL
export GRADLE_OPTS="-Dorg.gradle.daemon=false"

# Build with verbose output
buildozer -v android debug 2>&1 | tee wsl_build.log
EOF
chmod +x build_wsl.sh

# 8. Create a pre-build fix script
cat > prebuild_wsl.sh << 'EOF'
#!/bin/bash
# Fix any permission issues before build
find .buildozer -type d -exec chmod 755 {} \; 2>/dev/null || true
find .buildozer -name "*.py" -exec chmod 644 {} \; 2>/dev/null || true
find .buildozer -name "*.pyx" -exec chmod 644 {} \; 2>/dev/null || true
find .buildozer -name "*.pxi" -exec chmod 644 {} \; 2>/dev/null || true
EOF
chmod +x prebuild_wsl.sh

echo "================================================"
echo "WSL Fix Applied!"
echo "================================================"
echo ""
echo "To build your APK on WSL Ubuntu 22.04:"
echo "1. Run: ./prebuild_wsl.sh"
echo "2. Then: ./build_wsl.sh"
echo ""
echo "If you still have issues:"
echo "- Check Java version (Java 11 recommended)"
echo "- Ensure WSL2 is being used (not WSL1)"
echo "- Try: sudo sysctl -w vm.max_map_count=262144"
echo "================================================"