import os
import json
import shutil
import hashlib
from datetime import datetime
from typing import Dict, Optional, Tuple
import logging
from filelock import FileLock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CascadeCore:
    """Core functionality for Cascade memory and safety system"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.cascade_path = os.path.join(project_path, '.cascade')
        self._init_structure()

    def _init_structure(self):
        """Initialize minimal required directory structure"""
        dirs = ['data', 'backups', 'locks']
        for d in dirs:
            os.makedirs(os.path.join(self.cascade_path, d), exist_ok=True)

    def _get_lock(self, name: str) -> FileLock:
        """Get a named file lock"""
        lock_path = os.path.join(self.cascade_path, 'locks', f'{name}.lock')
        return FileLock(lock_path)

    def save_memory(self, name: str, content: Dict) -> bool:
        """Save a memory with automatic backup"""
        try:
            # Create quick backup
            self._quick_backup(name)

            # Save memory
            memory_path = os.path.join(self.cascade_path, 'data', f'{name}.json')
            with self._get_lock(name):
                with open(memory_path, 'w') as f:
                    json.dump({
                        'content': content,
                        'updated_at': datetime.utcnow().isoformat(),
                        'hash': self._hash_dict(content)
                    }, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save memory {name}: {e}")
            return False

    def load_memory(self, name: str) -> Optional[Dict]:
        """Load a memory with validation"""
        try:
            memory_path = os.path.join(self.cascade_path, 'data', f'{name}.json')
            if not os.path.exists(memory_path):
                return None
                
            with self._get_lock(name):
                with open(memory_path, 'r') as f:
                    data = json.load(f)
                    
                # Validate hash
                if self._hash_dict(data['content']) != data['hash']:
                    logger.warning(f"Memory {name} failed hash validation")
                    self._restore_backup(name)
                    return self.load_memory(name)
                    
                return data['content']
        except Exception as e:
            logger.error(f"Failed to load memory {name}: {e}")
            return None

    def _quick_backup(self, name: str):
        """Create a quick backup of a memory"""
        src = os.path.join(self.cascade_path, 'data', f'{name}.json')
        if not os.path.exists(src):
            return
            
        backup_dir = os.path.join(self.cascade_path, 'backups', name)
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        dst = os.path.join(backup_dir, f'{timestamp}.json')
        
        shutil.copy2(src, dst)
        
        # Keep only last 3 backups
        backups = sorted([f for f in os.listdir(backup_dir) if f.endswith('.json')])
        for old in backups[:-3]:
            os.remove(os.path.join(backup_dir, old))

    def _restore_backup(self, name: str) -> bool:
        """Restore most recent backup of a memory"""
        backup_dir = os.path.join(self.cascade_path, 'backups', name)
        if not os.path.exists(backup_dir):
            return False
            
        backups = sorted([f for f in os.listdir(backup_dir) if f.endswith('.json')])
        if not backups:
            return False
            
        # Get most recent backup
        latest = backups[-1]
        src = os.path.join(backup_dir, latest)
        dst = os.path.join(self.cascade_path, 'data', f'{name}.json')
        
        shutil.copy2(src, dst)
        return True

    @staticmethod
    def _hash_dict(data: Dict) -> str:
        """Create deterministic hash of dictionary"""
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

# Example usage
if __name__ == "__main__":
    cascade = CascadeCore("/root/mcp-server")
    
    # Save build plan
    build_plan = {
        "current_stage": 1,
        "stages": [
            {
                "name": "Security Implementation",
                "status": "in_progress",
                "tasks": ["Rate limiting", "Input validation"]
            }
        ]
    }
    cascade.save_memory("build_plan", build_plan)
    
    # Load and verify
    loaded = cascade.load_memory("build_plan")
    assert loaded == build_plan, "Memory validation failed"
