#!/bin/bash

# Create packages directory
mkdir -p .buildozer/android/platform/build-arm64-v8a/packages

cd .buildozer/android/platform/build-arm64-v8a/packages

echo "=== Pre-downloading essential packages with resume support ==="

# Core packages needed for minimal build
PACKAGES=(
    "freetype|https://download.savannah.gnu.org/releases/freetype/freetype-2.10.1.tar.gz"
    "hostpython3|https://www.python.org/ftp/python/3.11.5/Python-3.11.5.tgz"
    "libffi|https://github.com/libffi/libffi/archive/v3.4.2.tar.gz"
    "openssl|https://www.openssl.org/source/openssl-1.1.1w.tar.gz"
    "sdl2|https://github.com/libsdl-org/SDL/releases/download/release-2.28.5/SDL2-2.28.5.tar.gz"
    "python3|https://www.python.org/ftp/python/3.11.5/Python-3.11.5.tgz"
    "setuptools|https://pypi.python.org/packages/source/s/setuptools/setuptools-51.3.3.tar.gz"
    "pillow|https://github.com/python-pillow/Pillow/archive/8.4.0.tar.gz"
    "kivy|https://github.com/kivy/kivy/archive/2.3.0.zip"
)

for package_info in "${PACKAGES[@]}"; do
    IFS='|' read -r package_name url <<< "$package_info"
    
    # Create package directory
    mkdir -p $package_name
    cd $package_name
    
    filename=$(basename $url)
    
    if [ -f "$filename" ]; then
        echo "✓ $package_name already downloaded"
    else
        echo "Downloading $package_name..."
        # Use wget with resume capability and progress bar
        wget -c --progress=bar:force --timeout=60 --tries=5 "$url" || echo "Failed to download $package_name"
    fi
    
    cd ..
done

echo "=== Download complete ==="
ls -la */*.tar.gz */*.zip 2>/dev/null | wc -l
echo "packages ready"