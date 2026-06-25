"""
Dependências da API - Injeção de dependência
"""
from typing import Optional, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.infrastructure.auth.jwt_handler import verify_token, TokenData
from app.infrastructure.auth.audit_logger import audit_logger
from app.infrastructure.repositories.supabase_user_repository import SupabaseUserRepository
from app.domain.entities.user import UserRole

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Dependency para obter usuário autenticado do JWT"""
    token = credentials.credentials
    try:
        token_data = verify_token(token)
        return token_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_role(*roles: UserRole):
    """Factory de dependência para controle de acesso por role"""
    async def role_checker(current_user: TokenData = Depends(get_current_user)):
        if current_user.role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acesso negado. Roles necessários: {[r.value for r in roles]}"
            )
        return current_user
    return role_checker


# Dependências pré-configuradas para roles
require_admin = require_role(UserRole.ADMIN)
require_eng_or_admin = require_role(UserRole.ADMIN, UserRole.ENGENHEIRO)
require_n3_or_admin = require_role(UserRole.ADMIN, UserRole.N3)
