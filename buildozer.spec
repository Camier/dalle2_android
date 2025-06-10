[app]
title = DALL-E 2 Complete
package.name = dalle2complete
package.domain = com.aiart
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
version = 2.0

# Requirements including opencv for inpainting
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pillow,requests,certifi,urllib3,openai,pyjnius,android,cryptography,numpy

# Resources
presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png

# Android configuration
orientation = portrait
fullscreen = 0
android.api = 31
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.arch = arm64-v8a

# Permissions for all features
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,ACCESS_NETWORK_STATE,VIBRATE

# Android specific
android.gradle_dependencies = com.google.android.material:material:1.6.1, androidx.appcompat:appcompat:1.4.2
android.enable_androidx = True
android.add_gradle_maven_dependencies = True
android.gradle_repositories = google(),mavenCentral(),jcenter()

# Build settings
android.release = False
android.debug = True
p4a.bootstrap = sdl2
log_level = 2
warn_on_root = 0

# Exclude unnecessary files
android.blacklist_src = venv,tests,*.pyc,*.pyo

[buildozer]
# Buildozer settings
log_level = 2
warn_on_root = 0

# Custom build options
android.skip_update = False
android.gradle_timeout = 300
