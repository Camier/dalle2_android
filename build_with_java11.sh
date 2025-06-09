#!/bin/bash
cd /home/mik/dalle_android

echo "=== Building with Java 11 ==="
source venv/bin/activate

# Use Java 11
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/usr/lib/wsl/lib

echo "Java version:"
java -version

# Clean gradle
pkill -f gradle
rm -rf ~/.gradle/daemon

# Ensure simplified version
cp main_simple.py main.py
cp buildozer_simple.spec buildozer.spec

# Build
buildozer android debug 2>&1 | tee build_java11.log

# Check result
if [ -f bin/*.apk ]; then
    echo "✅ SUCCESS!"
    ls -la bin/*.apk
else
    echo "❌ Failed. Check build_java11.log"
fi
EOF && chmod +x build_with_java11.sh
