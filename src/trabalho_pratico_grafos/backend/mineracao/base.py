"""Interface `GerenciadorMineracao` (costura 3).

As rotas e os schemas de mineração já existem desde o MVP; o que muda na Fase 6 é
a implementação por trás. O fluxo é em duas etapas para casar com `BackgroundTasks`:
`iniciar`/`atualizar` validam as pré-condições e **registram** o job (resposta
imediata 202), e `executar_job` roda a mineração **em background** e atualiza o job.
"""

from abc import ABC, abstractmethod

from ..schemas.repositorio import JobMineracao


class GerenciadorMineracao(ABC):
    @abstractmethod
    def iniciar(self, repo: str) -> JobMineracao:
        """Valida (repo deve estar AUSENTE) e registra um job de mineração novo."""

    @abstractmethod
    def atualizar(self, repo: str) -> JobMineracao:
        """Valida (repo deve estar DISPONIVEL) e registra um job de re-mineração."""

    @abstractmethod
    def executar_job(self, job_id: str) -> None:
        """Roda a mineração do job em background e atualiza seu estado/cache."""

    @abstractmethod
    def status(self, job_id: str) -> JobMineracao:
        """Estado atual de um job pelo seu id (404 se não existir)."""

    @abstractmethod
    def status_do_repo(self, repo: str) -> JobMineracao | None:
        """Último job conhecido de um repo (ou None) — usado para resolver o estado."""
