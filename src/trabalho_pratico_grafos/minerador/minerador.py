from dataclasses import dataclass, asdict
import time
from typing import TypedDict, Literal
import requests  
from threading import Thread, Lock
import json
import os

from trabalho_pratico_grafos.minerador.mapa_usuarios import MapaUsuarios

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

@dataclass
class Interacao:
    quemFez: str
    alvo: str
    peso: int
    tipo: str

@dataclass(frozen=True, slots=True)
class MinerarOpcoes:
    sleepTime: float = 0.8
    desc: str = ""
    cor: Cor = "nenhuma"
    header: dict | None = None

class TokenData(TypedDict):
    token: str
    usos: int

class Minerador:
    urlBase: str = "https://api.github.com"
    repositorio: str

    __mapaUsuarios: MapaUsuarios
    __mapaInteracoes: dict[tuple[str, str, str], Interacao]
    __interacoesLock: Lock

    __contadorGeralInteracoes: int = 0
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

    def __init__(self, repositorio: str, tokens: list[str], usar_cache: bool = False) -> None:
        self.repositorio = repositorio
        self.usar_cache = usar_cache
        if len(tokens) <= 0: raise ValueError("A lista de tokens não pode ser vazia!")

        self.__mapaUsuarios = MapaUsuarios()
        self.__mapaInteracoes = {}
        self.__interacoesLock = Lock()
        self.__requestsContadorLock = Lock()
        self.__tokens = [{"token": t, "usos": 0} for t in tokens]
        self.__tokenLock = Lock()

    def __getHeader(self) -> dict:
        with self.__tokenLock:
            # pega o token com a menor quantidade de usos por referência
            tokenMenosUsado = min(self.__tokens, key=lambda t: t["usos"])
            tokenMenosUsado["usos"] += 1
            return {
                "Authorization": f"Bearer {tokenMenosUsado['token']}",
                "Accept": "application/vnd.github+json"
            }

    def __obterCaminhoCache(self) -> str:
        return os.path.join(os.path.dirname(__file__), "..", "..", "data", f"{self.repositorio.replace('/', '_')}.json")

    def carregarDoCache(self) -> bool:
        caminho = self.__obterCaminhoCache()
        if not os.path.exists(caminho):
            return False
        try:
            with open(caminho, 'r') as f:
                dados = json.load(f)
                self.__mapaInteracoes = {}
                for chave, interacao in dados.items():
                    quem, alvo, tipo = eval(chave)  # reconstrói a tupla
                    self.__mapaUsuarios.buscarOuRegistrar(quem)
                    self.__mapaUsuarios.buscarOuRegistrar(alvo)
                    self.__mapaInteracoes[(quem, alvo, tipo)] = Interacao(**interacao)
                self.__contadorGeralInteracoes = len(self.__mapaInteracoes)
            print(f"Cache carregado de {caminho}")
            return True
        except Exception as e:
            print(f"Erro ao carregar cache: {e}")
            return False

    def salvarNoCache(self) -> None:
        caminho = self.__obterCaminhoCache()
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        try:
            dados = {str(chave): asdict(valor) for chave, valor in self.__mapaInteracoes.items()}
            with open(caminho, 'w') as f:
                json.dump(dados, f, indent=2)
            print(f"Cache salvo em {caminho}")
        except Exception as e:
            print(f"Erro ao salvar cache: {e}")


    def __aumentarContadorRequest(self):
        with self.__requestsContadorLock:
            self.__contadorRequests += 1

    def exibirRelatorioTokens(self):
        print("---= Relatório de Tokens =---")
        for i in range(len(self.__tokens)):
            print(f"Token {i+1}: {self.__tokens[i]['usos']} usos")
        print("---== -----+-----+----- ==---")

    def executar(self, sleepTime: float = 0.8):
        inicio = time.time()
        print(f" --- Começando minerador: {CORES['amarelo']}{self.repositorio}{RESET}  ---")

        if self.usar_cache and self.carregarDoCache():
            tempoTotal = time.time() - inicio
            print(f" --- Fim minerador (cache): {self.repositorio} ({tempoTotal:.2f}s) ---")
            return

        try:
            req = requests.get(f"{self.urlBase}/repos/{self.repositorio}", headers=self.__getHeader())
            if req.status_code == 404:
                print(f"Erro: Repositório '{self.repositorio}' não encontrado.")
                return
            elif req.status_code == 403:
                print(f"Erro 403: Token inválido, expirado ou sem permissões. Configure um novo token via variável de ambiente GITHUB_TOKEN.")
                return
            req.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Erro ao acessar o repositório '{self.repositorio}': {e}")
            return

        # informações básicas
        thread1 = Thread(target=lambda: self.__buscarIssues(sleepTime))
        thread2 = Thread(target=lambda: self.__buscarPullRequests(sleepTime))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        self.__definirAutoresIssuesPRs()

        # informações específicas
        threads = []
        threads.append(Thread(target=lambda: self.__minerarComentariosIssuesPR(sleepTime)))
        threads.append(Thread(target=lambda: self.__minerarComentariosInlinePullRequest(sleepTime)))
        threads.append(Thread(target=self.__minerarFechamentoIssues))
        threads.append(Thread(target=self.__minerarRevisoesPullRequests))
        threads.append(Thread(target=self.__minerarMergePullRequests))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        if self.usar_cache:
            self.salvarNoCache()

        tempoTotal = time.time() - inicio
        print(f" --- Fim minerador: {self.repositorio} ({CORES['amarelo']}{tempoTotal:.2f}s{RESET}) ---")
        print(f" --- Total de requests: {self.__contadorRequests} ---")


    # Só lista as interações, mais usado pra debug
    def verInteracoes(self):
        for key, value in self.__mapaInteracoes.items():
            print(f"{key}: {value}")

    def quantidadeInteracoes(self):
        return len(self.__mapaInteracoes)

    def quantidadeGeralInteracoes(self):
        return self.__contadorGeralInteracoes

    def quantidadeUsuarios(self):
        return self.__mapaUsuarios.quantidadeDeUsuarios()

    def __addInteraction(self, interacao: Interacao):
        with self.__interacoesLock:
            self.__contadorGeralInteracoes += 1
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

    def __minerar(self, endpoint: str, opts: MinerarOpcoes | None = None, params: dict = {}) -> list[dict]:
        opts = opts or MinerarOpcoes()
        # minera um endpoint até o final, todas as páginas
        resultado = []
        paginaAtual = 1

        description = opts.desc
        if (len(description) <= 0):
            description = f"Fazendo request {endpoint}..."

        nextPage = f"{self.urlBase}/{endpoint}"
        ultimoId = None
        headers = opts.header or self.__getHeader()

        while nextPage:
            self.__aumentarContadorRequest()
            print(f"{CORES[opts.cor]}{description}...{RESET}")
            req = requests.get(
                nextPage,
                { **params, "per_page": 100, "page": paginaAtual },
                headers=headers)

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
            time.sleep(opts.sleepTime) # faz ~4500 req/hora se com sleepTime padrão
        return resultado

    def __buscarPullRequests(self, sleepTime: float) -> None:
        self.__pullRequests = self.__minerar(f"repos/{self.repositorio}/pulls",
                                           MinerarOpcoes(sleepTime, "Buscando PRs do repositório...", "ciano"),
                                           params={ "state": "all" })

    def __buscarIssues(self, sleepTime: float) -> None:
        self.__issues = self.__minerar(f"repos/{self.repositorio}/issues", 
                                     MinerarOpcoes(sleepTime, "Buscando issues do repositório...", "azul"),
                                     params={ "state": "all" })

    def __definirAutoresIssuesPRs(self) -> None:
        self.__autoresIssuesPRs = dict()
        for issue in self.__issues:
            self.__autoresIssuesPRs[str(issue['number'])] = issue['user']['login']

        for pr in self.__pullRequests:
            self.__autoresIssuesPRs[str(pr['number'])] = pr['user']['login']

    def __minerarComentariosIssuesPR(self, sleepTime) -> None:
        comentarios = self.__minerar(f"repos/{self.repositorio}/issues/comments", 
                                   MinerarOpcoes(sleepTime, "Buscando comentários das issues...", "amarelo"))

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
            self.__addInteraction(i)

    def __minerarComentariosInlinePullRequest(self, sleepTime) -> None:
        comentarios = self.__minerar(f"repos/{self.repositorio}/pulls/comments", 
                                   MinerarOpcoes(sleepTime, "Buscando comentários dos pull requests...", "azul"))

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
            self.__addInteraction(i)

    def __minerarFechamentoIssues(self) -> None:
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
            self.__addInteraction(i)


    def __minerarRevisoesPullRequests(self) -> None:
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
            thread = Thread(target=self.__processarMergeOrReviewChunk, args=("review", chunk, "ciano",)) # precisa da , no final para tratar como tupla
            thread.start()
            threads.append(thread)

        # espera as 4 threads acabarem
        for thread in threads:
            thread.join()

    def __minerarMergePullRequests(self) -> None:
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
            thread = Thread(target=self.__processarMergeOrReviewChunk, args=("merge", chunk, "verde")) # precisa da , para tratar como tupla
            thread.start()
            threads.append(thread)

        # espera as 4 threads acabarem
        for thread in threads:
            thread.join()

    # chunk = array com números & autores de pull requests
    def __processarMergeOrReviewChunk(self, tipo: str, chunk, cor: Cor):
        headers = self.__getHeader()
        for i in range(len(chunk)):
            if (tipo == 'merge'):
                self.__aumentarContadorRequest()
                print(f"{CORES[cor]}Buscando merge #{chunk[i]['num']}...{RESET}")
                req = requests.get(f"{self.urlBase}/repos/{self.repositorio}/pulls/{chunk[i]['num']}", headers=headers)
                req.raise_for_status()
                pull = req.json()
                time.sleep(0.5)
                if not pull['merged_by'] or pull['merged_by']['login'] ==  chunk[i]['autorDoPull']:
                    continue
                self.__mapaUsuarios.buscarOuRegistrar(pull['merged_by']['login'])
                interacao = Interacao(pull['merged_by']['login'], chunk[i]['autorDoPull'], self.PESOS['merge_pull'], "merge_pull")
                self.__addInteraction(interacao)
                continue

            reviews = self.__minerar(f"repos/{self.repositorio}/pulls/{chunk[i]['num']}/reviews", 
                                   MinerarOpcoes(0.5, f"Buscando reviews do pull {chunk[i]['num']}...", cor, headers))
            self.__mapaUsuarios.buscarOuRegistrar(chunk[i]["autorDoPull"])
            for revisao in reviews:
                if not revisao.get("user") or revisao["user"]["login"] == chunk[i]["autorDoPull"]:  # pula revisões sem usuário & verifica loops
                    continue
                # registra o autor
                self.__mapaUsuarios.buscarOuRegistrar(revisao["user"]["login"])
                # registra a interação
                interacao = Interacao(revisao["user"]["login"], chunk[i]['autorDoPull'], self.PESOS["revisao_pull"], "revisao_pull")
                self.__addInteraction(interacao)
            time.sleep(0.5)
    
    def exportarDados(self) -> dict | None:
        if (self.__mapaUsuarios.quantidadeDeUsuarios() <= 0 or len(self.__mapaInteracoes) <= 0):
            return None
        # retorna cópia dos dados, evitando acesso por referência aos dados internos do minerador
        return {
            "usuarios": self.__mapaUsuarios.exportarUsuarios(),
            "interacoes": [
                {
                    "origem": interacao.quemFez,
                    "destino": interacao.alvo,
                    "peso": interacao.peso,
                    "tipo": interacao.tipo,
                }
                for interacao in self.__mapaInteracoes.values()
            ]
        }

