"""
Rotas de Autenticação
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from pydantic import BaseModel, EmailStr
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.deps import get_current_user
from app.application.use_cases.auth_use_cases import AuthUseCases
from app.infrastructure.repositories.supabase_user_repository import SupabaseUserRepository
from app.infrastructure.auth.jwt_handler import TokenData
from app.infrastructure.auth.audit_logger import audit_logger

router = APIRouter(prefix="/auth", tags=["Autenticação"])

# Rate limiter para login - 10 tentativas por minuto
limiter_auth = Limiter(key_func=get_remote_address, default_limits=["10/minute"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    totp_token: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class Setup2FARequest(BaseModel):
    totp_token: str


class ChangePasswordRequest(BaseModel):
    senha_atual: str
    nova_senha: str


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    req: Request
):
    """Autentica usuário e retorna tokens JWT"""
    user_repo = SupabaseUserRepository()
    use_cases = AuthUseCases(user_repo)

    try:
        token_pair, user = await use_cases.authenticate(
            email=request.email,
            password=request.password,
            totp_token=request.totp_token
        )

        # Log de login
        audit_logger.log(
            user_id=user.id,
            user_email=user.email,
            action="LOGIN",
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent")
        )

        role_value = user.role.value if hasattr(user.role, 'value') else user.role
        senha_padrao = getattr(user, 'senha_padrao', True)

        return TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            user={
                "id": user.id,
                "email": user.email,
                "nome_completo": user.nome_completo,
                "role": role_value,
                "totp_enabled": user.totp_enabled,
                "senha_padrao": senha_padrao
            }
        )
    except ValueError as e:
        audit_logger.log(
            user_id=None,
            user_email=request.email,
            action="LOGIN_FAILED",
            details={"error": str(e)},
            ip_address=req.client.host if req.client else None,
            user_agent=req.headers.get("user-agent")
        )
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout(
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Logout do usuário"""
    audit_logger.log(
        user_id=current_user.user_id,
        user_email=current_user.email,
        action="LOGOUT",
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent")
    )
    return {"message": "Logout realizado com sucesso"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """Renova token de acesso"""
    user_repo = SupabaseUserRepository()
    use_cases = AuthUseCases(user_repo)

    try:
        token_pair, user = await use_cases.refresh_tokens(request.refresh_token)
        role_value = user.role.value if hasattr(user.role, 'value') else user.role
        return TokenResponse(
            access_token=token_pair.access_token,
            refresh_token=token_pair.refresh_token,
            user={
                "id": user.id,
                "email": user.email,
                "role": role_value
            }
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Token de refresh inválido")


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Altera a senha do usuário"""
    user_repo = SupabaseUserRepository()
    use_cases = AuthUseCases(user_repo)

    try:
        success = await use_cases.change_password(
            user_id=current_user.user_id,
            senha_atual=request.senha_atual,
            nova_senha=request.nova_senha
        )
        if success:
            audit_logger.log(
                user_id=current_user.user_id,
                user_email=current_user.email,
                action="PASSWORD_CHANGE",
                ip_address=None
            )
        return {"message": "Senha alterada com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/2fa/setup")
async def setup_2fa(current_user: TokenData = Depends(get_current_user)):
    """Configura 2FA - retorna QR Code"""
    user_repo = SupabaseUserRepository()
    use_cases = AuthUseCases(user_repo)

    try:
        secret, qr_code = await use_cases.setup_2fa(current_user.user_id)
        return {
            "secret": secret,
            "qr_code": qr_code
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/2fa/enable")
async def enable_2fa(
    request: Setup2FARequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Habilita 2FA após verificar token"""
    user_repo = SupabaseUserRepository()
    use_cases = AuthUseCases(user_repo)

    success = await use_cases.enable_2fa(current_user.user_id, request.totp_token)
    if not success:
        raise HTTPException(status_code=400, detail="Código 2FA inválido")

    return {"message": "2FA habilitado com sucesso"}


@router.post("/2fa/disable")
async def disable_2fa(
    password: str = Body(...),
    current_user: TokenData = Depends(get_current_user)
):
    """Desabilita 2FA com verificação de senha"""
    user_repo = SupabaseUserRepository()
    use_cases = AuthUseCases(user_repo)

    try:
        success = await use_cases.disable_2fa(current_user.user_id, password)
        if not success:
            raise HTTPException(status_code=400, detail="Senha incorreta")
        return {"message": "2FA desabilitado com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/me")
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user)
):
    """Retorna informações do usuário logado"""
    user_repo = SupabaseUserRepository()
    from app.application.use_cases.user_use_cases import UserUseCases
    use_cases = UserUseCases(user_repo)

    user = await use_cases.get_user(current_user.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {
        "id": user.id,
        "email": user.email,
        "nome_completo": user.nome_completo,
        "role": user.role.value if hasattr(user.role, 'value') else user.role,
        "totp_enabled": user.totp_enabled,
        "is_active": user.is_active
    }
