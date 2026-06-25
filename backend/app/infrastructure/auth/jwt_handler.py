"""
Handler de JWT para autenticação
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel
from app.config import settings


class TokenData(BaseModel):
    """Dados extraídos do token"""
    user_id: str
    email: str
    role: str
    exp: datetime


class TokenPair(BaseModel):
    """Par de tokens"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


def create_access_token(user_id: str, email: str, role: str) -> str:
    """Cria um token de acesso"""
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": user_id,
        "email": email,
        "role": role,
        "type": "access",
        "exp": expire
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Cria um token de refresh"""
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str, token_type: str = "access") -> TokenData:
    """Verifica e decodifica um token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        if payload.get("type") != token_type:
            raise JWTError("Invalid token type")

        return TokenData(
            user_id=payload.get("sub"),
            email=payload.get("email"),
            role=payload.get("role"),
            exp=datetime.fromtimestamp(payload.get("exp"))
        )
    except JWTError as e:
        raise ValueError(f"Invalid token: {str(e)}")
