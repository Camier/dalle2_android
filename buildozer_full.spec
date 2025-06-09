[app]
# Basic application info
title = DALL-E AI Art Generator
package.name = dalleaiart
package.domain = com.camier
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,md
version = 1.0

# Main script
source.main = main_full.py

# Application requirements
requirements = python3,kivy==2.2.1,kivymd==1.1.1,requests,pillow,certifi,urllib3,idna,charset-normalizer

# Graphics
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png

# Orientation
orientation = portrait
fullscreen = 0

# Android specific
android.api = 31
android.minapi = 21
android.ndk = 25b
android.sdk = 31
android.accept_sdk_license = True
android.arch = arm64-v8a
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE
android.gradle_dependencies = com.google.android.material:material:1.6.1

# Whitelist for including specific files
android.whitelist = lib-dynload/termios.so

# Application metadata
android.meta_data = com.google.android.gms.ads.APPLICATION_ID=ca-app-pub-xxxxx~xxxxx

# iOS specific (for future)
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.7.0

[buildozer]
# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .ipa) storage
bin_dir = ./bin

# Custom source folders
exclude_dirs = venv,build,dist,__pycache__,.git,.buildozer,bin

# Build configuration
android.release_artifact = apk
android.aab_copies_apk = False
android.p4a_branch = master
