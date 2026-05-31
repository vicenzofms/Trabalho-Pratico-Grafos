from dataclasses import dataclass
import time
import requests
from threading import Thread

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

    __mapaUsuarios: MapaUsuarios
    __mapaInteracoes: dict[tuple[str, str, str], Interacao]

    PESOS = {
        # colocar mais pesos depois
        "comentario_issue": 2,
        "fechamento_issue": 1
    }

    def __init__(self, repositorio: str, token: str) -> None:
        self.repositorio = repositorio
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }
        self.__mapaUsuarios = MapaUsuarios()
        self.__mapaInteracoes = {}

    def executar(self, sleepTime: float = 0.8):
        print(f" --- Começando minerador: {self.repositorio}  ---")
        thread1 = Thread(target=lambda: self.minerarComentariosIssues(sleepTime))
        thread2 = Thread(target=lambda: self.minerarFechamentoIssues(sleepTime))

        thread1.start()
        thread2.start()

        # esperar as threads acabarem
        thread1.join()
        thread2.join()
        print(f" --- Fim minerador: {self.repositorio}  ---")

    # Só lista as interações, mais usado pra debug
    def verInteracoes(self):
        for key, value in self.__mapaInteracoes.items():
            print(f"{key}: {value}")

    def quantidadeInteracoes(self):
        return len(self.__mapaInteracoes)

    def quantidadeUsuarios(self):
        return self.__mapaUsuarios.quantidadeDeUsuarios()

    def addInteraction(self, interacao: Interacao):
        chave = (interacao["quemFez"], interacao["alvo"], interacao["tipo"])
        existente = self.__mapaInteracoes.get(chave)
        if existente:
            existente["peso"] += interacao["peso"]
            return
        self.__mapaInteracoes[chave] = interacao

    # Só lista os usuarios que foram registrados, por causa do mapa ele não registra duplicado
    # por mais que a função seja chamada várias vezes pro mesmo usuário
    # tmb mais usado pra debug
    def verUsuarios(self):
        self.__mapaUsuarios.listarUsuarios()

    def minerar(self, endpoint: str, sleepTime: float, desc: str = "", params: dict = {}) -> list[dict]:
        # minera um endpoint até o final, todas as páginas
        resultado = []
        paginaAtual = 1

        description = desc
        if (len(desc) <= 0):
            description = f"Fazendo request {endpoint}..."

        nextPage = f"{self.urlBase}/{endpoint}"
        ultimoId = None

        while nextPage:
            print(f"{description} [{paginaAtual} requests]...")
            req = requests.get(
                nextPage,
                { **params, "per_page": 100, "page": paginaAtual },
                headers=self.headers
            )

            req.raise_for_status() # se a request der ruim para a execução
            data = req.json()
            if (not data):
                break # cheguei no final, para o loop

            idAtual = data[-1]["id"]

            if idAtual == ultimoId:
                break

            ultimoId = idAtual

            nextPage = req.links.get("next", {}).get("url")

            resultado.extend(data)
            if (len(data) < 100): # estou na última página
                return resultado

            # ainda faltam páginas
            paginaAtual += 1
            time.sleep(sleepTime) # faz ~4500 req/hora
        return resultado

    def minerarComentariosIssues(self, sleepTime) -> None:
        issues = []
        comentarios = []

        thread1 = Thread(
            target=lambda: issues.extend(self.minerar(f"repos/{self.repositorio}/issues", sleepTime, desc="Buscando issues do repositório...",params={ "state": "all" }))
        )
        thread2 = Thread(
            target=lambda: comentarios.extend(self.minerar(f"repos/{self.repositorio}/issues/comments", sleepTime, desc=f"Buscando comentários das issues..."))
        )

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        autoresIssues = dict()
        for issue in issues:
            autoresIssues[str(issue['number'])] = issue['user']['login']

        for comentario in comentarios:
            autorDoComentario = comentario["user"]["login"]
            numeroDaIssue = comentario['issue_url'].split('issues/')[1]

            # apenas se a issue foi registrada pela API /issues
            if (not numeroDaIssue in autoresIssues):
                continue

            autorDaIssue = autoresIssues[numeroDaIssue]
            # caso o comentário seja do autor (seria um loop)
            if (autorDoComentario == autorDaIssue):
                continue

            # registra os envolvidos
            self.__mapaUsuarios.buscarOuRegistrar(autorDoComentario)
            self.__mapaUsuarios.buscarOuRegistrar(autorDaIssue)

            # registra a interação
            self.addInteraction({
                "quemFez": autorDoComentario,
                "alvo": autorDaIssue,
                "peso": self.PESOS["comentario_issue"],
                "tipo": "comentario_issue",
            })

    def minerarFechamentoIssues(self, sleepTime: float) -> None:
        resultadoMineracao = self.minerar(f"repos/{self.repositorio}/issues", sleepTime, desc="Buscando fechamento de issues...", params={ "state": "closed" })
        for issue in resultadoMineracao:
            if not issue["closed_by"]:
                continue;

            quemFez = issue["closed_by"]["login"]
            autorDaIssue = issue["user"]["login"]

            if (quemFez == autorDaIssue):
                continue;

            # registra os dois usuarios
            self.__mapaUsuarios.buscarOuRegistrar(quemFez)
            self.__mapaUsuarios.buscarOuRegistrar(autorDaIssue)

            # registra a interação
            self.addInteraction({
                "quemFez": quemFez,
                "alvo": autorDaIssue,
                "peso": self.PESOS["fechamento_issue"],
                "tipo": "fechamento_issue",
            })

    def minerarPullRequests(self, sleepTime: float):
        # TODO
        pass
