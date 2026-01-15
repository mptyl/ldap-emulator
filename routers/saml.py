"""
SAML Federation Metadata endpoint.
"""
from fastapi import APIRouter
from fastapi.responses import Response
from services import key_service
from config import config
from cryptography.hazmat.primitives import serialization
import base64

router = APIRouter()


@router.get("/{tenant}/FederationMetadata/2007-06/FederationMetadata.xml")
async def federation_metadata(tenant: str):
    """SAML 2.0 Federation Metadata."""
    
    # Get public key certificate (simplified - in production would use X.509)
    public_pem = key_service.get_public_key_pem()
    # Remove headers and format as single line
    cert_content = public_pem.replace("-----BEGIN PUBLIC KEY-----", "")
    cert_content = cert_content.replace("-----END PUBLIC KEY-----", "")
    cert_content = cert_content.replace("\n", "")
    
    entity_id = f"https://sts.windows.net/{tenant}/"
    base_url = config.ISSUER_URL
    
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<EntityDescriptor xmlns="urn:oasis:names:tc:SAML:2.0:metadata" 
                  entityID="{entity_id}">
  <IDPSSODescriptor protocolSupportEnumeration="urn:oasis:names:tc:SAML:2.0:protocol">
    <KeyDescriptor use="signing">
      <KeyInfo xmlns="http://www.w3.org/2000/09/xmldsig#">
        <X509Data>
          <X509Certificate>{cert_content}</X509Certificate>
        </X509Data>
      </KeyInfo>
    </KeyDescriptor>
    <SingleLogoutService 
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" 
      Location="{base_url}/{tenant}/saml2"/>
    <SingleSignOnService 
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect" 
      Location="{base_url}/{tenant}/saml2"/>
    <SingleSignOnService 
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" 
      Location="{base_url}/{tenant}/saml2"/>
  </IDPSSODescriptor>
</EntityDescriptor>"""
    
    return Response(content=xml, media_type="application/xml")
