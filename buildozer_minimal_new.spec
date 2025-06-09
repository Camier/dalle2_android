[app]
title = DALL-E AI Art
package.name = dalleai
package.domain = com.camier
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

# Use full version with all features
source.main = main_full.py

# Minimal requirements first
requirements = python3,kivy==2.2.1,kivymd==1.1.1,requests,pillow

# Resources
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png

# Basic Android config
orientation = portrait
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.arch = arm64-v8a
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

[buildozer]
log_level = 2
warn_on_root = 1
