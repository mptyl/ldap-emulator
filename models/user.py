"""
User model for Microsoft Entra ID Emulator.
"""
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class User(BaseModel):
    """User model matching Office 365 structure."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    userPrincipalName: str  # email
    displayName: str
    givenName: Optional[str] = None
    surname: Optional[str] = None
    mail: Optional[str] = None
    jobTitle: Optional[str] = None
    department: Optional[str] = None
    passwordHash: str  # bcrypt hash
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "12345678-1234-1234-1234-123456789012",
                "userPrincipalName": "mario.rossi@contoso.onmicrosoft.com",
                "displayName": "Mario Rossi",
                "givenName": "Mario",
                "surname": "Rossi",
                "mail": "mario.rossi@contoso.onmicrosoft.com",
                "jobTitle": "Developer",
                "department": "IT",
                "passwordHash": "$2b$12$..."
            }
        }
