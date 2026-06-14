"""Gerência de jobs de mineração pela API do GitHub.

O fluxo é em duas etapas para casar com `BackgroundTasks`: `iniciar`/`atualizar`
validam as pré-condições e registram o job (resposta imediata 202), enquanto
`executar_job` roda a mineração em background e atualiza o estado do job.
"""

import threading
import uuid
from typing import Callable, Protocol

from ..erros import ConflitoMineracaoError, JobNaoEncontradoError, TokensAusentesError
from ..fontes import FonteDeDados
from ..schemas.repositorio import JobMineracao

ESTADOS_ATIVOS = {"pendente", "executando"}


class _MineradorLike(Protocol):
    def executar(self, sleepTime: float = ..., reprocessar_pendencias: bool = ...) -> None: ...
    def salvarNoCache(self) -> None: ...


def _criar_minerador(repo: str, tokens: list[str]) -> _MineradorLike:
    # Import tardio: evita puxar o minerador quando o backend roda só em modo leitura
    # e mantém o módulo testável sem rede.
    from trabalho_pratico_grafos.minerador import Minerador

    return Minerador(repo, tokens, usar_cache=False)


class GerenciadorMineracao:
    def __init__(
        self,
        fonte: FonteDeDados,
        tokens: list[str],
        criar_miner: Callable[[str, list[str]], _MineradorLike] = _criar_minerador,
    ) -> None:
        self._fonte = fonte
        self._tokens = tokens
        self._criar_miner = criar_miner
        self._jobs: dict[str, JobMineracao] = {}
        self._job_por_repo: dict[str, str] = {}
        self._lock = threading.Lock()

    def iniciar(self, repo: str) -> JobMineracao:
        """Valida (repo deve estar AUSENTE) e registra um job de mineração novo."""
        with self._lock:
            self._exigir_tokens()
            if self._fonte.versao(repo) is not None:
                raise ConflitoMineracaoError(f"Repositório '{repo}' já existe; use atualizar.")
            self._exigir_nenhuma_mineracao_global()
            return self._registrar(repo)

    def atualizar(self, repo: str) -> JobMineracao:
        """Valida (repo deve estar DISPONIVEL) e registra um job de re-mineração."""
        with self._lock:
            self._exigir_tokens()
            if self._fonte.versao(repo) is None:
                raise ConflitoMineracaoError(f"Repositório '{repo}' não existe; use minerar.")
            self._exigir_nenhuma_mineracao_global()
            return self._registrar(repo)

    def executar_job(self, job_id: str) -> None:
        """Roda a mineração do job em background e atualiza seu estado/cache."""
        job = self._jobs.get(job_id)
        if job is None:
            return
        try:
            miner = self._criar_miner(job.repo, self._tokens)
            miner.executar(reprocessar_pendencias=True)
            miner.salvarNoCache()
            self._definir_estado(job_id, "concluido", self._resumo(miner))
        except Exception as erro:  # noqa: BLE001 - qualquer falha vira estado de erro do job
            self._definir_estado(job_id, "erro", f"{type(erro).__name__}: {erro}")

    def status(self, job_id: str) -> JobMineracao:
        """Estado atual de um job pelo seu id (404 se não existir)."""
        with self._lock:
            job = self._jobs.get(job_id)
        if job is None:
            raise JobNaoEncontradoError(job_id)
        return job

    def status_do_repo(self, repo: str) -> JobMineracao | None:
        """Último job conhecido de um repo, usado para resolver o estado."""
        with self._lock:
            job_id = self._job_por_repo.get(repo)
            return self._jobs.get(job_id) if job_id is not None else None

    def remover_job(self, repo: str) -> None:
        """Esquece o job associado a um repo, por exemplo após exclusão."""
        with self._lock:
            job_id = self._job_por_repo.pop(repo, None)
            if job_id is not None:
                self._jobs.pop(job_id, None)

    def _exigir_tokens(self) -> None:
        if not self._tokens:
            raise TokensAusentesError()

    def _exigir_nenhuma_mineracao_global(self) -> None:
        """Trava global: só uma mineração por vez, em qualquer repo."""
        for job in self._jobs.values():
            if job.estado in ESTADOS_ATIVOS:
                raise ConflitoMineracaoError(
                    f"Já existe uma mineração em andamento ('{job.repo}'); aguarde concluir."
                )

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
