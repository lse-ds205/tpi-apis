# auth/dependencies.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

from schemas import User
from authentication.database import decode_access_token

# OAuth2 scheme — this tells FastAPI where clients should get the token from
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/token")


# Dependency: Get current user from token

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    user = decode_access_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# Dependency: Ensure current user is active 

async def get_current_active_user(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user
