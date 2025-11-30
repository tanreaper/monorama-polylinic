"""
Authentication Service - Simple username/password auth with JWT tokens
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import hashlib

# Security settings
SECRET_KEY = "monorama-clinic-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

# Simple hash function
def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

  # Hardcoded credentials
USERS = {
    "monoramaclinic_admin": {
        "username": "monoramaclinic_admin",
        "hashed_password": hash_password("monorama2024"),
        "role": "admin"
    }
}
class AuthService:
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return hash_password(plain_password) == hashed_password

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        """
        Authenticate a user with username and password.

        Returns user dict if valid, None otherwise.
        """
        user = USERS.get(username)
        if not user:
            return None
        if not self.verify_password(password, user["hashed_password"]):
            return None
        return user
    

    def create_access_token(self, data: dict) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Dictionary to encode in the token

        Returns:
            JWT token string
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})

        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[dict]:
        """
        Verify and decode a JWT token.

        Returns:
            Decoded token data if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return payload
        except JWTError:
            return None

# Singleton instance
auth_service = AuthService()       
    