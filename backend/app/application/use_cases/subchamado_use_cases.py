"""
Use Cases para SubChamado
Contém toda a lógica de negócio da aplicação
"""
from datetime import datetime, timedelta
from typing import List, Optional

from app.domain.entities.subchamado import (
    SubChamadoCreate, SubChamadoUpdate, SubChamadoResponse,
    StatusSubchamado, Prioridade
)
from app.domain.repositories.subchamado_repository import ISubChamadoRepository


def calcular_proximo_dia_util(data: datetime) -> datetime:
    """Calcula o próximo dia útil (exclui finais de semana)"""
    while data.weekday() >= 5:  # 5=Sábado, 6=Domingo
        data += timedelta(days=1)
    return data


def calcular_prazo_sla(data_criacao: datetime, horas_uteis: int = 48) -> datetime:
    """
    Calcula o prazo do SLA (48h úteis)
    Cada dia útil conta como 24h. Fins de semana são ignorados.
    Ex: Qua 11:51 → Sex 11:51 = 48h úteis
    """
    prazo = data_criacao
    horas_acumuladas = 0

    while horas_acumuladas < horas_uteis:
        dia_semana = prazo.weekday()

        # Se é fim de semana, avança para segunda
        if dia_semana >= 5:
            prazo = calcular_proximo_dia_util(prazo)
            prazo = prazo.replace(hour=data_criacao.hour, minute=data_criacao.minute, second=0, microsecond=0)
            continue

        # É dia útil: conta 24h ou o que falta
        horas_restantes = horas_uteis - horas_acumuladas
        horas_hoje = min(24, horas_restantes)
        horas_acumuladas += horas_hoje
        prazo += timedelta(hours=horas_hoje)

    return prazo


class SubChamadoUseCases:
    """Caso de uso para gerenciamento de sub-chamados"""

    def __init__(self, repository: ISubChamadoRepository):
        self._repository = repository

    async def criar_subchamado(
        self,
        dados: SubChamadoCreate,
        criado_por: str
    ) -> SubChamadoResponse:
        """Cria um novo sub-chamado"""
        subchamado = await self._repository.create(dados, criado_por)
        return SubChamadoResponse(**subchamado)

    async def buscar_subchamado(self, id: str) -> Optional[SubChamadoResponse]:
        """Busca um sub-chamado pelo ID"""
        subchamado = await self._repository.get_by_id(id)
        if subchamado:
            return SubChamadoResponse(**subchamado)
        return None

    async def listar_subchamados(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[StatusSubchamado] = None
    ) -> tuple[List[SubChamadoResponse], int]:
        """Lista sub-chamados com paginação"""
        subchamados, total = await self._repository.get_all(skip, limit, status)
        return (
            [SubChamadoResponse(**s) for s in subchamados],
            total
        )

    async def atualizar_subchamado(
        self,
        id: str,
        dados: SubChamadoUpdate
    ) -> Optional[SubChamadoResponse]:
        """Atualiza um sub-chamado"""
        subchamado = await self._repository.update(id, dados)
        if subchamado:
            return SubChamadoResponse(**subchamado)
        return None

    async def deletar_subchamado(self, id: str) -> bool:
        """Deleta um sub-chamado"""
        return await self._repository.delete(id)

    async def adicionar_analise(
        self,
        id: str,
        analise: str,
        imagens: List[str]
    ) -> Optional[SubChamadoResponse]:
        """Adiciona análise a um sub-chamado"""
        subchamado = await self._repository.add_analise(id, analise, imagens)
        if subchamado:
            return SubChamadoResponse(**subchamado)
        return None

    async def listar_atrasados(
        self,
        data_referencia: Optional[datetime] = None
    ) -> List[SubChamadoResponse]:
        """Lista sub-chamados em atraso"""
        subchamados = await self._repository.get_atrasados(data_referencia)
        return [SubChamadoResponse(**s) for s in subchamados]

    async def gerar_relatorio_diario(
        self,
        data: Optional[datetime] = None
    ) -> dict:
        """Gera relatório diário de atrasos"""
        return await self._repository.get_relatorio_diario(data)

    async def obter_estatisticas(self) -> dict:
        """Obtém estatísticas dos sub-chamados"""
        return await self._repository.count_by_status()
