# DALL-E Image Generator for Android

A simple, clean Android application that uses OpenAI's DALL-E 2 API to generate images from text descriptions. Built with Python, Kivy, and Material Design components.

## Features

- 🎨 Generate images from text prompts using DALL-E 2
- 🔒 Secure API key storage with encryption
- 💾 Save generated images to device gallery
- 📱 Material Design UI with responsive layout
- 🔄 Loading states and error handling
- 🌐 Network connectivity checking
- 📷 High-quality image generation (1024x1024)

## Requirements

### For Development
- Python 3.8+
- pip (Python package manager)
- Git
- Java JDK 8 or higher (for Android build)
- Android SDK (API level 33)

### For Running the App
- Android device or emulator (Android 5.0+)
- OpenAI API key with DALL-E access
- Internet connection

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd dalle_android
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install Buildozer (for APK building)
```bash
pip install buildozer

# On Ubuntu/Debian, install additional dependencies:
sudo apt update
sudo apt install -y python3-pip build-essential git python3 python3-dev \
    ffmpeg libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    libportmidi-dev libswscale-dev libavformat-dev libavcodec-dev zlib1g-dev \
    libgstreamer1.0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good
```

### 4. Get OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API keys section
4. Create a new API key
5. Make sure your account has access to DALL-E 2

## Building the APK

### Debug Build (for testing)
```bash
# Initialize buildozer (first time only)
buildozer init

# Build debug APK
buildozer android debug
```

The APK will be created in the `bin/` directory.

### Release Build (for distribution)
```bash
# Build release APK
buildozer android release
```

For release builds, you'll need to sign the APK. Follow [Android's signing guide](https://developer.android.com/studio/publish/app-signing).

## Installation on Android Device

### Method 1: Direct Install (Debug APK)
1. Enable "Install from Unknown Sources" in Android settings
2. Transfer the APK to your device
3. Open the APK file to install

### Method 2: Using ADB
```bash
# Connect your device via USB with debugging enabled
adb install bin/dalleimages-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

## Using the App

1. **First Launch**
   - The app will prompt for your OpenAI API key
   - Enter your key and tap "SAVE"
   - The key is encrypted and stored locally

2. **Generating Images**
   - Enter a descriptive prompt (e.g., "A sunset over mountains in watercolor style")
   - Tap "Generate Image"
   - Wait for the image to generate (usually 5-10 seconds)

3. **Saving Images**
   - Once generated, tap "Save to Gallery"
   - The image will be saved to your Pictures/DALLE folder
   - You'll see a confirmation message

4. **Managing API Key**
   - Tap "API Settings" to change or update your key

## Project Structure

```
dalle_android/
├── main.py                 # App entry point
├── screens/
│   └── main_screen.py      # Main UI screen
├── services/
│   └── dalle_api.py        # DALL-E API integration
├── utils/
│   ├── storage.py          # Secure key storage
│   └── image_utils.py      # Image saving utilities
├── assets/
│   ├── icon.png            # App icon
│   └── presplash.png       # Splash screen
├── buildozer.spec          # Build configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Troubleshooting

### Build Issues

**Issue**: `buildozer android debug` fails with SDK/NDK errors
```bash
# Clean and rebuild
buildozer android clean
buildozer android debug
```

**Issue**: Missing dependencies
```bash
# Make sure all system dependencies are installed
buildozer android requirements
```

### Runtime Issues

**Issue**: "Invalid API key" error
- Verify your API key is correct
- Check that your OpenAI account has DALL-E access
- Ensure you have available credits

**Issue**: Network errors
- Check internet connection
- Verify the device can reach api.openai.com
- Try using a different network

**Issue**: Images not saving
- Ensure the app has storage permissions
- Check available storage space
- Try reinstalling the app

### Development Testing

To test on desktop before building APK:
```bash
python main.py
```

## API Usage and Costs

- Each image generation uses DALL-E 2 API credits
- Current pricing: ~$0.02 per 1024x1024 image
- Monitor usage at [OpenAI Usage Dashboard](https://platform.openai.com/usage)

## Security Notes

- API keys are encrypted using Fernet encryption
- Keys are stored locally on the device
- Never share your APK with the API key hardcoded
- Consider implementing additional authentication for production apps

## Future Enhancements

- [ ] Multiple image sizes (512x512, 256x256)
- [ ] Image variation generation
- [ ] History of generated images
- [ ] Share functionality
- [ ] Batch generation
- [ ] Custom styles/presets
- [ ] Offline mode with cached images

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided as-is for educational purposes. Please respect OpenAI's terms of service when using the DALL-E API.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review OpenAI's documentation
3. Open an issue on GitHub

---

**Note**: This app requires an active internet connection and valid OpenAI API key with DALL-E access.