"""
Use Cases para Gerenciamento de Usuários
Contém toda a lógica de negócio de usuários
"""
from typing import List, Optional, Tuple
from app.domain.entities.user import UserCreate, UserUpdate, UserResponse, UserInDB
from app.domain.repositories.user_repository import IUserRepository


class UserUseCases:
    """Caso de uso para gerenciamento de usuários"""

    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Cria um novo usuário (admin only)"""
        existing = await self._user_repo.get_by_email(user_data.email)
        if existing:
            raise ValueError("Email já cadastrado")

        user = await self._user_repo.create(user_data)
        return UserResponse(
            id=user.id,
            email=user.email,
            nome_completo=user.nome_completo,
            role=user.role,
            is_active=user.is_active,
            totp_enabled=user.totp_enabled,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    async def get_user(self, user_id: str) -> Optional[UserResponse]:
        """Busca usuário pelo ID"""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            return None
        return UserResponse(
            id=user.id,
            email=user.email,
            nome_completo=user.nome_completo,
            role=user.role,
            is_active=user.is_active,
            totp_enabled=user.totp_enabled,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> Tuple[List[UserResponse], int]:
        """Lista todos os usuários com paginação"""
        users, total = await self._user_repo.get_all(skip, limit)
        responses = []
        for u in users:
            responses.append(UserResponse(
                id=u.id,
                email=u.email,
                nome_completo=u.nome_completo,
                role=u.role,
                is_active=u.is_active,
                totp_enabled=u.totp_enabled,
                created_at=u.created_at,
                updated_at=u.updated_at
            ))
        return responses, total

    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[UserResponse]:
        """Atualiza um usuário"""
        user = await self._user_repo.update(user_id, user_data)
        if not user:
            return None
        return UserResponse(
            id=user.id,
            email=user.email,
            nome_completo=user.nome_completo,
            role=user.role,
            is_active=user.is_active,
            totp_enabled=user.totp_enabled,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    async def deactivate_user(self, user_id: str) -> bool:
        """Desativa um usuário (soft delete)"""
        return await self._user_repo.delete(user_id)
