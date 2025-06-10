#!/bin/bash

echo "=== Quick Fix for Slow Downloads ==="

# 1. Clean up stuck processes
pkill -9 buildozer python timeout || true

# 2. Use system python and buildozer
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH
export PYJNIUS_PYTHON_VERSION=3

# 3. Install buildozer system-wide if needed
if ! command -v buildozer &> /dev/null; then
    pip3 install --user buildozer
fi

# 4. Create minimal test to verify setup
cat > main_minimal.py << 'EOF'
from kivy.app import App
from kivy.uix.label import Label

class TestApp(App):
    def build(self):
        return Label(text='Hello Android!')

if __name__ == '__main__':
    TestApp().run()
EOF

# 5. Backup main.py and use minimal
mv main.py main_backup.py
mv main_minimal.py main.py

# 6. Try build with system buildozer
echo "=== Starting minimal build ==="
~/.local/bin/buildozer android debug 2>&1 | grep -v "Download [0-9]" | tee quick_build.log

# 7. Restore original main.py
mv main.py main_minimal.py
mv main_backup.py main.py

# Check result
if [ -f "bin/dalleaiart-1.0.0-debug.apk" ]; then
    echo "=== SUCCESS! APK created ==="
    ls -lh bin/*.apk
else
    echo "=== Checking build status ==="
    tail -50 quick_build.log | grep -E "(Building|Compiling|ERROR|error)"
fi