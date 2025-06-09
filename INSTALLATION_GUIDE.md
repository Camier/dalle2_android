# DALL-E Android App - Installation Guide for Ubuntu/WSL

## Step 1: Install System Dependencies

```bash
# Update package manager
sudo apt update

# Install Python 3.10 (IMPORTANT: Don't use Python 3.13+)
sudo apt install python3.10 python3.10-venv python3.10-dev

# Install build tools and libraries
sudo apt install -y \
    build-essential \
    git \
    ffmpeg \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libportmidi-dev \
    libswscale-dev \
    libavformat-dev \
    libavcodec-dev \
    zlib1g-dev \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    openjdk-8-jdk \
    unzip \
    autoconf \
    libtool \
    pkg-config \
    libssl-dev \
    xclip \
    xsel
```

## Step 2: Install Android SDK

```bash
# Create directory for Android tools
mkdir -p ~/android-tools
cd ~/android-tools

# Download Android command line tools
wget https://dl.google.com/android/repository/commandlinetools-linux-9477386_latest.zip
unzip commandlinetools-linux-9477386_latest.zip
rm commandlinetools-linux-9477386_latest.zip

# Set environment variables
echo 'export ANDROID_HOME=$HOME/android-tools' >> ~/.bashrc
echo 'export PATH=$PATH:$ANDROID_HOME/cmdline-tools/bin:$ANDROID_HOME/platform-tools' >> ~/.bashrc
source ~/.bashrc

# Accept licenses and install SDK components
yes | sdkmanager --sdk_root=$ANDROID_HOME --licenses
sdkmanager --sdk_root=$ANDROID_HOME "platform-tools" "platforms;android-33" "build-tools;33.0.0"
```

## Step 3: Set Up Project

```bash
# Navigate to the project directory
cd ~/dalle_android

# Create virtual environment with Python 3.10
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install Python dependencies
pip install -r requirements.txt

# Install buildozer
pip install buildozer
```

## Step 4: Get OpenAI API Key

1. Visit https://platform.openai.com/signup
2. Create or sign in to your account
3. Go to https://platform.openai.com/api-keys
4. Click "Create new secret key"
5. Copy the key (starts with `sk-`)

## Step 5: Test on Desktop

```bash
# Activate virtual environment if not already
source venv/bin/activate

# Run the app
python test_desktop.py

# When prompted:
# 1. Enter your OpenAI API key
# 2. Try generating an image with "a cute robot"
# 3. Press Ctrl+C to exit when done testing
```

## Step 6: Build the APK

```bash
# Make sure you're in the project directory
cd ~/dalle_android

# Activate virtual environment
source venv/bin/activate

# Clean any previous builds
rm -rf .buildozer bin/

# Build the APK (this takes 10-20 minutes first time)
buildozer android debug

# The APK will be in: bin/dalleimages-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

## Step 7: Install on Android Device

### Enable Developer Mode on Your Phone:
1. Settings → About Phone
2. Tap "Build Number" 7 times
3. Go back → Developer Options
4. Enable "USB Debugging"
5. Enable "Install from Unknown Sources"

### Connect and Install:
```bash
# Connect phone via USB
# Verify connection
adb devices

# Install the app
adb install bin/dalleimages-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

### Alternative: Manual Installation
1. Copy the APK to your phone
2. Use a file manager to open and install it

## Troubleshooting

### "Kivy compilation failed" Error
```bash
# Make sure you're using Python 3.10, not 3.13
python --version  # Should show 3.10.x

# If wrong version, recreate venv:
deactivate
rm -rf venv
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### "SDK not found" Error
```bash
# Verify ANDROID_HOME is set
echo $ANDROID_HOME

# Re-source bashrc
source ~/.bashrc
```

### "adb: command not found"
```bash
# Add to PATH
export PATH=$PATH:~/android-tools/platform-tools
# Then verify
adb version
```

### Build Takes Too Long
- First build downloads many dependencies (normal)
- Subsequent builds are much faster
- Use `buildozer android clean` if stuck

## Quick Commands Reference

```bash
# Activate virtual environment
source venv/bin/activate

# Test on desktop
python test_desktop.py

# Build APK
buildozer android debug

# Install on device
adb install bin/*.apk

# View device logs
adb logcat | grep python

# Clean build
buildozer android clean
```

## Success Checklist
- [ ] Python 3.10 installed (not 3.13)
- [ ] All system dependencies installed
- [ ] Android SDK installed
- [ ] Virtual environment created with Python 3.10
- [ ] All pip packages installed successfully
- [ ] Desktop test runs without errors
- [ ] OpenAI API key works
- [ ] APK builds successfully
- [ ] App installs and runs on Android device

## Common Issues on WSL

If running on WSL and GUI doesn't work:
```bash
# Install X server on Windows (VcXsrv or Xming)
# Then in WSL:
export DISPLAY=:0
python test_desktop.py
```

For Android device connection in WSL2:
- Use USB/IP or
- Build APK in WSL, transfer to Windows, install from there