class Vertice:
    rotulo: str
    __peso: float
    __grauEntrada: int
    __grauSaida: int

    def __init__(self, rotulo: str) -> None:
        self.rotulo = rotulo
        self.__grauEntrada = 0
        self.__grauSaida = 0
        self.__peso = 0

    def aumentarGrauEntrada(self):
        self.__grauEntrada += 1

    def aumentarGrauSaida(self):
        self.__grauSaida += 1

    def diminuirGrauEntrada(self):
        self.__grauEntrada -= 1

    def diminuirGrauSaida(self):
        self.__grauSaida -= 1

    def setPeso(self, peso: float):
        self.__peso = peso

    @property
    def peso(self):
        return self.__peso

    @property # para ser acessado como vert.grauCentralidade
    def grauCentralidade(self):
        return self.__grauEntrada + self.__grauSaida


