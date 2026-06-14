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


class MineracaoIndisponivelError(ErroBackend):
    """Mineração desabilitada no MVP (stub) → 501 Not Implemented."""

    def __init__(self, detalhe: str = "mineração indisponível neste modo") -> None:
        super().__init__(detalhe)
