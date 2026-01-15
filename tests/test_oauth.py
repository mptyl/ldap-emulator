"""
OAuth 2.0 endpoint tests.
"""
import pytest
import httpx


def test_authorization_endpoint_redirect(client: httpx.Client, test_app: dict, test_user: dict):
    """Test authorization endpoint with test_user parameter."""
    params = {
        "client_id": test_app["client_id"],
        "response_type": "code",
        "redirect_uri": test_app["redirect_uri"],
        "scope": "openid profile",
        "state": "test-state-123",
        "test_user": test_user["username"]
    }
    
    response = client.get("/common/oauth2/v2.0/authorize", params=params, follow_redirects=False)
    
    assert response.status_code == 307
    assert "code=" in response.headers.get("location", "")
    assert "state=test-state-123" in response.headers.get("location", "")


def test_token_endpoint_client_credentials(client: httpx.Client, service_app: dict):
    """Test client credentials flow."""
    data = {
        "grant_type": "client_credentials",
        "client_id": service_app["client_id"],
        "client_secret": service_app["client_secret"],
        "scope": "api://.default"
    }
    
    response = client.post("/common/oauth2/v2.0/token", data=data)
    
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert json_data["token_type"] == "Bearer"
    assert json_data["expires_in"] == 3600


def test_token_endpoint_authorization_code(client: httpx.Client, test_app: dict, test_user: dict):
    """Test authorization code flow."""
    # First, get authorization code
    auth_params = {
        "client_id": test_app["client_id"],
        "response_type": "code",
        "redirect_uri": test_app["redirect_uri"],
        "scope": "openid profile",
        "test_user": test_user["username"]
    }
    
    auth_response = client.get("/common/oauth2/v2.0/authorize", params=auth_params, follow_redirects=False)
    location = auth_response.headers.get("location", "")
    
    # Extract code from redirect URL
    code = location.split("code=")[1].split("&")[0] if "code=" in location else None
    assert code is not None
    
    # Exchange code for token
    token_data = {
        "grant_type": "authorization_code",
        "client_id": test_app["client_id"],
        "client_secret": test_app["client_secret"],
        "code": code,
        "redirect_uri": test_app["redirect_uri"]
    }
    
    token_response = client.post("/common/oauth2/v2.0/token", data=token_data)
    
    assert token_response.status_code == 200
    json_data = token_response.json()
    assert "access_token" in json_data
    assert "id_token" in json_data
    assert "refresh_token" in json_data


def test_token_refresh(client: httpx.Client, test_app: dict, test_user: dict):
    """Test refresh token flow."""
    # Get initial tokens via ROPC
    ropc_data = {
        "grant_type": "password",
        "client_id": test_app["client_id"],
        "username": test_user["username"],
        "password": test_user["password"],
        "scope": "openid profile"
    }
    
    ropc_response = client.post("/common/oauth2/v2.0/token", data=ropc_data)
    refresh_token = ropc_response.json().get("refresh_token")
    
    assert refresh_token is not None
    
    # Use refresh token to get new tokens
    refresh_data = {
        "grant_type": "refresh_token",
        "client_id": test_app["client_id"],
        "refresh_token": refresh_token,
        "scope": "openid profile"
    }
    
    refresh_response = client.post("/common/oauth2/v2.0/token", data=refresh_data)
    
    assert refresh_response.status_code == 200
    json_data = refresh_response.json()
    assert "access_token" in json_data
    assert "refresh_token" in json_data


def test_ropc_flow(client: httpx.Client, test_app: dict, test_user: dict):
    """Test Resource Owner Password Credentials flow."""
    data = {
        "grant_type": "password",
        "client_id": test_app["client_id"],
        "username": test_user["username"],
        "password": test_user["password"],
        "scope": "openid profile email"
    }
    
    response = client.post("/common/oauth2/v2.0/token", data=data)
    
    assert response.status_code == 200
    json_data = response.json()
    assert "access_token" in json_data
    assert "id_token" in json_data
    assert json_data["token_type"] == "Bearer"
