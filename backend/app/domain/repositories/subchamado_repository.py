"""
Interface do Repository de SubChamado
Define o contrato para persistência de dados
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from app.domain.entities.subchamado import SubChamadoCreate, SubChamadoUpdate, StatusSubchamado


class ISubChamadoRepository(ABC):
    """Interface abstrata para repositório de sub-chamados"""

    @abstractmethod
    async def create(self, subchamado: SubChamadoCreate, criado_por: str) -> dict:
        """Cria um novo sub-chamado"""
        pass

    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[dict]:
        """Busca um sub-chamado pelo ID"""
        pass

    @abstractmethod
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[StatusSubchamado] = None
    ) -> tuple[List[dict], int]:
        """Lista todos os sub-chamados com paginação"""
        pass

    @abstractmethod
    async def update(self, id: str, subchamado: SubChamadoUpdate) -> Optional[dict]:
        """Atualiza um sub-chamado"""
        pass

    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Deleta um sub-chamado"""
        pass

    @abstractmethod
    async def add_analise(self, id: str, analise: str, imagens: List[str]) -> Optional[dict]:
        """Adiciona análise a um sub-chamado"""
        pass

    @abstractmethod
    async def get_atrasados(self, data_referencia: Optional[datetime] = None) -> List[dict]:
        """Busca sub-chamados em atraso (SLA 48h úteis)"""
        pass

    @abstractmethod
    async def get_relatorio_diario(self, data: Optional[datetime] = None) -> dict:
        """Gera relatório diário de atrasos"""
        pass

    @abstractmethod
    async def count_by_status(self) -> dict:
        """Conta sub-chamados por status"""
        pass
