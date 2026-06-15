"""Schemas de grafo."""

from pydantic import BaseModel


class GrafoResumo(BaseModel):
    tipo: str  # integrado | comentarios | fechamento | prs
    vertices: int
    arestas: int
    # PENDÊNCIA (parte A): `densidade` viria de `coesao.densidade`, que ainda não
    # existe. Fiel à regra "o backend não calcula métrica nenhuma", o campo é
    # Optional e fica `None` até `coesao.densidade` existir — então popula sozinho
    # (try-import no serviço), sem mudar este contrato.
    densidade: float | None = None


class NoGrafo(BaseModel):
    id: str  # rótulo do vértice (username); id estável para o vis.js
    grau_entrada: int
    grau_saida: int


class ArestaGrafo(BaseModel):
    origem: str
    destino: str
    peso: float


class GrafoVisualizacao(BaseModel):
    """Topologia do grafo (nós + arestas dirigidas) para renderização no front."""

    tipo: str
    nos: list[NoGrafo]
    arestas: list[ArestaGrafo]
