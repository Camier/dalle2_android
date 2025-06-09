# DALL-E AI Art Generator - Installation Guide

## APK Information
- **File**: `dalle-ai-art-v1.0-debug.apk`
- **Size**: 56MB
- **Version**: 1.0 (Debug)
- **Package**: com.camier.dalleai
- **Min Android**: 5.0 (API 21)
- **Architecture**: ARM64-v8a

## Features Included
✅ Single image generation with DALL-E 2
✅ **NEW: Batch generation (1-4 images)**
✅ Gallery with zoom/pan functionality
✅ History tracking
✅ Share images via Android intent
✅ Save to device gallery
✅ Material Design UI
✅ Settings management
✅ API key secure storage

## Installation Methods

### Method 1: Using ADB (Recommended)
```bash
# Connect your Android device with USB debugging enabled
adb devices  # Verify device is connected

# Install the APK
adb install -r bin/dalle-ai-art-v1.0-debug.apk

# Or if you're in the project directory:
adb install -r ~/dalle_android/bin/dalle-ai-art-v1.0-debug.apk
```

### Method 2: Direct File Transfer
1. Copy `dalle-ai-art-v1.0-debug.apk` to your device:
   - Via USB cable
   - Via Google Drive/Dropbox
   - Via email attachment

2. On your Android device:
   - Go to Settings > Security
   - Enable "Unknown sources" or "Install unknown apps"
   - Navigate to the APK file
   - Tap to install

### Method 3: Local Web Server
```bash
# In the project directory
cd ~/dalle_android
python3 -m http.server 8000

# On your Android device:
# 1. Connect to same WiFi network
# 2. Open browser
# 3. Navigate to: http://[your-computer-ip]:8000/bin/
# 4. Download dalle-ai-art-v1.0-debug.apk
# 5. Install from Downloads
```

## First Run Setup
1. Launch "DALL-E AI Art" app
2. Enter your OpenAI API key when prompted
3. Start generating amazing AI art!

## Using Batch Generation
1. Scroll down on main screen
2. Find "Batch Generation" section
3. Enter your prompt
4. Select 1-4 images with slider
5. Tap "Generate Batch"
6. Each image can be saved/shared individually

## Troubleshooting

### Installation Blocked
- Enable "Install from unknown sources" in Settings
- For newer Android: Settings > Apps > Special access > Install unknown apps

### App Crashes on Start
- Ensure your device is ARM64 compatible
- Clear app data and cache
- Reinstall the APK

### API Key Issues
- Get key from: https://platform.openai.com/api-keys
- Ensure key has DALL-E access enabled
- Check internet connection

## Build Information
- Built with: Kivy 2.2.1 + KivyMD 1.1.1
- Python: 3.10
- Build date: June 9, 2025
- Build type: Debug (not optimized)

## Next Steps
- Test all features thoroughly
- Report any bugs or issues
- Consider building release version for production
