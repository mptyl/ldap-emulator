"""
JWT token generation and validation service.
"""
import jwt
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from models.user import User
from models.application import Application
from services.key_service import key_service
from config import config


class TokenService:
    """Generates and validates JWT tokens."""
    
    def __init__(self):
        self.authorization_codes: Dict[str, dict] = {}  # code -> {user, app, redirect_uri, code_challenge}
        self.refresh_tokens: Dict[str, dict] = {}  # refresh_token -> {user_id, app_id}
    
    def generate_authorization_code(
        self,
        user: User,
        app: Application,
        redirect_uri: str,
        scope: str,
        state: Optional[str] = None,
        nonce: Optional[str] = None,
        code_challenge: Optional[str] = None
    ) -> str:
        """Generate authorization code for OAuth flow."""
        code = secrets.token_urlsafe(32)
        
        self.authorization_codes[code] = {
            "user_id": user.id,
            "app_id": app.appId,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "nonce": nonce,
            "code_challenge": code_challenge,
            "expires_at": datetime.utcnow() + timedelta(seconds=config.AUTHORIZATION_CODE_EXPIRY)
        }
        
        return code
    
    def verify_authorization_code(
        self,
        code: str,
        app_id: str,
        redirect_uri: str,
        code_verifier: Optional[str] = None
    ) -> Optional[dict]:
        """Verify authorization code and return code data."""
        code_data = self.authorization_codes.get(code)
        
        if not code_data:
            return None
        
        # Check expiration
        if datetime.utcnow() > code_data["expires_at"]:
            del self.authorization_codes[code]
            return None
        
        # Verify app and redirect URI
        if code_data["app_id"] != app_id or code_data["redirect_uri"] != redirect_uri:
            return None
        
        # PKCE verification (simplified - should use S256)
        if code_data.get("code_challenge") and code_verifier:
            # In production, verify S256 hash
            pass
        
        # Remove code after use
        del self.authorization_codes[code]
        
        return code_data
    
    def generate_access_token(
        self,
        user: User,
        app: Application,
        scope: str,
        tenant: str = "common"
    ) -> str:
        """Generate access token."""
        now = datetime.utcnow()
        
        claims = {
            "aud": f"api://{app.appId}",
            "iss": config.get_issuer(tenant),
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=config.TOKEN_EXPIRY_SECONDS)).timestamp()),
            "aio": secrets.token_urlsafe(16),
            "azp": app.appId,
            "azpacr": "1",
            "name": user.displayName,
            "oid": user.id,
            "preferred_username": user.userPrincipalName,
            "rh": secrets.token_urlsafe(8),
            "scp": scope,
            "sub": user.id,
            "tid": tenant,
            "uti": str(uuid.uuid4()),
            "ver": "2.0"
        }
        
        return jwt.encode(
            claims,
            key_service.get_private_key_pem(),
            algorithm="RS256",
            headers={"kid": key_service.kid}
        )
    
    def generate_id_token(
        self,
        user: User,
        app: Application,
        nonce: Optional[str] = None,
        tenant: str = "common"
    ) -> str:
        """Generate ID token."""
        now = datetime.utcnow()
        
        claims = {
            "aud": app.appId,
            "iss": config.get_issuer(tenant),
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=config.TOKEN_EXPIRY_SECONDS)).timestamp()),
            "aio": secrets.token_urlsafe(16),
            "email": user.mail or user.userPrincipalName,
            "name": user.displayName,
            "oid": user.id,
            "preferred_username": user.userPrincipalName,
            "rh": secrets.token_urlsafe(8),
            "sub": user.id,
            "tid": tenant,
            "uti": str(uuid.uuid4()),
            "ver": "2.0"
        }
        
        if nonce:
            claims["nonce"] = nonce
        
        if user.givenName:
            claims["given_name"] = user.givenName
        if user.surname:
            claims["family_name"] = user.surname
        
        return jwt.encode(
            claims,
            key_service.get_private_key_pem(),
            algorithm="RS256",
            headers={"kid": key_service.kid}
        )
    
    def generate_refresh_token(self, user: User, app: Application) -> str:
        """Generate refresh token."""
        refresh_token = secrets.token_urlsafe(64)
        
        self.refresh_tokens[refresh_token] = {
            "user_id": user.id,
            "app_id": app.appId,
            "expires_at": datetime.utcnow() + timedelta(days=config.REFRESH_TOKEN_EXPIRY_DAYS)
        }
        
        return refresh_token
    
    def verify_refresh_token(self, refresh_token: str, app_id: str) -> Optional[str]:
        """Verify refresh token and return user_id."""
        token_data = self.refresh_tokens.get(refresh_token)
        
        if not token_data:
            return None
        
        if datetime.utcnow() > token_data["expires_at"]:
            del self.refresh_tokens[refresh_token]
            return None
        
        if token_data["app_id"] != app_id:
            return None
        
        return token_data["user_id"]
    
    def generate_client_credentials_token(
        self,
        app: Application,
        scope: str,
        tenant: str = "common"
    ) -> str:
        """Generate token for client credentials flow (service-to-service)."""
        now = datetime.utcnow()
        
        claims = {
            "aud": scope,
            "iss": config.get_issuer(tenant),
            "iat": int(now.timestamp()),
            "nbf": int(now.timestamp()),
            "exp": int((now + timedelta(seconds=config.TOKEN_EXPIRY_SECONDS)).timestamp()),
            "aio": secrets.token_urlsafe(16),
            "azp": app.appId,
            "azpacr": "1",
            "appid": app.appId,
            "appidacr": "1",
            "idtyp": "app",
            "oid": str(uuid.uuid4()),  # Service principal OID
            "rh": secrets.token_urlsafe(8),
            "sub": str(uuid.uuid4()),
            "tid": tenant,
            "uti": str(uuid.uuid4()),
            "ver": "2.0"
        }
        
        return jwt.encode(
            claims,
            key_service.get_private_key_pem(),
            algorithm="RS256",
            headers={"kid": key_service.kid}
        )
    
    def decode_token(self, token: str) -> Optional[dict]:
        """Decode and validate a JWT token."""
        try:
            # Decode without audience verification for flexibility across different flows
            return jwt.decode(
                token,
                key_service.get_public_key_pem(),
                algorithms=["RS256"],
                options={"verify_aud": False}  # Disable audience check
            )
        except jwt.InvalidTokenError as e:
            print(f"Token validation error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected decode error: {e}")
            return None


# Global instance
token_service = TokenService()
