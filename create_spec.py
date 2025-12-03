#!/usr/bin/env python3
import sys
import os

# ?????????? buildozer.spec  BOM
spec_content = '''[app]
title = ARTEM Messenger
package.name = artem.messenger
package.domain = artem
source.dir = .
version = 1.0
requirements = python3,flet
orientation = portrait
android.api = 33
android.minapi = 21

[buildozer]
log_level = 2'''

# ???? ????  BOM
with open('buildozer.spec', 'wb') as f:
    f.write(spec_content.encode('utf-8'))

print("buildozer.spec created without BOM")

# ???????? ?????? ?????
with open('buildozer.spec', 'rb') as f:
    first_bytes = f.read(10)
    print(f"First 10 bytes (hex): {first_bytes.hex()}")
    
    # ????? ?????????? ? 0x5B = '['
    if first_bytes[0] == 0x5B:
        print("? File starts with '[' - NO BOM")
    else:
        print(f"? File starts with {hex(first_bytes[0])} -???BOM")
        sys.exit(1)
