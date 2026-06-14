from .grafo_abstrato import GrafoAbstrato
from array import array

class GrafoMatrizAdjacencia(GrafoAbstrato):

    def __init__(self, numeroVertices: int):
        super().__init__(numeroVertices)
        # utilizando array('d') ao invés de list[float] por questões de otimização
        # a matriz ainda pode ser acessada por self.matriz[i][j]
        self.matriz = [array('d', [0.0] * self.qntdVertices) for _ in range(self.qntdVertices)]
        # Cache das listas de sucessores e predecessores. Sem ele, cada
        # getSucessores/getPredecessores varre uma linha/coluna inteira (O(V)) —
        # e a análise (que chama isso ~100·V vezes em pagerank/autovetor e V vezes
        # em cada BFS) fica O(V³), inviável em grafos grandes. As listas são
        # construídas sob demanda numa única varredura e qualquer mutação as invalida.
        self._cacheSucessores: list[list[int]] | None = None
        self._cachePredecessores: list[list[int]] | None = None

    def _construirCacheAdjacencia(self) -> None:
        """Varre a matriz uma única vez preenchendo sucessores e predecessores."""
        n = self.qntdVertices
        sucessores: list[list[int]] = [[] for _ in range(n)]
        predecessores: list[list[int]] = [[] for _ in range(n)]
        for u in range(n):
            linha = self.matriz[u]
            for v in range(n):
                if linha[v] != 0.0:
                    sucessores[u].append(v)
                    predecessores[v].append(u)
        self._cacheSucessores = sucessores
        self._cachePredecessores = predecessores

    def _invalidarCacheAdjacencia(self) -> None:
        self._cacheSucessores = None
        self._cachePredecessores = None

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
        if self._cachePredecessores is None:
            self._construirCacheAdjacencia()
        return self._cachePredecessores[u]

    def getSucessores(self, u: int) -> list[int]:
        self._validarIndices(u)
        if self._cacheSucessores is None:
            self._construirCacheAdjacencia()
        return self._cacheSucessores[u]

    def _inserirAresta(self, u: int, v: int, peso: float) -> None:
        # lógicas de validação já foram feitas no Template Method
        self.matriz[u][v] = peso
        self._invalidarCacheAdjacencia()

    def _deletarAresta(self, u: int, v: int):
        # lógicas de validação já foram feitas no Template Method
        self.matriz[u][v] = 0.0
        self._invalidarCacheAdjacencia()

