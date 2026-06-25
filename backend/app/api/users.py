"""
Rotas de Gerenciamento de Usuários (Admin only)
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from app.api.deps import get_current_user, require_admin
from app.application.use_cases.user_use_cases import UserUseCases
from app.infrastructure.repositories.supabase_user_repository import SupabaseUserRepository
from app.infrastructure.auth.jwt_handler import TokenData
from app.infrastructure.auth.audit_logger import audit_logger
from app.domain.entities.user import UserCreate, UserUpdate, UserRole

router = APIRouter(prefix="/users", tags=["Usuários"])


@router.get("")
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: TokenData = Depends(require_admin)
):
    """Lista todos os usuários (admin only)"""
    user_repo = SupabaseUserRepository()
    use_cases = UserUseCases(user_repo)
    users, total = await use_cases.get_all_users(skip, limit)
    return {
        "items": [u.model_dump() for u in users],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("")
async def create_user(
    user_data: UserCreate,
    req: Request,
    current_user: TokenData = Depends(require_admin)
):
    """Cria um novo usuário (admin only)"""
    user_repo = SupabaseUserRepository()
    use_cases = UserUseCases(user_repo)

    try:
        user = await use_cases.create_user(user_data)

        audit_logger.log(
            user_id=current_user.user_id,
            user_email=current_user.email,
            action="USER_CREATE",
            resource_type="user",
            resource_id=user.id,
            details={"created_email": user_data.email, "role": user_data.role.value},
            ip_address=req.client.host if req.client else None
        )

        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: TokenData = Depends(require_admin)
):
    """Busca usuário pelo ID (admin only)"""
    user_repo = SupabaseUserRepository()
    use_cases = UserUseCases(user_repo)
    user = await use_cases.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return user


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    req: Request,
    current_user: TokenData = Depends(require_admin)
):
    """Atualiza um usuário (admin only)"""
    user_repo = SupabaseUserRepository()
    use_cases = UserUseCases(user_repo)
    user = await use_cases.update_user(user_id, user_data)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    audit_logger.log(
        user_id=current_user.user_id,
        user_email=current_user.email,
        action="USER_UPDATE",
        resource_type="user",
        resource_id=user_id,
        details=user_data.model_dump(exclude_unset=True),
        ip_address=req.client.host if req.client else None
    )

    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    req: Request,
    current_user: TokenData = Depends(require_admin)
):
    """Desativa um usuário (admin only)"""
    user_repo = SupabaseUserRepository()
    use_cases = UserUseCases(user_repo)

    success = await use_cases.deactivate_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    audit_logger.log(
        user_id=current_user.user_id,
        user_email=current_user.email,
        action="USER_DEACTIVATE",
        resource_type="user",
        resource_id=user_id,
        ip_address=req.client.host if req.client else None
    )

    return {"message": "Usuário desativado com sucesso"}
