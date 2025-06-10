# Python 2 vs Python 3 Compatibility Fix for Buildozer

## Problem
The buildozer build is failing with "undeclared name not builtin: long" error in pyjnius compilation. This is because:
1. Cython defaults to Python 2 language level
2. Python 2's `long` type doesn't exist in Python 3
3. The pyjnius recipe needs to be configured for Python 3

## Solutions

I've created multiple fix approaches for you:

### Solution 1: Custom Recipe Fix (Recommended)
Run: `./fix_cython_python3.sh`

This creates:
- A custom pyjnius recipe that forces Python 3 language level
- Updated buildozer.spec with local recipes
- Updated requirements with Cython 3.0.0

### Solution 2: Environment Variable Fix
Run: `./fix_build_python3.sh`

This creates:
- Environment scripts that set CYTHON_DIRECTIVE
- A wrapper script for cython
- A build script that sets up the environment

### Solution 3: Source Code Patching
Run: `python3 fix_pyjnius_python3.py`

This:
- Patches pyjnius source files to replace Python 2 constructs
- Fixes `long` type references
- Creates a fixed buildozer spec

## Quick Fix Steps

1. **Clean previous builds:**
   ```bash
   rm -rf .buildozer/android/platform/build-*
   rm -rf build/
   rm -rf bin/
   ```

2. **Apply the recommended fix:**
   ```bash
   ./fix_cython_python3.sh
   ```

3. **Update your virtual environment:**
   ```bash
   pip install -r requirements_python3.txt
   ```

4. **Build with the fixed configuration:**
   ```bash
   buildozer -v android clean
   buildozer -v android debug -s buildozer_python3_fix.spec
   ```

## Manual Fix (if scripts don't work)

1. **Update requirements.txt:**
   ```
   cython==3.0.0
   kivy==2.3.0
   kivymd==1.2.0
   openai
   requests
   pillow
   cryptography
   pyjnius==1.6.1
   buildozer
   ```

2. **Create setup.cfg in project root:**
   ```ini
   [build_ext]
   cython_directives = language_level=3
   ```

3. **Set environment before building:**
   ```bash
   export CYTHON_DIRECTIVE="language_level=3"
   export CYTHON_LANGUAGE_LEVEL=3
   ```

4. **Use a modified buildozer.spec** with:
   - `requirements = python3,kivy==2.3.0,pillow,requests,certifi,urllib3,pyjnius==1.6.1,cython==3.0.0`
   - Add `p4a.local_recipes = ./recipes` if using custom recipes

## Root Cause
The issue stems from:
- Cython 0.29.x defaulting to Python 2 language level
- pyjnius code using Python 2's `long` type
- Missing language_level directives in .pyx files

## Verification
After building, check that:
1. No "long" type errors appear
2. The build completes successfully
3. The APK is generated in the bin/ directory

## Additional Notes
- Python 3 uses `int` instead of `long`
- Cython 3.0.0+ defaults to Python 3 language level
- Some recipes may need manual patching for full Python 3 compatibility