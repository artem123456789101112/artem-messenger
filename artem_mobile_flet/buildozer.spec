[app]
title = ARTEM Messenger
package.name = artem.messenger
package.domain = org.artem
source.dir = .
version = 1.0.0
requirements = python3,kivy==2.3.0,cython,flet==0.21.2
orientation = portrait
fullscreen = 0
android.api = 33
android.minapi = 21
android.accept_sdk_license = true
android.ndk = 25b
android.sdk = 33

[buildozer]
log_level = 2
warn_on_root = 1

[app:source.exclude_patterns]
*.pyc
__pycache__
.buildozer
