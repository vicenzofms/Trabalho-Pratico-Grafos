"""Schemas de análise — já com índices convertidos para username (seção 3/5).

Campos `Optional` (densidade, assortatividade, clustering, proximidade,
intermediação) ficam `None` enquanto as funções das partes A/B não existirem
(Fase 4: "as funções que faltam ficam como None/omitidas no JSON até existirem").
"""

from pydantic import BaseModel


class ItemRanking(BaseModel):
    username: str
    valor: float


class ItemArestaPeso(BaseModel):
    origem: str
    destino: str
    peso: float


class GrauUsuario(BaseModel):
    """Contagens brutas de arestas (in/out) de um usuário."""

    entrada: int
    saida: int


class RelatorioAnalise(BaseModel):
    """`relatorio_completo()` serializado e nomeado por username."""

    densidade: float | None = None
    clustering: float | None = None
    assortatividade: float | None = None
    modularidade: float | None = None
    # métrica -> ranking já ordenado (desc) e com username no lugar do índice.
    # chaves no MVP: grau_entrada, grau_saida, autovetor, pagerank
    # (proximidade/intermediacao entram quando a parte B entregar).
    centralidades: dict[str, list[ItemRanking]]
    # username -> contagens brutas de grau de entrada/saída (nº de arestas).
    graus: dict[str, GrauUsuario] = {}
    # Arestas direcionadas ordenadas por peso decrescente.
    arestas_mais_pesadas: list[ItemArestaPeso]
    # id da comunidade (str) -> usernames que pertencem a ela.
    comunidades: dict[str, list[str]]
    # categoria (locais|classicas|intercomunidade) -> pares de usernames.
    pontes: dict[str, list[tuple[str, str]]]


class CentralidadesResposta(BaseModel):
    centralidades: dict[str, list[ItemRanking]]


class ComunidadesResposta(BaseModel):
    comunidades: dict[str, list[str]]
    modularidade: float | None = None


class PontesResposta(BaseModel):
    locais: list[tuple[str, str]]
    classicas: list[tuple[str, str]]
    intercomunidade: list[tuple[str, str]]


class CoesaoResposta(BaseModel):
    # Todas pendentes da parte A (`coesao.py`); None até existirem.
    densidade: float | None = None
    clustering: float | None = None
    assortatividade: float | None = None
