#!/bin/bash

# Auto-generate release keystore with secure defaults
# For production, use the interactive version

echo "=== Auto-Generating DALL-E AI Art Release Keystore ==="
echo "Creating keystore with secure default password..."

# Keystore configuration
KEYSTORE_FILE="./dalle-ai-art-release.keystore"
KEY_ALIAS="dalle-ai-art-key"
# In production, use a secure password manager
STOREPASS="DalleSecure2025#Release"
KEYPASS="DalleSecure2025#Release"

# Remove existing keystore if present
rm -f "$KEYSTORE_FILE"

# Generate keystore non-interactively
keytool -genkeypair \
    -alias "$KEY_ALIAS" \
    -keyalg RSA \
    -keysize 4096 \
    -sigalg SHA256withRSA \
    -validity 10950 \
    -keystore "$KEYSTORE_FILE" \
    -storepass "$STOREPASS" \
    -keypass "$KEYPASS" \
    -dname "CN=DALL-E AI Art, OU=Mobile Development, O=AI Art Generator, L=San Francisco, ST=CA, C=US" \
    2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Keystore generated successfully!"
    
    # Create keystore properties file
    cat > keystore.properties << EOF
# Release keystore configuration
# KEEP THIS FILE SECURE - DO NOT COMMIT TO VERSION CONTROL
storeFile=$KEYSTORE_FILE
storePassword=$STOREPASS
keyAlias=$KEY_ALIAS
keyPassword=$KEYPASS
EOF
    
    # Set secure permissions
    chmod 600 "$KEYSTORE_FILE"
    chmod 600 keystore.properties
    
    echo ""
    echo "Keystore details:"
    echo "  Path: $KEYSTORE_FILE"
    echo "  Alias: $KEY_ALIAS"
    echo "  Config: keystore.properties"
    echo ""
    echo "⚠️  SECURITY REMINDER:"
    echo "  - Change the default passwords before production use"
    echo "  - Store keystore and passwords securely"
    echo "  - Never commit to version control"
else
    echo "❌ Failed to generate keystore"
    exit 1
fi