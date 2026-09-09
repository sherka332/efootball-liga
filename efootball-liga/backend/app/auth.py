from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, Header
from sqlalchemy.orm import Session
from .config import settings
from .models import User

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGO = "HS256"

def hash_password(password: str):
    return pwd.hash(password)

def verify_password(password: str, hashed: str):
    return pwd.verify(password, hashed)

def make_token(user: User):
    payload = {
        "sub": str(user.id),
        "exp": datetime.utcnow() + timedelta(days=30),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGO)

def current_user(db: Session, authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Authorization required")
    token = authorization[7:]
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGO])
        uid = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(401, "Invalid token")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(401, "User not found")
    if user.is_banned:
        raise HTTPException(403, "User is banned")
    return user

def require_admin(user: User):
    if user.role != "ADMIN":
        raise HTTPException(403, "Admin only")
    return user
