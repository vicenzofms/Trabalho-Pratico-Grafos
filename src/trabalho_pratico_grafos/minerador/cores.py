from typing import Literal

Cor = Literal["nenhuma","vermelho", "verde", "amarelo", "azul", "roxo", "ciano"]

CORES: dict[Cor, str] = {
    "nenhuma" : "",
    "vermelho": "\033[31m",
    "verde": "\033[32m",
    "amarelo": "\033[33m",
    "azul": "\033[34m",
    "roxo": "\033[35m",
    "ciano": "\033[36m",
}
RESET = "\033[0m"

def colorir(texto: str, cor: Cor):
    print(f"{CORES[cor]}{texto}{RESET}")

