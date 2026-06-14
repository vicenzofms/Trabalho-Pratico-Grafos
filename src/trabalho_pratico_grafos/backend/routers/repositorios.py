"""Rotas de repositórios — leitura (MVP) + mineração (stub 501 no MVP).

As três rotas de mineração já existem aqui com schema definido, mas respondem
501 via o `GerenciadorMineracao` stub. A Fase 6 só troca o stub pela
implementação real; estas rotas e os schemas ficam intactos.
"""

from fastapi import APIRouter, Depends

from ..dependencias import get_gerenciador_mineracao, get_repositorio_servico
from ..mineracao import GerenciadorMineracao
from ..schemas.repositorio import JobMineracao, RepositorioResumo
from ..servicos import RepositorioServico

router = APIRouter(prefix="/repositorios", tags=["repositorios"])


@router.get("", response_model=list[RepositorioResumo])
def listar_repositorios(
    servico: RepositorioServico = Depends(get_repositorio_servico),
) -> list[RepositorioResumo]:
    """Lista os repositórios com `estado` (no MVP, todos os do cache em src/data)."""
    return servico.listar()


@router.get("/{owner}/{repo}", response_model=RepositorioResumo)
def obter_repositorio(
    owner: str,
    repo: str,
    servico: RepositorioServico = Depends(get_repositorio_servico),
) -> RepositorioResumo:
    """Resumo + `estado`. Sempre responde 200 (estado AUSENTE se não houver cache)."""
    return servico.obter(f"{owner}/{repo}")


# --- Mineração (Fase 6) — schemas fixos, stub respondendo 501 no MVP ---------
@router.post("/{owner}/{repo}/minerar", response_model=JobMineracao)
def minerar_repositorio(
    owner: str,
    repo: str,
    gerenciador: GerenciadorMineracao = Depends(get_gerenciador_mineracao),
) -> JobMineracao:
    """Dispara a mineração de um repo novo (501 no MVP)."""
    return gerenciador.iniciar(f"{owner}/{repo}")


@router.post("/{owner}/{repo}/atualizar", response_model=JobMineracao)
def atualizar_repositorio(
    owner: str,
    repo: str,
    gerenciador: GerenciadorMineracao = Depends(get_gerenciador_mineracao),
) -> JobMineracao:
    """Re-minera um repo existente, invalidando os caches (501 no MVP)."""
    return gerenciador.atualizar(f"{owner}/{repo}")


@router.get("/{owner}/{repo}/minerar/status", response_model=JobMineracao)
def status_mineracao(
    owner: str,
    repo: str,
    job_id: str,
    gerenciador: GerenciadorMineracao = Depends(get_gerenciador_mineracao),
) -> JobMineracao:
    """Status de um job de mineração (501 no MVP)."""
    return gerenciador.status(job_id)
