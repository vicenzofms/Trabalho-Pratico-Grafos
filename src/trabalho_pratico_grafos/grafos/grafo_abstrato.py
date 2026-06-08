from abc import ABC, abstractmethod

class GrafoAbstrato(ABC):
    # faltando convergente, incidente e divergente

    qntdVertices: int
    qntdArestas: int
    rotulosVertices: list[str]
    grausEntrada: list[int]
    grausSaida: list[int]
    pesosVertices: list[float]

    def __init__(self, numeroVertices) -> None:
        self.qntdVertices = numeroVertices
        self.qntdArestas = 0
        # inicializa os arrays com tudo "" ou tudo 0
        self.rotulosVertices = [""] * self.qntdVertices
        self.grausEntrada = [0] * self.qntdVertices
        self.grausSaida = [0] * self.qntdVertices
        self.pesosVertices = [0.0] * self.qntdVertices

    def isVazio(self) -> bool:
        # como o número de vertices é definido no __init__
        # não faz sentido olhar a qntd de vértices, mas TODO: confirmar depois
        return self.qntdArestas == 0
    
    def setPesoVertice(self, u: int, peso: float):
        self._validarIndices(u)
        self.pesosVertices[u] = peso

    def getPesoVertice(self, u: int):
        self._validarIndices(u)
        return self.pesosVertices[u]

    def getQuantidadeVertices(self) -> int:
        return self.qntdVertices

    def getQuantidadeArestas(self) -> int:
        return self.qntdArestas

    def setRotuloVertice(self, u: int, rotulo: str):
        self._validarIndices(u)
        self.rotulosVertices[u] = rotulo

    def getRotuloVertice(self, u: int):
        self._validarIndices(u)
        return self.rotulosVertices[u]

    def getGrauEntrada(self, u):
        self._validarIndices(u)
        return self.grausEntrada[u]

    def getGrauSaida(self, u):
        self._validarIndices(u)
        return self.grausSaida[u]

    def adicionarAresta(self, u: int, v: int, peso: float = 1.0): # Template Method, lógica da inserção fica em _inserirAresta
        self._validarAresta(u, v)
        # garante que não existe essa aresta ainda
        if (self.existeAresta(u, v)):
            return # método deve ser idempotente, rodar 2 vezes deve ter o mesmo resultado

        if (peso <= 0):
            raise ValueError("O peso deve ser um valor positivo")

        self._inserirAresta(u, v, peso)
        self.grausEntrada[v] += 1
        self.grausSaida[u] += 1
        self.qntdArestas += 1

    def removeAresta(self, u: int, v: int) -> None: # Template Method, lógica da inserção fica em _deletarAresta
        self._validarAresta(u, v)
        # garante que existe essa aresta 
        if (not self.existeAresta(u, v)):
            return

        self._deletarAresta(u, v)
        self.grausEntrada[v] -= 1
        self.grausSaida[u] -= 1
        self.qntdArestas -= 1

    def isConexo(self) -> bool: #BFS no subjacente tem que chegar em todos os vértices do grafo
        if self.qntdVertices == 0: return True

        # BFS começando
        # 0 é a raiz
        visitados = {0} # define um set
        fila = [0]

        # ainda há vértices a processar
        while len(fila) != 0:
            u = fila.pop(0) # pega o 1o elemento da fila
            for v in range(self.qntdVertices): # percorre todos os vértices do grafo
                # se for igual só pula
                if (v == u): 
                    continue
                # se não v não foi visitado porém é vizinho de u (no grafo subjacente)
                if (v not in visitados and (self.isSucessor(u, v) or self.isPredecessor(u, v))):
                    fila.append(v)
                    visitados.add(v)
        # se eu visitei todo mundo é conexo, caso contrário não é
        return len(visitados) == self.qntdVertices

    def isCompleto(self) -> bool:
        # se cada vértice tem n-1 arestas saindo
        return self.qntdArestas == (self.qntdVertices * (self.qntdVertices-1))

    def _validarAresta(self, u: int, v: int) -> None:
        # não pode ser laço
        if (u == v):
            raise ValueError("Não pode ser um laço")
        self._validarIndices(u, v)

    def _validarIndices(self, *args: int) -> None:
        # garantir que estão nos bounds
        for index in args:
            if (index < 0 or index >= self.qntdVertices):
                raise ValueError("Vértice(s) inválido(s)")

    @abstractmethod
    def setPesoAresta(self, u: int, v: int, peso: float):
        pass

    @abstractmethod
    def getPesoAresta(self, u: int, v: int) -> float:
        pass

    @abstractmethod
    def isSucessor(self, u: int, v: int) -> bool:
        pass

    @abstractmethod
    def isPredecessor(self, u: int, v: int) -> bool:
        pass

    @abstractmethod
    def _inserirAresta(self, u: int, v: int, peso: float) -> None:
        pass

    @abstractmethod
    def _deletarAresta(self, u: int, v: int):
        pass

    @abstractmethod
    def existeAresta(self, u: int, v: int) -> bool:
        pass


