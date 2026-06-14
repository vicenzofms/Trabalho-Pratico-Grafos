"""Rotas de análise — relatório completo e sub-recursos (Fase 4/5).

Todas derivam do mesmo `analise_servico.relatorio(repo, tipo)` (cacheado por
`(repo, tipo, mtime)`). O grafo analisado por padrão é o `integrado` (o principal,
conforme a seção 11 do pacote `analise`); um `?tipo=` opcional permite analisar os
demais. Handlers declarados como `def` para rodar no threadpool (análise é
CPU-bound e síncrona).
"""

from fastapi import APIRouter, Depends, Query

from ..erros import MetricaInvalidaError
from ..dependencias import get_analise_servico
from ..schemas.analise import (
    CentralidadesResposta,
    CoesaoResposta,
    ComunidadesResposta,
    ItemRanking,
    PontesResposta,
    RelatorioAnalise,
)
from ..servicos import AnaliseServico

router = APIRouter(prefix="/repositorios", tags=["analise"])


@router.get("/{owner}/{repo}/analise", response_model=RelatorioAnalise)
def relatorio_completo(
    owner: str,
    repo: str,
    tipo: str = Query("integrado"),
    servico: AnaliseServico = Depends(get_analise_servico),
) -> dict:
    """`relatorio_completo()` serializado (índices já convertidos em usernames)."""
    return servico.relatorio(f"{owner}/{repo}", tipo)


@router.get("/{owner}/{repo}/analise/centralidades", response_model=CentralidadesResposta)
def centralidades(
    owner: str,
    repo: str,
    tipo: str = Query("integrado"),
    servico: AnaliseServico = Depends(get_analise_servico),
) -> dict:
    relatorio = servico.relatorio(f"{owner}/{repo}", tipo)
    return {"centralidades": relatorio["centralidades"]}


@router.get("/{owner}/{repo}/analise/comunidades", response_model=ComunidadesResposta)
def comunidades(
    owner: str,
    repo: str,
    tipo: str = Query("integrado"),
    servico: AnaliseServico = Depends(get_analise_servico),
) -> dict:
    relatorio = servico.relatorio(f"{owner}/{repo}", tipo)
    return {
        "comunidades": relatorio["comunidades"],
        "modularidade": relatorio["modularidade"],
    }


@router.get("/{owner}/{repo}/analise/pontes", response_model=PontesResposta)
def pontes(
    owner: str,
    repo: str,
    tipo: str = Query("integrado"),
    servico: AnaliseServico = Depends(get_analise_servico),
) -> dict:
    return servico.relatorio(f"{owner}/{repo}", tipo)["pontes"]


@router.get("/{owner}/{repo}/analise/coesao", response_model=CoesaoResposta)
def coesao(
    owner: str,
    repo: str,
    tipo: str = Query("integrado"),
    servico: AnaliseServico = Depends(get_analise_servico),
) -> dict:
    """Densidade, clustering e assortatividade (parte A; None até existirem)."""
    relatorio = servico.relatorio(f"{owner}/{repo}", tipo)
    return {
        "densidade": relatorio["densidade"],
        "clustering": relatorio["clustering"],
        "assortatividade": relatorio["assortatividade"],
    }


@router.get("/{owner}/{repo}/analise/ranking/{metrica}", response_model=list[ItemRanking])
def ranking(
    owner: str,
    repo: str,
    metrica: str,
    top: int = Query(10, ge=1),
    tipo: str = Query("integrado"),
    servico: AnaliseServico = Depends(get_analise_servico),
) -> list[dict]:
    """Top-N por métrica de centralidade. Métrica inexistente → 404."""
    centralidades = servico.relatorio(f"{owner}/{repo}", tipo)["centralidades"]
    if metrica not in centralidades:
        raise MetricaInvalidaError(metrica, sorted(centralidades))
    return centralidades[metrica][:top]
