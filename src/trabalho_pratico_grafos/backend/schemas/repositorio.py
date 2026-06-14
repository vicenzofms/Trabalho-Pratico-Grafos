"""Schemas de repositório — inclui o campo `estado` (costura 2 do plano)."""

from enum import Enum

from pydantic import BaseModel


class EstadoRepositorio(str, Enum):
    """Estado de um repositório no backend.

    No MVP só existem `DISPONIVEL` (tem cache) e `AUSENTE` (nunca minerado). A
    Fase 6 acrescenta `MINERANDO`/`ERRO` sem quebrar o contrato — o front já
    ramifica por `estado`, então novos valores só habilitam telas novas.
    """

    DISPONIVEL = "disponivel"
    AUSENTE = "ausente"
    # Fase 6 acrescenta: MINERANDO = "minerando", ERRO = "erro"


class RepositorioResumo(BaseModel):
    nome: str  # "owner/repo"
    estado: EstadoRepositorio
    quantidade_usuarios: int | None = None  # None enquanto AUSENTE
    quantidade_interacoes: int | None = None


class JobMineracao(BaseModel):
    """Usado só na Fase 6, mas definido já no MVP para fixar o contrato HTTP."""

    job_id: str
    repo: str
    estado: str  # "pendente" | "executando" | "concluido" | "erro"
    detalhe: str | None = None
