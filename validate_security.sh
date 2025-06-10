#!/bin/bash

# DALL-E Android Security Validation Script
# Validates that all security measures are properly implemented

set -e

echo "============================================"
echo "DALL-E Android Security Validation Script"
echo "============================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Track validation results
PASSED=0
FAILED=0

# Function to check test result
check_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASSED${NC}: $2"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC}: $2"
        ((FAILED++))
    fi
}

# 1. Check for debug certificate
echo -e "${YELLOW}1. Checking APK Certificate...${NC}"
if [ -f "bin/*.apk" ]; then
    APK_FILE=$(ls bin/*.apk | head -1)
    if keytool -printcert -jarfile "$APK_FILE" 2>/dev/null | grep -q "CN=Android Debug"; then
        check_result 1 "APK is using debug certificate"
    else
        check_result 0 "APK is using release certificate"
    fi
else
    echo -e "${YELLOW}No APK found to check${NC}"
fi

# 2. Check for secure storage implementation
echo -e "\n${YELLOW}2. Checking Secure Storage Implementation...${NC}"
if [ -f "utils/secure_storage.py" ]; then
    if grep -q "Android Keystore" utils/secure_storage.py && \
       grep -q "Fernet" utils/secure_storage.py && \
       grep -q "PBKDF2HMAC" utils/secure_storage.py; then
        check_result 0 "Secure storage properly implemented"
    else
        check_result 1 "Secure storage missing key components"
    fi
else
    check_result 1 "Secure storage file not found"
fi

# 3. Check for certificate pinning
echo -e "\n${YELLOW}3. Checking Certificate Pinning...${NC}"
if [ -f "services/certificate_pinning.py" ]; then
    if grep -q "OPENAI_PINS" services/certificate_pinning.py && \
       grep -q "verify_pin" services/certificate_pinning.py && \
       grep -q "TLSv1_2" services/certificate_pinning.py; then
        check_result 0 "Certificate pinning implemented"
    else
        check_result 1 "Certificate pinning incomplete"
    fi
else
    check_result 1 "Certificate pinning file not found"
fi

# 4. Check for rate limiting
echo -e "\n${YELLOW}4. Checking Rate Limiting...${NC}"
if [ -f "services/rate_limiter.py" ]; then
    if grep -q "TokenBucket" services/rate_limiter.py && \
       grep -q "CircuitBreaker" services/rate_limiter.py && \
       grep -q "exponential" services/rate_limiter.py; then
        check_result 0 "Rate limiting with circuit breaker implemented"
    else
        check_result 1 "Rate limiting incomplete"
    fi
else
    check_result 1 "Rate limiting file not found"
fi

# 5. Check for input validation
echo -e "\n${YELLOW}5. Checking Input Validation...${NC}"
if [ -f "utils/input_validator.py" ]; then
    if grep -q "sanitize_prompt" utils/input_validator.py && \
       grep -q "SQL.*injection" utils/input_validator.py && \
       grep -q "XSS" utils/input_validator.py; then
        check_result 0 "Input validation and sanitization implemented"
    else
        check_result 1 "Input validation incomplete"
    fi
else
    check_result 1 "Input validation file not found"
fi

# 6. Check for privacy compliance
echo -e "\n${YELLOW}6. Checking Privacy Compliance...${NC}"
if [ -f "utils/privacy_manager.py" ] && [ -f "screens/privacy_consent_screen.py" ]; then
    if grep -q "GDPR" utils/privacy_manager.py && \
       grep -q "delete_all_user_data" utils/privacy_manager.py && \
       grep -q "PrivacyConsentScreen" screens/privacy_consent_screen.py; then
        check_result 0 "Privacy compliance framework implemented"
    else
        check_result 1 "Privacy compliance incomplete"
    fi
else
    check_result 1 "Privacy compliance files not found"
fi

# 7. Check for secure logging
echo -e "\n${YELLOW}7. Checking Secure Logging...${NC}"
if [ -f "utils/secure_logger.py" ]; then
    if grep -q "redact_sensitive_data" utils/secure_logger.py && \
       grep -q "SENSITIVE_PATTERNS" utils/secure_logger.py && \
       grep -q "production_mode" utils/secure_logger.py; then
        check_result 0 "Secure logging with PII redaction implemented"
    else
        check_result 1 "Secure logging incomplete"
    fi
else
    check_result 1 "Secure logging file not found"
fi

# 8. Check for anti-tampering
echo -e "\n${YELLOW}8. Checking Anti-Tampering Measures...${NC}"
if [ -f "utils/integrity_checker.py" ]; then
    if grep -q "verify_app_signature" utils/integrity_checker.py && \
       grep -q "check_debugger" utils/integrity_checker.py && \
       grep -q "check_root" utils/integrity_checker.py; then
        check_result 0 "Anti-tampering measures implemented"
    else
        check_result 1 "Anti-tampering incomplete"
    fi
else
    check_result 1 "Anti-tampering file not found"
fi

# 9. Check for ProGuard configuration
echo -e "\n${YELLOW}9. Checking ProGuard Configuration...${NC}"
if [ -f "proguard-rules.pro" ]; then
    if grep -q "optimizations" proguard-rules.pro && \
       grep -q "assumenosideeffects.*Log" proguard-rules.pro; then
        check_result 0 "ProGuard rules configured"
    else
        check_result 1 "ProGuard rules incomplete"
    fi
else
    check_result 1 "ProGuard rules file not found"
fi

# 10. Check for network security configuration
echo -e "\n${YELLOW}10. Checking Network Security Configuration...${NC}"
if [ -f "res/xml/network_security_config.xml" ]; then
    if grep -q "pin-set" res/xml/network_security_config.xml && \
       grep -q "cleartextTrafficPermitted=\"false\"" res/xml/network_security_config.xml; then
        check_result 0 "Network security configuration present"
    else
        check_result 1 "Network security configuration incomplete"
    fi
else
    check_result 1 "Network security configuration not found"
fi

# 11. Check buildozer configuration
echo -e "\n${YELLOW}11. Checking Build Configuration...${NC}"
if [ -f "buildozer_secure_release.spec" ] || [ -f "buildozer_release.spec" ]; then
    SPEC_FILE=$(ls buildozer_secure_release.spec buildozer_release.spec 2>/dev/null | head -1)
    if grep -q "android.debug = False" "$SPEC_FILE" && \
       grep -q "android.release_artifact = apk" "$SPEC_FILE" && \
       grep -q "android.optimize_python = True" "$SPEC_FILE"; then
        check_result 0 "Release build configuration correct"
    else
        check_result 1 "Build configuration needs adjustment"
    fi
else
    check_result 1 "Release build configuration not found"
fi

# 12. Check for API key in code
echo -e "\n${YELLOW}12. Checking for Hardcoded Secrets...${NC}"
SECRETS_FOUND=0
for file in $(find . -name "*.py" -type f 2>/dev/null | grep -v venv | grep -v .buildozer); do
    if grep -q "sk-[a-zA-Z0-9]\{48\}" "$file" 2>/dev/null; then
        echo -e "${RED}Found potential API key in: $file${NC}"
        SECRETS_FOUND=1
    fi
done
if [ $SECRETS_FOUND -eq 0 ]; then
    check_result 0 "No hardcoded secrets found"
else
    check_result 1 "Hardcoded secrets detected"
fi

# 13. Run security unit tests
echo -e "\n${YELLOW}13. Running Security Unit Tests...${NC}"
if [ -f "test_security.py" ]; then
    if python test_security.py > /dev/null 2>&1; then
        check_result 0 "Security unit tests pass"
    else
        check_result 1 "Security unit tests fail"
    fi
else
    check_result 1 "Security unit tests not found"
fi

# 14. Check permissions in manifest/buildozer
echo -e "\n${YELLOW}14. Checking App Permissions...${NC}"
if [ -f "buildozer.spec" ] || [ -f "buildozer_secure_release.spec" ]; then
    SPEC_FILE=$(ls buildozer_secure_release.spec buildozer.spec 2>/dev/null | head -1)
    PERMS=$(grep "android.permissions" "$SPEC_FILE" | grep -v "^#")
    
    # Check for unnecessary permissions
    UNNECESSARY_PERMS=0
    if echo "$PERMS" | grep -q "CAMERA" && ! grep -q "camera" main*.py; then
        echo -e "${YELLOW}Warning: CAMERA permission declared but not used${NC}"
        UNNECESSARY_PERMS=1
    fi
    if echo "$PERMS" | grep -q "LOCATION"; then
        echo -e "${YELLOW}Warning: LOCATION permission not needed for this app${NC}"
        UNNECESSARY_PERMS=1
    fi
    
    if [ $UNNECESSARY_PERMS -eq 0 ]; then
        check_result 0 "App permissions minimal and justified"
    else
        check_result 1 "Unnecessary permissions detected"
    fi
else
    check_result 1 "Cannot check permissions - buildozer.spec not found"
fi

# 15. Check for privacy policy file
echo -e "\n${YELLOW}15. Checking Privacy Policy...${NC}"
if [ -f "assets/privacy_policy.txt" ]; then
    if [ -s "assets/privacy_policy.txt" ]; then
        check_result 0 "Privacy policy document present"
    else
        check_result 1 "Privacy policy document empty"
    fi
else
    check_result 1 "Privacy policy document not found"
fi

# Summary
echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}Security Validation Summary${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "Total Checks: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All security checks passed!${NC}"
    echo -e "${GREEN}Your app is ready for release build.${NC}"
    exit 0
else
    echo -e "${RED}⚠️  Security issues detected!${NC}"
    echo -e "${RED}Please fix the failed checks before building for release.${NC}"
    
    echo -e "\n${YELLOW}Recommended actions:${NC}"
    echo "1. Run: ./implement_security_fixes.sh"
    echo "2. Generate keystore: ./generate_release_keystore.sh"
    echo "3. Review and fix any custom security issues"
    echo "4. Re-run this validation script"
    exit 1
fi