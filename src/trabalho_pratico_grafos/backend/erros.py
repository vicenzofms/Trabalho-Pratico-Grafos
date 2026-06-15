"""Exceções de domínio do backend.

Os **serviços** levantam estas exceções (sem conhecer HTTP), e o ``main.py``
registra *exception handlers* que as traduzem para os códigos de status do
contrato (seção 6 do plano). Isso mantém os serviços testáveis isoladamente, sem
acoplar a camada de negócio ao FastAPI.
"""


class ErroBackend(Exception):
    """Base de todos os erros traduzíveis para resposta HTTP."""


class RepositorioAusenteError(ErroBackend):
    """Repositório sem cache (estado AUSENTE) acessado em rota de leitura → 404."""

    def __init__(self, repo: str) -> None:
        self.repo = repo
        super().__init__(f"Repositório '{repo}' não está disponível (sem cache).")


class TipoGrafoInvalidoError(ErroBackend):
    """Tipo de grafo fora de {integrado, comentarios, fechamento, prs} → 422."""

    def __init__(self, tipo: str, validos: list[str]) -> None:
        self.tipo = tipo
        self.validos = validos
        super().__init__(f"Tipo de grafo inválido: '{tipo}'. Válidos: {validos}.")


class MetricaInvalidaError(ErroBackend):
    """Métrica inexistente em /ranking → 404 com a lista de métricas válidas."""

    def __init__(self, metrica: str, validas: list[str]) -> None:
        self.metrica = metrica
        self.validas = validas
        super().__init__(f"Métrica inválida: '{metrica}'. Válidas: {validas}.")


class ConflitoMineracaoError(ErroBackend):
    """Pré-condição de mineração violada (Fase 6) → 409 Conflict.

    Ex.: `minerar` num repo que já existe (use `atualizar`), `atualizar` num repo
    ausente (use `minerar`), ou disparo enquanto já há um job em andamento.
    """


class JobNaoEncontradoError(ErroBackend):
    """Consulta de status com job_id inexistente (Fase 6) → 404."""

    def __init__(self, job_id: str) -> None:
        self.job_id = job_id
        super().__init__(f"Job de mineração '{job_id}' não encontrado.")


class TokensAusentesError(ErroBackend):
    """Mineração pedida sem nenhum token do GitHub configurado → 503.

    A mineração está implementada (Fase 6), mas indisponível por falta de
    `GITHUB_TOKENS` no ambiente.
    """

    def __init__(self) -> None:
        super().__init__("nenhum token do GitHub configurado (defina GITHUB_TOKENS)")
