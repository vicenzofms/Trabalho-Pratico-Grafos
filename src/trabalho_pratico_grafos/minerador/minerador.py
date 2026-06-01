from dataclasses import dataclass
import time
import requests
from threading import Thread, Lock

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
    __interacoesLock: Lock

    __contadorRequests: int = 0

    __autoresIssuesPRs: dict[str, str]
    
    __pullRequests: list[dict]
    __issues: list[dict]

    PESOS = {
        # colocar mais pesos depois
        "comentario_issue": 2,
        "comentario_pull_request": 2,
        "fechamento_issue": 1,
        "merge_pull": 5,
        "revisao_pull": 4
    }

    def __init__(self, repositorio: str, token: str) -> None:
        self.repositorio = repositorio
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        }
        self.__mapaUsuarios = MapaUsuarios()
        self.__mapaInteracoes = {}
        self.__interacoesLock = Lock()

    def executar(self, sleepTime: float = 0.8):
        inicio = time.time()
        print(f" --- Começando minerador: {self.repositorio}  ---")
        # informações básicas
        thread1 = Thread(target=lambda: self.buscarIssues(sleepTime))
        thread2 = Thread(target=lambda: self.buscarPullRequests(sleepTime))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        self.definirAutoresIssuesPRs()

        # informações específicas
        thread3 = Thread(target=lambda: self.minerarComentariosIssuesPR(sleepTime))
        thread4 = Thread(target=lambda: self.minerarComentariosInlinePullRequest(sleepTime))
        thread5 = Thread(target=lambda: self.minerarFechamentoIssues(sleepTime))
        thread6 = Thread(target=lambda: self.minerarRevisoesPullRequests(sleepTime))
        thread7 = Thread(target=lambda: self.minerarMergePullRequests(sleepTime))

        thread3.start()
        thread4.start()
        thread5.start()
        thread6.start()
        thread7.start()

        thread3.join()
        thread4.join()
        thread5.join()
        thread6.join()
        thread7.join()

        print(f" --- Fim minerador: {self.repositorio}  ---")
        tempoTotal = time.time() - inicio
        print(f" --- Fim minerador: {self.repositorio} ({tempoTotal:.2f}s) ---")

    # Só lista as interações, mais usado pra debug
    def verInteracoes(self):
        for key, value in self.__mapaInteracoes.items():
            print(f"{key}: {value}")

    def quantidadeInteracoes(self):
        return len(self.__mapaInteracoes)

    def quantidadeUsuarios(self):
        return self.__mapaUsuarios.quantidadeDeUsuarios()

    def addInteraction(self, interacao: Interacao):
        with self.__interacoesLock:
            chave = (interacao.quemFez, interacao.alvo, interacao.tipo)
            existente = self.__mapaInteracoes.get(chave)
            if existente:
                existente.peso += interacao.peso
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
            self.__contadorRequests += 1;
            print(f"{description} [{self.__contadorRequests} requests]...")
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

    def buscarPullRequests(self, sleepTime: float) -> None:
        self.__pullRequests = self.minerar(f"repos/{self.repositorio}/pulls", sleepTime, desc="Buscando PRs do repositório...",params={ "state": "all" })

    def buscarIssues(self, sleepTime: float) -> None:
        self.__issues = self.minerar(f"repos/{self.repositorio}/issues", sleepTime, desc="Buscando issues do repositório...",params={ "state": "all" })

    def definirAutoresIssuesPRs(self) -> None:
        self.__autoresIssuesPRs = dict()
        for issue in self.__issues:
            self.__autoresIssuesPRs[str(issue['number'])] = issue['user']['login']
            
        for pr in self.__pullRequests:
            self.__autoresIssuesPRs[str(pr['number'])] = pr['user']['login']

    def minerarComentariosIssuesPR(self, sleepTime) -> None:
        comentarios = self.minerar(f"repos/{self.repositorio}/issues/comments", sleepTime, desc=f"Buscando comentários das issues...")
        
        for comentario in comentarios:
            autorDoComentario = comentario["user"]["login"]
            numeroDaIssue = comentario['issue_url'].split('issues/')[1]

            autorDaIssue = self.__autoresIssuesPRs[numeroDaIssue]
            # caso o comentário seja do autor (seria um loop)
            if (autorDoComentario == autorDaIssue):
                continue

            # registra os envolvidos
            self.__mapaUsuarios.buscarOuRegistrar(autorDoComentario)
            self.__mapaUsuarios.buscarOuRegistrar(autorDaIssue)

            # registra a interação
            i = Interacao(autorDoComentario, autorDaIssue, self.PESOS["comentario_issue"], "comentarios_issue")
            self.addInteraction(i)

    def minerarComentariosInlinePullRequest(self, sleepTime) -> None:
        comentarios = self.minerar(f"repos/{self.repositorio}/pulls/comments", sleepTime, desc=f"Buscando comentários dos pull requests...")

        for comentario in comentarios:
            autorDoComentario = comentario["user"]["login"]
            autorDoPullRequest = self.__autoresIssuesPRs[comentario['pull_request_url'].split('pulls/')[1]]

            if autorDoComentario == autorDoPullRequest:
                continue

            # registra os envolvidos
            self.__mapaUsuarios.buscarOuRegistrar(autorDoComentario)
            self.__mapaUsuarios.buscarOuRegistrar(autorDoPullRequest)

            # registra a interação
            i = Interacao(autorDoComentario, autorDoPullRequest, self.PESOS["comentario_pull_request"], "comentarios_pull_request")
            self.addInteraction(i)

    def minerarFechamentoIssues(self, sleepTime: float) -> None:
        for issue in self.__issues:
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
            i = Interacao(quemFez, autorDaIssue, self.PESOS["fechamento_issue"], "fechamento_issue")
            self.addInteraction(i)


    def minerarRevisoesPullRequests(self, sleepTime: float) -> None:
        for pull in self.__pullRequests:
            statusDoPull = pull["state"]
            autorDoPull = pull["user"]["login"]
            autorDoRepositorio = self.repositorio.split("/")[0]
            # registra os dois usuarios
            self.__mapaUsuarios.buscarOuRegistrar(autorDoPull)
            self.__mapaUsuarios.buscarOuRegistrar(autorDoRepositorio)
            revisoes = self.minerar(f"repos/{self.repositorio}/pulls/{pull['number']}/reviews", sleepTime, desc=f"Buscando revisões do pull {pull['number']}")

            for revisao in revisoes:
                if not revisao.get("user"):  # pula revisões sem usuário
                    continue
                autorDaRevisao = revisao["user"]["login"]
                statusRevisao = revisao["state"]
                if (autorDaRevisao == autorDoRepositorio):
                    continue
                # registra o autor
                self.__mapaUsuarios.buscarOuRegistrar(autorDaRevisao)
                # registra a interação

                i = Interacao(autorDaRevisao, autorDoPull, self.PESOS["revisao_pull"], "revisao_pull")
                self.addInteraction(i)


    def minerarMergePullRequests(self, sleepTime: float) -> None:
        for pull in self.__pullRequests:
            if not pull.get("merged_at"):
                continue
            autorDoPull = pull["user"]["login"]
            number = pull["number"]

            mergeAutor = pull["merged_at"]
            if mergeAutor == autorDoPull:
                continue

            self.__mapaUsuarios.buscarOuRegistrar(autorDoPull)

            i = Interacao(mergeAutor, autorDoPull, self.PESOS["merge_pull"], "merge_pull")
            self.addInteraction(i)


