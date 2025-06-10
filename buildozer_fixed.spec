[app]
title = DALL-E AI Art
package.name = dalleaiart
package.domain = com.aiart
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt,ttf,otf,xml
version = 1.0.0

# Minimal requirements without specific SDL2 versions
# Buildozer will automatically include SDL2 dependencies needed by Kivy
requirements = python3,kivy==2.3.0,kivymd,pillow,requests,certifi,urllib3,cryptography,pycryptodome,openai,pyjnius,android

# Orientation
orientation = portrait

# Android configuration
android.permissions = INTERNET,VIBRATE,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True
android.archs = arm64-v8a,armeabi-v7a

# Build optimizations
android.release = False
android.minify_code = 0
android.optimize_python = 1

# Local recipes
p4a.local_recipes = ./recipes
p4a.prebuild_cmd = ./prebuild.sh

# Enable features
android.gradle_dependencies = com.google.android.material:material:1.5.0,androidx.appcompat:appcompat:1.4.1
android.enable_androidx = True
android.add_gradle_repositories = google(),mavenCentral()

# App assets
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png
android.splash_color = #FFFFFF

# Build settings
log_level = 2
warn_on_root = 1

[buildozer]
android.skip_update = False