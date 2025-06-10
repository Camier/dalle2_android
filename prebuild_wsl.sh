#!/bin/bash
# Fix any permission issues before build
find .buildozer -type d -exec chmod 755 {} \; 2>/dev/null || true
find .buildozer -name "*.py" -exec chmod 644 {} \; 2>/dev/null || true
find .buildozer -name "*.pyx" -exec chmod 644 {} \; 2>/dev/null || true
find .buildozer -name "*.pxi" -exec chmod 644 {} \; 2>/dev/null || true
