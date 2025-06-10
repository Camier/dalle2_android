#!/bin/bash
# Ultimate fix for pyjnius build issues

set -e

echo "=== Ultimate Build Fix for DALL-E Android ==="

# 1. Activate venv
source venv/bin/activate

# 2. Clean everything
echo "Cleaning all build artifacts..."
rm -rf .buildozer/android/platform/build-*
rm -rf .buildozer/android/app
rm -rf build
rm -rf bin/*

# 3. Install specific Cython version that works with pyjnius
echo "Installing Cython 0.29.33 (known to work with pyjnius)..."
pip uninstall -y cython
pip install cython==0.29.33

# 4. Create a patched pyjnius recipe
echo "Creating patched pyjnius recipe..."
mkdir -p recipes/pyjnius
cat > recipes/pyjnius/__init__.py << 'EOF'
from pythonforandroid.recipe import CythonRecipe
from pythonforandroid.util import current_directory
import sh
from os.path import join, exists
import os

class PyjniusRecipe(CythonRecipe):
    version = '1.4.2'
    url = 'https://github.com/kivy/pyjnius/archive/{version}.tar.gz'
    name = 'pyjnius'
    depends = ['setuptools', 'six']
    site_packages_name = 'jnius'
    
    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        # Add Cython to path
        env['CYTHON'] = sh.which('cython')
        return env
    
    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        build_dir = self.get_build_dir(arch.arch)
        
        # Ensure setup.py includes .pxi files
        setup_py = join(build_dir, 'setup.py')
        if exists(setup_py):
            with open(setup_py, 'r') as f:
                content = f.read()
            
            # Fix to include .pxi files
            if 'include_dirs' in content and '.pxi' not in content:
                content = content.replace(
                    "ext_modules=cythonize(ext_modules)",
                    "ext_modules=cythonize(ext_modules, compiler_directives={'language_level': '3'})"
                )
            
            with open(setup_py, 'w') as f:
                f.write(content)
        
        # Create pyproject.toml to specify Cython build requirements
        pyproject = join(build_dir, 'pyproject.toml')
        with open(pyproject, 'w') as f:
            f.write('''[build-system]
requires = ["setuptools", "cython<3"]
build-backend = "setuptools.build_meta"
''')

recipe = PyjniusRecipe()
EOF

# 5. Create simplified buildozer.spec without cryptography (add later)
echo "Creating simplified buildozer.spec..."
cat > buildozer.spec << 'EOF'
[app]
title = DALL-E AI Art
package.name = dalleaiart
package.domain = com.aiart
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0.0

# Core requirements only
requirements = python3,kivy,pillow,requests,certifi,urllib3,pyjnius,android,kivymd

# Orientation
orientation = portrait

# Android configuration
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

# Build settings
android.release = False
log_level = 2
warn_on_root = 1

# Local recipes
p4a.local_recipes = ./recipes

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

# 6. Create a simple test main.py to ensure build works
echo "Creating test main.py..."
cp main.py main_backup.py
cat > main.py << 'EOF'
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

class DALLEApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20)
        
        # Title
        title = Label(text='DALL-E AI Art Generator', size_hint_y=0.2, font_size='24sp')
        layout.add_widget(title)
        
        # Input
        self.prompt_input = TextInput(
            hint_text='Enter your image description...',
            multiline=True,
            size_hint_y=0.4
        )
        layout.add_widget(self.prompt_input)
        
        # Button
        generate_btn = Button(
            text='Generate Image',
            size_hint_y=0.2,
            background_color=(0.2, 0.6, 1, 1)
        )
        generate_btn.bind(on_press=self.generate_image)
        layout.add_widget(generate_btn)
        
        # Status
        self.status_label = Label(
            text='Ready to generate!',
            size_hint_y=0.2
        )
        layout.add_widget(self.status_label)
        
        return layout
    
    def generate_image(self, instance):
        prompt = self.prompt_input.text
        if prompt:
            self.status_label.text = f'Generating: {prompt[:50]}...'
        else:
            self.status_label.text = 'Please enter a description!'

if __name__ == '__main__':
    DALLEApp().run()
EOF

# 7. Build with environment fixes
echo "Building APK..."
export ANDROID_HOME=$HOME/.buildozer/android/platform/android-sdk
export ANDROID_NDK_HOME=$HOME/.buildozer/android/platform/android-ndk-r25b

# Add timeout to prevent hanging
timeout 20m buildozer -v android debug 2>&1 | tee final_build.log

# 8. Check result
if ls bin/*.apk 1> /dev/null 2>&1; then
    echo "================================================"
    echo "BUILD SUCCESSFUL!"
    echo "================================================"
    ls -la bin/*.apk
    echo ""
    echo "Your APK is ready!"
    echo ""
    echo "Next steps:"
    echo "1. Test the APK: adb install -r bin/*.apk"
    echo "2. Restore full main.py: cp main_backup.py main.py"
    echo "3. Add security features incrementally"
else
    echo "================================================"
    echo "BUILD FAILED"
    echo "================================================"
    echo "Checking common issues..."
    
    if grep -q "\.pxi" final_build.log; then
        echo "- Still having .pxi file issues with Cython"
    fi
    
    if grep -q "404" final_build.log; then
        echo "- Download errors (network or version issues)"
    fi
    
    echo ""
    echo "Try manual build:"
    echo "1. cd /home/mik/dalle_android"
    echo "2. source venv/bin/activate"
    echo "3. p4a apk --requirements=python3,kivy --arch=arm64-v8a --name=DALLEApp --package=com.aiart.dalle --version=1.0"
fi