import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session
from config import Config
import pyotp
import qrcode
import io
import base64

class AdvancedAuth:
    def __init__(self):
        self.failed_attempts = {}
        self.lockout_threshold = 5
        self.lockout_duration = timedelta(minutes=30)
    
    def generate_token(self, user_id, role):
        """JWT token generation"""
        payload = {
            'user_id': user_id,
            'role': role,
            'exp': datetime.utcnow() + timedelta(hours=24),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')
    
    def verify_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def setup_2fa(self, user_id, email):
        """Setup Two-Factor Authentication"""
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(email, issuer_name="Attendify")
        
        # Generate QR code
        img = qrcode.make(uri)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'secret': secret,
            'qr_code': qr_base64,
            'uri': uri
        }
    
    def verify_2fa(self, secret, token):
        """Verify 2FA token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token)
    
    def check_rate_limit(self, identifier):
        """Check and update rate limiting"""
        now = datetime.now()
        
        if identifier in self.failed_attempts:
            attempts, first_attempt = self.failed_attempts[identifier]
            
            # Reset if lockout period passed
            if now - first_attempt > self.lockout_duration:
                del self.failed_attempts[identifier]
                return True
            
            # Check threshold
            if attempts >= self.lockout_threshold:
                return False
        
        return True
    
    def record_failed_attempt(self, identifier):
        """Record failed login attempt"""
        now = datetime.now()
        
        if identifier in self.failed_attempts:
            attempts, _ = self.failed_attempts[identifier]
            self.failed_attempts[identifier] = (attempts + 1, now)
        else:
            self.failed_attempts[identifier] = (1, now)
    
    def reset_failed_attempts(self, identifier):
        """Reset failed attempts on success"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]

# Initialize
auth_system = AdvancedAuth()