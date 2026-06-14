"""`GerenciadorMineracaoReal` — mineração pela API (Fase 6).

Mantém os jobs em memória (dict protegido por lock) e roda a mineração em
background (via `BackgroundTasks`, agendado pela rota). `iniciar`/`atualizar`
validam as pré-condições e registram o job; `executar_job` faz o trabalho pesado
e grava o JSON com `salvarNoCache()` — o novo mtime invalida o cache de análise
sozinho (costura 4).

A criação do `Minerador` é injetável (`criar_miner`) para que os testes rodem sem
rede nem token. Em produção, usa o `Minerador` real com `usar_cache=False`
(força mineração nova) seguido de `salvarNoCache()` — o que serve tanto para
`minerar` (repo novo) quanto para `atualizar` (re-minerar).

Limitação conhecida: o `Minerador.salvarNoCache()` grava num caminho fixo
(`src/data`), independente de `DIRETORIO_DADOS`. A mineração real, portanto, só
enxerga o resultado quando a `FonteCache` aponta para `src/data` (o default).
"""

import threading
import uuid
from typing import Callable, Protocol

from ..erros import ConflitoMineracaoError, JobNaoEncontradoError, TokensAusentesError
from ..fontes import FonteDeDados
from ..schemas.repositorio import JobMineracao
from .base import GerenciadorMineracao

ESTADOS_ATIVOS = {"pendente", "executando"}


class _MineradorLike(Protocol):
    def executar(self, sleepTime: float = ..., reprocessar_pendencias: bool = ...) -> None: ...
    def salvarNoCache(self) -> None: ...


def _criar_minerador_real(repo: str, tokens: list[str]) -> _MineradorLike:
    # Import tardio: evita puxar o minerador (e suas deps) quando o backend roda
    # só em modo leitura, e mantém o módulo testável sem rede.
    from trabalho_pratico_grafos.minerador import Minerador

    return Minerador(repo, tokens, usar_cache=False)


class GerenciadorMineracaoReal(GerenciadorMineracao):
    def __init__(
        self,
        fonte: FonteDeDados,
        tokens: list[str],
        criar_miner: Callable[[str, list[str]], _MineradorLike] = _criar_minerador_real,
    ) -> None:
        self._fonte = fonte
        self._tokens = tokens
        self._criar_miner = criar_miner
        self._jobs: dict[str, JobMineracao] = {}
        self._job_por_repo: dict[str, str] = {}
        self._lock = threading.Lock()

    # --- API pública -------------------------------------------------------
    def iniciar(self, repo: str) -> JobMineracao:
        with self._lock:
            self._exigir_tokens()
            if self._fonte.versao(repo) is not None:
                raise ConflitoMineracaoError(f"Repositório '{repo}' já existe; use atualizar.")
            self._exigir_sem_job_ativo(repo)
            return self._registrar(repo)

    def atualizar(self, repo: str) -> JobMineracao:
        with self._lock:
            self._exigir_tokens()
            if self._fonte.versao(repo) is None:
                raise ConflitoMineracaoError(f"Repositório '{repo}' não existe; use minerar.")
            self._exigir_sem_job_ativo(repo)
            return self._registrar(repo)

    def executar_job(self, job_id: str) -> None:
        # roda fora do lock (mineração é demorada); só o update de estado o usa.
        job = self._jobs.get(job_id)
        if job is None:
            return
        try:
            miner = self._criar_miner(job.repo, self._tokens)
            miner.executar(reprocessar_pendencias=True)
            miner.salvarNoCache()
            self._definir_estado(job_id, "concluido", self._resumo(miner))
        except Exception as erro:  # noqa: BLE001 — qualquer falha vira estado de erro do job
            self._definir_estado(job_id, "erro", f"{type(erro).__name__}: {erro}")

    def status(self, job_id: str) -> JobMineracao:
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise JobNaoEncontradoError(job_id)
        return job

    def status_do_repo(self, repo: str) -> JobMineracao | None:
        with self._lock:
            job_id = self._job_por_repo.get(repo)
            return self._jobs.get(job_id) if job_id is not None else None

    # --- Helpers (assumem o lock já adquirido, salvo onde indicado) ---------
    def _exigir_tokens(self) -> None:
        if not self._tokens:
            raise TokensAusentesError()

    def _exigir_sem_job_ativo(self, repo: str) -> None:
        job_id = self._job_por_repo.get(repo)
        if job_id is not None and self._jobs[job_id].estado in ESTADOS_ATIVOS:
            raise ConflitoMineracaoError(f"Repositório '{repo}' já está sendo minerado.")

    def _registrar(self, repo: str) -> JobMineracao:
        job_id = uuid.uuid4().hex
        job = JobMineracao(job_id=job_id, repo=repo, estado="executando")
        self._jobs[job_id] = job
        self._job_por_repo[repo] = job_id
        return job

    def _definir_estado(self, job_id: str, estado: str, detalhe: str | None) -> None:
        with self._lock:
            anterior = self._jobs[job_id]
            self._jobs[job_id] = anterior.model_copy(update={"estado": estado, "detalhe": detalhe})

    @staticmethod
    def _resumo(miner: _MineradorLike) -> str:
        # Melhor esforço: inclui contagens se o minerador as expuser.
        try:
            usuarios = miner.quantidadeUsuarios()  # type: ignore[attr-defined]
            interacoes = miner.quantidadeInteracoes()  # type: ignore[attr-defined]
            return f"mineração concluída: {usuarios} usuários, {interacoes} interações"
        except Exception:  # noqa: BLE001
            return "mineração concluída"
