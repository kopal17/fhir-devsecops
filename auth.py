"""
Token verification utility.
In production: validates Azure AD / Entra ID JWT tokens.
"""

from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)


def verify_token(authorization: str | None) -> str:
    """
    Validate Bearer token.
    Production: use msal or python-jose to verify Entra ID JWT.
    Returns caller identity (never log the token itself).
    """
    if not authorization:
        logger.warning("Request received with no Authorization header")
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Bearer token required"
        )

    token = authorization.split(" ", 1)[1]

    # --- PRODUCTION: replace below with Entra ID JWT validation ---
    # from msal import ConfidentialClientApplication
    # Validate signature, expiry, audience, issuer
    # ---------------------------------------------------------------

    # Simulated validation for demo
    if token == "INVALID":
        raise HTTPException(status_code=401, detail="Token validation failed")

    # Return a caller identifier (e.g. service principal or user OID)
    return "demo-caller-oid-abc123"
