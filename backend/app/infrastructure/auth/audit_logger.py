"""
Audit Logger - Registra todas as ações no sistema
"""
from datetime import datetime
from typing import Optional
import httpx
from app.config import settings


class AuditLogger:
    """Logger de auditoria que salva no Supabase"""

    def __init__(self):
        self.url = f"{settings.SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": settings.SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

    def log(
        self,
        user_id: Optional[str],
        user_email: Optional[str],
        action: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: dict = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Registra uma ação no log de auditoria"""
        try:
            data = {
                "user_id": user_id,
                "user_email": user_email,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {},
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.utcnow().isoformat()
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.request(
                    method="POST",
                    url=f"{self.url}/audit_logs",
                    headers=self.headers,
                    json=data
                )
                response.raise_for_status()
        except Exception as e:
            # Não falha a operação principal se o log falhar
            print(f"Audit log failed: {e}")


# Instância global do audit logger
audit_logger = AuditLogger()
