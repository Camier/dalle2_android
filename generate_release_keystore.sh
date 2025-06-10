#!/bin/bash

# DALL-E AI Art Release Keystore Generator
# This script generates a secure keystore for signing the release APK

echo "=== DALL-E AI Art Release Keystore Generator ==="
echo "This will create a keystore for signing your release APK."
echo "IMPORTANT: Keep the keystore and passwords secure!"
echo ""

# Set keystore parameters
KEYSTORE_PATH="./dalle-ai-art-release.keystore"
KEY_ALIAS="dalle-ai-art-key"
VALIDITY_DAYS=10950  # 30 years

# Check if keystore already exists
if [ -f "$KEYSTORE_PATH" ]; then
    echo "WARNING: Keystore already exists at $KEYSTORE_PATH"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborting..."
        exit 1
    fi
fi

# Get user information
read -p "Enter your full name (CN): " CN
read -p "Enter your organizational unit (OU): " OU
read -p "Enter your organization (O): " O
read -p "Enter your city/locality (L): " L
read -p "Enter your state/province (ST): " ST
read -p "Enter your country code (C) [e.g., US]: " C

# Generate keystore
echo ""
echo "Generating keystore..."
echo "You will be prompted to create and confirm a keystore password."
echo "You will also need to create a key password (can be the same)."
echo ""

keytool -genkeypair \
    -keystore "$KEYSTORE_PATH" \
    -alias "$KEY_ALIAS" \
    -keyalg RSA \
    -keysize 4096 \
    -sigalg SHA256withRSA \
    -validity $VALIDITY_DAYS \
    -dname "CN=$CN, OU=$OU, O=$O, L=$L, ST=$ST, C=$C"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Keystore generated successfully!"
    echo ""
    echo "Keystore details:"
    echo "  Path: $KEYSTORE_PATH"
    echo "  Alias: $KEY_ALIAS"
    echo "  Algorithm: RSA 4096-bit"
    echo "  Signature: SHA256withRSA"
    echo "  Validity: $VALIDITY_DAYS days"
    echo ""
    echo "⚠️  IMPORTANT SECURITY NOTES:"
    echo "1. Store the keystore file securely (backup to secure location)"
    echo "2. Never commit the keystore to version control"
    echo "3. Remember your passwords - they cannot be recovered"
    echo "4. You'll need this keystore for all future app updates"
    echo ""
    echo "Creating .gitignore entry for keystore..."
    echo "*.keystore" >> .gitignore
    echo "*.jks" >> .gitignore
    echo ""
    echo "Creating keystore configuration file..."
    cat > keystore.properties << EOF
# Release keystore configuration
# DO NOT COMMIT THIS FILE TO VERSION CONTROL
key.store=$KEYSTORE_PATH
key.alias=$KEY_ALIAS
# Add passwords when building (do not store here)
# key.store.password=YOUR_KEYSTORE_PASSWORD
# key.alias.password=YOUR_KEY_PASSWORD
EOF
    echo "✅ Configuration saved to keystore.properties"
else
    echo "❌ Failed to generate keystore"
    exit 1
fi