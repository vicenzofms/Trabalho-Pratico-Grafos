"""Construção dos 4 grafos a partir dos dados da fonte (Fase 3).

A lógica de `construir_grafo_por_tipo` / `agregar_aresta` / `definir_rotulos` é a
mesma já validada no `scripts/builder.py`, migrada para cá com tipos de retorno
testáveis. O serviço depende só da abstração `GrafoAbstrato` e da `FonteDeDados`.
"""

from trabalho_pratico_grafos.grafos import GrafoAbstrato, GrafoMatrizAdjacencia

from ..erros import RepositorioAusenteError, TipoGrafoInvalidoError
from ..fontes import FonteDeDados
from ..schemas.grafo import GrafoResumo
from .analise_servico import densidade_opcional

# tipo do grafo -> conjunto de `tipo` de interação que o compõem.
# Conjunto vazio = todas as interações (grafo integrado). Mapeia exatamente os
# grafos do builder: geral, comentários, fechamento e PR (revisão + merge).
TIPOS_INTERACAO: dict[str, set[str]] = {
    "integrado": set(),
    "comentarios": {"comentario_issue", "comentario_pull_request"},
    "fechamento": {"fechamento_issue"},
    "prs": {"revisao_pull", "merge_pull"},
}


def agregar_aresta(grafo: GrafoAbstrato, u: int, v: int, peso: float) -> None:
    """Soma o peso à aresta u->v se já existir; senão cria (idempotente por par)."""
    if grafo.existeAresta(u, v):
        grafo.setPesoAresta(u, v, grafo.getPesoAresta(u, v) + peso)
    else:
        grafo.adicionarAresta(u, v, peso)


def definir_rotulos(grafo: GrafoAbstrato, rotulos: list[str]) -> None:
    if grafo.getQuantidadeVertices() != len(rotulos):
        raise ValueError("O grafo não possui a mesma quantidade de vértices passados")
    for i, rotulo in enumerate(rotulos):
        grafo.setRotuloVertice(i, rotulo)


def construir_grafo_por_tipo(dados: dict, tipos: set[str]) -> GrafoAbstrato:
    """Monta um `GrafoMatrizAdjacencia` filtrando as interações por `tipos`.

    `tipos` vazio inclui todas as interações. Cada usuário vira um vértice (na
    ordem em que aparece); arestas com o mesmo par são agregadas pelo peso.
    """
    interacoes = (
        [i for i in dados["interacoes"] if i["tipo"] in tipos]
        if len(tipos) > 0
        else dados["interacoes"]
    )

    usernames: list[str] = []
    mapa_ids: dict[str, int] = {}
    for interacao in interacoes:
        for nome in (interacao["origem"], interacao["destino"]):
            if nome not in mapa_ids:
                mapa_ids[nome] = len(usernames)
                usernames.append(nome)

    grafo = GrafoMatrizAdjacencia(len(usernames))
    for interacao in interacoes:
        u = mapa_ids[interacao["origem"]]
        v = mapa_ids[interacao["destino"]]
        agregar_aresta(grafo, u, v, interacao["peso"])
    definir_rotulos(grafo, usernames)
    return grafo


class GrafoServico:
    def __init__(self, fonte: FonteDeDados) -> None:
        self._fonte = fonte

    def _dados(self, repo: str) -> dict:
        dados = self._fonte.carregar(repo)
        if dados is None:
            raise RepositorioAusenteError(repo)
        return dados

    def construir(self, repo: str, tipo: str) -> GrafoAbstrato:
        if tipo not in TIPOS_INTERACAO:
            raise TipoGrafoInvalidoError(tipo, list(TIPOS_INTERACAO))
        return construir_grafo_por_tipo(self._dados(repo), TIPOS_INTERACAO[tipo])

    def construir_todos(self, repo: str) -> dict[str, GrafoAbstrato]:
        dados = self._dados(repo)
        return {
            tipo: construir_grafo_por_tipo(dados, tipos)
            for tipo, tipos in TIPOS_INTERACAO.items()
        }

    def _resumir(self, tipo: str, grafo: GrafoAbstrato) -> GrafoResumo:
        return GrafoResumo(
            tipo=tipo,
            vertices=grafo.getQuantidadeVertices(),
            arestas=grafo.getQuantidadeArestas(),
            densidade=densidade_opcional(grafo),  # None até a parte A entregar coesao.densidade
        )

    def resumir(self, repo: str, tipo: str) -> GrafoResumo:
        return self._resumir(tipo, self.construir(repo, tipo))

    def resumir_todos(self, repo: str) -> list[GrafoResumo]:
        return [self._resumir(tipo, grafo) for tipo, grafo in self.construir_todos(repo).items()]
