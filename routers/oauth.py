"""
OAuth 2.0 endpoints for Microsoft Entra ID Emulator.
"""
from fastapi import APIRouter, Form, Query, HTTPException, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from services import user_service, app_service, token_service
from config import config

router = APIRouter()
templates = Jinja2Templates(directory=str(config.TEMPLATES_DIR))


@router.get("/{tenant}/oauth2/v2.0/authorize")
async def authorize(
    request: Request,
    tenant: str,
    client_id: str = Query(...),
    response_type: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query("openid profile"),
    state: Optional[str] = Query(None),
    nonce: Optional[str] = Query(None),
    code_challenge: Optional[str] = Query(None),
    code_challenge_method: Optional[str] = Query(None),
    response_mode: Optional[str] = Query("query"),
    # Simulate logged-in user via query param for testing
    test_user: Optional[str] = Query(None)
):
    """OAuth 2.0 authorization endpoint."""
    
    # Verify application
    app = app_service.get_app_by_id(client_id)
    if not app:
        raise HTTPException(status_code=400, detail="Invalid client_id")
    
    # Verify redirect URI
    if not app_service.is_redirect_uri_valid(client_id, redirect_uri):
        raise HTTPException(status_code=400, detail="Invalid redirect_uri")
    
    # In a real implementation, this would show a login page
    # For testing, we accept test_user parameter to simulate authentication
    if test_user:
        user = user_service.get_user_by_upn(test_user)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid test_user")
    else:
        # Return login page
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": scope,
                "state": state,
                "nonce": nonce,
                "code_challenge": code_challenge,
                "response_type": response_type
            }
        )
    
    # Generate authorization code
    auth_code = token_service.generate_authorization_code(
        user=user,
        app=app,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        nonce=nonce,
        code_challenge=code_challenge
    )
    
    # Build redirect URL
    separator = "&" if "?" in redirect_uri else "?"
    redirect_url = f"{redirect_uri}{separator}code={auth_code}"
    if state:
        redirect_url += f"&state={state}"
    
    return RedirectResponse(url=redirect_url)


