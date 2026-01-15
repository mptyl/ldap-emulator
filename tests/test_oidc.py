"""
OpenID Connect endpoint tests.
"""
import pytest
import httpx


def test_discovery_document(client: httpx.Client):
    """Test OIDC discovery document."""
    response = client.get("/common/v2.0/.well-known/openid-configuration")
    
    assert response.status_code == 200
    json_data = response.json()
    
    assert "issuer" in json_data
    assert "authorization_endpoint" in json_data
    assert "token_endpoint" in json_data
    assert "jwks_uri" in json_data
    assert "userinfo_endpoint" in json_data
    assert "openid" in json_data["scopes_supported"]
    assert "RS256" in json_data["id_token_signing_alg_values_supported"]


def test_jwks_endpoint(client: httpx.Client):
    """Test JWKS endpoint."""
    response = client.get("/common/discovery/v2.0/keys")
    
    assert response.status_code == 200
    json_data = response.json()
    
    assert "keys" in json_data
    assert len(json_data["keys"]) > 0
    
    key = json_data["keys"][0]
    assert key["kty"] == "RSA"
    assert key["use"] == "sig"
    assert key["alg"] == "RS256"
    assert "kid" in key
    assert "n" in key
    assert "e" in key


def test_userinfo_endpoint(client: httpx.Client, test_app: dict, test_user: dict):
    """Test UserInfo endpoint."""
    # Get access token via ROPC
    token_data = {
        "grant_type": "password",
        "client_id": test_app["client_id"],
        "username": test_user["username"],
        "password": test_user["password"],
        "scope": "openid profile email"
    }
    
    token_response = client.post("/common/oauth2/v2.0/token", data=token_data)
    access_token = token_response.json().get("access_token")
    
    assert access_token is not None
    
    # Call userinfo endpoint
    headers = {"Authorization": f"Bearer {access_token}"}
    userinfo_response = client.get("/oidc/userinfo", headers=headers)
    
    assert userinfo_response.status_code == 200
    user_data = userinfo_response.json()
    
    assert "sub" in user_data
    assert "name" in user_data
    assert "preferred_username" in user_data
    assert user_data["preferred_username"] == test_user["username"]
