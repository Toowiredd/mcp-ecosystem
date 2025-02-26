import os
import shutil
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import hashlib
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CascadeSafety:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.cascade_path = os.path.join(project_path, '.cascade')
        self.backup_path = os.path.join(self.cascade_path, 'backups')
        self.safety_path = os.path.join(self.cascade_path, 'safety')
        
        # Create necessary directories
        os.makedirs(self.backup_path, exist_ok=True)
        os.makedirs(self.safety_path, exist_ok=True)

    def _calculate_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file"""
        if not os.path.exists(file_path):
            return ""
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def create_backup(self) -> str:
        """Create a backup of the entire .cascade directory"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_name = f"cascade_backup_{timestamp}"
        backup_dir = os.path.join(self.backup_path, backup_name)
        
        try:
            # Create backup directory
            os.makedirs(backup_dir)
            
            # Copy all files except backups directory
            for item in os.listdir(self.cascade_path):
                if item != 'backups':
                    src = os.path.join(self.cascade_path, item)
                    dst = os.path.join(backup_dir, item)
                    if os.path.isdir(src):
                        shutil.copytree(src, dst)
                    else:
                        shutil.copy2(src, dst)
            
            # Create backup manifest
            manifest = {
                "timestamp": datetime.utcnow().isoformat(),
                "files": []
            }
            
            for root, _, files in os.walk(backup_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, backup_dir)
                    manifest["files"].append({
                        "path": rel_path,
                        "hash": self._calculate_hash(file_path)
                    })
            
            # Save manifest
            manifest_path = os.path.join(backup_dir, "manifest.json")
            with open(manifest_path, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Created backup: {backup_name}")
            return backup_name
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            raise

    def safe_to_modify(self, file_path: str) -> Tuple[bool, str]:
        """Check if it's safe to modify a file"""
        if not os.path.exists(file_path):
            return True, "File does not exist"
            
        # Get file metadata
        stat = os.stat(file_path)
        file_hash = self._calculate_hash(file_path)
        
        # Check safety record
        safety_record_path = os.path.join(
            self.safety_path, 
            f"{os.path.basename(file_path)}.json"
        )
        
        if os.path.exists(safety_record_path):
            with open(safety_record_path, 'r') as f:
                record = json.load(f)
                
            if record["hash"] != file_hash:
                return False, "File has been modified outside of Cascade"
                
            if record["mtime"] != stat.st_mtime:
                return False, "File timestamp has changed"
                
        return True, "Safe to modify"

    def record_file_state(self, file_path: str):
        """Record the current state of a file"""
        if not os.path.exists(file_path):
            return
            
        stat = os.stat(file_path)
        record = {
            "path": file_path,
            "hash": self._calculate_hash(file_path),
            "mtime": stat.st_mtime,
            "recorded_at": datetime.utcnow().isoformat()
        }
        
        safety_record_path = os.path.join(
            self.safety_path, 
            f"{os.path.basename(file_path)}.json"
        )
        
        with open(safety_record_path, 'w') as f:
            json.dump(record, f, indent=2)

    def cleanup_old_backups(self, keep_last: int = 5):
        """Clean up old backups, keeping the specified number of most recent ones"""
        backups = []
        for item in os.listdir(self.backup_path):
            item_path = os.path.join(self.backup_path, item)
            if os.path.isdir(item_path) and item.startswith("cascade_backup_"):
                backups.append(item)
        
        backups.sort(reverse=True)  # Sort by timestamp (newest first)
        
        # Remove old backups
        for backup in backups[keep_last:]:
            backup_path = os.path.join(self.backup_path, backup)
            try:
                shutil.rmtree(backup_path)
                logger.info(f"Removed old backup: {backup}")
            except Exception as e:
                logger.error(f"Failed to remove backup {backup}: {str(e)}")

# Self-critique
IMPLEMENTATION_CRITIQUE = {
    "strengths": [
        "Automatic backup system with manifests",
        "File state tracking with hashes",
        "Safety checks before modifications",
        "Cleanup of old backups"
    ],
    "weaknesses": [
        "No compression for backups",
        "Single-threaded backup process",
        "Basic file comparison (could use more sophisticated diff)",
        "No restore functionality yet"
    ],
    "improvements": [
        "Add backup compression",
        "Implement parallel backup for large directories",
        "Add detailed file diff functionality",
        "Add backup restore capability",
        "Add selective backup feature"
    ]
}
