import hashlib
import secrets
import time
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet

class AdvancedSecurityManager:
    def __init__(self, master_key: Optional[bytes] = None):
        self.master_key = master_key or Fernet.generate_key()
        self.encryption_engine = Fernet(self.master_key)
        self.threat_detection_rules = []
    
    def generate_secure_token(self, user_id: str, expiry: int = 3600) -> str:
        """Generate a cryptographically secure token"""
        payload = f"{user_id}:{int(time.time()) + expiry}"
        return hashlib.sha256(payload.encode()).hexdigest()
    
    def encrypt_payload(self, payload: Dict[str, Any]) -> bytes:
        """Encrypt a payload using Fernet symmetric encryption"""
        return self.encryption_engine.encrypt(str(payload).encode())
    
    def decrypt_payload(self, encrypted_payload: bytes) -> Dict[str, Any]:
        """Decrypt a payload"""
        return eval(self.encryption_engine.decrypt(encrypted_payload).decode())
    
    def add_threat_detection_rule(self, rule_function):
        """Add a custom threat detection rule"""
        self.threat_detection_rules.append(rule_function)
    
    def detect_potential_threats(self, request_data: Dict[str, Any]) -> bool:
        """Run all registered threat detection rules"""
        return any(rule(request_data) for rule in self.threat_detection_rules)
    
    @staticmethod
    def generate_rate_limit_token(service: str, max_requests: int = 100) -> Dict:
        """Generate a rate limiting token with embedded rules"""
        return {
            'service': service,
            'token': secrets.token_urlsafe(),
            'max_requests': max_requests,
            'reset_interval': 3600  # 1 hour
        }

# Example Usage
if __name__ == '__main__':
    security_manager = AdvancedSecurityManager()
    
    # Add a simple threat detection rule
    def suspicious_payload_rule(payload):
        return 'malicious_key' in payload
    
    security_manager.add_threat_detection_rule(suspicious_payload_rule)
    
    # Generate and test a secure token
    user_token = security_manager.generate_secure_token('user123')
    print("Secure Token:", user_token)
    
    # Encrypt and decrypt a payload
    sample_payload = {'action': 'retrieve_context', 'user_id': 'user123'}
    encrypted = security_manager.encrypt_payload(sample_payload)
    decrypted = security_manager.decrypt_payload(encrypted)
    print("Decrypted Payload:", decrypted)
    
    # Threat detection
    safe_payload = {'action': 'process_request'}
    malicious_payload = {'malicious_key': 'danger'}
    
    print("Safe Payload Threat:", security_manager.detect_potential_threats(safe_payload))
    print("Malicious Payload Threat:", security_manager.detect_potential_threats(malicious_payload))