@router.post("/{tenant}/oauth2/v2.0/authorize")
async def authorize_post(
    tenant: str,
    username: str = Form(...),
    password: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form("openid profile"),
    state: Optional[str] = Form(None),
    nonce: Optional[str] = Form(None),
    code_challenge: Optional[str] = Form(None),
    response_type: str = Form("code")
):
    """Handle login form submission."""
    
    # Verify credentials
    user = user_service.verify_password(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify application
    app = app_service.get_app_by_id(client_id)
    if not app:
        raise HTTPException(status_code=400, detail="Invalid client_id")
    
    # Generate authorization code
    auth_code = token_service.generate_authorization_code(
        user=user,
        app=app,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        nonce=nonce,
        code_challenge=code_challenge
    )
    
    # Redirect back to application
    separator = "&" if "?" in redirect_uri else "?"
    redirect_url = f"{redirect_uri}{separator}code={auth_code}"
    if state:
        redirect_url += f"&state={state}"
    
    return RedirectResponse(url=redirect_url, status_code=302)


@router.post("/{tenant}/oauth2/v2.0/token")
async def token(
    tenant: str,
    grant_type: str = Form(...),
    client_id: str = Form(...),
    client_secret: Optional[str] = Form(None),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    scope: Optional[str] = Form(None),
    username: Optional[str] = Form(None),  # ROPC
    password: Optional[str] = Form(None),  # ROPC
    code_verifier: Optional[str] = Form(None)  # PKCE
):
    """OAuth 2.0 token endpoint."""
    
    # Verify client
    app = app_service.get_app_by_id(client_id)
    if not app:
        raise HTTPException(status_code=400, detail="invalid_client")
    
    if grant_type == "authorization_code":
        # Authorization Code Flow
        if not code or not redirect_uri:
            raise HTTPException(status_code=400, detail="invalid_request")
        
        # Verify client secret if provided
        if client_secret and app.clientSecret:
            if not app_service.verify_client_secret(client_id, client_secret):
                raise HTTPException(status_code=401, detail="invalid_client")
        
        # Verify authorization code
        code_data = token_service.verify_authorization_code(
            code, client_id, redirect_uri, code_verifier
        )
        if not code_data:
            raise HTTPException(status_code=400, detail="invalid_grant")
        
        # Get user
        user = user_service.get_user_by_id(code_data["user_id"])
        if not user:
            raise HTTPException(status_code=400, detail="invalid_grant")
        
        # Generate tokens
        access_token = token_service.generate_access_token(
            user, app, code_data["scope"], tenant
        )
        id_token = token_service.generate_id_token(
            user, app, code_data.get("nonce"), tenant
        )
        refresh_token = token_service.generate_refresh_token(user, app)
        
        return {
            "token_type": "Bearer",
            "expires_in": config.TOKEN_EXPIRY_SECONDS,
            "ext_expires_in": config.TOKEN_EXPIRY_SECONDS,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "id_token": id_token
        }
    
    elif grant_type == "client_credentials":
        # Client Credentials Flow
        if not client_secret:
            raise HTTPException(status_code=400, detail="invalid_request")
        
        if not app_service.verify_client_secret(client_id, client_secret):
            raise HTTPException(status_code=401, detail="invalid_client")
        
        scope = scope or "api://.default"
        access_token = token_service.generate_client_credentials_token(app, scope, tenant)
        
        return {
            "token_type": "Bearer",
            "expires_in": config.TOKEN_EXPIRY_SECONDS,
            "access_token": access_token
        }
    
    elif grant_type == "refresh_token":
        # Refresh Token Flow
        if not refresh_token:
            raise HTTPException(status_code=400, detail="invalid_request")
        
        user_id = token_service.verify_refresh_token(refresh_token, client_id)
        if not user_id:
            raise HTTPException(status_code=400, detail="invalid_grant")
        
        user = user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=400, detail="invalid_grant")
        
        scope = scope or "openid profile"
        access_token = token_service.generate_access_token(user, app, scope, tenant)
        id_token = token_service.generate_id_token(user, app, None, tenant)
        new_refresh_token = token_service.generate_refresh_token(user, app)
        
        return {
            "token_type": "Bearer",
            "expires_in": config.TOKEN_EXPIRY_SECONDS,
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "id_token": id_token
        }
    
    elif grant_type == "password":
        # Resource Owner Password Credentials (ROPC) - for testing only
        if not username or not password:
            raise HTTPException(status_code=400, detail="invalid_request")
        
        user = user_service.verify_password(username, password)
        if not user:
            raise HTTPException(status_code=401, detail="invalid_grant")
        
        scope = scope or "openid profile"
        access_token = token_service.generate_access_token(user, app, scope, tenant)
        id_token = token_service.generate_id_token(user, app, None, tenant)
        refresh_token = token_service.generate_refresh_token(user, app)
        
        return {
            "token_type": "Bearer",
            "expires_in": config.TOKEN_EXPIRY_SECONDS,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "id_token": id_token
        }
    
    else:
        raise HTTPException(status_code=400, detail="unsupported_grant_type")


@router.get("/{tenant}/oauth2/v2.0/logout")
async def logout_get(
    tenant: str,
    post_logout_redirect_uri: Optional[str] = Query(None),
    id_token_hint: Optional[str] = Query(None),
    state: Optional[str] = Query(None)
):
    """
    OAuth 2.0 / OIDC end_session endpoint (GET).
    
    This endpoint handles user logout and optionally redirects to 
    post_logout_redirect_uri if provided and valid.
    """
    # In a real implementation, you would:
    # 1. Validate id_token_hint if provided
    # 2. Clear server-side session
    # 3. Validate post_logout_redirect_uri against registered URIs
    
    # For the emulator, we simply redirect if a URI is provided
    if post_logout_redirect_uri:
        redirect_url = post_logout_redirect_uri
        if state:
            separator = "&" if "?" in redirect_url else "?"
            redirect_url += f"{separator}state={state}"
        return RedirectResponse(url=redirect_url, status_code=302)
    
    # If no redirect URI, return a simple logout confirmation
    return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Signed Out</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                       display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;
                       background: #f5f5f5; }
                .container { text-align: center; padding: 40px; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; margin-bottom: 10px; }
                p { color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>You have been signed out</h1>
                <p>You have successfully signed out of your account.</p>
            </div>
        </body>
        </html>
    """, status_code=200)


@router.post("/{tenant}/oauth2/v2.0/logout")
async def logout_post(
    tenant: str,
    post_logout_redirect_uri: Optional[str] = Form(None),
    id_token_hint: Optional[str] = Form(None),
    state: Optional[str] = Form(None)
):
    """
    OAuth 2.0 / OIDC end_session endpoint (POST).
    
    Same as GET but accepts form data.
    """
    return await logout_get(tenant, post_logout_redirect_uri, id_token_hint, state)

