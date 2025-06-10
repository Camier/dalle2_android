"""
App Integrity Checker - Anti-tampering protection
"""

import hashlib
import hmac
import os
from kivy.utils import platform
from kivy.logger import Logger

class IntegrityChecker:
    """
    Verifies app integrity and detects tampering
    """
    
    def __init__(self):
        self.package_name = "com.dalleandroid.dalleaiart"
        self.expected_signature = None
        self.init_integrity_checks()
    
    def init_integrity_checks(self):
        """Initialize integrity checking"""
        if platform == 'android':
            self._init_android_checks()
    
    def _init_android_checks(self):
        """Initialize Android-specific integrity checks"""
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PackageManager = autoclass('android.content.pm.PackageManager')
            PackageInfo = autoclass('android.content.pm.PackageInfo')
            Signature = autoclass('android.content.pm.Signature')
            
            # Get package info
            context = PythonActivity.mActivity
            pm = context.getPackageManager()
            package_info = pm.getPackageInfo(
                self.package_name,
                PackageManager.GET_SIGNATURES
            )
            
            # Get signature
            signatures = package_info.signatures
            if signatures and len(signatures) > 0:
                self.expected_signature = self._hash_signature(signatures[0])
                Logger.info(f"IntegrityChecker: Initialized with signature hash: {self.expected_signature[:10]}...")
            
        except Exception as e:
            Logger.error(f"IntegrityChecker: Failed to initialize: {e}")
    
    def _hash_signature(self, signature):
        """Hash app signature for comparison"""
        return hashlib.sha256(signature.toByteArray()).hexdigest()
    
    def verify_app_signature(self):
        """Verify app signature hasn't changed"""
        if platform != 'android':
            return True  # Skip on non-Android platforms
        
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PackageManager = autoclass('android.content.pm.PackageManager')
            
            context = PythonActivity.mActivity
            pm = context.getPackageManager()
            package_info = pm.getPackageInfo(
                self.package_name,
                PackageManager.GET_SIGNATURES
            )
            
            signatures = package_info.signatures
            if signatures and len(signatures) > 0:
                current_signature = self._hash_signature(signatures[0])
                
                if current_signature != self.expected_signature:
                    Logger.error("IntegrityChecker: Signature mismatch - possible tampering!")
                    return False
                
            return True
            
        except Exception as e:
            Logger.error(f"IntegrityChecker: Verification failed: {e}")
            return False
    
    def check_debugger(self):
        """Check if debugger is attached"""
        if platform != 'android':
            return False
        
        try:
            from jnius import autoclass
            Debug = autoclass('android.os.Debug')
            
            if Debug.isDebuggerConnected():
                Logger.warning("IntegrityChecker: Debugger detected!")
                return True
                
        except:
            pass
        
        return False
    
    def check_emulator(self):
        """Check if running on emulator"""
        if platform != 'android':
            return False
        
        try:
            from jnius import autoclass
            Build = autoclass('android.os.Build')
            
            # Common emulator indicators
            emulator_indicators = [
                Build.FINGERPRINT.startswith("generic"),
                Build.FINGERPRINT.startswith("unknown"),
                Build.MODEL.contains("google_sdk"),
                Build.MODEL.contains("Emulator"),
                Build.MODEL.contains("Android SDK built for x86"),
                Build.MANUFACTURER.contains("Genymotion"),
                Build.HARDWARE.contains("goldfish"),
                Build.HARDWARE.contains("ranchu"),
                Build.PRODUCT.contains("sdk"),
                Build.PRODUCT.contains("google_sdk"),
                Build.PRODUCT.contains("sdk_x86"),
                Build.PRODUCT.contains("vbox86p"),
                Build.DEVICE.contains("generic")
            ]
            
            if any(emulator_indicators):
                Logger.warning("IntegrityChecker: Emulator detected!")
                return True
                
        except:
            pass
        
        return False
    
    def check_root(self):
        """Check if device is rooted"""
        if platform != 'android':
            return False
        
        # Check for common root indicators
        root_paths = [
            "/system/app/Superuser.apk",
            "/sbin/su",
            "/system/bin/su",
            "/system/xbin/su",
            "/data/local/xbin/su",
            "/data/local/bin/su",
            "/system/sd/xbin/su",
            "/system/bin/failsafe/su",
            "/data/local/su",
            "/su/bin/su"
        ]
        
        for path in root_paths:
            if os.path.exists(path):
                Logger.warning(f"IntegrityChecker: Root indicator found: {path}")
                return True
        
        # Check for root management apps
        try:
            from jnius import autoclass
            
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            PackageManager = autoclass('android.content.pm.PackageManager')
            
            context = PythonActivity.mActivity
            pm = context.getPackageManager()
            
            root_packages = [
                "com.topjohnwu.magisk",
                "com.koushikdutta.superuser",
                "com.noshufou.android.su",
                "com.thirdparty.superuser",
                "eu.chainfire.supersu",
                "com.yellowes.su"
            ]
            
            for package in root_packages:
                try:
                    pm.getPackageInfo(package, 0)
                    Logger.warning(f"IntegrityChecker: Root app found: {package}")
                    return True
                except:
                    continue
                    
        except:
            pass
        
        return False
    
    def perform_integrity_check(self):
        """Perform full integrity check"""
        results = {
            'signature_valid': self.verify_app_signature(),
            'debugger_attached': self.check_debugger(),
            'emulator_detected': self.check_emulator(),
            'root_detected': self.check_root()
        }
        
        # Overall integrity status
        results['integrity_ok'] = (
            results['signature_valid'] and
            not results['debugger_attached'] and
            not results['root_detected']
        )
        
        return results

# Global integrity checker instance
_integrity_checker = None

def get_integrity_checker():
    """Get singleton integrity checker instance"""
    global _integrity_checker
    if _integrity_checker is None:
        _integrity_checker = IntegrityChecker()
    return _integrity_checker
