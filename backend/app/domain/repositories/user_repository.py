"""
Interface do Repositório de Usuários
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
from app.domain.entities.user import UserCreate, UserUpdate, UserInDB


class IUserRepository(ABC):
    """Interface abstrata para repositório de usuários"""

    @abstractmethod
    async def create(self, user: UserCreate) -> UserInDB:
        """Cria um novo usuário"""
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Busca usuário pelo ID"""
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        """Busca usuário pelo email"""
        pass

    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[UserInDB], int]:
        """Lista todos os usuários com paginação"""
        pass

    @abstractmethod
    async def update(self, user_id: str, user: UserUpdate) -> Optional[UserInDB]:
        """Atualiza um usuário"""
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Deleta um usuário (soft delete - desativa)"""
        pass

    @abstractmethod
    async def update_totp(self, user_id: str, secret: Optional[str], enabled: bool) -> bool:
        """Atualiza configurações de TOTP"""
        pass

    @abstractmethod
    async def update_password(self, user_id: str, new_password_hash: str) -> bool:
        """Atualiza a senha do usuário"""
        pass
