"""
RSA key management service for JWT signing and validation.
"""
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from typing import Tuple
import base64
import hashlib
from config import config


class KeyService:
    """Manages RSA keys for JWT signing."""
    
    def __init__(self):
        self.private_key = None
        self.public_key = None
        self.kid = None
        self._load_or_generate_keys()
    
    def _load_or_generate_keys(self):
        """Load existing keys or generate new ones."""
        if config.PRIVATE_KEY_FILE.exists() and config.PUBLIC_KEY_FILE.exists():
            self._load_keys()
        else:
            self._generate_keys()
    
    def _generate_keys(self):
        """Generate new RSA key pair."""
        # Generate private key
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        
        # Save private key
        with open(config.PRIVATE_KEY_FILE, 'wb') as f:
            f.write(self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        # Save public key
        with open(config.PUBLIC_KEY_FILE, 'wb') as f:
            f.write(self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        
        self._generate_kid()
    
    def _load_keys(self):
        """Load existing keys from files."""
        with open(config.PRIVATE_KEY_FILE, 'rb') as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        
        with open(config.PUBLIC_KEY_FILE, 'rb') as f:
            self.public_key = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )
        
        self._generate_kid()
    
    def _generate_kid(self):
        """Generate key ID from public key."""
        public_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        self.kid = base64.urlsafe_b64encode(
            hashlib.sha256(public_bytes).digest()[:8]
        ).decode('utf-8').rstrip('=')
    
    def get_private_key_pem(self) -> str:
        """Get private key in PEM format."""
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')
    
    def get_public_key_pem(self) -> str:
        """Get public key in PEM format."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
    
    def get_jwks(self) -> dict:
        """Get JWKS (JSON Web Key Set) for public key."""
        public_numbers = self.public_key.public_numbers()
        
        # Convert to base64url
        def int_to_base64url(num: int) -> str:
            num_bytes = num.to_bytes((num.bit_length() + 7) // 8, byteorder='big')
            return base64.urlsafe_b64encode(num_bytes).decode('utf-8').rstrip('=')
        
        return {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "kid": self.kid,
                    "alg": "RS256",
                    "n": int_to_base64url(public_numbers.n),
                    "e": int_to_base64url(public_numbers.e)
                }
            ]
        }


# Global instance
key_service = KeyService()
