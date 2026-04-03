"""
Token-based access control implemented as FastAPI dependencies.

Roles:
  viewer  → read-only access
  analyst → read access + filter parameters
  admin   → full CRUD access
"""

import base64
import json
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Literal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

Role = Literal["viewer", "analyst", "admin"]

ROLE_HIERARCHY: dict[Role, int] = {
    "viewer": 1,
    "analyst": 2,
    "admin": 3,
}

def create_access_token(username: str) -> str:
    """
    Mock JWT creation using base64.
    Grants admin role if 'admin' is in username, else analyst if 'analyst', else viewer.
    """
    role = "viewer"
    if "admin" in username.lower():
        role = "admin"
    elif "analyst" in username.lower():
        role = "analyst"
    
    data = {"sub": username, "role": role}
    # Base64 encode it to simulate a token payload
    return base64.b64encode(json.dumps(data).encode()).decode()

def _get_current_role(token: str = Depends(oauth2_scheme)) -> Role:
    """
    Decode the mock token and extract the role.
    """
    try:
        decoded_bytes = base64.b64decode(token)
        payload = json.loads(decoded_bytes.decode())
        role = payload.get("role", "viewer")
        
        if role not in ROLE_HIERARCHY:
            raise ValueError()
        
        return role  # type: ignore[return-value]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(minimum_role: Role):
    """
    Dependency factory: returns a FastAPI dependency that enforces a minimum role level.
    """

    def _check(role: Role = Depends(_get_current_role)) -> None:
        if ROLE_HIERARCHY[role] < ROLE_HIERARCHY[minimum_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: '{minimum_role}', your role: '{role}'.",
            )

    return _check
