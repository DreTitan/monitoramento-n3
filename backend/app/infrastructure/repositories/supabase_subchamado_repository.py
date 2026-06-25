"""
Repositório Supabase para SubChamado
Implementação concreta usando httpx (REST API direta)
"""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid
import httpx

from app.domain.entities.subchamado import (
    SubChamadoCreate, SubChamadoUpdate, StatusSubchamado, Prioridade
)
from app.domain.repositories.subchamado_repository import ISubChamadoRepository
from app.config import settings
from app.application.use_cases.subchamado_use_cases import calcular_prazo_sla


def agora_local():
    """Retorna datetime atual no timezone de São Paulo (UTC-3)"""
    return datetime.now(timezone(timedelta(hours=-3)))


class SupabaseSubChamadoRepository(ISubChamadoRepository):
    """Implementação do repositório usando REST API do Supabase"""

    def __init__(self):
        self._url = f"{settings.SUPABASE_URL}/rest/v1"
        self._headers = {
            "apikey": settings.SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        self._table_name = "subchamados"

    def _row_to_dict(self, row) -> dict:
        """Converte linha do banco para dicionário"""
        if row is None:
            return None
        # Se já for um dicionário, usa diretamente
        if isinstance(row, dict):
            data = row.copy()
        else:
            data = dict(row)
        # Converte datas de string para datetime se necessário
        for key in ['data_fabricacao', 'criado_em', 'atualizado_em', 'prazo_sla']:
            if key in data and data[key] and isinstance(data[key], str):
                try:
                    data[key] = datetime.fromisoformat(data[key].replace('Z', '+00:00'))
                except:
                    pass
        return data

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

    async def create(self, subchamado: SubChamadoCreate, criado_por: str) -> dict:
        """Cria um novo sub-chamado"""
        agora = agora_local()
        id_gerado = str(uuid.uuid4())

        # Usa a data fornecida ou a atual
        data_criacao = subchamado.criado_em if subchamado.criado_em else agora
        prazo = calcular_prazo_sla(data_criacao)

        data = {
            "id": id_gerado,
            "cliente": subchamado.cliente,
            "numero_serie": subchamado.numero_serie,
            "hgid": subchamado.hgid,
            "data_fabricacao": subchamado.data_fabricacao.isoformat() if subchamado.data_fabricacao else None,
            "quantidade_exames": subchamado.quantidade_exames,
            "go_premium": subchamado.go_premium,
            "descricao": subchamado.descricao,
            "prioridade": subchamado.prioridade.value if subchamado.prioridade else Prioridade.MEDIA.value,
            "status": StatusSubchamado.ABERTO.value,
            "criado_por": criado_por,
            "criado_em": data_criacao.isoformat(),
            "atualizado_em": agora.isoformat(),
            "prazo_sla": prazo.isoformat(),
            "analise": None,
            "imagens": []
        }

        result = self._request("POST", self._table_name, json=data)
        # Supabase retorna uma lista com return=representation
        if isinstance(result, list) and len(result) > 0:
            return self._row_to_dict(result[0])
        return self._row_to_dict(result)

    async def get_by_id(self, id: str) -> Optional[dict]:
        """Busca um sub-chamado pelo ID"""
        result = self._request("GET", f"{self._table_name}", params={"id": f"eq.{id}", "limit": 1})
        if result and len(result) > 0:
            return self._row_to_dict(result[0])
        return None

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[StatusSubchamado] = None
    ) -> tuple[List[dict], int]:
        """Lista todos os sub-chamados com paginação"""
        params = {
            "offset": skip,
            "limit": limit,
            "order": "criado_em.desc"
        }

        if status:
            params["status"] = f"eq.{status.value}"

        # Buscar todos para contar
        all_data = self._request("GET", self._table_name, params={"select": "id"})
        total = len(all_data) if all_data else 0

        # Buscar com paginação
        result = self._request("GET", self._table_name, params=params)
        items = [self._row_to_dict(row) for row in result] if result else []
        return items, total

    async def update(self, id: str, subchamado: SubChamadoUpdate) -> Optional[dict]:
        """Atualiza um sub-chamado"""
        existing = await self.get_by_id(id)
        if not existing:
            return None

        update_data = {"atualizado_em": agora_local().isoformat()}

        update_dict = subchamado.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                if hasattr(value, 'value'):  # Enum
                    update_data[key] = value.value
                else:
                    update_data[key] = value

        result = self._request("PATCH", f"{self._table_name}", json=update_data, params={"id": f"eq.{id}"})
        if result and len(result) > 0:
            return self._row_to_dict(result[0])
        return None

    async def delete(self, id: str) -> bool:
        """Deleta um sub-chamado"""
        self._request("DELETE", f"{self._table_name}", params={"id": f"eq.{id}"})
        return True

    async def add_analise(
        self,
        id: str,
        analise: str,
        imagens: List[str]
    ) -> Optional[dict]:
        """Adiciona análise a um sub-chamado"""
        update_data = {
            "analise": analise,
            "imagens": imagens,
            "status": StatusSubchamado.EM_ANALISE.value,
            "atualizado_em": agora_local().isoformat()
        }

        result = self._request("PATCH", f"{self._table_name}", json=update_data, params={"id": f"eq.{id}"})
        if result and len(result) > 0:
            return self._row_to_dict(result[0])
        return None

    async def get_atrasados(
        self,
        data_referencia: Optional[datetime] = None
    ) -> List[dict]:
        """Busca sub-chamados em atraso (SLA 48h úteis)"""
        if data_referencia is None:
            data_referencia = agora_local()

        # Busca registros que ainda estão abertos e passaram do prazo
        params = {
            "status": f"in.({StatusSubchamado.ABERTO.value},{StatusSubchamado.EM_ANALISE.value})"
        }

        result = self._request("GET", self._table_name, params=params)

        atrasados = []
        for row in (result or []):
            data = self._row_to_dict(row)
            prazo = data.get('prazo_sla')
            if prazo and prazo < data_referencia:
                atrasados.append(data)

        return atrasados

    async def get_relatorio_diario(self, data: Optional[datetime] = None) -> dict:
        """Gera relatório diário de atrasos"""
        if data is None:
            data = agora_local()

        result = self._request("GET", self._table_name, params={"select": "status"})

        status_counts = {}
        for row in (result or []):
            status = row.get('status', 'desconhecido')
            status_counts[status] = status_counts.get(status, 0) + 1

        atrasados = await self.get_atrasados(data)

        return {
            "data": data.strftime("%Y-%m-%d"),
            "total_abertos": status_counts.get(StatusSubchamado.ABERTO.value, 0),
            "total_em_analise": status_counts.get(StatusSubchamado.EM_ANALISE.value, 0),
            "total_resolvidos": status_counts.get(StatusSubchamado.RESOLVIDO.value, 0),
            "total_atrasados": len(atrasados),
            "subchamados_atrasados": atrasados
        }

    async def count_by_status(self) -> dict:
        """Conta sub-chamados por status"""
        result = self._request("GET", self._table_name, params={"select": "status"})

        status_counts = {}
        for row in (result or []):
            status = row.get('status', 'desconhecido')
            status_counts[status] = status_counts.get(status, 0) + 1

        return status_counts
