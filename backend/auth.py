"""
Authentication utilities and JWT handling
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from . import models
from .database import get_db

# Security configuration
SECRET_KEY = "your-secret-key-change-in-production"  # TODO: Move to environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8

# Bearer token scheme
security = HTTPBearer()

# In-memory token blacklist — tokens added here are immediately rejected
_token_blacklist: set = set()


def blacklist_token(token: str) -> None:
    """Add a token to the blacklist (call on logout)"""
    _token_blacklist.add(token)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_token_payload(token: str) -> Optional[dict]:
    """Decode a JWT token and return its payload"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[str]:
    """Decode a class JWT token and return the class_name"""
    payload = decode_token_payload(token)
    if not payload:
        return None

    if payload.get("role") not in (None, "class"):
        return None

    class_name: str = payload.get("sub")
    return class_name


def authenticate_class(db: Session, class_name: str, password: str) -> Optional[models.Class]:
    """Authenticate a class/faculty"""
    class_obj = db.query(models.Class).filter(models.Class.class_name == class_name).first()
    
    if not class_obj:
        return None
    
    if not verify_password(password, class_obj.password_hash):
        return None
    
    return class_obj


def authenticate_admin(db: Session, username: str, password: str) -> Optional[models.AdminUser]:
    """Authenticate an admin user"""
    admin = db.query(models.AdminUser).filter(models.AdminUser.username == username).first()

    if not admin:
        return None

    if not verify_password(password, admin.password_hash):
        return None

    return admin


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.AdminUser:
    """Dependency to get the current authenticated admin"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    if token in _token_blacklist:
        raise credentials_exception

    payload = decode_token_payload(token)
    if not payload or payload.get("role") != "admin":
        raise credentials_exception

    username = payload.get("sub")
    if not username:
        raise credentials_exception

    admin = db.query(models.AdminUser).filter(models.AdminUser.username == username).first()
    if admin is None:
        raise credentials_exception

    return admin


async def get_current_class(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.Class:
    """Dependency to get the current authenticated class"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials

    # Reject blacklisted tokens immediately
    if token in _token_blacklist:
        raise credentials_exception

    class_name = decode_access_token(token)

    if class_name is None:
        raise credentials_exception

    class_obj = db.query(models.Class).filter(models.Class.class_name == class_name).first()

    if class_obj is None:
        raise credentials_exception

    return class_obj
