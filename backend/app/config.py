"""
Configurações da aplicação usando Pydantic Settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import secrets


def generate_secret_key() -> str:
    """Gera uma chave secreta segura"""
    return secrets.token_hex(32)


class Settings(BaseSettings):
    """Configurações do aplicativo"""

    # Configurações do banco de dados
    DATABASE_URL: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # Configurações da aplicação
    APP_NAME: str = "Sistema de Monitoramento de Calibração"
    DEBUG: bool = True

    # Configurações JWT
    JWT_SECRET_KEY: str = generate_secret_key()
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Retorna as configurações em singleton"""
    return Settings()


settings = get_settings()
