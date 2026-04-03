"""
Authentication routes for generating tokens.
"""

from fastapi import APIRouter
from schemas.auth import LoginRequest, TokenResponse
from schemas.transaction import StandardResponse
from services.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=StandardResponse[TokenResponse], summary="Obtain access token")
def login(payload: LoginRequest):
    """
    Mock login mechanism.
    If username contains 'admin', grants admin role.
    If username contains 'analyst', grants analyst role.
    Otherwise, grants viewer role.
    """
    token = create_access_token(payload.username)
    data = TokenResponse(access_token=token, token_type="bearer")
    return StandardResponse(data=data, message="Login successful.")
