# Quick Fix for Build Issues

## If you see "Cython not found" error:
```bash
source venv/bin/activate
pip install cython
```

## If you see "Aidl not found" or license errors:

The build process is downloading and installing Android SDK components automatically. This is normal for the first build and takes 10-20 minutes.

## Current Status:
- ✅ Cython installed
- ✅ Android licenses pre-accepted
- 🔄 Android SDK components downloading (build-tools, platform-tools)
- 🔄 First build in progress

## To monitor build progress:
```bash
source venv/bin/activate
buildozer android debug
```

## Expected first build time: 15-30 minutes
- Downloads Android SDK components
- Downloads Android NDK
- Compiles Python for Android
- Builds all dependencies
- Creates APK

## After first build completes:
- APK will be in: `bin/dalleimages-1.0.0-arm64-v8a_armeabi-v7a-debug.apk`
- Subsequent builds only take 1-2 minutes

## If build fails:
```bash
# Clean and retry
buildozer android clean
buildozer android debug
```