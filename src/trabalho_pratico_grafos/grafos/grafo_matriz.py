from .grafo_abstrato import GrafoAbstrato
from array import array

class GrafoMatrizAdjacencia(GrafoAbstrato):

    def __init__(self, numeroVertices: int):
        super().__init__(numeroVertices)
        # utilizando array('d') ao invés de list[float] por questões de otimização
        # a matriz ainda pode ser acessada por self.matriz[i][j]
        self.matriz = [array('d', [0.0] * self.qntdVertices) for _ in range(self.qntdVertices)]

