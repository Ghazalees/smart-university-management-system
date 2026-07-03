"""Validates internal service credentials and enforces AI endpoint security."""

import os
import secrets

from fastapi import Header, HTTPException, status


def require_internal_api_key(x_internal_api_key: str = Header(default="")):
    expected = os.getenv("AI_SERVICE_API_KEY", "dev-ai-service-key")
    if not expected or not secrets.compare_digest(x_internal_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal service credentials",
        )
