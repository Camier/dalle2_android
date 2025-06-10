"""
Privacy Manager Module for DALL-E AI Art App
Implements comprehensive privacy compliance features including GDPR compliance,
consent management, age verification, and data portability.
"""

import os
import json
import datetime
import zipfile
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from kivy.logger import Logger
from kivy.utils import platform
from kivy.clock import Clock
from kivy.app import App

from .secure_storage import get_secure_storage
from .storage import get_storage_path


class PrivacyManager:
    """Manages privacy compliance features for the app"""
    
    # Privacy consent types
    CONSENT_TYPES = {
        'essential': {
            'name': 'Essential Services',
            'description': 'Required for app functionality (API communication, image generation)',
            'required': True,
            'default': True
        },
        'analytics': {
            'name': 'Analytics & Performance',
            'description': 'Help us improve the app by collecting anonymous usage data',
            'required': False,
            'default': False
        },
        'crash_reports': {
            'name': 'Crash Reports',
            'description': 'Send crash reports to help us fix issues',
            'required': False,
            'default': False
        },
        'personalization': {
            'name': 'Personalization',
            'description': 'Store preferences and settings for a personalized experience',
            'required': False,
            'default': True
        }
    }
    
    # Minimum age requirements by region
    AGE_REQUIREMENTS = {
        'default': 13,  # COPPA compliance
        'eu': 16,       # GDPR
        'us': 13,       # COPPA
    }
    
    def __init__(self):
        self.secure_storage = get_secure_storage()
        self.privacy_data_file = Path(get_storage_path()) / 'privacy_settings.json'
        self.audit_log_file = Path(get_storage_path()) / 'privacy_audit.log'
        self._load_privacy_settings()
        Logger.info("PrivacyManager: Initialized")
    
    def _load_privacy_settings(self):
        """Load privacy settings from storage"""
        self.settings = {
            'consent': {},
            'age_verified': False,
            'age_verification_date': None,
            'user_region': 'default',
            'privacy_policy_version': '1.0.0',
            'privacy_policy_accepted': False,
            'privacy_policy_accepted_date': None,
            'data_retention_days': 365,
            'last_consent_review': None,
            'user_id': self._get_or_create_user_id()
        }
        
        if self.privacy_data_file.exists():
            try:
                with open(self.privacy_data_file, 'r') as f:
                    stored_settings = json.load(f)
                    self.settings.update(stored_settings)
            except Exception as e:
                Logger.error(f"PrivacyManager: Failed to load settings: {e}")
    
    def _save_privacy_settings(self):
        """Save privacy settings to storage"""
        try:
            self.privacy_data_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.privacy_data_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
            self._log_privacy_event("settings_updated", {"settings": self.settings})
        except Exception as e:
            Logger.error(f"PrivacyManager: Failed to save settings: {e}")
    
    def _get_or_create_user_id(self):
        """Get or create a unique user ID for privacy tracking"""
        user_id = self.secure_storage.get_data('privacy_user_id')
        if not user_id:
            # Generate anonymous user ID
            user_id = hashlib.sha256(
                f"{datetime.datetime.now().isoformat()}_{os.urandom(16).hex()}".encode()
            ).hexdigest()[:16]
            self.secure_storage.store_data('privacy_user_id', user_id)
        return user_id
    
    def _log_privacy_event(self, event_type: str, details: Dict[str, Any]):
        """Log privacy-related events for audit trail"""
        try:
            self.audit_log_file.parent.mkdir(parents=True, exist_ok=True)
            log_entry = {
                'timestamp': datetime.datetime.now().isoformat(),
                'user_id': self.settings['user_id'],
                'event_type': event_type,
                'details': details
            }
            
            with open(self.audit_log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            Logger.error(f"PrivacyManager: Failed to log event: {e}")
    
    # Consent Management
    
    def get_consent_status(self, consent_type: str) -> bool:
        """Get consent status for a specific type"""
        if consent_type not in self.CONSENT_TYPES:
            return False
        
        # Required consents are always True
        if self.CONSENT_TYPES[consent_type]['required']:
            return True
        
        return self.settings['consent'].get(consent_type, 
                                           self.CONSENT_TYPES[consent_type]['default'])
    
    def update_consent(self, consent_type: str, granted: bool):
        """Update consent for a specific type"""
        if consent_type not in self.CONSENT_TYPES:
            return False
        
        # Cannot revoke required consents
        if self.CONSENT_TYPES[consent_type]['required'] and not granted:
            return False
        
        self.settings['consent'][consent_type] = granted
        self.settings['last_consent_review'] = datetime.datetime.now().isoformat()
        self._save_privacy_settings()
        self._log_privacy_event("consent_updated", {
            "consent_type": consent_type,
            "granted": granted
        })
        return True
    
    def get_all_consents(self) -> Dict[str, bool]:
        """Get all consent statuses"""
        consents = {}
        for consent_type in self.CONSENT_TYPES:
            consents[consent_type] = self.get_consent_status(consent_type)
        return consents
    
    def update_all_consents(self, consents: Dict[str, bool]):
        """Update multiple consents at once"""
        for consent_type, granted in consents.items():
            self.update_consent(consent_type, granted)
    
    def reset_consents_to_minimum(self):
        """Reset all consents to minimum required (GDPR compliance)"""
        for consent_type, config in self.CONSENT_TYPES.items():
            if not config['required']:
                self.settings['consent'][consent_type] = False
        self._save_privacy_settings()
        self._log_privacy_event("consents_reset", {"reason": "user_request"})
    
    # Age Verification
    
    def verify_age(self, birth_date: datetime.date, region: str = 'default') -> bool:
        """Verify user age meets requirements"""
        try:
            today = datetime.date.today()
            age = today.year - birth_date.year - (
                (today.month, today.day) < (birth_date.month, birth_date.day)
            )
            
            min_age = self.AGE_REQUIREMENTS.get(region, self.AGE_REQUIREMENTS['default'])
            
            if age >= min_age:
                self.settings['age_verified'] = True
                self.settings['age_verification_date'] = datetime.datetime.now().isoformat()
                self.settings['user_region'] = region
                self._save_privacy_settings()
                self._log_privacy_event("age_verified", {
                    "age": age,
                    "region": region,
                    "min_required": min_age
                })
                return True
            else:
                self._log_privacy_event("age_verification_failed", {
                    "age": age,
                    "region": region,
                    "min_required": min_age
                })
                return False
        except Exception as e:
            Logger.error(f"PrivacyManager: Age verification error: {e}")
            return False
    
    def is_age_verified(self) -> bool:
        """Check if user age has been verified"""
        return self.settings.get('age_verified', False)
    
    def get_minimum_age(self, region: str = None) -> int:
        """Get minimum age requirement for region"""
        if region is None:
            region = self.settings.get('user_region', 'default')
        return self.AGE_REQUIREMENTS.get(region, self.AGE_REQUIREMENTS['default'])
    
    # Privacy Policy
    
    def accept_privacy_policy(self, version: str = '1.0.0'):
        """Record privacy policy acceptance"""
        self.settings['privacy_policy_accepted'] = True
        self.settings['privacy_policy_version'] = version
        self.settings['privacy_policy_accepted_date'] = datetime.datetime.now().isoformat()
        self._save_privacy_settings()
        self._log_privacy_event("privacy_policy_accepted", {"version": version})
    
    def is_privacy_policy_accepted(self) -> bool:
        """Check if current privacy policy has been accepted"""
        return self.settings.get('privacy_policy_accepted', False)
    
    def get_privacy_policy_version(self) -> str:
        """Get accepted privacy policy version"""
        return self.settings.get('privacy_policy_version', '1.0.0')
    
    # Data Management (GDPR Compliance)
    
    def export_user_data(self) -> str:
        """Export all user data (GDPR data portability)"""
        try:
            export_dir = Path(get_storage_path()) / 'exports'
            export_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            export_file = export_dir / f'user_data_export_{timestamp}.zip'
            
            with zipfile.ZipFile(export_file, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Privacy settings
                zf.writestr('privacy_settings.json', 
                           json.dumps(self.settings, indent=2))
                
                # Secure storage data (excluding encryption keys)
                secure_data = {
                    'api_key_stored': bool(self.secure_storage.get_api_key()),
                    'user_id': self.settings['user_id']
                }
                zf.writestr('secure_data.json', 
                           json.dumps(secure_data, indent=2))
                
                # Audit log
                if self.audit_log_file.exists():
                    zf.write(self.audit_log_file, 'privacy_audit.log')
                
                # Generated images metadata
                images_dir = Path(get_storage_path()) / 'images'
                if images_dir.exists():
                    image_metadata = []
                    for img_file in images_dir.glob('*.png'):
                        metadata = {
                            'filename': img_file.name,
                            'size': img_file.stat().st_size,
                            'created': datetime.datetime.fromtimestamp(
                                img_file.stat().st_ctime
                            ).isoformat()
                        }
                        image_metadata.append(metadata)
                    zf.writestr('images_metadata.json', 
                               json.dumps(image_metadata, indent=2))
                
                # App settings and preferences
                app = App.get_running_app()
                if app and hasattr(app, 'config'):
                    config_data = {}
                    for section in app.config.sections():
                        config_data[section] = dict(app.config.items(section))
                    zf.writestr('app_config.json', 
                               json.dumps(config_data, indent=2))
            
            self._log_privacy_event("data_exported", {"export_file": str(export_file)})
            return str(export_file)
            
        except Exception as e:
            Logger.error(f"PrivacyManager: Failed to export data: {e}")
            return None
    
    def delete_all_user_data(self, confirm_token: str = None) -> bool:
        """Delete all user data (GDPR right to erasure)"""
        # Require confirmation token to prevent accidental deletion
        expected_token = hashlib.sha256(
            f"DELETE_{self.settings['user_id']}".encode()
        ).hexdigest()[:8]
        
        if confirm_token != expected_token:
            Logger.warning(f"PrivacyManager: Invalid deletion token. Expected: {expected_token}")
            return False
        
        try:
            # Log deletion request first
            self._log_privacy_event("data_deletion_requested", {
                "user_id": self.settings['user_id'],
                "timestamp": datetime.datetime.now().isoformat()
            })
            
            # Clear secure storage
            self.secure_storage.clear_all_data()
            
            # Delete privacy settings
            if self.privacy_data_file.exists():
                self.privacy_data_file.unlink()
            
            # Delete images
            images_dir = Path(get_storage_path()) / 'images'
            if images_dir.exists():
                for img_file in images_dir.glob('*.png'):
                    img_file.unlink()
            
            # Clear app config
            app = App.get_running_app()
            if app and hasattr(app, 'config'):
                for section in app.config.sections():
                    app.config.remove_section(section)
                app.config.write()
            
            # Archive audit log (don't delete for legal compliance)
            if self.audit_log_file.exists():
                archive_file = self.audit_log_file.with_suffix('.archived')
                self.audit_log_file.rename(archive_file)
            
            Logger.info("PrivacyManager: All user data deleted successfully")
            return True
            
        except Exception as e:
            Logger.error(f"PrivacyManager: Failed to delete data: {e}")
            return False
    
    def get_deletion_token(self) -> str:
        """Get token required for data deletion"""
        return hashlib.sha256(
            f"DELETE_{self.settings['user_id']}".encode()
        ).hexdigest()[:8]
    
    def anonymize_data(self):
        """Anonymize user data instead of deleting"""
        try:
            # Generate new anonymous user ID
            new_user_id = hashlib.sha256(os.urandom(32)).hexdigest()[:16]
            
            # Update user ID everywhere
            old_user_id = self.settings['user_id']
            self.settings['user_id'] = new_user_id
            self.secure_storage.store_data('privacy_user_id', new_user_id)
            
            # Clear personal identifiers
            self.settings['age_verification_date'] = None
            self.settings['privacy_policy_accepted_date'] = None
            
            self._save_privacy_settings()
            self._log_privacy_event("data_anonymized", {
                "old_user_id": old_user_id,
                "new_user_id": new_user_id
            })
            
            return True
        except Exception as e:
            Logger.error(f"PrivacyManager: Failed to anonymize data: {e}")
            return False
    
    # Data Retention
    
    def cleanup_old_data(self):
        """Clean up data older than retention period"""
        try:
            retention_days = self.settings.get('data_retention_days', 365)
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)
            
            # Clean old images
            images_dir = Path(get_storage_path()) / 'images'
            if images_dir.exists():
                for img_file in images_dir.glob('*.png'):
                    if datetime.datetime.fromtimestamp(img_file.stat().st_mtime) < cutoff_date:
                        img_file.unlink()
                        Logger.info(f"PrivacyManager: Deleted old image: {img_file.name}")
            
            # Clean old exports
            export_dir = Path(get_storage_path()) / 'exports'
            if export_dir.exists():
                for export_file in export_dir.glob('*.zip'):
                    if datetime.datetime.fromtimestamp(export_file.stat().st_mtime) < cutoff_date:
                        export_file.unlink()
                        Logger.info(f"PrivacyManager: Deleted old export: {export_file.name}")
            
            self._log_privacy_event("data_cleanup", {
                "retention_days": retention_days,
                "cutoff_date": cutoff_date.isoformat()
            })
            
        except Exception as e:
            Logger.error(f"PrivacyManager: Failed to cleanup old data: {e}")
    
    def set_data_retention_period(self, days: int):
        """Set data retention period in days"""
        if days < 1:
            return False
        
        self.settings['data_retention_days'] = days
        self._save_privacy_settings()
        self._log_privacy_event("retention_period_updated", {"days": days})
        return True
    
    # Consent Review Reminder
    
    def should_review_consents(self) -> bool:
        """Check if user should review consents (e.g., annually)"""
        last_review = self.settings.get('last_consent_review')
        if not last_review:
            return True
        
        try:
            last_review_date = datetime.datetime.fromisoformat(last_review)
            days_since_review = (datetime.datetime.now() - last_review_date).days
            return days_since_review > 365  # Annual review
        except:
            return True
    
    def mark_consent_reviewed(self):
        """Mark consents as reviewed"""
        self.settings['last_consent_review'] = datetime.datetime.now().isoformat()
        self._save_privacy_settings()
        self._log_privacy_event("consent_reviewed", {})


# Singleton instance
_privacy_manager = None

def get_privacy_manager():
    """Get singleton instance of PrivacyManager"""
    global _privacy_manager
    if _privacy_manager is None:
        _privacy_manager = PrivacyManager()
    return _privacy_manager