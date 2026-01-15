"""
Application registry service.
"""
import json
from typing import Optional, List
from models.application import Application
from config import config


class AppService:
    """Manages application registrations."""
    
    def __init__(self):
        self.applications: List[Application] = []
        self._load_applications()
    
    def _load_applications(self):
        """Load applications from JSON file."""
        if config.APPLICATIONS_FILE.exists():
            with open(config.APPLICATIONS_FILE, 'r') as f:
                data = json.load(f)
                self.applications = [Application(**app) for app in data]
        else:
            # Create default test applications
            self._create_default_applications()
    
    def _create_default_applications(self):
        """Create default test applications."""
        default_apps = [
            Application(
                appId="test-app-123",
                displayName="Test Web Application",
                clientSecret="test-secret",
                redirectUris=["http://localhost:3029/callback", "http://localhost:3029/auth"],
                allowedScopes=["openid", "profile", "email", "User.Read"]
            ),
            Application(
                appId="service-app-456",
                displayName="Test Service Application",
                clientSecret="service-secret",
                redirectUris=[],
                allowedScopes=["api://.default", "https://graph.microsoft.com/.default"]
            )
        ]
        self.applications = default_apps
        self._save_applications()
    
    def _save_applications(self):
        """Save applications to JSON file."""
        with open(config.APPLICATIONS_FILE, 'w') as f:
            json.dump([app.model_dump() for app in self.applications], f, indent=2)
    
    def get_app_by_id(self, app_id: str) -> Optional[Application]:
        """Get application by client ID."""
        return next((a for a in self.applications if a.appId == app_id), None)
    
    def verify_client_secret(self, app_id: str, client_secret: str) -> Optional[Application]:
        """Verify client credentials."""
        app = self.get_app_by_id(app_id)
        if app and app.clientSecret == client_secret:
            return app
        return None
    
    def is_redirect_uri_valid(self, app_id: str, redirect_uri: str) -> bool:
        """Check if redirect URI is valid for the application."""
        app = self.get_app_by_id(app_id)
        return app is not None and redirect_uri in app.redirectUris
    
    def create_app(self, app: Application) -> Application:
        """Create a new application."""
        self.applications.append(app)
        self._save_applications()
        return app
    
    def list_applications(self) -> List[Application]:
        """List all applications."""
        return self.applications


# Global instance
app_service = AppService()
