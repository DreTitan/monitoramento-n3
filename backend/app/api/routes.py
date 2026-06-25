"""
Rotas da API - Presentation Layer
Endpoints REST para sub-chamados (PROTEGIDOS)
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Body, Depends, Request

from app.api.deps import get_current_user, require_n3_or_admin, require_eng_or_admin
from app.infrastructure.auth.jwt_handler import TokenData
from app.infrastructure.auth.audit_logger import audit_logger
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
async def criar_subchamado(
    request: dict,
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Cria um novo sub-chamado de calibração."""
    try:
        # Usa o nome do usuário logado (não mais necessário pegar do request)
        criado_por = request.pop("criado_por", None)
        if not criado_por:
            criado_por = current_user.email

        dados = SubChamadoCreate(**request)
        result = await use_cases.criar_subchamado(dados, criado_por)

        # Log de auditoria
        audit_logger.log(
            user_id=current_user.user_id,
            user_email=current_user.email,
            action="SUBCHAMADO_CREATE",
            resource_type="subchamado",
            resource_id=result.id,
            details={"cliente": dados.cliente},
            ip_address=req.client.host if req.client else None
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subchamados", response_model=dict)
async def listar_subchamados(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[StatusSubchamado] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """Lista todos os sub-chamados com paginação."""
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
    data_referencia: Optional[datetime] = Query(None),
    current_user: TokenData = Depends(get_current_user)
):
    """Lista sub-chamados em atraso (SLA 48h úteis)."""
    try:
        return await use_cases.listar_atrasados(data_referencia)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subchamados/{subchamado_id}", response_model=SubChamadoResponse)
async def buscar_subchamado(
    subchamado_id: str,
    current_user: TokenData = Depends(get_current_user)
):
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
    dados: SubChamadoUpdate,
    req: Request,
    current_user: TokenData = Depends(get_current_user)
):
    """Atualiza um sub-chamado existente."""
    try:
        subchamado = await use_cases.atualizar_subchamado(subchamado_id, dados)
        if not subchamado:
            raise HTTPException(status_code=404, detail="Sub-chamado não encontrado")

        # Log de auditoria
        audit_logger.log(
            user_id=current_user.user_id,
            user_email=current_user.email,
            action="SUBCHAMADO_UPDATE",
            resource_type="subchamado",
            resource_id=subchamado_id,
            details=dados.model_dump(exclude_unset=True),
            ip_address=req.client.host if req.client else None
        )

        return subchamado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/subchamados/{subchamado_id}", status_code=204)
async def deletar_subchamado(
    subchamado_id: str,
    req: Request,
    current_user: TokenData = Depends(require_n3_or_admin)
):
    """Deleta um sub-chamado (N3 e Admin apenas)."""
    try:
        deleted = await use_cases.deletar_subchamado(subchamado_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Sub-chamado não encontrado")

        # Log de auditoria
        audit_logger.log(
            user_id=current_user.user_id,
            user_email=current_user.email,
            action="SUBCHAMADO_DELETE",
            resource_type="subchamado",
            resource_id=subchamado_id,
            ip_address=req.client.host if req.client else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/subchamados/{subchamado_id}/analise", response_model=SubChamadoResponse)
async def adicionar_analise(
    subchamado_id: str,
    analise: str = Body(...),
    imagens: Optional[List[str]] = Body(None),
    req: Request = None,
    current_user: TokenData = Depends(require_eng_or_admin)
):
    """Adiciona análise a um sub-chamado (Engenharia e Admin apenas)."""
    try:
        subchamado = await use_cases.adicionar_analise(
            subchamado_id,
            analise,
            imagens or []
        )
        if not subchamado:
            raise HTTPException(status_code=404, detail="Sub-chamado não encontrado")

        # Log de auditoria
        if req:
            audit_logger.log(
                user_id=current_user.user_id,
                user_email=current_user.email,
                action="SUBCHAMADO_ANALISE",
                resource_type="subchamado",
                resource_id=subchamado_id,
                details={"analise_preview": analise[:100]},
                ip_address=req.client.host if req.client else None
            )

        return subchamado
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/relatorio-diario", response_model=dict)
async def gerar_relatorio_diario(
    data: Optional[datetime] = Query(None),
    current_user: TokenData = Depends(get_current_user)
):
    """Gera relatório diário de sub-chamados atrasados."""
    try:
        return await use_cases.gerar_relatorio_diario(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/estatisticas", response_model=dict)
async def obter_estatisticas(
    current_user: TokenData = Depends(get_current_user)
):
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
    file_data: str = Body(...),
    current_user: TokenData = Depends(get_current_user)
):
    """Faz upload de uma evidência para o Supabase Storage."""
    import base64
    import httpx
    import uuid
    from app.config import settings

    try:
        # Decodifica o arquivo Base64
        file_bytes = base64.b64decode(file_data)

        # Gera nome único para o arquivo
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
