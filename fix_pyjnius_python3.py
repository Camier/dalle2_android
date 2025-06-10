#!/usr/bin/env python3
"""
Fix pyjnius Python 2 vs Python 3 compatibility issues
"""
import os
import re
import shutil

def fix_pyjnius_long_type():
    """Fix 'long' type issues in pyjnius for Python 3"""
    
    # Find pyjnius source files in buildozer cache
    pyjnius_paths = []
    
    for root, dirs, files in os.walk('.buildozer'):
        if 'pyjnius' in root:
            for file in files:
                if file.endswith(('.pyx', '.pxd', '.py')):
                    pyjnius_paths.append(os.path.join(root, file))
    
    print(f"Found {len(pyjnius_paths)} pyjnius files to check")
    
    # Python 2 to Python 3 replacements
    replacements = [
        # Replace 'long' with 'int' in Python 3
        (r'\blong\b(?!\s*\()', 'int'),
        # Fix basestring references
        (r'\bbasestring\b', 'str'),
        # Fix unicode references
        (r'\bunicode\b', 'str'),
        # Fix iteritems
        (r'\.iteritems\(\)', '.items()'),
        # Fix itervalues
        (r'\.itervalues\(\)', '.values()'),
        # Fix iterkeys
        (r'\.iterkeys\(\)', '.keys()'),
        # Fix xrange
        (r'\bxrange\b', 'range'),
    ]
    
    for filepath in pyjnius_paths:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Add language_level directive if it's a .pyx file
            if filepath.endswith('.pyx') and '# cython: language_level=' not in content:
                content = '# cython: language_level=3\n' + content
            
            # Apply replacements
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            # Special handling for Cython long type declarations
            # In Cython, 'cdef long' should remain, but Python long should be int
            if filepath.endswith(('.pyx', '.pxd')):
                # Restore 'cdef long' declarations
                content = re.sub(r'cdef\s+int\b', 'cdef long', content)
                # Restore 'ctypedef long' declarations
                content = re.sub(r'ctypedef\s+int\b', 'ctypedef long', content)
                # But keep Python long as int
                content = re.sub(r'(\s+)int\s*\(', r'\1int(', content)
            
            if content != original_content:
                # Backup original
                shutil.copy2(filepath, filepath + '.bak')
                
                # Write fixed content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Fixed: {filepath}")
        
        except Exception as e:
            print(f"Error processing {filepath}: {e}")

def create_fixed_buildozer_spec():
    """Create a buildozer spec with proper Python 3 configuration"""
    
    spec_content = '''[app]
title = DALL-E AI Art Generator
package.name = dalleaiart
package.domain = com.aiart
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,xml
source.exclude_exts = spec
source.exclude_dirs = tests, bin, build, dist, __pycache__, .git, venv
version = 1.0.0

# Requirements with Python 3 compatible versions
requirements = python3,kivy==2.3.0,pillow,requests,certifi,urllib3,pyjnius

orientation = portrait
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,VIBRATE
android.api = 33
android.minapi = 26
android.ndk = 25b
android.features = android.hardware.touchscreen
android.archs = arm64-v8a,armeabi-v7a
android.release = True
android.gradle_dependencies = androidx.security:security-crypto:1.1.0-alpha06

# Python 3 optimizations
android.gradle_python_compile_options = -Xlanguage_level=3

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = ./build
bin_dir = ./bin
'''
    
    with open('buildozer_python3_fixed.spec', 'w') as f:
        f.write(spec_content)
    
    print("Created buildozer_python3_fixed.spec")

def main():
    """Main function to apply all fixes"""
    print("Applying Python 3 compatibility fixes for pyjnius...")
    
    # Create fixed buildozer spec
    create_fixed_buildozer_spec()
    
    # Fix pyjnius source files if they exist
    if os.path.exists('.buildozer'):
        fix_pyjnius_long_type()
    else:
        print("No .buildozer directory found. Run this after initial build failure.")
    
    print("\nFix complete!")
    print("\nTo apply these fixes:")
    print("1. If you haven't built yet, run: buildozer android debug")
    print("2. When it fails with 'long' error, run: python3 fix_pyjnius_python3.py")
    print("3. Then run: buildozer android debug -s buildozer_python3_fixed.spec")

if __name__ == '__main__':
    main()