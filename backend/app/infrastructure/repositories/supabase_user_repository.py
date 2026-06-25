"""
Implementação do Repositório de Usuários usando Supabase
"""
from typing import List, Optional, Tuple
import httpx
from datetime import datetime, timezone, timedelta

from app.domain.entities.user import UserCreate, UserUpdate, UserInDB, UserRole
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.auth.password_handler import hash_password
from app.config import settings


def agora_local():
    """Retorna datetime atual no timezone de São Paulo (UTC-3)"""
    return datetime.now(timezone(timedelta(hours=-3)))


class SupabaseUserRepository(IUserRepository):
    """Implementação do repositório usando REST API do Supabase"""

    def __init__(self):
        self._url = f"{settings.SUPABASE_URL}/rest/v1"
        self._headers = {
            "apikey": settings.SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self._table_name = "app_users"

    def _request(self, method: str, path: str, json: Optional[dict] = None, params: Optional[dict] = None) -> dict:
        """Executa requisição HTTP para o Supabase"""
        url = f"{self._url}/{path}"
        with httpx.Client(timeout=30.0) as client:
            response = client.request(
                method=method,
                url=url,
                headers=self._headers,
                json=json,
                params=params
            )
            response.raise_for_status()
            if response.text:
                return response.json()
            return None

    def _row_to_dict(self, row) -> dict:
        """Converte linha do banco para dicionário"""
        if row is None:
            return None
        if isinstance(row, dict):
            return row.copy()
        return dict(row)

    def _map_to_user_db(self, data: dict) -> UserInDB:
        """Mapeia dados do banco para UserInDB"""
        role_str = data.get('role', 'n3')
        if isinstance(role_str, str):
            try:
                role = UserRole(role_str)
            except ValueError:
                role = UserRole.N3
        else:
            role = role_str

        return UserInDB(
            id=data["id"],
            email=data["email"],
            nome_completo=data["nome_completo"],
            role=role,
            is_active=data.get("is_active", True),
            password_hash=data.get("password_hash", ""),
            totp_secret=data.get("totp_secret"),
            totp_enabled=data.get("totp_enabled", False),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            senha_padrao=data.get("senha_padrao", True)
        )

    async def create(self, user: UserCreate) -> UserInDB:
        """Cria um novo usuário"""
        agora = agora_local()
        role_value = user.role.value if isinstance(user.role, UserRole) else user.role

        data = {
            "email": user.email,
            "nome_completo": user.nome_completo,
            "password_hash": hash_password(user.password),
            "role": role_value,
            "is_active": True,
            "totp_enabled": False,
            "created_at": agora.isoformat(),
            "updated_at": agora.isoformat()
        }

        result = self._request("POST", self._table_name, json=data)
        if isinstance(result, list) and len(result) > 0:
            return self._map_to_user_db(result[0])
        return self._map_to_user_db(result)

    async def get_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Busca usuário pelo ID"""
        result = self._request("GET", self._table_name, params={"id": f"eq.{user_id}", "limit": 1})
        if result and len(result) > 0:
            return self._map_to_user_db(result[0])
        return None

    async def get_by_email(self, email: str) -> Optional[UserInDB]:
        """Busca usuário pelo email"""
        result = self._request("GET", self._table_name, params={"email": f"eq.{email}", "limit": 1})
        if result and len(result) > 0:
            return self._map_to_user_db(result[0])
        return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[UserInDB], int]:
        """Lista todos os usuários com paginação"""
        # Contar total
        all_data = self._request("GET", self._table_name, params={"select": "id"})
        total = len(all_data) if all_data else 0

        # Buscar com paginação
        result = self._request("GET", self._table_name, params={
            "offset": skip,
            "limit": limit,
            "order": "created_at.desc"
        })

        users = [self._map_to_user_db(row) for row in result] if result else []
        return users, total

    async def update(self, user_id: str, user: UserUpdate) -> Optional[UserInDB]:
        """Atualiza um usuário"""
        update_data = {"updated_at": agora_local().isoformat()}

        update_dict = user.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                if key == "role" and hasattr(value, 'value'):
                    update_data[key] = value.value
                else:
                    update_data[key] = value

        result = self._request("PATCH", self._table_name, json=update_data, params={"id": f"eq.{user_id}"})
        if result and len(result) > 0:
            return self._map_to_user_db(result[0])
        return None

    async def delete(self, user_id: str) -> bool:
        """Desativa um usuário (soft delete)"""
        update_data = {
            "is_active": False,
            "updated_at": agora_local().isoformat()
        }
        result = self._request("PATCH", self._table_name, json=update_data, params={"id": f"eq.{user_id}"})
        return result is not None and len(result) > 0

    async def update_totp(self, user_id: str, secret: Optional[str], enabled: bool) -> bool:
        """Atualiza configurações de TOTP"""
        update_data = {
            "totp_enabled": enabled,
            "updated_at": agora_local().isoformat()
        }
        if secret:
            update_data["totp_secret"] = secret

        result = self._request("PATCH", self._table_name, json=update_data, params={"id": f"eq.{user_id}"})
        return result is not None and len(result) > 0

    async def update_password(self, user_id: str, new_password_hash: str) -> bool:
        """Atualiza a senha do usuário"""
        update_data = {
            "password_hash": new_password_hash,
            "senha_padrao": False,
            "updated_at": agora_local().isoformat()
        }
        result = self._request("PATCH", self._table_name, json=update_data, params={"id": f"eq.{user_id}"})
        return result is not None and len(result) > 0
