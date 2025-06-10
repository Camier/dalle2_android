# Production APK Build Checklist

## Pre-Build Verification

### 1. Security Configuration
- [ ] Update keystore passwords in buildozer.spec (use strong passwords)
- [ ] Verify network_security_config.xml is properly configured
- [ ] Check certificate pinning is up to date
- [ ] Review ProGuard rules for sensitive code obfuscation
- [ ] Ensure all API keys are encrypted and not hardcoded

### 2. App Metadata
- [ ] Verify package name follows reverse domain notation (com.aiart.dalleaiart)
- [ ] Increment version code for each release
- [ ] Update version name if needed
- [ ] Verify app title and description

### 3. Permissions
- [ ] Review Android permissions - only request what's necessary
- [ ] Remove any debug permissions
- [ ] Test app with minimal permissions

### 4. Assets
- [ ] App icon is high quality (512x512 for Play Store)
- [ ] Splash screen is optimized and looks good on all screen sizes
- [ ] All images are compressed appropriately

### 5. Architecture Support
- [ ] Verify both arm64-v8a and armeabi-v7a are included
- [ ] Test on both 32-bit and 64-bit devices

## Build Process

### 1. Clean Build
```bash
# Clean previous builds
rm -rf .buildozer build dist

# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### 2. Build Release APK
```bash
# Build with explicit clean
buildozer android clean
buildozer android release
```

### 3. Sign APK (if not done automatically)
```bash
# If manual signing is needed
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \
    -keystore dalle-ai-art-release.keystore \
    bin/*.apk dalleaiart
```

### 4. Optimize APK
```bash
# Align the APK
zipalign -v 4 bin/*-release-unsigned.apk bin/*-release.apk
```

## Post-Build Verification

### 1. APK Analysis
- [ ] Check APK size is reasonable (target < 100MB)
- [ ] Verify APK contents don't contain sensitive data
- [ ] Run `aapt dump badging` to verify metadata
- [ ] Check for any debug information leakage

### 2. Security Testing
- [ ] Test certificate pinning works correctly
- [ ] Verify API communications are encrypted
- [ ] Check ProGuard obfuscation is effective
- [ ] Test on rooted device to ensure anti-tampering works

### 3. Compatibility Testing
- [ ] Test on minimum API level device (Android 8.0)
- [ ] Test on latest Android version
- [ ] Test on different screen sizes
- [ ] Test on both ARM architectures

### 4. Performance Testing
- [ ] App starts within 3 seconds
- [ ] Image generation is responsive
- [ ] Memory usage is reasonable
- [ ] No memory leaks during extended use

### 5. Privacy Compliance
- [ ] Privacy policy is accessible
- [ ] Age verification works correctly
- [ ] Data deletion features work
- [ ] Consent management is functional

## Distribution Preparation

### 1. Google Play Store
- [ ] Generate signed AAB if needed (`android.aab = True`)
- [ ] Prepare store listing screenshots
- [ ] Write compelling app description
- [ ] Set up content rating questionnaire
- [ ] Configure pricing and distribution

### 2. Alternative Distribution
- [ ] Host APK securely if distributing outside Play Store
- [ ] Provide clear installation instructions
- [ ] Include SHA-256 checksum for APK verification

## Final Checks

### 1. Legal Compliance
- [ ] Privacy policy URL is valid and accessible
- [ ] Terms of service are up to date
- [ ] GDPR compliance for EU users
- [ ] COPPA compliance for users under 13

### 2. Monitoring Setup
- [ ] Analytics integration (if used) respects user consent
- [ ] Crash reporting is configured
- [ ] Update mechanism is in place

### 3. Backup and Documentation
- [ ] Backup keystore file securely (multiple locations)
- [ ] Document keystore passwords securely
- [ ] Archive this specific build configuration
- [ ] Tag release in version control

## Emergency Procedures

### If Keystore is Lost
1. You cannot update the app with the same package name
2. Must publish as new app with different package name
3. Notify users to install new version

### If Security Breach Detected
1. Immediately revoke compromised API keys
2. Push update with new security measures
3. Notify affected users per privacy policy
4. Update certificate pins if needed

## Notes

- Always test the exact APK that will be distributed
- Keep build environment consistent (use Docker if needed)
- Monitor user feedback closely after release
- Plan for regular security updates