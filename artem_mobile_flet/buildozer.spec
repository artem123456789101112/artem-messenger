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
android.ndk = 25b
android.ndk_path = /tmp/android-ndk-r25b
android.sdk_path = /tmp/android-cmdline-tools
android.accept_sdk_license = True
android.archs = arm64-v8a,armeabi-v7a

# Permissions
android.permissions = INTERNET, ACCESS_NETWORK_STATE

# Buildozer settings
[buildozer]
log_level = 2
warn_on_root = 1
