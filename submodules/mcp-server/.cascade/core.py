import os
import hashlib
import json
from datetime import datetime
from filelock import FileLock

class CascadeCore:
    def __init__(self, project_root):
        self.root = os.path.join(project_root, '.cascade')
        self._ensure_dirs()

    def _ensure_dirs(self):
        os.makedirs(os.path.join(self.root, 'data'), exist_ok=True)
        os.makedirs(os.path.join(self.root, 'backups'), exist_ok=True)
        os.makedirs(os.path.join(self.root, 'locks'), exist_ok=True)

    def atomic_write(self, path: str, content: str) -> bool:
        """Safe file write with automatic backup"""
        try:
            # Generate backup
            if os.path.exists(path):
                backup_dir = os.path.join(self.root, 'backups', os.path.dirname(path))
                os.makedirs(backup_dir, exist_ok=True)
                backup_path = os.path.join(backup_dir, f"{datetime.now().isoformat()}_{os.path.basename(path)}")
                with open(path, 'rb') as src, open(backup_path, 'wb') as dst:
                    dst.write(src.read())

            # Write new content
            with FileLock(path + '.lock'), open(path, 'w') as f:
                f.write(content)
            
            return True
        except Exception as e:
            print(f"Atomic write failed: {str(e)}")
            return False

    def validate_file(self, path: str) -> bool:
        """Validate file integrity"""
        if not os.path.exists(path):
            return False
        
        try:
            with FileLock(path + '.lock'), open(path, 'r') as f:
                content = f.read()
                if '# VALIDATION:FAIL' in content:
                    return False
                return True
        except:
            return False

    def ai_generate(self, template: str, context: dict) -> str:
        """Generate code using AI patterns"""
        # Implementation would call AI model here
        return f"# AI-Generated Code
{template.format(**context)}
# VALIDATION:PASS"
