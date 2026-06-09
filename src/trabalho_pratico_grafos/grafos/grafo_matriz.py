from .grafo_abstrato import GrafoAbstrato
from array import array

class GrafoMatrizAdjacencia(GrafoAbstrato):

    def __init__(self, numeroVertices: int):
        super().__init__(numeroVertices)
        # utilizando array('d') ao invés de list[float] por questões de otimização
        # a matriz ainda pode ser acessada por self.matriz[i][j]
        self.matriz = [array('d', [0.0] * self.qntdVertices) for _ in range(self.qntdVertices)]

    def setPesoAresta(self, u: int, v: int, peso: float):
        self._validarAresta(u, v)
        if (not self.existeAresta(u, v)):
            raise ValueError("A aresta não existe")
        if (peso <= 0):
            raise ValueError("O peso deve ser um valor positivo")
        self.matriz[u][v] = peso

    def getPesoAresta(self, u: int, v: int):
        self._validarIndices(u, v) # retorna 0.0 em caso de laço, por consistência com existeAresta
        return self.matriz[u][v]

    def existeAresta(self, u: int, v: int) -> bool:
        self._validarIndices(u, v)
        return self.matriz[u][v] != 0.0

    def isSucessor(self, u: int, v: int) -> bool:
        # não pode ser igual
        if (u == v):
            return False
        self._validarIndices(u, v)
        return self.existeAresta(u, v)

    def isPredecessor(self, u: int, v: int) -> bool:
        # não pode ser igual
        if (u == v):
            return False
        self._validarIndices(u, v)
        return self.matriz[v][u] != 0.0

    def getPredecessores(self, u: int) -> list[int]:
        self._validarIndices(u)
        predecessores = []
        for i in range(self.getQuantidadeVertices()):
            if self.matriz[i][u] != 0.0:
                predecessores.append(i)
        return predecessores
       
    def getSucessores(self, u: int) -> list[int]:
        self._validarIndices(u)
        sucessores = []
        for i in range(self.getQuantidadeVertices()):
            if self.matriz[u][i] != 0.0:
                sucessores.append(i)
        return sucessores
       
    def _inserirAresta(self, u: int, v: int, peso: float) -> None:
        # lógicas de validação já foram feitas no Template Method
        self.matriz[u][v] = peso

    def _deletarAresta(self, u: int, v: int):
        # lógicas de validação já foram feitas no Template Method
        self.matriz[u][v] = 0.0

