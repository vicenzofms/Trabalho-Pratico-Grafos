from abc import ABC, abstractmethod

class GrafoAbstrato(ABC):
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
    
    def adicionarAresta(self, u: int, v: int, peso: float = 1.0): # Template Method, lógica da inserção fica em _inserirAresta
        self._validarAresta(u, v)
        # garante que não existe essa aresta ainda
        if (self.existeAresta(u, v)):
            return # método deve ser idempotente, rodar 2 vezes deve ter o mesmo resultado (por isso não usar _exigirAresta)

        if (peso <= 0):
            raise ValueError("O peso deve ser um valor positivo")

        self._inserirAresta(u, v, peso)
        self.grausEntrada[v] += 1
        self.grausSaida[u] += 1
        self.qntdArestas += 1

    def removeAresta(self, u: int, v: int) -> None: # Template Method, lógica da inserção fica em _deletarAresta
        """Remove a aresta u -> v do grafo"""
        self._validarAresta(u, v)
        # garante que existe essa aresta (não usamos _exigirAresta porque o método deve ser idempotente)
        if (not self.existeAresta(u, v)):
            return

        self._deletarAresta(u, v)
        self.grausEntrada[v] -= 1
        self.grausSaida[u] -= 1
        self.qntdArestas -= 1

    def isConexo(self) -> bool: 
        """Verifica se o grafo é fracamente conexo, ao fazer uma BFS no grafo subjacente"""
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
    
    # Métodos de consulta usam _exigirAresta e, por consequência levantam exceção caso aresta não exista
    # já que seria uma operação inconsistente
    def isIncidente(self, u: int, v: int, x: int) -> bool:
        # verificar se a aresta u -> v incide em x
        # ou seja, se x é uma das pontas da aresta
        self._validarIndices(x)
        self._exigirAresta(u, v)
        return x == u or x == v

    def isConvergente(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        # relação entre 2 arestas
        # elas convergem se chegam no mesmo vértice
        self._exigirAresta(u1, v1)
        self._exigirAresta(u2, v2)
        if u1 == u2 and v1 == v2:
            raise ValueError("As arestas devem ser diferentes uma da outra")
        return v1 == v2
    
    def isDivergente(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        # relação entre 2 arestas
        # se as 2 arestas saem do mesmo vértice
        self._exigirAresta(u1, v1)
        self._exigirAresta(u2, v2)
        if u1 == u2 and v1 == v2:
            raise ValueError("As arestas devem ser diferentes uma da outra")
        return u1 == u2

    # --- Métodos Helpers
    def _validarAresta(self, u: int, v: int) -> None:
        """Garante que os vértices existem e que não é um laço, não verifica existência da aresta"""
        # garante que os vértices estão no grafo
        self._validarIndices(u, v)
        # não pode ser laço
        if (u == v):
            raise ValueError("Não pode ser um laço")


    def _validarIndices(self, *args: int) -> None:
        """Valida se os vértices existem no grafo"""
        # garantir que estão nos bounds
        # valida quantos vértices quiser
        for index in args:
            if (index < 0 or index >= self.qntdVertices):
                raise IndexError("Vértice(s) inválido(s)")

    def _exigirAresta(self, u, v):
        """Garante que a aresta u -> v já existe no grafo"""
        self._validarAresta(u, v) # verifica laços e índices inválidos
        if not self.existeAresta(u, v):
            raise ValueError(f"Não existe aresta {u} -> {v} no grafo")
    # ---------------
        
    # métodos getters e setters
    # usam os helpers e levantam exceção caso valores inválidos, quando necessário,
    # para garantir operações consistentes
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

    def getVerticePorRotulo(self, rotulo: str) -> int | None:
        # retorna o 1o vértice do grafo com esse rótulo
        if rotulo in self.rotulosVertices:
            return self.rotulosVertices.index(rotulo)
        return None

    def getRotuloVertice(self, u: int):
        self._validarIndices(u)
        return self.rotulosVertices[u]

    def getGrauEntrada(self, u):
        self._validarIndices(u)
        return self.grausEntrada[u]

    def getGrauSaida(self, u):
        self._validarIndices(u)
        return self.grausSaida[u]

    # --- Métodos Abstratos, precisam ser implementados nas subclasses
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
    def getPredecessores(self, u: int) -> list[int]:
        pass

    @abstractmethod
    def getSucessores(self, u: int) -> list[int]:
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


