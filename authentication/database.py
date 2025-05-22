"""

This file contains a dictionary that simulate the user database. Real data to be entered in the future.

"""

from schemas import UserInDB

from datetime import datetime, timedelta
from typing import Optional

import os
from dotenv import load_dotenv
load_dotenv()

from jose import JWTError, jwt
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


users_db = {
    "tom": {
        "username": "tom",
        "email": "tom@example.com",
        "hashed_password": hash_password("tompassword"),
        "disabled": False,
    },
    "jerry": {
        "username": "jerry",
        "email": "jerry@example.com",
        "hashed_password": hash_password("jerrypassword"),
        "disabled": True,
    },
}


def get_user(username: str) -> UserInDB | None:
    user_dict = users_db.get(username)
    if user_dict:
        return UserInDB(**user_dict)
    return None


SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


# JWT token create and decode

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=30))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[UserInDB]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None

    user = get_user(username)
    return user