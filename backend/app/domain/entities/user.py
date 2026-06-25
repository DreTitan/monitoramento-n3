"""
Entidade User - Domínio
Representa um usuário do sistema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    """Roles do usuário"""
    ADMIN = "admin"
    ENGENHEIRO = "engenheiro"
    N3 = "n3"
    N2 = "n2"


class UserBase(BaseModel):
    """Schema base para User"""
    email: EmailStr
    nome_completo: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.N3


class UserCreate(UserBase):
    """Schema para criação de User"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema para atualização de User"""
    email: Optional[EmailStr] = None
    nome_completo: Optional[str] = Field(None, min_length=2, max_length=255)
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema de resposta para User"""
    id: str
    is_active: bool
    totp_enabled: bool
    senha_padrao: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    """Schema para User no banco"""
    password_hash: str
    totp_secret: Optional[str] = None
