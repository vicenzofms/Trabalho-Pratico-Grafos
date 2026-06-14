"""Lista/resume repositórios e resolve o `estado` (Fase 2).

Consome a `FonteDeDados` (costura 1) — nunca lê `src/data/` direto.
"""

from ..fontes import FonteDeDados
from ..schemas.repositorio import EstadoRepositorio, RepositorioResumo


class RepositorioServico:
    def __init__(self, fonte: FonteDeDados) -> None:
        self._fonte = fonte

    def listar(self) -> list[RepositorioResumo]:
        return [self.obter(nome) for nome in self._fonte.listar()]

    def obter(self, repo: str) -> RepositorioResumo:
        dados = self._fonte.carregar(repo)
        if dados is None:
            # No MVP, sem cache => AUSENTE. O resumo sempre responde (com estado);
            # quem exige dados (grafos/análise) é que devolve 404.
            return RepositorioResumo(nome=repo, estado=EstadoRepositorio.AUSENTE)
        return RepositorioResumo(
            nome=repo,
            estado=EstadoRepositorio.DISPONIVEL,
            quantidade_usuarios=dados["usuarios"]["quantidade"],
            quantidade_interacoes=len(dados["interacoes"]),
        )
