"""
Use Cases para Autenticação
Contém toda a lógica de negócio de autenticação
"""
from typing import Optional, Tuple
from app.domain.entities.user import UserInDB, UserRole
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.auth.jwt_handler import (
    create_access_token, create_refresh_token, verify_token, TokenPair
)
from app.infrastructure.auth.password_handler import verify_password, hash_password
from app.infrastructure.auth.totp_handler import (
    generate_totp_secret, get_totp_uri, verify_totp, generate_qr_code_base64
)


class AuthUseCases:
    """Caso de uso para autenticação"""

    def __init__(self, user_repo: IUserRepository):
        self._user_repo = user_repo

    async def authenticate(
        self,
        email: str,
        password: str,
        totp_token: Optional[str] = None
    ) -> Tuple[TokenPair, UserInDB]:
        """Autentica usuário e retorna tokens"""
        user = await self._user_repo.get_by_email(email)

        if not user:
            raise ValueError("Email ou senha incorretos")

        if not user.is_active:
            raise ValueError("Usuário desativado")

        if not verify_password(password, user.password_hash):
            raise ValueError("Email ou senha incorretos")

        # Verificar 2FA se habilitado
        if user.totp_enabled:
            if not totp_token:
                raise ValueError("Código 2FA obrigatório")
            if not verify_totp(user.totp_secret, totp_token):
                raise ValueError("Código 2FA inválido")

        # Gerar tokens
        role_value = user.role.value if isinstance(user.role, UserRole) else user.role
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=role_value
        )
        refresh_token = create_refresh_token(user_id=user.id)

        token_pair = TokenPair(
            access_token=access_token,
            refresh_token=refresh_token
        )

        # Verificar se é senha padrão (retorna flag para o frontend)
        return token_pair, user

    async def refresh_tokens(self, refresh_token: str) -> Tuple[TokenPair, UserInDB]:
        """Renova tokens usando refresh token"""
        token_data = verify_token(refresh_token, token_type="refresh")

        user = await self._user_repo.get_by_id(token_data.user_id)
        if not user or not user.is_active:
            raise ValueError("Usuário não encontrado ou desativado")

        role_value = user.role.value if isinstance(user.role, UserRole) else user.role
        access_token = create_access_token(
            user_id=user.id,
            email=user.email,
            role=role_value
        )
        new_refresh_token = create_refresh_token(user_id=user.id)

        return TokenPair(
            access_token=access_token,
            refresh_token=new_refresh_token
        ), user

    async def setup_2fa(self, user_id: str) -> Tuple[str, str]:
        """Configura 2FA para usuário - retorna (secret, qr_code_base64)"""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")

        secret = generate_totp_secret()
        uri = get_totp_uri(secret, user.email)
        qr_code = generate_qr_code_base64(uri)

        # Armazenar secret temporariamente (ainda não habilitado)
        await self._user_repo.update_totp(user_id, secret, False)

        return secret, f"data:image/png;base64,{qr_code}"

    async def enable_2fa(self, user_id: str, totp_token: str) -> bool:
        """Verifica token e habilita 2FA"""
        user = await self._user_repo.get_by_id(user_id)
        if not user or not user.totp_secret:
            raise ValueError("2FA não foi configurado")

        if not verify_totp(user.totp_secret, totp_token):
            return False

        await self._user_repo.update_totp(user_id, None, True)
        return True

    async def disable_2fa(self, user_id: str, password: str) -> bool:
        """Desabilita 2FA com verificação de senha"""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")

        if not verify_password(password, user.password_hash):
            raise ValueError("Senha incorreta")

        await self._user_repo.update_totp(user_id, None, False)
        return True

    async def change_password(self, user_id: str, senha_atual: str, nova_senha: str) -> bool:
        """Altera a senha do usuário"""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")

        # Verificar senha atual
        if not verify_password(senha_atual, user.password_hash):
            raise ValueError("Senha atual incorreta")

        # Validar nova senha
        if len(nova_senha) < 8:
            raise ValueError("Nova senha deve ter pelo menos 8 caracteres")

        # Atualizar senha
        await self._user_repo.update_password(user_id, hash_password(nova_senha))
        return True
