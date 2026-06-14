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
