"""Routers package."""
from .oauth import router as oauth_router
from .oidc import router as oidc_router
from .saml import router as saml_router

__all__ = ["oauth_router", "oidc_router", "saml_router"]
