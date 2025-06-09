#!/bin/bash
# Script to fix common Gradle issues in Android builds

echo "Applying Gradle fixes..."

# Find all build directories
BUILD_DIRS=$(find .buildozer -name "build.gradle" -type f 2>/dev/null | xargs dirname | sort -u)

if [ -z "$BUILD_DIRS" ]; then
    echo "No build.gradle files found. Build may not have started yet."
    exit 1
fi

for BUILD_DIR in $BUILD_DIRS; do
    echo "Processing: $BUILD_DIR"
    cd "$BUILD_DIR"
    
    # Fix 1: Replace deprecated jcenter with mavenCentral
    echo "  - Updating repositories..."
    find . -name "build.gradle" -type f -exec sed -i.bak 's/jcenter()/mavenCentral()/g' {} \;
    find . -name "build.gradle" -type f -exec sed -i 's/jcenter()/mavenCentral()/g' {} \;
    
    # Fix 2: Add google() repository if missing
    for gradle_file in $(find . -name "build.gradle" -type f); do
        if ! grep -q "google()" "$gradle_file"; then
            echo "  - Adding Google repository to $gradle_file"
            sed -i '/repositories {/a \        google()' "$gradle_file"
        fi
    done
    
    # Fix 3: Update Android Gradle Plugin to compatible version
    echo "  - Updating Gradle plugin version..."
    find . -name "build.gradle" -type f -exec sed -i 's/com.android.tools.build:gradle:[0-9.]\+/com.android.tools.build:gradle:7.2.2/g' {} \;
    
    # Fix 4: Update Gradle wrapper if exists
    if [ -f "gradle/wrapper/gradle-wrapper.properties" ]; then
        echo "  - Updating Gradle wrapper..."
        sed -i 's/distributionUrl=.*gradle-.*-all.zip/distributionUrl=https\\:\\/\\/services.gradle.org\\/distributions\\/gradle-7.4.2-all.zip/g' gradle/wrapper/gradle-wrapper.properties
    fi
    
    # Fix 5: Fix potential duplicate repository declarations
    echo "  - Cleaning duplicate declarations..."
    for gradle_file in $(find . -name "build.gradle" -type f); do
        # Remove duplicate google() entries
        awk '!seen[$0]++ || !/google\(\)/' "$gradle_file" > "$gradle_file.tmp" && mv "$gradle_file.tmp" "$gradle_file"
    done
    
    cd - > /dev/null
done

echo "Gradle fixes applied!"
echo ""
echo "Additional manual fixes that might be needed:"
echo "1. Ensure JAVA_HOME points to Java 11:"
echo "   export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64"
echo ""
echo "2. Clear Gradle cache if issues persist:"
echo "   rm -rf ~/.gradle/caches/"
echo "   rm -rf ~/.gradle/daemon/"
echo ""
echo "3. If SSL errors occur, add to gradle.properties:"
echo "   systemProp.https.protocols=TLSv1.2"
