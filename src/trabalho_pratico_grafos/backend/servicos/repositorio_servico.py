"""Lista/resume repositórios e resolve o `estado` (Fase 2 + Fase 6).

Consome a `FonteDeDados` (costura 1) e consulta o `GerenciadorMineracao`
(costura 3) para refletir os estados `MINERANDO`/`ERRO` de um job em andamento.
"""

from ..fontes import FonteDeDados
from ..mineracao import GerenciadorMineracao
from ..schemas.repositorio import EstadoRepositorio, RepositorioResumo


class RepositorioServico:
    def __init__(self, fonte: FonteDeDados, gerenciador: GerenciadorMineracao) -> None:
        self._fonte = fonte
        self._gerenciador = gerenciador

    def listar(self) -> list[RepositorioResumo]:
        return [self.obter(nome) for nome in self._fonte.listar()]

    def obter(self, repo: str) -> RepositorioResumo:
        # Um job em andamento/falho tem prioridade sobre o estado derivado do cache.
        job = self._gerenciador.status_do_repo(repo)
        if job is not None and job.estado in ("pendente", "executando"):
            return RepositorioResumo(nome=repo, estado=EstadoRepositorio.MINERANDO)
        if job is not None and job.estado == "erro":
            return RepositorioResumo(nome=repo, estado=EstadoRepositorio.ERRO)

        # Sem job ativo: estado derivado do cache (como no MVP).
        dados = self._fonte.carregar(repo)
        if dados is None:
            return RepositorioResumo(nome=repo, estado=EstadoRepositorio.AUSENTE)
        return RepositorioResumo(
            nome=repo,
            estado=EstadoRepositorio.DISPONIVEL,
            quantidade_usuarios=dados["usuarios"]["quantidade"],
            quantidade_interacoes=len(dados["interacoes"]),
        )
