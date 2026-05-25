from abc import ABC, abstractmethod

from trabalho_pratico_grafos.grafos import *

class GrafoAbstrato(ABC):
    # faltando convergente, incidente e divergente

    # @abstractmethod
    # def isVazio(self) -> bool:
    #     pass
    #
    # @abstractmethod
    # def isConexo(self) -> bool:
    #     pass
    #
    # @abstractmethod
    # def isCompleto(self) -> bool:
    #     pass
    #
    # @abstractmethod
    # def getQuantidadeVertices(self) -> int:
    #     pass
    #
    # @abstractmethod
    # def getQuantidadeArestas(self) -> int:
    #     pass
    #
    # @abstractmethod
    # def existeAresta(self, u: int, v: int) -> bool:
    #     pass
    #
    # @abstractmethod
    # def adicionarAresta(self, u: int, v: int):
    #     pass
    #
    # @abstractmethod
    # def removeAresta(self, u: int, v: int) -> None:
    #     pass
    #
    # @abstractmethod
    # def isSucessor(self, u: int, v: int) -> bool:
    #     pass
    #
    # @abstractmethod
    # def isPredecessor(self, u: int, v: int) -> bool:
    #     pass
    #
    # @abstractmethod
    # def setPesoVertice(self, u: int, peso: float):
    #     pass
    #
    # @abstractmethod
    # def getPesoVertice(self, u: int):
    #     pass
    #
    # @abstractmethod
    # def setPesoAresta(self, u: int, v: int, peso: float):
    #     pass
    #
    # @abstractmethod
    # def getPesoAresta(self, u: int, v: int):
    #     pass
    #
    pass

class AdjacenciaGrafo(GrafoAbstrato):

    __vertices: dict

    def __init__(self):
        self.__vertices = dict()

    def adicionarVertice(self, rotulo: str):
        v = Vertice(rotulo)
        self.__vertices[v] = list()

    def adicionarAresta(self, u: Vertice, v: Vertice):
        self.__vertices[u].append(v);

    pass

