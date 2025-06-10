#!/usr/bin/env python3
import struct
import sys

def read_string_from_pool(data, string_pool_offset, index):
    """Read a string from the string pool"""
    if index == 0xFFFFFFFF:
        return ""
    
    # Navigate to string offset table
    offset_pos = string_pool_offset + 8 + (index * 4)
    if offset_pos + 4 > len(data):
        return ""
    
    string_offset = struct.unpack('<I', data[offset_pos:offset_pos+4])[0]
    string_pos = string_pool_offset + 8 + string_offset
    
    if string_pos >= len(data):
        return ""
    
    # Read UTF-16 string
    result = []
    pos = string_pos + 2  # Skip length bytes
    while pos < len(data) - 1:
        char = struct.unpack('<H', data[pos:pos+2])[0]
        if char == 0:
            break
        result.append(chr(char))
        pos += 2
    
    return ''.join(result)

def parse_android_manifest(filename):
    """Simple parser for Android binary XML"""
    with open(filename, 'rb') as f:
        data = f.read()
    
    # Check magic number
    magic = struct.unpack('<H', data[0:2])[0]
    if magic != 0x0003:
        print(f"Invalid magic number: {hex(magic)}")
        return
    
    # Get file size
    file_size = struct.unpack('<I', data[4:8])[0]
    print(f"File size: {file_size} bytes")
    
    # Find string pool
    offset = 8
    string_pool_offset = 0
    string_count = 0
    
    while offset < len(data):
        chunk_type = struct.unpack('<H', data[offset:offset+2])[0]
        chunk_size = struct.unpack('<I', data[offset+4:offset+8])[0]
        
        if chunk_type == 0x0001:  # String pool
            string_pool_offset = offset
            string_count = struct.unpack('<I', data[offset+8:offset+12])[0]
            print(f"Found string pool at offset {offset} with {string_count} strings")
            
            # Print some strings
            print("\nSample strings from pool:")
            for i in range(min(string_count, 50)):
                s = read_string_from_pool(data, string_pool_offset, i)
                if s and len(s) > 2:
                    print(f"  [{i}]: {s}")
            break
            
        offset += chunk_size
    
    # Look for package name pattern
    print("\nSearching for package name...")
    for i in range(len(data) - 10):
        if data[i:i+3] == b'com' or data[i:i+3] == b'org' or data[i:i+3] == b'net':
            # Try to extract as string
            try:
                end = data.find(b'\x00', i)
                if end > i and end - i < 100:
                    potential_pkg = data[i:end].decode('utf-8', errors='ignore')
                    if '.' in potential_pkg and len(potential_pkg) > 5:
                        print(f"Potential package: {potential_pkg}")
            except:
                pass

if __name__ == "__main__":
    parse_android_manifest("/home/mik/dalle_android/apk_extracted/AndroidManifest.xml")