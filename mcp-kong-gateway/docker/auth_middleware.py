import jwt
import datetime
from functools import wraps
from flask import request, jsonify

class MCPAuthMiddleware:
    def __init__(self, secret_key):
        self.secret_key = secret_key
    
    def generate_token(self, user_id, expiration=30):
        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=expiration)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def validate_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def token_required(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'No authentication token'}), 401
            
            payload = self.validate_token(token)
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            return f(*args, **kwargs)
        return decorated
