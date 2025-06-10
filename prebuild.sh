#!/bin/bash
echo "Running prebuild fixes..."

# Fix Cython language level globally
export CYTHON_DIRECTIVE="language_level=3"
export CYTHON_LANGUAGE_LEVEL=3

# Find all pyjnius files and fix them
find . -name "*.pyx" -o -name "*.pxi" | while read file; do
    if [[ "$file" == *"pyjnius"* ]] && grep -q '\blong\b' "$file" 2>/dev/null; then
        echo "Patching $file for Python 3..."
        sed -i.bak 's/\blong\b/int/g' "$file"
        sed -i.bak 's/basestring/str/g' "$file"
    fi
done

# Create Cython directives for all setup.py files
find . -name "setup.py" | while read setup; do
    dir=$(dirname "$setup")
    if [[ "$dir" == *"pyjnius"* ]] || [[ "$dir" == *"jnius"* ]]; then
        echo "[build_ext]" > "$dir/setup.cfg"
        echo "cython-directives=language_level=3" >> "$dir/setup.cfg"
    fi
done

echo "Prebuild fixes complete"
