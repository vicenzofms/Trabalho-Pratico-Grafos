"""Stub do `GerenciadorMineracao` (modo cache-only) — responde 501.

Mantido para o modo sem mineração: todas as rotas de disparo respondem
501 Not Implemented. `status_do_repo` devolve None, então o `RepositorioServico`
resolve o estado só pelo cache (DISPONIVEL/AUSENTE), como no MVP.
"""

from ..erros import MineracaoIndisponivelError
from ..schemas.repositorio import JobMineracao
from .base import GerenciadorMineracao


class GerenciadorMineracaoStub(GerenciadorMineracao):
    def iniciar(self, repo: str) -> JobMineracao:
        raise MineracaoIndisponivelError()

    def atualizar(self, repo: str) -> JobMineracao:
        raise MineracaoIndisponivelError()

    def executar_job(self, job_id: str) -> None:  # nunca chamado (iniciar já levanta 501)
        raise MineracaoIndisponivelError()

    def status(self, job_id: str) -> JobMineracao:
        raise MineracaoIndisponivelError()

    def status_do_repo(self, repo: str) -> JobMineracao | None:
        return None

    def remover_job(self, repo: str) -> None:  # sem jobs no modo stub
        return None
