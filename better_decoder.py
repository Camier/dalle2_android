#!/usr/bin/env python3
import struct
import re

def parse_axml(filename):
    """Parse Android Binary XML and extract key information"""
    with open(filename, 'rb') as f:
        data = f.read()
    
    print("=== Android APK Analysis ===\n")
    
    # Look for package name patterns in the binary
    print("Package Information:")
    package_pattern = rb'org\.test\.[a-zA-Z0-9_]+'
    matches = re.findall(package_pattern, data)
    if matches:
        for match in set(matches):
            print(f"  Package: {match.decode('utf-8', errors='ignore')}")
    
    # Look for activity names
    print("\nActivities:")
    activity_pattern = rb'[a-zA-Z0-9_.]+Activity'
    activities = re.findall(activity_pattern, data)
    for activity in set(activities):
        decoded = activity.decode('utf-8', errors='ignore')
        if len(decoded) > 5 and '.' not in decoded[:3]:
            print(f"  - {decoded}")
    
    # Look for permissions
    print("\nPermissions:")
    permission_patterns = [
        rb'android\.permission\.[A-Z_]+',
        rb'INTERNET',
        rb'READ_EXTERNAL_STORAGE',
        rb'WRITE_EXTERNAL_STORAGE',
        rb'CAMERA',
        rb'ACCESS_NETWORK_STATE'
    ]
    
    found_permissions = set()
    for pattern in permission_patterns:
        matches = re.findall(pattern, data)
        for match in matches:
            perm = match.decode('utf-8', errors='ignore')
            if 'android.permission' in perm or perm in ['INTERNET', 'READ_EXTERNAL_STORAGE', 'WRITE_EXTERNAL_STORAGE']:
                found_permissions.add(perm)
    
    for perm in sorted(found_permissions):
        print(f"  - {perm}")
    
    # Look for version information
    print("\nVersion Information:")
    # Look for numeric patterns that might be version codes
    version_data = data[1000:2000]  # Check a section where version info might be
    for i in range(len(version_data) - 4):
        val = struct.unpack('<I', version_data[i:i+4])[0]
        if 1 <= val <= 100:  # Reasonable version code range
            print(f"  Possible version code: {val}")
            break
    
    # Check strings in the data
    print("\nOther interesting strings:")
    interesting_patterns = [
        rb'dalle',
        rb'DALLE',
        rb'main\.py',
        rb'\.pyc',
        rb'kivy',
        rb'python',
        rb'SDL'
    ]
    
    for pattern in interesting_patterns:
        if re.search(pattern, data, re.IGNORECASE):
            matches = re.findall(pattern, data, re.IGNORECASE)
            if matches:
                print(f"  Found: {matches[0].decode('utf-8', errors='ignore')}")

# Also check the private.tar structure
print("\n=== Python App Structure ===")
import os

assets_dir = "/home/mik/dalle_android/apk_extracted/assets"
if os.path.exists(assets_dir):
    print("\nPython modules found:")
    for root, dirs, files in os.walk(assets_dir):
        for file in files:
            if file.endswith('.pyc'):
                rel_path = os.path.relpath(os.path.join(root, file), assets_dir)
                module_name = rel_path.replace('/', '.').replace('.pyc', '')
                print(f"  - {module_name}")

if __name__ == "__main__":
    parse_axml("/home/mik/dalle_android/apk_extracted/AndroidManifest.xml")