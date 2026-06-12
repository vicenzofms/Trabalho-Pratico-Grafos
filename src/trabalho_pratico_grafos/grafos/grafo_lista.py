from .grafo_abstrato import GrafoAbstrato

class GrafoListaAdjacencia(GrafoAbstrato):

    def __init__(self, numeroVertices: int) :
        super().__init__(numeroVertices)
        self.lista = [{} for _ in range(self.qntdVertices)]

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
        predecessores = []
        for i in range(self.qntdVertices):
            if u in self.lista[i]:
                predecessores.append(i)

        return predecessores


    def _inserirAresta(self, u: int, v: int, peso: float) -> None:
         #Validação dos parâmetros realizada no Method
        self.lista[u][v] = peso

    def _deletarAresta(self, u:int, v:int) -> None:
        self.lista[u].pop(v, None)