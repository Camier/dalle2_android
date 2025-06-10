[app]
# Application metadata
title = DALL-E AI Art
package.name = dalleaiart
package.domain = com.dalleandroid
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,md
version = 1.0.1

# Main entry point
source.main = main.py

# Requirements with specific versions for security
requirements = python3==3.11.0,kivy==2.2.1,kivymd==1.1.1,requests==2.31.0,pillow==10.2.0,cryptography==41.0.7,certifi==2023.11.17

# Application resources
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png

# Android configuration
orientation = portrait
fullscreen = 0

# Android API levels
android.api = 33
android.minapi = 24
android.ndk = 25c
android.sdk = 33
android.accept_sdk_license = True

# Architecture - support both arm64 and armeabi for wider compatibility
android.archs = arm64-v8a,armeabi-v7a

# Permissions - only what's necessary
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Release build configuration
android.release_artifact = apk
android.debug = False

# Optimization
android.optimize_python = True
android.skip_byte_compile_for_files = 

# Security features
android.gradle_dependencies = com.google.android.gms:play-services-safetynet:18.0.1,androidx.security:security-crypto:1.1.0-alpha06

# Proguard for code obfuscation
android.add_gradle_maven_dependencies = True
android.gradle_repositories = google(),mavenCentral()
android.enable_androidx = True
android.add_src = 

# App bundle configuration for Google Play
android.aab = False

# Privacy and security metadata
android.meta_data = com.google.android.gms.ads.AD_MANAGER_APP=true

# Build optimizations
p4a.branch = stable
p4a.bootstrap = sdl2
p4a.local_recipes = ./recipes

[buildozer]
# Build configuration
log_level = 1
warn_on_root = 1

# Build in release mode
build_mode = release

# Clean build
clean_build = True

# Parallel build
parallel = True

# Release signing configuration
android.release_artifact = apk
android.keystore = ./dalle-ai-art-release.keystore
android.keystore_alias = dalle-ai-art-key
# Passwords will be prompted during build for security
# android.keystore_password = 
# android.keyalias_password =