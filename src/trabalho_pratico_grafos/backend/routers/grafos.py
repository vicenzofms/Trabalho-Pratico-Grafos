"""Rotas de grafos — resumo dos 4 grafos, detalhe, visualização e download GEPHI.

A rota `.../visualizacao` devolve a topologia (nós + arestas dirigidas) em JSON para
o front renderizar o grafo com vis.js. O CSV do GEPHI continua disponível para a
análise externa no próprio GEPHI.
"""

import shutil
import tempfile

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from trabalho_pratico_grafos.gephi.gephi import para_gephi

from ..dependencias import get_grafo_servico
from ..schemas.grafo import GrafoResumo, GrafoVisualizacao
from ..servicos import GrafoServico

router = APIRouter(prefix="/repositorios", tags=["grafos"])


@router.get("/{owner}/{repo}/grafos", response_model=list[GrafoResumo])
def resumir_grafos(
    owner: str,
    repo: str,
    representacao: str = Query("matriz"),
    servico: GrafoServico = Depends(get_grafo_servico),
) -> list[GrafoResumo]:
    """Resumo dos 4 grafos (vértices, arestas, densidade)."""
    return servico.resumir_todos(f"{owner}/{repo}", representacao)


@router.get("/{owner}/{repo}/grafos/{tipo}", response_model=GrafoResumo)
def detalhar_grafo(
    owner: str,
    repo: str,
    tipo: str,
    representacao: str = Query("matriz"),
    servico: GrafoServico = Depends(get_grafo_servico),
) -> GrafoResumo:
    """Detalhe de um grafo (tipo inválido → 422)."""
    return servico.resumir(f"{owner}/{repo}", tipo, representacao)


@router.get("/{owner}/{repo}/grafos/{tipo}/visualizacao", response_model=GrafoVisualizacao)
def visualizar_grafo(
    owner: str,
    repo: str,
    tipo: str,
    representacao: str = Query("matriz"),
    servico: GrafoServico = Depends(get_grafo_servico),
) -> GrafoVisualizacao:
    """Topologia (nós + arestas dirigidas) para o front renderizar com vis.js."""
    return servico.visualizar(f"{owner}/{repo}", tipo, representacao)


@router.get("/{owner}/{repo}/grafos/{tipo}/gephi")
def baixar_gephi(
    owner: str,
    repo: str,
    tipo: str,
    representacao: str = Query("matriz"),
    servico: GrafoServico = Depends(get_grafo_servico),
) -> FileResponse:
    """Baixa o CSV de arestas no formato GEPHI."""
    grafo = servico.construir(f"{owner}/{repo}", tipo, representacao)
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
