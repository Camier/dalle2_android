#!/usr/bin/env python3
import urllib.request
import time

urls = [
    "https://github.com",
    "https://pypi.org",
    "https://download.savannah.gnu.org",
    "https://www.python.org"
]

print("Testing network connectivity...")
for url in urls:
    try:
        start = time.time()
        response = urllib.request.urlopen(url, timeout=10)
        elapsed = time.time() - start
        print(f"✓ {url} - {response.status} ({elapsed:.2f}s)")
    except Exception as e:
        print(f"✗ {url} - {str(e)}")

print("\nTesting download speed...")
test_url = "https://www.python.org/ftp/python/3.11.5/Python-3.11.5.tgz"
try:
    start = time.time()
    response = urllib.request.urlopen(test_url, timeout=30)
    # Read first 1MB
    data = response.read(1024 * 1024)
    elapsed = time.time() - start
    speed = (len(data) / elapsed) / 1024 / 1024  # MB/s
    print(f"\nDownload speed: {speed:.2f} MB/s")
except Exception as e:
    print(f"\nDownload test failed: {str(e)}")