"""
Microsoft Entra ID Emulator - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from routers import oauth_router, oidc_router, saml_router
from config import config

# Create FastAPI app
app = FastAPI(
    title="Microsoft Entra ID Emulator",
    description="OAuth 2.0 and OpenID Connect emulator for development and testing",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(oauth_router, tags=["OAuth 2.0"])
app.include_router(oidc_router, tags=["OpenID Connect"])
app.include_router(saml_router, tags=["SAML"])


@app.get("/")
async def root():
    """Root endpoint with emulator information."""
    return {
        "service": "Microsoft Entra ID Emulator",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "discovery": f"/{config.TENANT_ID}/v2.0/.well-known/openid-configuration",
            "authorize": f"/{config.TENANT_ID}/oauth2/v2.0/authorize",
            "token": f"/{config.TENANT_ID}/oauth2/v2.0/token",
            "jwks": f"/{config.TENANT_ID}/discovery/v2.0/keys",
            "userinfo": "/oidc/userinfo",
            "federation_metadata": f"/{config.TENANT_ID}/FederationMetadata/2007-06/FederationMetadata.xml"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint for Docker."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level="info"
    )
