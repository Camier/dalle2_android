# How to Install the DALL-E APK on Your Android Device

## Method 1: Direct File Transfer (Easiest)

1. **Locate the APK:**
   ```bash
   ls -la bin/*.apk
   ```
   File: `bin/dalleimages-1.0.0-arm64-v8a_armeabi-v7a-debug.apk`

2. **Copy to Windows (if using WSL):**
   ```bash
   cp bin/*.apk /mnt/c/Users/YOUR_USERNAME/Desktop/
   ```

3. **Transfer to Phone:**
   - Email the APK to yourself
   - Upload to Google Drive/Dropbox
   - Use USB cable to copy directly

4. **Install on Phone:**
   - Enable "Install from Unknown Sources" in Settings
   - Open the APK file on your phone
   - Tap "Install"

## Method 2: Using ADB from Windows

If ADB doesn't work in WSL, use Windows ADB:

1. **Download ADB for Windows:**
   - https://developer.android.com/studio/releases/platform-tools
   - Extract to C:\adb

2. **Copy APK to Windows:**
   ```bash
   cp bin/*.apk /mnt/c/adb/
   ```

3. **Install from Windows CMD:**
   ```cmd
   cd C:\adb
   adb install dalleimages-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
   ```

## Method 3: Using a File Manager App

1. **Copy APK to shared folder:**
   ```bash
   cp bin/*.apk /mnt/c/Users/Public/
   ```

2. **On your phone:**
   - Install a file manager (like Files by Google)
   - Connect phone to PC via USB
   - Copy APK from PC to phone's Downloads folder
   - Open file manager and install

## Method 4: QR Code (Quick Share)

1. **Upload APK to temporary hosting:**
   - Use file.io, WeTransfer, or similar
   - Get shareable link

2. **Generate QR code:**
   - Visit qr-code-generator.com
   - Paste your link
   - Scan with phone

## Enable Installation on Android

### For Android 8.0+:
1. Settings → Apps & notifications
2. Advanced → Special app access
3. Install unknown apps
4. Select your browser/file manager
5. Allow from this source

### For older Android:
1. Settings → Security
2. Enable "Unknown sources"

## After Installation

1. Open "DALL-E Image Generator" app
2. Enter your OpenAI API key when prompted
3. Start generating images!

## Troubleshooting

**"App not installed" error:**
- Ensure you have enough storage space
- Check if an older version is installed (uninstall first)
- Verify your Android version is 5.0+

**"Parse error":**
- APK might be corrupted during transfer
- Re-copy the file
- Make sure you're copying the complete file

**Can't find APK on phone:**
- Check Downloads folder
- Check file manager's recent files
- Search for "dalleimages" in file manager