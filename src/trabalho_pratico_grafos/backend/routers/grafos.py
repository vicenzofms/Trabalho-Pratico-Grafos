"""Rotas de grafos — resumo dos 4 grafos, detalhe e download GEPHI (Fase 3/5).

Não há rota de visualização (nós + arestas): o front não renderiza o grafo; a
visualização é feita inteiramente no GEPHI, a partir do CSV exportado aqui.
"""

import shutil
import tempfile

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from trabalho_pratico_grafos.gephi.gephi import para_gephi

from ..dependencias import get_grafo_servico
from ..schemas.grafo import GrafoResumo
from ..servicos import GrafoServico

router = APIRouter(prefix="/repositorios", tags=["grafos"])


@router.get("/{owner}/{repo}/grafos", response_model=list[GrafoResumo])
def resumir_grafos(
    owner: str,
    repo: str,
    servico: GrafoServico = Depends(get_grafo_servico),
) -> list[GrafoResumo]:
    """Resumo dos 4 grafos (vértices, arestas, densidade)."""
    return servico.resumir_todos(f"{owner}/{repo}")


@router.get("/{owner}/{repo}/grafos/{tipo}", response_model=GrafoResumo)
def detalhar_grafo(
    owner: str,
    repo: str,
    tipo: str,
    servico: GrafoServico = Depends(get_grafo_servico),
) -> GrafoResumo:
    """Detalhe de um grafo (tipo inválido → 422)."""
    return servico.resumir(f"{owner}/{repo}", tipo)


@router.get("/{owner}/{repo}/grafos/{tipo}/gephi")
def baixar_gephi(
    owner: str,
    repo: str,
    tipo: str,
    servico: GrafoServico = Depends(get_grafo_servico),
) -> FileResponse:
    """Baixa o CSV de arestas no formato GEPHI."""
    grafo = servico.construir(f"{owner}/{repo}", tipo)
    nome = f"{owner}_{repo}_{tipo}"
    # Gera num diretório temporário e o remove depois que a resposta é enviada,
    # para não acumular arquivos em data/gephi a cada download.
    pasta = tempfile.mkdtemp(prefix="gephi_")
    caminho = para_gephi(grafo, nome, pasta)
    return FileResponse(
        caminho,
        media_type="text/csv",
        filename=f"{nome}.csv",
        background=BackgroundTask(shutil.rmtree, pasta, ignore_errors=True),
    )
