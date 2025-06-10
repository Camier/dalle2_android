#!/bin/bash

echo "=== Fixing SDL2 dependency issues ==="
echo "This script will clean the buildozer cache and rebuild with compatible SDL2 versions"

# Clean previous build artifacts
echo "1. Cleaning buildozer cache..."
buildozer android clean

# Remove the problematic SDL2 packages if they exist
echo "2. Removing cached SDL2 packages..."
rm -rf .buildozer/android/platform/build-*/packages/sdl2_*
rm -rf .buildozer/android/platform/build-*/build/other_builds/sdl2_*

# Kill any running gradle daemons
echo "3. Stopping gradle daemons..."
pkill -f gradle || true
rm -rf ~/.gradle/daemon/

# Create a backup of the original buildozer.spec
echo "4. Backing up buildozer.spec..."
cp buildozer.spec buildozer.spec.backup

# Start the build
echo "5. Starting build with updated dependencies..."
echo "Note: SDL2 libraries will be downloaded with buildozer's default compatible versions"
buildozer android debug

echo "=== Build process complete ==="
echo "If the build still fails, check the error messages above."
echo "The original buildozer.spec has been backed up to buildozer.spec.backup"