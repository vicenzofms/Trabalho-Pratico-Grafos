from abc import ABC, abstractmethod
from trabalho_pratico_grafos.grafos import *

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

    def isVazio(self) -> bool:
        return self.qntdVertices == 0
    
    def setPesoVertice(self, u: int, peso: float):
        self.pesosVertices[u] = peso

    def getPesoVertice(self, u: int):
        return self.pesosVertices[u]

    def getQuantidadeVertices(self) -> int:
        return self.qntdVertices

    def getQuantidadeArestas(self) -> int:
        return self.qntdArestas

    def setRotuloVertice(self, u: int, rotulo: str):
        self.rotulosVertices[u] = rotulo

    def getRotuloVertice(self, u: int):
        return self.rotulosVertices[u]

    def adicionarAresta(self, u: int, v: int, peso: float = 0.5): # Template Method, lógica da inserção fica em _inserirAresta
        # garante que não é um laço
        if (u == v):
            return
        # garante que não existe essa aresta ainda
        if (self.existeAresta(u, v)):
            return

        self.__inserirAresta(u, v, peso)
        self.grausEntrada[v] += 1
        self.grausSaida[u] += 1
        self.qntdArestas += 1

    def removeAresta(self, u: int, v: int) -> None: # Template Method, lógica da inserção fica em _deletarAresta
        # garante que existe essa aresta 
        if (not self.existeAresta(u, v)):
            return

        self.__deletarAresta(u, v)
        self.grausEntrada[v] -= 1
        self.grausSaida[u] -= 1
        self.qntdArestas -= 1

    def isConexo(self) -> bool: #BFS no subjacente tem que chegar em todos os vértices do grafo
        if self.qntdVertices == 0: return True

        # BFS começando
        # 0 é a raiz
        visitados = [0]
        fila = [0]

        # ainda há vértices a processar
        while len(fila) != 0:
            u = fila.pop() # pega o 1o elemento da fila
            for v in range(self.qntdVertices): # percorre todos os vértices do grafo
                # se for igual só pula
                if (v == u): 
                    continue
                # se não v não foi visitado porém é vizinho de u (no grafo subjacente)
                if (v not in visitados and (self.isSucessor(u, v) or self.isPredecessor(u, v))):
                    fila.append(v)
                    visitados.append(v)
        # se eu visitei todo mundo é conexo, caso contrário não é
        return len(visitados) == self.qntdVertices

    def isCompleto(self) -> bool:
        # se cada vértice tem n-1 arestas saindo
        return self.qntdArestas == (self.qntdVertices * (self.qntdVertices-1))

    @abstractmethod
    def setPesoAresta(self, u: int, v: int, peso: float):
        pass

    @abstractmethod
    def getPesoAresta(self, u: int, v: int):
        pass

    @abstractmethod
    def isSucessor(self, u: int, v: int) -> bool:
        pass

    @abstractmethod
    def isPredecessor(self, u: int, v: int) -> bool:
        pass

    @abstractmethod
    def __inserirAresta(self, u: int, v: int, peso: float) -> None:
        pass

    @abstractmethod
    def __deletarAresta(self, u: int, v: int):
        pass

    @abstractmethod
    def existeAresta(self, u: int, v: int) -> bool:
        pass


