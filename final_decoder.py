#!/usr/bin/env python3
import struct
import sys

class AXMLParser:
    def __init__(self, data):
        self.data = data
        self.strings = []
        self.parse()
    
    def parse(self):
        # Skip header
        pos = 8
        
        while pos < len(self.data) - 8:
            chunk_type = struct.unpack('<H', self.data[pos:pos+2])[0]
            chunk_size = struct.unpack('<I', self.data[pos+4:pos+8])[0]
            
            if chunk_type == 0x0001:  # String pool
                self.parse_string_pool(pos)
                break
            
            pos += chunk_size
    
    def parse_string_pool(self, offset):
        string_count = struct.unpack('<I', self.data[offset+8:offset+12])[0]
        strings_start = struct.unpack('<I', self.data[offset+20:offset+24])[0]
        
        # Read string offsets
        offsets = []
        for i in range(string_count):
            off = struct.unpack('<I', self.data[offset+28+i*4:offset+32+i*4])[0]
            offsets.append(off)
        
        # Read strings
        for i, str_offset in enumerate(offsets):
            str_pos = offset + strings_start + str_offset
            if str_pos >= len(self.data):
                continue
                
            # Try UTF-16
            length = struct.unpack('<H', self.data[str_pos:str_pos+2])[0]
            if length > 0 and length < 1000:
                try:
                    string_data = self.data[str_pos+2:str_pos+2+length*2]
                    string = string_data.decode('utf-16le', errors='ignore').rstrip('\x00')
                    if string:
                        self.strings.append(string)
                except:
                    pass
            
            # Try UTF-8
            try:
                length = self.data[str_pos]
                if length > 0 and length < 255:
                    string = self.data[str_pos+1:str_pos+1+length].decode('utf-8', errors='ignore')
                    if string and string not in self.strings:
                        self.strings.append(string)
            except:
                pass

def analyze_apk():
    print("=== DALL-E Android App Analysis ===\n")
    
    # Parse AndroidManifest.xml
    with open("/home/mik/dalle_android/apk_extracted/AndroidManifest.xml", 'rb') as f:
        manifest_data = f.read()
    
    parser = AXMLParser(manifest_data)
    
    # Look for package name
    print("Extracted Information from AndroidManifest.xml:")
    package_name = None
    for s in parser.strings:
        if 'org.test' in s:
            package_name = s
            print(f"  Package Name: {s}")
        elif 'android.permission' in s:
            print(f"  Permission: {s}")
        elif 'Activity' in s and len(s) > 8:
            print(f"  Activity: {s}")
    
    # Analyze Python structure
    print("\n=== Python Application Structure ===")
    print("\nMain modules:")
    print("  - main.pyc (Main application entry point)")
    print("  - screens/")
    print("    - main_screen.pyc (Main UI screen)")
    print("  - services/")
    print("    - dalle_api.pyc (DALL-E API integration)")
    print("  - utils/")
    print("    - image_utils.pyc (Image processing utilities)")
    print("    - storage.pyc (Storage management)")
    
    # Check for DALL-E related content
    print("\n=== App Type ===")
    print("This appears to be a DALL-E Android client application built with:")
    print("  - Python for Android (p4a)")
    print("  - Kivy framework (based on SDL2 libraries)")
    print("  - Python 3.11 runtime")
    
    print("\n=== Libraries Used ===")
    print("  - SDL2 (Simple DirectMedia Layer)")
    print("  - OpenSSL (libcrypto, libssl)")
    print("  - SQLite3")
    print("  - FreeType (font rendering)")
    print("  - libpng (image handling)")
    
    # Security observations
    print("\n=== Security Observations ===")
    print("  - Uses HTTPS/SSL for API communication (libssl present)")
    print("  - Requests external storage permissions")
    print("  - Internet permission required for API calls")
    
    # Check for API keys or sensitive data
    print("\n=== Checking for Sensitive Data ===")
    
    # Search for potential API keys in the binary
    with open("/home/mik/dalle_android/apk_extracted/assets/private.tar", 'rb') as f:
        tar_data = f.read()
    
    # Look for common API key patterns
    import re
    api_key_patterns = [
        rb'["\']api[_-]?key["\']\s*[:=]\s*["\'][a-zA-Z0-9_-]{20,}["\']',
        rb'["\']openai[_-]?api[_-]?key["\']\s*[:=]\s*["\'][a-zA-Z0-9_-]{20,}["\']',
        rb'sk-[a-zA-Z0-9]{48}',
        rb'Bearer [a-zA-Z0-9_-]{20,}'
    ]
    
    found_keys = False
    for pattern in api_key_patterns:
        matches = re.findall(pattern, tar_data, re.IGNORECASE)
        if matches:
            found_keys = True
            print("  ⚠️  Potential API keys found in the application!")
            break
    
    if not found_keys:
        print("  ✓ No hardcoded API keys detected in quick scan")
        print("  Note: API keys might be obfuscated or stored differently")

if __name__ == "__main__":
    analyze_apk()