"""Stub do `GerenciadorMineracao` (MVP) — responde 501 Not Implemented.

Fixa o contrato HTTP das rotas de mineração desde já. A Fase 6 troca esta classe
por uma implementação real na injeção de dependência; rotas e schemas ficam
intactos.
"""

from ..erros import MineracaoIndisponivelError
from ..schemas.repositorio import JobMineracao
from .base import GerenciadorMineracao


class GerenciadorMineracaoStub(GerenciadorMineracao):
    def iniciar(self, repo: str) -> JobMineracao:
        raise MineracaoIndisponivelError()

    def atualizar(self, repo: str) -> JobMineracao:
        raise MineracaoIndisponivelError()

    def status(self, job_id: str) -> JobMineracao:
        raise MineracaoIndisponivelError()
