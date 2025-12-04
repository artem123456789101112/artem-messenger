[app]
title = ARTEM Messenger
package.name = artem.messenger
package.domain = org.artem
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,flet==0.21.2
orientation = portrait
fullscreen = 0

# Android configurations
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 25b
android.ndk_path = /tmp/android-ndk-r25b
android.sdk_path = /usr/local/lib/android/sdk
android.accept_sdk_license = True
android.arch = arm64-v8a

# Buildozer settings
[buildozer]
log_level = 2
warn_on_root = 1

# Permissions
android.permissions = INTERNET, ACCESS_NETWORK_STATE

# Presplash
#presplash.filename = %(source.dir)s/assets/icon.png
#icon.filename = %(source.dir)s/assets/icon.png
