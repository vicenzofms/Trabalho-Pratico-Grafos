from dataclasses import dataclass
import time
from typing import TypedDict
import requests
from threading import Thread, Lock

from trabalho_pratico_grafos.minerador.mapa_usuarios import MapaUsuarios

@dataclass
class Interacao:
    quemFez: str
    alvo: str
    peso: int
    tipo: str

class TokenData(TypedDict):
    token: str
    usos: int

class Minerador:
    urlBase: str = "https://api.github.com"
    repositorio: str

    __mapaUsuarios: MapaUsuarios
    mapaInteracoes: dict[tuple[str, str, str], Interacao]
    __interacoesLock: Lock

    contadorGeralInteracoes: int = 0
    __contadorRequests: int = 0
    __requestsContadorLock: Lock

    __autoresIssuesPRs: dict[str, str]

    __pullRequests: list[dict]
    __issues: list[dict]

    __tokens: list[TokenData]
    __tokenLock: Lock

    PESOS = {
        # colocar mais pesos depois
        "comentario_issue": 2,
        "comentario_pull_request": 2,
        "fechamento_issue": 1,
        "merge_pull": 5,
        "revisao_pull": 4
    }

    def __init__(self, repositorio: str, tokens: list[str]) -> None:
        self.repositorio = repositorio
        if len(tokens) <= 0: raise ValueError("A lista de tokens não pode ser vazia!")

        self.__mapaUsuarios = MapaUsuarios()
        self.mapaInteracoes = {}
        self.__interacoesLock = Lock()
        self.__requestsContadorLock = Lock()
        self.__tokens = [{"token": t, "usos": 0} for t in tokens]
        self.__tokenLock = Lock()

    def getHeader(self) -> dict:
        with self.__tokenLock:
            # pega o token com a menor quantidade de usos por referência
            tokenMenosUsado = min(self.__tokens, key=lambda t: t["usos"]) 
            tokenMenosUsado["usos"] += 1
            return {
                "Authorization": f"token {tokenMenosUsado['token']}",
                "Accept": "application/vnd.github+json"
            }


    def aumentarContadorRequest(self):
        with self.__requestsContadorLock:
            self.__contadorRequests += 1

    def exibirRelatorioTokens(self):
        print("---= Relatório de Tokens =---")
        for i in range(len(self.__tokens)):
            print(f"Token {i+1}: {self.__tokens[i]['usos']} usos")
        print("---== -----+-----+----- ==---")

    def executar(self, sleepTime: float = 0.8):
        inicio = time.time()
        print(f" --- Começando minerador: {self.repositorio}  ---")

        try:
            req = requests.get(f"{self.urlBase}/repos/{self.repositorio}", headers=self.getHeader())
            if req.status_code == 404:
                print(f"Erro: Repositório '{self.repositorio}' não encontrado.")
                return
            req.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar o repositório '{self.repositorio}': {e}")
            return

        # informações básicas
        thread1 = Thread(target=lambda: self.buscarIssues(sleepTime))
        thread2 = Thread(target=lambda: self.buscarPullRequests(sleepTime))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        self.definirAutoresIssuesPRs()

        # informações específicas
        threads = []
        threads.append(Thread(target=lambda: self.minerarComentariosIssuesPR(sleepTime)))
        threads.append(Thread(target=lambda: self.minerarComentariosInlinePullRequest(sleepTime)))
        threads.append(Thread(target=lambda: self.minerarFechamentoIssues(sleepTime)))
        threads.append(Thread(target=self.minerarRevisoesPullRequests))
        threads.append(Thread(target=self.minerarMergePullRequests))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        tempoTotal = time.time() - inicio
        print(f" --- Fim minerador: {self.repositorio} ({tempoTotal:.2f}s) ---")
        print(f" --- Total de requests: {self.__contadorRequests} ---")

    # Só lista as interações, mais usado pra debug
    def verInteracoes(self):
        for key, value in self.mapaInteracoes.items():
            print(f"{key}: {value}")

    def quantidadeInteracoes(self):
        return len(self.mapaInteracoes)

    def quantidadeUsuarios(self):
        return self.__mapaUsuarios.quantidadeDeUsuarios()

    def addInteraction(self, interacao: Interacao):
        with self.__interacoesLock:
            self.contadorGeralInteracoes += 1
            chave = (interacao.quemFez, interacao.alvo, interacao.tipo)
            existente = self.mapaInteracoes.get(chave)
            if existente:
                existente.peso += interacao.peso
                return
            self.mapaInteracoes[chave] = interacao

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
        headers = self.getHeader()

        while nextPage:
            self.aumentarContadorRequest()
            print(f"{description}...")
            req = requests.get(
                nextPage,
                { **params, "per_page": 100, "page": paginaAtual },
                headers=headers
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

            # Comentário em issue fantasma
            if not numeroDaIssue in self.__autoresIssuesPRs:
                continue

            autorDaIssue = self.__autoresIssuesPRs[numeroDaIssue]
            # caso o comentário seja do autor (seria um loop)
            if (autorDoComentario == autorDaIssue):
                continue

            # registra os envolvidos
            self.__mapaUsuarios.buscarOuRegistrar(autorDoComentario)
            self.__mapaUsuarios.buscarOuRegistrar(autorDaIssue)

            # registra a interação
            i = Interacao(autorDoComentario, autorDaIssue, self.PESOS["comentario_issue"], "comentario_issue")
            self.addInteraction(i)

    def minerarComentariosInlinePullRequest(self, sleepTime) -> None:
        comentarios = self.minerar(f"repos/{self.repositorio}/pulls/comments", sleepTime, desc=f"Buscando comentários dos pull requests...")

        for comentario in comentarios:
            autorDoComentario = comentario["user"]["login"]

            # Comentário em PR fantasma
            if not comentario["pull_request_url"].split("pulls/")[1] in self.__autoresIssuesPRs:
                continue

            autorDoPullRequest = self.__autoresIssuesPRs[comentario['pull_request_url'].split('pulls/')[1]]

            # caso o comentário seja do autor (seria um loop)
            if autorDoComentario == autorDoPullRequest:
                continue

            # registra os envolvidos
            self.__mapaUsuarios.buscarOuRegistrar(autorDoComentario)
            self.__mapaUsuarios.buscarOuRegistrar(autorDoPullRequest)

            # registra a interação
            i = Interacao(autorDoComentario, autorDoPullRequest, self.PESOS["comentario_pull_request"], "comentario_pull_request")
            self.addInteraction(i)

    def minerarFechamentoIssues(self, sleepTime: float) -> None:
        for issue in self.__issues:
            if not issue["closed_by"] or issue.get("pull_request"):
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


    def minerarRevisoesPullRequests(self) -> None:
        # dividir o array de prs em 4 subarrays
        qntd = len(self.__pullRequests)
        qntdPorGrupo, sobra = divmod(qntd, 4)
        chunks = []
        inicio = 0
        for i in range(4):
            fim = inicio + qntdPorGrupo + (1 if i < sobra else 0) # ternário para que caso seja um grupo que tem a mais adicionar 1 item
            chunks.append([ {"num": pr['number'], "autorDoPull": pr['user']['login']} for pr in self.__pullRequests[inicio:fim] ])
            inicio = fim

        # cria as threads
        threads = []
        for chunk in chunks:
            thread = Thread(target=self.processarMergeOrReviewChunk, args=("review", chunk,)) # precisa da , no final para tratar como tupla
            thread.start()
            threads.append(thread)

        # espera as 4 threads acabarem
        for thread in threads:
            thread.join()

    def minerarMergePullRequests(self) -> None:
        merges = []
        for pull in self.__pullRequests:
            if not pull.get("merged_at"):
                continue
            autorDoPull = pull["user"]["login"]
            self.__mapaUsuarios.buscarOuRegistrar(autorDoPull)
            merges.append({"autorDoPull": autorDoPull, "num": pull["number"]})

        # dividir o array de merges em 4 subarrays
        qntd = len(merges)
        qntdPorGrupo, sobra = divmod(qntd, 4)
        chunks = []
        inicio = 0
        for i in range(4):
            fim = inicio + qntdPorGrupo + (1 if i < sobra else 0) # ternário para que caso seja um grupo que tem a mais adicionar 1 item
            chunks.append(merges[inicio:fim])
            inicio = fim

        # cria as threads
        threads = []
        for chunk in chunks:
            thread = Thread(target=self.processarMergeOrReviewChunk, args=("merge", chunk,)) # precisa da , para tratar como tupla
            thread.start()
            threads.append(thread)

        # espera as 4 threads acabarem
        for thread in threads:
            thread.join()

    # chunk = array com números & autores de pull requests
    def processarMergeOrReviewChunk(self, tipo: str, chunk):
        headers = self.getHeader()
        for i in range(len(chunk)):
            if (tipo == 'merge'):
                self.aumentarContadorRequest()
                print(f"Buscando merge #{chunk[i]['num']}...")
                req = requests.get(f"{self.urlBase}/repos/{self.repositorio}/pulls/{chunk[i]['num']}", headers=headers)
                req.raise_for_status()
                pull = req.json()
                time.sleep(0.5)
                if not pull['merged_by'] or pull['merged_by']['login'] ==  chunk[i]['autorDoPull']:
                    continue
                self.__mapaUsuarios.buscarOuRegistrar(pull['merged_by']['login'])
                interacao = Interacao(pull['merged_by']['login'], chunk[i]['autorDoPull'], self.PESOS['merge_pull'], "merge_pull")
                self.addInteraction(interacao)
                continue

            reviews = self.minerar(f"repos/{self.repositorio}/pulls/{chunk[i]['num']}/reviews", 0.5, f"Buscando reviews do pull {chunk[i]['num']}...")
            self.__mapaUsuarios.buscarOuRegistrar(chunk[i]["autorDoPull"])
            for revisao in reviews:
                if not revisao.get("user") or revisao["user"]["login"] == chunk[i]["autorDoPull"]:  # pula revisões sem usuário & verifica loops
                    continue
                # registra o autor
                self.__mapaUsuarios.buscarOuRegistrar(revisao["user"]["login"])
                # registra a interação
                interacao = Interacao(revisao["user"]["login"], chunk[i]['autorDoPull'], self.PESOS["revisao_pull"], "revisao_pull")
                self.addInteraction(interacao)
            time.sleep(0.5)

