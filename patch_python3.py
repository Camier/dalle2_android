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
