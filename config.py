"""
Configuration module for Microsoft Entra ID Emulator.
Loads settings from environment variables for Docker deployment.
"""
import os
from pathlib import Path


class Config:
    """Application configuration loaded from environment variables."""
    
    # Server settings
    HOST: str = os.getenv("EMULATOR_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("EMULATOR_PORT", "8029"))
    
    # Tenant settings
    TENANT_ID: str = os.getenv("TENANT_ID", "common")
    ISSUER_URL: str = os.getenv("ISSUER_URL", "http://localhost:8029")
    
    # Token settings
    TOKEN_EXPIRY_SECONDS: int = int(os.getenv("TOKEN_EXPIRY_SECONDS", "3600"))
    REFRESH_TOKEN_EXPIRY_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRY_DAYS", "14"))
    
    # Directory settings
    BASE_DIR: Path = Path(__file__).parent
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
    KEYS_DIR: Path = Path(os.getenv("KEYS_DIR", BASE_DIR / "keys"))
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    
    # Ensure directories exist
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    KEYS_DIR.mkdir(parents=True, exist_ok=True)
    
    # File paths
    USERS_FILE: Path = DATA_DIR / "users.json"
    APPLICATIONS_FILE: Path = DATA_DIR / "applications.json"
    PRIVATE_KEY_FILE: Path = KEYS_DIR / "private_key.pem"
    PUBLIC_KEY_FILE: Path = KEYS_DIR / "public_key.pem"
    
    # OAuth/OIDC settings
    AUTHORIZATION_CODE_EXPIRY: int = 600  # 10 minutes
    
    @classmethod
    def get_issuer(cls, tenant: str = None) -> str:
        """Get issuer URL for a specific tenant."""
        tenant = tenant or cls.TENANT_ID
        return f"{cls.ISSUER_URL}/{tenant}/v2.0"
    
    @classmethod
    def get_jwks_uri(cls, tenant: str = None) -> str:
        """Get JWKS URI for a specific tenant."""
        tenant = tenant or cls.TENANT_ID
        return f"{cls.ISSUER_URL}/{tenant}/discovery/v2.0/keys"


config = Config()
