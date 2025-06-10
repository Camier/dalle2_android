#!/bin/bash
# Fix any Python 2/3 compatibility issues
find .buildozer -name "*.pyx" -o -name "*.pxi" | while read file; do
    if grep -q '\blong\b' "$file" 2>/dev/null; then
        echo "Patching $file..."
        sed -i 's/\blong\b/int/g' "$file"
    fi
done
