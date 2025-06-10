#!/bin/bash

# Fix Python 3 compatibility issues for buildozer

echo "Fixing Python 3 compatibility issues..."

# Clean problematic builds
echo "Cleaning build caches..."
rm -rf build/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/pyjnius*
rm -rf build/android/platform/build-arm64-v8a_armeabi-v7a/build/other_builds/cython*
rm -rf build/android/platform/build-arm64-v8a_armeabi-v7a/dists/dalleaiart

# Update Cython to a compatible version
echo "Ensuring compatible Cython version..."
pip install --upgrade "cython<3"

# Create a requirements fix
cat > requirements_fix.txt << 'EOF'
kivy==2.3.0
pillow
requests
cryptography
certifi
urllib3
pycryptodome
pyjnius==1.4.2
cython<3
EOF

echo "Requirements fixed. Now rebuilding..."
echo ""
echo "To continue building, run:"
echo "  ./build_apk.sh debug"