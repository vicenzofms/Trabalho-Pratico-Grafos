from .vertice import Vertice

class Aresta:
    __peso: float
    __inicio: Vertice
    __fim: Vertice

    def __init__(self, peso: float, inicio: Vertice, fim: Vertice) -> None:
        self.__peso = peso
        self.__inicio = inicio
        self.__fim = fim

        inicio.aumentarGrauSaida()
        fim.aumentarGrauEntrada()

    @property
    def peso(self):
        return self.__peso

