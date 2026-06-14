from .grafo_abstrato import GrafoAbstrato

class GrafoListaAdjacencia(GrafoAbstrato):

    def __init__(self, numeroVertices: int) :
        super().__init__(numeroVertices)
        self.lista = [{} for _ in range(self.qntdVertices)]
        # Cache dos predecessores. getSucessores já é O(grau) (chaves do dict),
        # mas getPredecessores teria que varrer todos os V vértices a cada chamada
        # (O(V)) — e pagerank/autovetor/clustering chamam isso ~100·V vezes, o que
        # torna a análise inviável em grafos grandes. A lista é construída sob
        # demanda numa única varredura e qualquer mutação a invalida.
        self._cachePredecessores: list[list[int]] | None = None

    def _construirCachePredecessores(self) -> None:
        """Varre a lista uma única vez montando os predecessores de cada vértice."""
        predecessores: list[list[int]] = [[] for _ in range(self.qntdVertices)]
        for u in range(self.qntdVertices):
            for v in self.lista[u]:
                predecessores[v].append(u)
        self._cachePredecessores = predecessores

    def _invalidarCachePredecessores(self) -> None:
        self._cachePredecessores = None

    def setPesoAresta(self, u: int, v: int, peso: float): # Utilizado para incrementar pesos em arestas já detectadas anteriormente.
        self._validarAresta(u, v)
        if not self.existeAresta(u, v):
            raise ValueError("A aresta não existe.")
        if(peso <= 0):
            raise ValueError("O peso deve ser um valor positivo.")
        self.lista[u][v] = peso


    def getPesoAresta(self, u: int, v: int) -> float:
        self._exigirAresta(u, v)
        return self.lista[u][v]

    def existeAresta(self, u: int, v: int) -> bool:
        self._validarIndices(u, v)
        return v in self.lista[u] #Verifica se existe o vértice v na lista de dicionários do vértice u.

    def isSucessor(self, u: int, v: int) -> bool:
        if u == v:
            return False
        self._validarIndices(u, v)
        return self.existeAresta(u, v)

    def isPredecessor(self, u: int, v: int) -> bool:
        if u == v:
            return False
        self._validarIndices(u, v)
        return self.existeAresta(v, u)

    def getSucessores(self, u: int) -> list[int]:
        self._validarIndices(u)
        return list(self.lista[u].keys())

    def getPredecessores(self, u: int) -> list[int]:
        self._validarIndices(u)
        if self._cachePredecessores is None:
            self._construirCachePredecessores()
        return self._cachePredecessores[u]


    def _inserirAresta(self, u: int, v: int, peso: float) -> None:
         #Validação dos parâmetros realizada no Method
        self.lista[u][v] = peso
        self._invalidarCachePredecessores()

    def _deletarAresta(self, u:int, v:int) -> None:
        self.lista[u].pop(v, None)
        self._invalidarCachePredecessores()