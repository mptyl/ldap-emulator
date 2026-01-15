"""
OpenID Connect endpoints for Microsoft Entra ID Emulator.
"""
from fastapi import APIRouter, Header, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from services import key_service, token_service, user_service
from config import config

router = APIRouter()
security = HTTPBearer()


@router.get("/{tenant}/v2.0/.well-known/openid-configuration")
async def openid_configuration(tenant: str):
    """OpenID Connect Discovery Document."""
    base_url = config.ISSUER_URL
    
    return {
        "issuer": config.get_issuer(tenant),
        "authorization_endpoint": f"{base_url}/{tenant}/oauth2/v2.0/authorize",
        "token_endpoint": f"{base_url}/{tenant}/oauth2/v2.0/token",
        "token_endpoint_auth_methods_supported": [
            "client_secret_post",
            "client_secret_basic"
        ],
        "jwks_uri": config.get_jwks_uri(tenant),
        "response_modes_supported": ["query", "fragment", "form_post"],
        "subject_types_supported": ["pairwise"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "response_types_supported": [
            "code",
            "id_token",
            "code id_token",
            "id_token token"
        ],
        "scopes_supported": [
            "openid",
            "profile",
            "email",
            "offline_access"
        ],
        "issuer": config.get_issuer(tenant),
        "claims_supported": [
            "sub",
            "iss",
            "aud",
            "exp",
            "iat",
            "auth_time",
            "acr",
            "nonce",
            "preferred_username",
            "name",
            "tid",
            "ver",
            "at_hash",
            "c_hash",
            "email"
        ],
        "request_uri_parameter_supported": False,
        "userinfo_endpoint": f"{base_url}/oidc/userinfo",
        "end_session_endpoint": f"{base_url}/{tenant}/oauth2/v2.0/logout",
        "http_logout_supported": True,
        "frontchannel_logout_supported": True
    }


@router.get("/{tenant}/discovery/v2.0/keys")
async def jwks(tenant: str):
    """JWKS endpoint - exposes public keys for JWT validation."""
    return key_service.get_jwks()


@router.get("/oidc/userinfo")
async def userinfo(authorization: Optional[str] = Header(None)):
    """UserInfo endpoint - returns user information based on access token."""
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = parts[1]
    
    # Decode and validate token
    claims = token_service.decode_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get user
    user_id = claims.get("oid") or claims.get("sub")
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return user info
    return {
        "sub": user.id,
        "name": user.displayName,
        "given_name": user.givenName,
        "family_name": user.surname,
        "preferred_username": user.userPrincipalName,
        "email": user.mail or user.userPrincipalName
    }
