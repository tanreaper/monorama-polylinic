from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from services.auth_service import auth_service
from typing import Optional

router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)

security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """
    Login with username and password.

    Returns JWT token for authenticated requests.
    """
    user = auth_service.authenticate_user(
        credentials.username,
        credentials.password
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password"
        )

    # Create access token
    access_token = auth_service.create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user["username"]
    }


@router.get("/verify")
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify if a token is valid.
    """
    token = credentials.credentials
    payload = auth_service.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return {
        "valid": True,
        "username": payload.get("sub"),
        "role": payload.get("role")
    }


# Dependency for protected routes
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dependency to protect routes - requires valid JWT token.

    Usage in other routers:
        @router.post("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            # user is authenticated
    """
    token = credentials.credentials
    payload = auth_service.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return payload
