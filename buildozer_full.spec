[app]
title = DALL-E AI Art
package.name = dalleaiart
package.domain = com.aiart
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0.0

# Requirements - order matters! Added opencv and numpy for inpainting
requirements = python3,kivy==2.3.0,pyjnius,android,openai,pillow,requests,certifi,chardet,idna,urllib3,opencv-python,numpy

# Android configuration
android.permissions = INTERNET,ACCESS_NETWORK_STATE
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a

# Build settings
android.release = False
android.debug = True
log_level = 2
warn_on_root = 0

# Gradle configuration
android.gradle_dependencies = androidx.appcompat:appcompat:1.4.1
android.enable_androidx = True
android.add_gradle_repositories = google(),mavenCentral()

[buildozer]
# Prevent re-downloading
android.skip_update = False
android.auto_update_sdk = False

# Use local recipes
p4a.local_recipes = ./recipes
