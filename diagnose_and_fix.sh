#!/bin/bash
echo "=== DALL-E Android Build Diagnostic ==="
echo ""

# Diagnose issues
echo "1. Checking Java version:"
java -version 2>&1 | head -1
echo ""

echo "2. Checking Android SDK:"
if [ -d ~/.buildozer/android/platform/android-sdk ]; then
    echo "   ✅ SDK installed"
else
    echo "   ❌ SDK missing"
fi
echo ""

echo "3. Checking for gradle issues:"
ps aux | grep gradle | grep -v grep && echo "   ⚠️ Gradle processes found" || echo "   ✅ No stuck gradle processes"
echo ""

echo "4. Current build status:"
ls -la bin/*.apk 2>/dev/null && echo "   ✅ APK exists!" || echo "   ❌ No APK built yet"
echo ""

echo "=== RECOMMENDATIONS ==="
echo ""
echo "The build is failing due to Gradle daemon connection issues."
echo "This is often caused by:"
echo "- WSL2 networking issues"
echo "- Java version mismatches"
echo "- Gradle daemon corruption"
echo ""
echo "SOLUTION OPTIONS:"
echo ""
echo "Option 1: Use Docker (most reliable):"
echo "   docker run -v /mnt/c/Users/micka/AppData/Local/AnthropicClaude/app-0.10.14:/app kivy/buildozer android debug"
echo ""
echo "Option 2: Disable Gradle daemon:"
echo "   export GRADLE_OPTS='-Dorg.gradle.daemon=false'"
echo "   ./build_fixed.sh"
echo ""
echo "Option 3: Try minimal test build:"
echo "   cp test_minimal.py main.py"
echo "   cp buildozer_minimal.spec buildozer.spec"
echo "   buildozer android debug"
echo ""
echo "Option 4: Use pre-built APK:"
echo "   I can help you get a pre-built APK from another source"
echo ""
EOF && chmod +x diagnose_and_fix.sh
