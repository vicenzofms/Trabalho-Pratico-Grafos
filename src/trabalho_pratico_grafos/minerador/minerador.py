from dataclasses import dataclass
import time
import requests

from trabalho_pratico_grafos.minerador.mapa_usuarios import MapaUsuarios

@dataclass
class Interacao:
    quemFez: str
    alvo: str
    peso: int
    tipo: str

class Minerador:
    urlBase: str = "https://api.github.com"
    repositorio: str
    headers: dict

    interacoes = [] # depois pode mudar pra lista ser o retornoo da função executar, mas pra debug assim ta mais fácil

    __mapaUsuarios: MapaUsuarios

    PESOS = {
        # colocar mais pesos depois
        "comentario_issue": 2
    }

    def __init__(self, repositorio: str, token: str) -> None:
        self.repositorio = repositorio
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }
        self.__mapaUsuarios = MapaUsuarios()

    def executar(self):
        print(f" --- Começando minerador: {self.repositorio}  ---")
        interacoes = []
        interacoes.extend(self.minerarComentariosIssues())
        print(f" --- Fim minerador: {self.repositorio}  ---")
        self.interacoes.extend(interacoes) 

    # Só lista as interações, mais usado pra debug
    def verInteracoes(self):
        for i in self.interacoes:
            print(i)

    # Só lista os usuarios que foram registrados, por causa do mapa ele não registra duplicado
    # por mais que a função seja chamada várias vezes pro mesmo usuário
    # tmb mais usado pra debug
    def verUsuarios(self):
        self.__mapaUsuarios.listarUsuarios()

    def minerar(self, endpoint: str, params: dict = {}) -> list[dict]:
        # minera um endpoint até o final, todas as páginas
        resultado = []
        paginaAtual = 1
        while True:
            print(f"Fazendo request: {self.urlBase}/{endpoint}")
            req = requests.get(
                f"{self.urlBase}/{endpoint}",
                { **params, "per_page": 100, "page": paginaAtual },
                headers=self.headers
            )
            req.raise_for_status() # se a request der ruim para a execução
            data = req.json()
            if not data:
                break # cheguei no final, para o loop
            resultado.extend(data)
            paginaAtual += 1
            time.sleep(0.8) # faz ~4500 req/hora
        return resultado

    def minerarComentariosIssues(self) -> list:
        resultadoMineracao = self.minerar(f"repos/{self.repositorio}/issues/comments")
        interacoes = []
        for comentario in resultadoMineracao:
            quemFez = comentario["user"]["login"]
            autorDaIssue = self.repositorio.split("/")[0]

            # registra os dois usuarios
            self.__mapaUsuarios.buscarOuRegistrar(quemFez)
            self.__mapaUsuarios.buscarOuRegistrar(autorDaIssue)

            # registra a interação
            interacoes.append({ 
                "quemFez": quemFez,
                "alvo": autorDaIssue,
                "peso": self.PESOS["comentario_issue"],
                "tipo": "comentario_issue",
            })
        return interacoes


    def minerarFechamentoIssues(self):
        # TODO
        pass

    def minerarPullRequests(self):
        # TODO
        pass
