"""
Settings Sync Worker for DALL-E Android App
Handles settings export/import and backup operations
"""

import json
import os
import time
import shutil
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import zipfile

from .base_worker import BaseWorker, WorkerPriority

class SyncOperation(Enum):
    EXPORT = "export"
    IMPORT = "import"
    BACKUP = "backup"
    RESTORE = "restore"
    CLOUD_SYNC = "cloud_sync"
    VALIDATE = "validate"

@dataclass
class SettingsData:
    """Application settings structure"""
    api_key: str = ""
    model: str = "dall-e-2"
    image_size: str = "1024x1024"
    quality: str = "standard"
    batch_size: int = 1
    save_history: bool = True
    auto_save: bool = True
    theme: str = "light"
    gallery_columns: int = 2
    cache_size_mb: int = 500
    version: str = "1.0"
    last_modified: str = ""

@dataclass
class HistoryEntry:
    """Image generation history entry"""
    prompt: str
    timestamp: str
    image_path: str
    model: str
    size: str
    metadata: Dict[str, Any] = None

@dataclass
class AppData:
    """Complete app data structure"""
    settings: SettingsData
    history: List[HistoryEntry]
    favorites: List[str]
    custom_styles: Dict[str, str]
    version: str = "1.0"
    export_timestamp: str = ""

@dataclass
class SyncTask:
    """Settings sync task"""
    operation: SyncOperation
    source_path: Optional[str] = None
    destination_path: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    include_images: bool = False
    callback: Optional[callable] = None
    metadata: Dict[str, Any] = None

