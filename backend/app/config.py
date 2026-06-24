"""
Configurações da aplicação usando Pydantic Settings
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


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

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Retorna as configurações em singleton"""
    return Settings()


settings = get_settings()
