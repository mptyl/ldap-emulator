"""
User management service.
"""
import json
import bcrypt
from typing import Optional, List
from models.user import User
from config import config


class UserService:
    """Manages users and authentication."""
    
    def __init__(self):
        self.users: List[User] = []
        self._load_users()
    
    def _load_users(self):
        """Load users from JSON file."""
        if config.USERS_FILE.exists():
            with open(config.USERS_FILE, 'r') as f:
                data = json.load(f)
                self.users = [User(**user) for user in data]
        else:
            # Create default test users
            self._create_default_users()
    
    def _create_default_users(self):
        """Create default test users."""
        default_users = [
            User(
                userPrincipalName="admin@contoso.onmicrosoft.com",
                displayName="Admin User",
                givenName="Admin",
                surname="User",
                mail="admin@contoso.onmicrosoft.com",
                jobTitle="Administrator",
                department="IT",
                passwordHash=bcrypt.hashpw("Password123!".encode(), bcrypt.gensalt()).decode()
            ),
            User(
                userPrincipalName="test@contoso.onmicrosoft.com",
                displayName="Test User",
                givenName="Test",
                surname="User",
                mail="test@contoso.onmicrosoft.com",
                jobTitle="Developer",
                department="Engineering",
                passwordHash=bcrypt.hashpw("Test123!".encode(), bcrypt.gensalt()).decode()
            )
        ]
        self.users = default_users
        self._save_users()
    
    def _save_users(self):
        """Save users to JSON file."""
        with open(config.USERS_FILE, 'w') as f:
            json.dump([user.model_dump() for user in self.users], f, indent=2)
    
    def get_user_by_upn(self, upn: str) -> Optional[User]:
        """Get user by userPrincipalName."""
        return next((u for u in self.users if u.userPrincipalName == upn), None)
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return next((u for u in self.users if u.id == user_id), None)
    
    def verify_password(self, upn: str, password: str) -> Optional[User]:
        """Verify user credentials."""
        user = self.get_user_by_upn(upn)
        if user and bcrypt.checkpw(password.encode(), user.passwordHash.encode()):
            return user
        return None
    
    def create_user(self, user: User) -> User:
        """Create a new user."""
        # Hash password if it's plain text
        if not user.passwordHash.startswith("$2b$"):
            user.passwordHash = bcrypt.hashpw(user.passwordHash.encode(), bcrypt.gensalt()).decode()
        
        self.users.append(user)
        self._save_users()
        return user
    
    def list_users(self) -> List[User]:
        """List all users."""
        return self.users


# Global instance
user_service = UserService()
