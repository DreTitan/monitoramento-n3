"""
Cliente Supabase
Conexão com o banco de dados
"""
from supabase import create_client, Client
from app.config import settings


def get_supabase_client() -> Client:
    """Retorna cliente Supabase configurado"""
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar configurados")

    client = create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_KEY
    )
    return client


def get_service_client() -> Client:
    """Retorna cliente Supabase com chave de serviço (para operações admin)"""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_URL e SUPABASE_SERVICE_KEY devem estar configurados")

    client = create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_SERVICE_KEY
    )
    return client
