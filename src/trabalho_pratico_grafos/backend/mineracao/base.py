"""Interface `GerenciadorMineracao` (costura 3).

As rotas e os schemas de mineração já existem no MVP, mas apontam para um stub
que responde 501. A migração da Fase 6 = trocar o stub por uma implementação real
(`BackgroundTasks` + dict de jobs), sem tocar nas rotas, schemas ou no front.
"""

from abc import ABC, abstractmethod

from ..schemas.repositorio import JobMineracao


class GerenciadorMineracao(ABC):
    @abstractmethod
    def iniciar(self, repo: str) -> JobMineracao:
        """Dispara a mineração de um repositório e devolve o job criado."""

    @abstractmethod
    def atualizar(self, repo: str) -> JobMineracao:
        """Re-minera um repositório já existente (regrava o JSON)."""

    @abstractmethod
    def status(self, job_id: str) -> JobMineracao:
        """Estado atual de um job de mineração."""
