"""Rotas de repositórios, incluindo leitura, exclusão e mineração assíncrona."""

from fastapi import APIRouter, BackgroundTasks, Depends

from ..dependencias import (
    get_analise_servico,
    get_gerenciador_mineracao,
    get_repositorio_servico,
)
from ..mineracao import GerenciadorMineracao
from ..schemas.repositorio import JobMineracao, RepositorioResumo
from ..servicos import AnaliseServico, RepositorioServico

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


@router.delete("/{owner}/{repo}", status_code=204)
def excluir_repositorio(
    owner: str,
    repo: str,
    servico: RepositorioServico = Depends(get_repositorio_servico),
    analise: AnaliseServico = Depends(get_analise_servico),
) -> None:
    """Exclui o cache do repo (idempotente, 204; 409 se houver mineração ativa)."""
    nome = f"{owner}/{repo}"
    servico.remover(nome)  # 409 se estiver minerando
    analise.invalidar(nome)  # limpa o cache de análise em memória


# --- Mineração: disparo assíncrono em background -----------------------------
@router.post("/{owner}/{repo}/minerar", response_model=JobMineracao, status_code=202)
def minerar_repositorio(
    owner: str,
    repo: str,
    tarefas: BackgroundTasks,
    gerenciador: GerenciadorMineracao = Depends(get_gerenciador_mineracao),
) -> JobMineracao:
    """Dispara a mineração de um repo **novo** (exige estado AUSENTE → senão 409)."""
    job = gerenciador.iniciar(f"{owner}/{repo}")  # valida pré-condições (409/503)
    tarefas.add_task(gerenciador.executar_job, job.job_id)
    return job


@router.post("/{owner}/{repo}/atualizar", response_model=JobMineracao, status_code=202)
def atualizar_repositorio(
    owner: str,
    repo: str,
    tarefas: BackgroundTasks,
    gerenciador: GerenciadorMineracao = Depends(get_gerenciador_mineracao),
) -> JobMineracao:
    """Re-minera um repo **existente** (exige DISPONIVEL → senão 409); regrava o JSON."""
    job = gerenciador.atualizar(f"{owner}/{repo}")
    tarefas.add_task(gerenciador.executar_job, job.job_id)
    return job


@router.get("/{owner}/{repo}/minerar/status", response_model=JobMineracao)
def status_mineracao(
    owner: str,
    repo: str,
    job_id: str,
    gerenciador: GerenciadorMineracao = Depends(get_gerenciador_mineracao),
) -> JobMineracao:
    """Status de um job de mineração (404 se o job_id não existir)."""
    return gerenciador.status(job_id)
