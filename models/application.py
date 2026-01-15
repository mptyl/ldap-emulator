"""
Application model for Microsoft Entra ID Emulator.
"""
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid


class Application(BaseModel):
    """Application registration model."""
    
    appId: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Client ID
    displayName: str
    clientSecret: Optional[str] = None  # For confidential clients
    redirectUris: List[str] = Field(default_factory=list)
    allowedScopes: List[str] = Field(default_factory=lambda: ["openid", "profile", "email"])
    
    class Config:
        json_schema_extra = {
            "example": {
                "appId": "00001111-aaaa-2222-bbbb-3333cccc4444",
                "displayName": "Test Application",
                "clientSecret": "secret123",
                "redirectUris": ["http://localhost:3029/callback"],
                "allowedScopes": ["openid", "profile", "email", "User.Read"]
            }
        }