class SettingsSyncWorker(BaseWorker):
    """
    Worker for handling settings synchronization, backup, and restore.
    Manages app configuration and user data persistence.
    """
    
    def __init__(self, app_data_dir: str, backup_dir: str = None):
        super().__init__("SettingsSync", max_queue_size=20)
        self.app_data_dir = app_data_dir
        self.backup_dir = backup_dir or os.path.join(app_data_dir, "backups")
        self.settings_file = os.path.join(app_data_dir, "settings.json")
        self.history_file = os.path.join(app_data_dir, "history.json")
        self.max_backups = 10
        
        # Ensure directories exist
        os.makedirs(self.app_data_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def process_task(self, task: SyncTask) -> Dict[str, Any]:
        """Process sync task"""
        self.logger.info(f"Processing {task.operation.value} operation")
        
        try:
            if task.operation == SyncOperation.EXPORT:
                return self._export_settings(task)
            elif task.operation == SyncOperation.IMPORT:
                return self._import_settings(task)
            elif task.operation == SyncOperation.BACKUP:
                return self._create_backup(task)
            elif task.operation == SyncOperation.RESTORE:
                return self._restore_backup(task)
            elif task.operation == SyncOperation.VALIDATE:
                return self._validate_data(task)
            else:
                raise ValueError(f"Unknown operation: {task.operation}")
                
        except Exception as e:
            self.logger.error(f"Error in sync operation: {str(e)}")
            error_result = {
                "success": False,
                "operation": task.operation.value,
                "error": str(e)
            }
            
            if task.callback:
                task.callback(error_result)
                
            return None
            
    def _export_settings(self, task: SyncTask) -> Dict[str, Any]:
        """Export app settings to JSON file"""
        try:
            # Load current data
            app_data = self._load_app_data()
            app_data.export_timestamp = datetime.now().isoformat()
            
            # Determine export path
            export_path = task.destination_path or os.path.join(
                self.app_data_dir, 
                f"dalle_settings_export_{int(time.time())}.json"
            )
            
            # Create export package
            if task.include_images:
                # Create zip with settings and images
                return self._create_export_package(app_data, export_path, task)
            else:
                # Export settings only
                with open(export_path, 'w') as f:
                    json.dump(asdict(app_data), f, indent=2)
                    
            result = {
                "success": True,
                "operation": "export",
                "path": export_path,
                "size": os.path.getsize(export_path),
                "timestamp": app_data.export_timestamp,
                "includes_images": task.include_images
            }
            
            if task.callback:
                task.callback(result)
                
            self.logger.info(f"Settings exported to {export_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Export failed: {str(e)}")
            raise
            
    def _import_settings(self, task: SyncTask) -> Dict[str, Any]:
        """Import settings from JSON file"""
        try:
            import_path = task.source_path
            if not os.path.exists(import_path):
                raise FileNotFoundError(f"Import file not found: {import_path}")
                
            # Create backup before import
            self._create_backup(SyncTask(
                operation=SyncOperation.BACKUP,
                metadata={"reason": "pre-import"}
            ))
            
            # Check if it's a zip package
            if zipfile.is_zipfile(import_path):
                return self._import_package(import_path, task)
                
            # Import JSON settings
            with open(import_path, 'r') as f:
                data = json.load(f)
                
            # Validate data structure
            validated_data = self._validate_import_data(data)
            
            # Apply settings
            self._apply_settings(validated_data)
            
            result = {
                "success": True,
                "operation": "import",
                "path": import_path,
                "settings_updated": True,
                "history_entries": len(validated_data.get('history', [])),
                "timestamp": datetime.now().isoformat()
            }
            
            if task.callback:
                task.callback(result)
                
            self.logger.info(f"Settings imported from {import_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Import failed: {str(e)}")
            raise
            
    def _create_backup(self, task: SyncTask) -> Dict[str, Any]:
        """Create automatic backup"""
        try:
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            reason = task.metadata.get('reason', 'manual') if task.metadata else 'manual'
            backup_name = f"backup_{reason}_{timestamp}.json"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Load current data
            app_data = self._load_app_data()
            
            # Save backup
            with open(backup_path, 'w') as f:
                json.dump(asdict(app_data), f, indent=2)
                
            # Manage backup rotation
            self._rotate_backups()
            
            result = {
                "success": True,
                "operation": "backup",
                "path": backup_path,
                "size": os.path.getsize(backup_path),
                "timestamp": timestamp,
                "reason": reason
            }
            
            if task.callback:
                task.callback(result)
                
            self.logger.info(f"Backup created: {backup_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Backup failed: {str(e)}")
            raise
            
    def _restore_backup(self, task: SyncTask) -> Dict[str, Any]:
        """Restore from backup"""
        try:
            backup_path = task.source_path
            
            if not os.path.exists(backup_path):
                # Try to find latest backup
                backups = self._list_backups()
                if not backups:
                    raise FileNotFoundError("No backups found")
                backup_path = backups[0]['path']
                
            # Import the backup
            import_task = SyncTask(
                operation=SyncOperation.IMPORT,
                source_path=backup_path,
                callback=task.callback
            )
            
            return self._import_settings(import_task)
            
        except Exception as e:
            self.logger.error(f"Restore failed: {str(e)}")
            raise
            
    def _validate_data(self, task: SyncTask) -> Dict[str, Any]:
        """Validate settings data structure"""
        try:
            data = task.data or self._load_app_data()
            
            issues = []
            
            # Check required fields
            if isinstance(data, dict):
                if 'settings' not in data:
                    issues.append("Missing 'settings' section")
                else:
                    settings = data['settings']
                    if not settings.get('api_key'):
                        issues.append("API key is empty")
                    if settings.get('cache_size_mb', 0) < 100:
                        issues.append("Cache size is too small")
                        
            # Validate history entries
            if 'history' in data:
                for i, entry in enumerate(data.get('history', [])):
                    if not entry.get('prompt'):
                        issues.append(f"History entry {i} missing prompt")
                        
            result = {
                "success": len(issues) == 0,
                "operation": "validate",
                "issues": issues,
                "data_version": data.get('version', 'unknown')
            }
            
            if task.callback:
                task.callback(result)
                
            return result
            
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            raise
            
    def _load_app_data(self) -> AppData:
        """Load current app data"""
        settings = self._load_settings()
        history = self._load_history()
        favorites = self._load_favorites()
        custom_styles = self._load_custom_styles()
        
        return AppData(
            settings=settings,
            history=history,
            favorites=favorites,
            custom_styles=custom_styles,
            version="1.0"
        )
        
    def _load_settings(self) -> SettingsData:
        """Load settings from file"""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                return SettingsData(**data)
            except:
                pass
        return SettingsData()
        
    def _load_history(self) -> List[HistoryEntry]:
        """Load history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                return [HistoryEntry(**entry) for entry in data]
            except:
                pass
        return []
        
    def _load_favorites(self) -> List[str]:
        """Load favorites list"""
        favorites_file = os.path.join(self.app_data_dir, "favorites.json")
        if os.path.exists(favorites_file):
            try:
                with open(favorites_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return []
        
    def _load_custom_styles(self) -> Dict[str, str]:
        """Load custom styles"""
        styles_file = os.path.join(self.app_data_dir, "custom_styles.json")
        if os.path.exists(styles_file):
            try:
                with open(styles_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
        
    def _apply_settings(self, data: Dict[str, Any]):
        """Apply imported settings"""
        # Save settings
        if 'settings' in data:
            with open(self.settings_file, 'w') as f:
                json.dump(data['settings'], f, indent=2)
                
        # Save history
        if 'history' in data:
            with open(self.history_file, 'w') as f:
                json.dump(data['history'], f, indent=2)
                
        # Save other data
        if 'favorites' in data:
            favorites_file = os.path.join(self.app_data_dir, "favorites.json")
            with open(favorites_file, 'w') as f:
                json.dump(data['favorites'], f, indent=2)
                
        if 'custom_styles' in data:
            styles_file = os.path.join(self.app_data_dir, "custom_styles.json")
            with open(styles_file, 'w') as f:
                json.dump(data['custom_styles'], f, indent=2)
                
    def _rotate_backups(self):
        """Maintain maximum number of backups"""
        backups = self._list_backups()
        
        if len(backups) > self.max_backups:
            # Sort by modification time
            backups.sort(key=lambda x: x['modified'], reverse=True)
            
            # Remove oldest backups
            for backup in backups[self.max_backups:]:
                try:
                    os.remove(backup['path'])
                    self.logger.info(f"Removed old backup: {backup['name']}")
                except:
                    pass
                    
    def _list_backups(self) -> List[Dict[str, Any]]:
        """List available backups"""
        backups = []
        
        for filename in os.listdir(self.backup_dir):
            if filename.startswith('backup_') and filename.endswith('.json'):
                path = os.path.join(self.backup_dir, filename)
                stat = os.stat(path)
                backups.append({
                    'name': filename,
                    'path': path,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
                
        return backups
        
    def _validate_import_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and migrate imported data"""
        # Ensure required structure
        if 'settings' not in data:
            data['settings'] = {}
            
        # Apply defaults for missing fields
        default_settings = asdict(SettingsData())
        for key, value in default_settings.items():
            if key not in data['settings']:
                data['settings'][key] = value
                
        return data
        
    def _create_export_package(self, app_data: AppData, export_path: str, 
                              task: SyncTask) -> Dict[str, Any]:
        """Create zip package with settings and images"""
        zip_path = export_path.replace('.json', '.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add settings
            settings_data = json.dumps(asdict(app_data), indent=2)
            zf.writestr('settings.json', settings_data)
            
            # Add images if requested
            if task.include_images:
                image_count = 0
                for entry in app_data.history:
                    if entry.image_path and os.path.exists(entry.image_path):
                        arc_name = f"images/{os.path.basename(entry.image_path)}"
                        zf.write(entry.image_path, arc_name)
                        image_count += 1
                        
            # Add metadata
            metadata = {
                'export_date': datetime.now().isoformat(),
                'app_version': app_data.version,
                'image_count': image_count if task.include_images else 0
            }
            zf.writestr('metadata.json', json.dumps(metadata, indent=2))
            
        return {
            "success": True,
            "operation": "export",
            "path": zip_path,
            "size": os.path.getsize(zip_path),
            "timestamp": app_data.export_timestamp,
            "includes_images": task.include_images,
            "format": "zip"
        }
        
    def _import_package(self, zip_path: str, task: SyncTask) -> Dict[str, Any]:
        """Import from zip package"""
        temp_dir = os.path.join(self.app_data_dir, 'temp_import')
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_dir)
                
            # Load settings
            settings_path = os.path.join(temp_dir, 'settings.json')
            with open(settings_path, 'r') as f:
                data = json.load(f)
                
            # Validate and apply settings
            validated_data = self._validate_import_data(data)
            self._apply_settings(validated_data)
            
            # Copy images if present
            images_dir = os.path.join(temp_dir, 'images')
            if os.path.exists(images_dir):
                target_images_dir = os.path.join(self.app_data_dir, 'gallery')
                os.makedirs(target_images_dir, exist_ok=True)
                
                for img_file in os.listdir(images_dir):
                    src = os.path.join(images_dir, img_file)
                    dst = os.path.join(target_images_dir, img_file)
                    shutil.copy2(src, dst)
                    
            return {
                "success": True,
                "operation": "import",
                "path": zip_path,
                "format": "zip",
                "settings_updated": True,
                "images_imported": len(os.listdir(images_dir)) if os.path.exists(images_dir) else 0
            }
            
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    def add_export_task(self, destination: str = None, 
                       include_images: bool = False,
                       priority: WorkerPriority = WorkerPriority.NORMAL,
                       callback: Optional[callable] = None) -> bool:
        """Add export task to queue"""
        task = SyncTask(
            operation=SyncOperation.EXPORT,
            destination_path=destination,
            include_images=include_images,
            callback=callback
        )
        return self.add_task(task, priority)
        
    def add_import_task(self, source: str,
                       priority: WorkerPriority = WorkerPriority.HIGH,
                       callback: Optional[callable] = None) -> bool:
        """Add import task to queue"""
        task = SyncTask(
            operation=SyncOperation.IMPORT,
            source_path=source,
            callback=callback
        )
        return self.add_task(task, priority)
        
    def add_backup_task(self, reason: str = "manual",
                       priority: WorkerPriority = WorkerPriority.LOW,
                       callback: Optional[callable] = None) -> bool:
        """Add backup task to queue"""
        task = SyncTask(
            operation=SyncOperation.BACKUP,
            metadata={"reason": reason},
            callback=callback
        )
        return self.add_task(task, priority)
