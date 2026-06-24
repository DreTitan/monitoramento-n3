"""
Rotas da API - Presentation Layer
Endpoints REST para sub-chamados
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Body

from app.domain.entities.subchamado import (
    SubChamadoCreate, SubChamadoUpdate, SubChamadoResponse,
    StatusSubchamado, Prioridade, AnaliseCreate
)
from app.infrastructure.repositories.supabase_subchamado_repository import SupabaseSubChamadoRepository
from app.application.use_cases.subchamado_use_cases import SubChamadoUseCases

router = APIRouter()

# Inicializar use cases com repositório
repository = SupabaseSubChamadoRepository()
use_cases = SubChamadoUseCases(repository)


@router.post("/subchamados", response_model=SubChamadoResponse, status_code=201)
async def criar_subchamado(request: dict):
    """
    Cria um novo sub-chamado de calibração.

    - **cliente**: Nome do cliente
    - **numero_serie**: Número de série do equipamento
    - **hgid**: ID HealthGo do equipamento
    - **data_fabricacao**: Data de fabricação (opcional)
    - **quantidade_exames**: Quantidade de exames realizados (opcional)
    - **go_premium**: Se o cliente tem Go Premium
    - **descricao**: Descrição do problema
    - **prioridade**: Prioridade (baixa, media, alta, critica)
    - **criado_por**: Nome de quem está criando
    """
    try:
        criado_por = request.pop("criado_por", None)
        if not criado_por:
            raise HTTPException(status_code=400, detail="criado_por é obrigatório")

        dados = SubChamadoCreate(**request)
        return await use_cases.criar_subchamado(dados, criado_por)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subchamados", response_model=dict)
async def listar_subchamados(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[StatusSubchamado] = None
):
    """
    Lista todos os sub-chamados com paginação.

    - **skip**: Número de registros para pular
    - **limit**: Limite de registros por página
    - **status**: Filtrar por status (opcional)
    """
    try:
        items, total = await use_cases.listar_subchamados(skip, limit, status)
        return {
            "items": [s.model_dump() for s in items],
            "total": total,
            "page": skip // limit + 1,
            "page_size": limit,
            "total_pages": (total + limit - 1) // limit
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subchamados/atrasados", response_model=List[SubChamadoResponse])
async def listar_subchamados_atrasados(
    data_referencia: Optional[datetime] = Query(None)
):
    """
    Lista sub-chamados em atraso (SLA 48h úteis).

    - **data_referencia**: Data de referência para verificar atrasos (opcional, padrão: agora)
    """
    try:
        return await use_cases.listar_atrasados(data_referencia)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subchamados/{subchamado_id}", response_model=SubChamadoResponse)
async def buscar_subchamado(subchamado_id: str):
    """Busca um sub-chamado pelo ID."""
    try:
        subchamado = await use_cases.buscar_subchamado(subchamado_id)
        if not subchamado:
            raise HTTPException(status_code=404, detail="Sub-chamado não encontrado")
        return subchamado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/subchamados/{subchamado_id}", response_model=SubChamadoResponse)
async def atualizar_subchamado(
    subchamado_id: str,
    dados: SubChamadoUpdate
):
    """
    Atualiza um sub-chamado existente.

    Todos os campos são opcionais - apenas os fornecidos serão atualizados.
    """
    try:
        subchamado = await use_cases.atualizar_subchamado(subchamado_id, dados)
        if not subchamado:
            raise HTTPException(status_code=404, detail="Sub-chamado não encontrado")
        return subchamado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/subchamados/{subchamado_id}", status_code=204)
async def deletar_subchamado(subchamado_id: str):
    """Deleta um sub-chamado."""
    try:
        deleted = await use_cases.deletar_subchamado(subchamado_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Sub-chamado não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subchamados/{subchamado_id}/analise", response_model=SubChamadoResponse)
async def adicionar_analise(
    subchamado_id: str,
    analise: str = Body(...),
    imagens: Optional[List[str]] = Body(None)
):
    """
    Adiciona análise a um sub-chamado (engenharia).

    - **analise**: Texto da análise da engenharia
    - **imagens**: URLs das imagens anexadas (opcional)
    """
    try:
        subchamado = await use_cases.adicionar_analise(
            subchamado_id,
            analise,
            imagens or []
        )
        if not subchamado:
            raise HTTPException(status_code=404, detail="Sub-chamado não encontrado")
        return subchamado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/relatorio-diario", response_model=dict)
async def gerar_relatorio_diario(
    data: Optional[datetime] = Query(None)
):
    """
    Gera relatório diário de sub-chamados atrasados.

    - **data**: Data do relatório (opcional, padrão: hoje)
    """
    try:
        return await use_cases.gerar_relatorio_diario(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/estatisticas", response_model=dict)
async def obter_estatisticas():
    """Obtém estatísticas dos sub-chamados por status."""
    try:
        return await use_cases.obter_estatisticas()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upload")
async def upload_evidencia(
    subchamado_id: str = Body(...),
    filename: str = Body(...),
    content_type: str = Body(...),
    file_data: str = Body(...)  # Base64 encoded
):
    """
    Faz upload de uma evidência para o Supabase Storage.

    - **subchamado_id**: ID do sub-chamado
    - **filename**: Nome do arquivo
    - **content_type**: Tipo MIME do arquivo
    - **file_data**: Conteúdo do arquivo em Base64
    """
    import base64
    import httpx
    from app.config import settings

    try:
        # Decodifica o arquivo Base64
        file_bytes = base64.b64decode(file_data)

        # Gera nome único para o arquivo
        import uuid
        ext = filename.split('.')[-1] if '.' in filename else ''
        unique_name = f"{uuid.uuid4()}.{ext}"
        path = f"{subchamado_id}/{unique_name}"

        # Upload para Supabase Storage
        url = f"{settings.SUPABASE_URL}/storage/v1/object/evidencias/{path}"

        headers = {
            "apikey": settings.SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
            "Content-Type": content_type,
            "x-upsert": "true"
        }

        with httpx.Client(timeout=60.0) as client:
            response = client.request(
                method="POST",
                url=url,
                headers=headers,
                content=file_bytes
            )
            response.raise_for_status()

        # Retorna URL pública
        public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/evidencias/{path}"
        return {"url": public_url, "path": path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
