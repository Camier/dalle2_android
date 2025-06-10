#!/bin/bash
source venv/bin/activate

# WSL-specific environment
export ANDROID_HOME=$HOME/.buildozer/android/platform/android-sdk
export ANDROID_NDK_HOME=$HOME/.buildozer/android/platform/android-ndk-r25b
export PATH=$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools

# Disable some problematic gradle features in WSL
export GRADLE_OPTS="-Dorg.gradle.daemon=false"

# Build with verbose output
buildozer -v android debug 2>&1 | tee wsl_build.log
