"""
Entidade SubChamado - Domínio
Representa um sub-chamado de calibração
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class StatusSubchamado(str, Enum):
    """Status do sub-chamado"""
    ABERTO = "aberto"
    EM_ANALISE = "em_analise"
    AGUARDANDO_INFORMACOES = "aguardando_informacoes"
    RESOLVIDO = "resolvido"
    CANCELADO = "cancelado"


class Prioridade(str, Enum):
    """Prioridade do sub-chamado"""
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class SubChamadoBase(BaseModel):
    """Schema base para SubChamado"""
    cliente: str = Field(..., min_length=1, max_length=255, description="Nome do cliente")
    numero_serie: str = Field(..., min_length=1, max_length=100, description="Número de série do equipamento")
    hgid: str = Field(..., min_length=1, max_length=50, description="ID HealthGo do equipamento")
    data_fabricacao: Optional[datetime] = Field(None, description="Data de fabricação do equipamento")
    quantidade_exames: Optional[int] = Field(None, ge=0, description="Quantidade de exames realizados")
    go_premium: bool = Field(False, description="Se o cliente tem Go Premium")
    descricao: str = Field(..., min_length=1, description="Descrição do problema")
    prioridade: Prioridade = Field(Prioridade.MEDIA, description="Prioridade do chamado")


class SubChamadoCreate(SubChamadoBase):
    """Schema para criação de SubChamado"""
    pass


class SubChamadoUpdate(BaseModel):
    """Schema para atualização de SubChamado"""
    cliente: Optional[str] = Field(None, min_length=1, max_length=255)
    numero_serie: Optional[str] = Field(None, min_length=1, max_length=100)
    hgid: Optional[str] = Field(None, min_length=1, max_length=50)
    data_fabricacao: Optional[datetime] = None
    quantidade_exames: Optional[int] = Field(None, ge=0)
    go_premium: Optional[bool] = None
    descricao: Optional[str] = Field(None, min_length=1)
    prioridade: Optional[Prioridade] = None
    status: Optional[StatusSubchamado] = None
    analise: Optional[str] = None


class AnaliseCreate(BaseModel):
    """Schema para adicionar análise"""
    analise: str = Field(..., min_length=1, description="Texto da análise da engenharia")
    imagens: Optional[List[str]] = Field(None, description="URLs das imagens anexadas")


class SubChamadoResponse(SubChamadoBase):
    """Schema de resposta para SubChamado"""
    id: str = Field(..., description="ID único do sub-chamado")
    status: StatusSubchamado = Field(StatusSubchamado.ABERTO, description="Status atual")
    analise: Optional[str] = Field(None, description="Análise da engenharia")
    imagens: List[str] = Field(default_factory=list, description="URLs das imagens")
    criado_por: str = Field(..., description="Nome de quem criou")
    criado_em: datetime = Field(..., description="Data/hora de criação")
    atualizado_em: datetime = Field(..., description="Data/hora da última atualização")
    prazo_sla: datetime = Field(..., description="Prazo do SLA (48h úteis)")

    class Config:
        from_attributes = True


class SubChamadoListResponse(BaseModel):
    """Schema para listagem de sub-chamados"""
    items: List[SubChamadoResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class RelatorioDiario(BaseModel):
    """Schema para relatório diário de atrasos"""
    data: str
    total_abertos: int
    total_em_atraso: int
    subchamados_atrasados: List[SubChamadoResponse]
