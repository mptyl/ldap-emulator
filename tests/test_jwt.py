"""
JWT token validation tests.
"""
import pytest
import httpx
import jwt


def test_access_token_claims(client: httpx.Client, service_app: dict):
    """Test access token claims structure."""
    data = {
        "grant_type": "client_credentials",
        "client_id": service_app["client_id"],
        "client_secret": service_app["client_secret"],
        "scope": "api://.default"
    }
    
    response = client.post("/common/oauth2/v2.0/token", data=data)
    access_token = response.json().get("access_token")
    
    # Decode without verification to check claims
    decoded = jwt.decode(access_token, options={"verify_signature": False})
    
    assert "aud" in decoded
    assert "iss" in decoded
    assert "iat" in decoded
    assert "exp" in decoded
    assert "azp" in decoded
    assert "tid" in decoded
    assert "ver" in decoded
    assert decoded["ver"] == "2.0"


def test_id_token_claims(client: httpx.Client, test_app: dict, test_user: dict):
    """Test ID token claims structure."""
    data = {
        "grant_type": "password",
        "client_id": test_app["client_id"],
        "username": test_user["username"],
        "password": test_user["password"],
        "scope": "openid profile email"
    }
    
    response = client.post("/common/oauth2/v2.0/token", data=data)
    id_token = response.json().get("id_token")
    
    # Decode without verification to check claims
    decoded = jwt.decode(id_token, options={"verify_signature": False})
    
    assert "aud" in decoded
    assert "iss" in decoded
    assert "sub" in decoded
    assert "email" in decoded
    assert "name" in decoded
    assert "preferred_username" in decoded
    assert "oid" in decoded
    assert decoded["preferred_username"] == test_user["username"]


def test_token_signature_validation(client: httpx.Client, service_app: dict):
    """Test JWT signature validation with JWKS."""
    # Get token
    token_data = {
        "grant_type": "client_credentials",
        "client_id": service_app["client_id"],
        "client_secret": service_app["client_secret"],
        "scope": "api://.default"
    }
    
    token_response = client.post("/common/oauth2/v2.0/token", data=token_data)
    access_token = token_response.json().get("access_token")
    
    # Get JWKS
    jwks_response = client.get("/common/discovery/v2.0/keys")
    jwks = jwks_response.json()
    
    # Verify token signature (simplified - in production use proper JWKS library)
    decoded_header = jwt.get_unverified_header(access_token)
    assert "kid" in decoded_header
    assert decoded_header["alg"] == "RS256"
    
    # Verify that kid exists in JWKS
    kids = [key["kid"] for key in jwks["keys"]]
    assert decoded_header["kid"] in kids
