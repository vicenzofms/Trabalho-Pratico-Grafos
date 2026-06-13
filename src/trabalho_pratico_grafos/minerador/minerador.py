from dataclasses import dataclass, asdict
from typing import TypedDict, Literal
from threading import Thread, Lock
from concurrent.futures import ThreadPoolExecutor, Future
import json
import time
import os

from trabalho_pratico_grafos.minerador.cliente_github import ClienteGithub, ErroRequestObrigatoria, MinerarOpcoes
from trabalho_pratico_grafos.minerador.cores import colorir
from trabalho_pratico_grafos.minerador.mapa_usuarios import MapaUsuarios

@dataclass
class Interacao:
    origem: str
    destino: str
    peso: int
    tipo: str

TipoPendencia = Literal["comentarios_issues", "comentarios_prs", "reviews", "merge"]
@dataclass(frozen=True, slots=True)
class RequestPendente:
    endpoint: str
    tipo: TipoPendencia
    pagina: int | None = None # usadas para pendências de comentários issues/prs
    autorPR: str | None = None # usado para pendências de review/merge
    numeroPR: int | None = None # usado para pendências de review/merge

class Minerador:
    __urlBase: str = "https://api.github.com"
    __clienteGithub: ClienteGithub
    __repositorio: str

    __contadorInteracoesRegistradas: int 

    # Lista de Requests que ficaram pendentes
    __requestsPendentes: list[RequestPendente]

    # Dados do Minerador
    __pullRequests: list[dict]
    __issues: list[dict]
    __autoresIssuesPRs: dict[str, str]
    __mapaUsuarios: MapaUsuarios
    __mapaInteracoes: dict[tuple[str, str, str], Interacao]

    # Locks
    __interacoesLock: Lock
    __pendenciasLock: Lock

    # Usados para montar interações
    PESOS = {
        "comentario_issue": 2,
        "comentario_pull_request": 2,
        "fechamento_issue": 1,
        "merge_pull": 5,
        "revisao_pull": 4
    }

    def __init__(self, repositorio: str, tokens: list[str], usar_cache: bool = False) -> None:
        self.__repositorio = repositorio
        self.usar_cache = usar_cache

        if len(tokens) <= 0: raise ValueError("A lista de tokens não pode ser vazia!")

        # Inicializações
        self.__clienteGithub = ClienteGithub(tokens, self.__urlBase)
        self.__contadorInteracoesRegistradas = 0
        self.__mapaUsuarios = MapaUsuarios()
        self.__mapaInteracoes = {}
        self.__requestsPendentes = []
        self.__interacoesLock = Lock()
        self.__pendenciasLock = Lock()
    
    # --- Cache
    def __obterCaminhoCache(self) -> str:
        return os.path.join(os.path.dirname(__file__), "..", "..", "data", f"{self.__repositorio.replace('/', '_')}.json")

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
                    self.__mapaInteracoes[(quem, alvo, tipo)] = Interacao(origem=quem, destino=alvo, tipo=tipo, peso=interacao["peso"])
                self.__contadorInteracoesRegistradas = len(self.__mapaInteracoes)
            print(colorir(f"Cache carregado de {caminho}", "roxo"))
            return True
        except Exception as e:
            print(colorir(f"Erro ao carregar cache: {e}", "vermelho"))
            return False

    def salvarNoCache(self) -> None:
        caminho = self.__obterCaminhoCache()
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        try:
            dados = {str(chave): asdict(valor) for chave, valor in self.__mapaInteracoes.items()}
            with open(caminho, 'w') as f:
                json.dump(dados, f, indent=2)
            print(colorir(f"Cache salvo em {caminho}", "roxo"))
        except Exception as e:
            print(colorir(f"Erro ao salvar cache: {e}", "vermelho"))
    # --- Fim do Cache

    def executar(self, sleepTime: float = 0.8):
        inicio = time.time()
        print(f"--- Começando minerador: {colorir(self.__repositorio, 'amarelo')} ---")

        # Tentar cache
        if self.usar_cache and self.carregarDoCache():
            tempoTotal = time.time() - inicio
            print(f"--- Fim minerador (cache): {self.__repositorio} ({colorir(f'{tempoTotal:.2f}s', 'roxo')}) ---")
            return

        # Verificar disponibilidade do repo
        try:
            self.__clienteGithub.get(f"repos/{self.__repositorio}", obrigatorio=True, opts=MinerarOpcoes(desc="Verificando repositório...", cor="roxo"))
        except ErroRequestObrigatoria as e:
            print(f"Erro ao acessar o repositório '{self.__repositorio}': {e}")
            return

        # informações básicas
        try:
            # cria 2 threads e joga nelas a busca dos pull requests e issues, um em cada
            with ThreadPoolExecutor(max_workers=2) as executor:
                futureIssues = executor.submit(self.__buscarIssues, sleepTime)
                futurePulls = executor.submit(self.__buscarPullRequests, sleepTime)
                futureIssues.result()
                futurePulls.result()
        except ErroRequestObrigatoria as e:
            # Alguma falhou e elas são obrigatórias, encerrando cedo...
            print(f"Mineração Encerrada com Erro: {e}")
            return

        # mapear os autores no mapa de usuários
        self.__definirAutoresIssuesPRs()

        # informações específicas
        # aqui vamos ter mais uma pool de threads, porém com 8 para dividir todo o resto
        with ThreadPoolExecutor(max_workers=8) as executor:
            futuros: dict[Future, str] = {}
            # Comentários são paginados
            futuros[executor.submit(self.__minerarComentariosIssuesPR, sleepTime)] = "Minerando comentários de issues e PRs"
            futuros[executor.submit(self.__minerarComentariosInlinePullRequest, sleepTime)] = "Minerando comentários de reviews de PRs"
            # esse é rápido, sem requests
            futuros[executor.submit(self.__processarFechamentoIssues)] = "Processando fechamento de issues" 
            # Agora, para cada PR vou criar uma chamada para sua review
            for pr in self.__pullRequests:
                if pr.get("user") is None: continue
                autorPR = pr["user"]["login"]
                numeroPR = pr["number"]
                futuros[executor.submit(self.__minerarReviewsDeUmPR, numeroPR, autorPR)] = f"Minerando reviews do PR #{numeroPR}"
                # e caso ele tenha sido mergeado, crio uma chamada para olhar o merge
                if pr.get("merged_at"):
                    futuros[executor.submit(self.__minerarMergeDeUmPR, numeroPR, autorPR)] = f"Minerando merge do PR #{numeroPR}"
            # Agora espera elas, em caso de erro avisa e continua as outras
            for future, desc in futuros.items():
                try:
                    future.result()
                except Exception as e:
                    print(f"Ocorreu um erro em \"{desc}\": {type(e).__name__} {e}")

        tempoTotal = time.time() - inicio # salva tempo final antes de responder
        if len(self.__requestsPendentes) > 0:
            print(f"Existem {len(self.__requestsPendentes)} requests que não foram concluídas")
            if input("Deseja tentar processá-las novamente? [s/N] -> ").strip().lower() == "s":
                inicio2 = time.time()
                self.__processarPendencias(sleepTime)
                tempoTotal += (time.time() - inicio2)
        if len(self.__requestsPendentes) > 0: # após reprocessar ainda há pendências
            print(colorir("[AVISO]: não foi possível completar todas as requests, EXISTEM dados parciais", 'vermelho'))

        # ao terminar se for para salvar cache é salvo
        if self.usar_cache:
            self.salvarNoCache()

        # Relatório final
        print(f"--- Fim minerador: {colorir(self.__repositorio, 'amarelo')} ({colorir(f'{tempoTotal:.2f}s', 'roxo')}) ---")
        print(f"--- Total de requests: {colorir(str(self.__clienteGithub.getQuantidadeRequests()), 'amarelo')} ---")
        if len(self.__requestsPendentes) > 0: print(colorir(f"--- {len(self.__requestsPendentes)} requests perdidas ---", 'vermelho'))
        print(f"--- {colorir(str(self.quantidadeUsuarios()), 'amarelo')} usuários | {colorir(str(self.quantidadeInteracoes()), 'amarelo')} interações distintas ---")


    # Só lista as interações, mais usado pra debug
    def exibirInteracoes(self):
        for key, value in self.__mapaInteracoes.items():
            print(f"{key}: {value}")

    def quantidadeInteracoes(self):
        return len(self.__mapaInteracoes)

    def quantidadeInteracoesRegistradas(self):
        return self.__contadorInteracoesRegistradas

    def quantidadeUsuarios(self):
        return self.__mapaUsuarios.quantidadeDeUsuarios()

    def __adicionarInteracao(self, interacao: Interacao):
        with self.__interacoesLock:
            self.__contadorInteracoesRegistradas += 1
            chave = (interacao.origem, interacao.destino, interacao.tipo)
            existente = self.__mapaInteracoes.get(chave)
            if existente:
                existente.peso += interacao.peso
                return
            self.__mapaInteracoes[chave] = interacao

    def __adicionarPendencia(self, pendencia: RequestPendente):
        with self.__pendenciasLock:
            self.__requestsPendentes.append(pendencia)

    # Só lista os usuarios que foram registrados, por causa do mapa ele não registra duplicado
    # por mais que a função seja chamada várias vezes pro mesmo usuário
    # tmb mais usado pra debug
    def exibirUsuarios(self):
        self.__mapaUsuarios.listarUsuarios()

    def exibirRelatorioTokens(self):
        self.__clienteGithub.exibirRelatorioTokens()

    # Buscas de Informações Primárias
    def __buscarPullRequests(self, sleepTime: float) -> None:
        self.__pullRequests = self.__clienteGithub.getPaginadoCursor(f"repos/{self.__repositorio}/pulls",
                                           opts=MinerarOpcoes(sleepTime, "Buscando PRs do repositório...", "ciano"),
                                           params={ "state": "all" },
                                           obrigatorio=True)

    def __buscarIssues(self, sleepTime: float) -> None:
        self.__issues = self.__clienteGithub.getPaginadoCursor(f"repos/{self.__repositorio}/issues", 
                                     opts=MinerarOpcoes(sleepTime, "Buscando issues do repositório...", "azul"),
                                     params={ "state": "all" },
                                     obrigatorio=True)

    def __definirAutoresIssuesPRs(self) -> None:
        self.__autoresIssuesPRs = dict()
        for issue in self.__issues:
            if issue.get("user") is None: continue
            self.__autoresIssuesPRs[str(issue['number'])] = issue['user']['login']

        for pr in self.__pullRequests:
            if pr.get("user") is None: continue
            self.__autoresIssuesPRs[str(pr['number'])] = pr['user']['login']

    # Funções de mineração
    # Usam o ClienteGithub para fazer todas as requests
    # depois de conseguir os dados jogam para as funções de processamento
    # lá os dados são tratados para virar interações
    def __minerarComentariosIssuesPR(self, sleepTime) -> None:
        endpoint = f"repos/{self.__repositorio}/issues/comments"
        resultado = self.__clienteGithub.getPaginado(endpoint, 
                                   opts=MinerarOpcoes(sleepTime, "Buscando comentários das issues...", "amarelo"))
        for pagina in resultado.paginasComFalha:
            self.__adicionarPendencia(RequestPendente(endpoint, "comentarios_issues", pagina=pagina))
        for comentario in resultado.itens:
            self.__processarComentarioIssue(comentario)   

    def __minerarComentariosInlinePullRequest(self, sleepTime) -> None:
        endpoint = f"repos/{self.__repositorio}/pulls/comments"
        resultado = self.__clienteGithub.getPaginado(endpoint, 
                                   opts=MinerarOpcoes(sleepTime, "Buscando comentários dos pull requests...", "azul"))
        for pagina in resultado.paginasComFalha:
            self.__adicionarPendencia(RequestPendente(endpoint, "comentarios_prs", pagina=pagina))
        for comentario in resultado.itens:
            self.__processarComentarioInlinePR(comentario)
            
    def __minerarMergeDeUmPR(self, numeroPR: int, autorPR: str):
        endpoint = f"repos/{self.__repositorio}/pulls/{numeroPR}"
        pull = self.__clienteGithub.get(endpoint, opts=MinerarOpcoes(desc=f"Buscando merge #{numeroPR}...", cor='verde'))
        time.sleep(0.5)
        if pull is None:
            self.__adicionarPendencia(RequestPendente(endpoint, 'merge', autorPR=autorPR, numeroPR=numeroPR))
            return               
        self.__processarMerge(pull, autorPR)

    def __minerarReviewsDeUmPR(self, numeroPR: int, autorPR: str):
        endpoint = f"repos/{self.__repositorio}/pulls/{numeroPR}/reviews"
        resultado = self.__clienteGithub.getPaginado(endpoint, 
                        opts=MinerarOpcoes(0.5, f"Buscando reviews do pull {numeroPR}...", cor="ciano"))
        self.__mapaUsuarios.buscarOuRegistrar(autorPR)
        if len(resultado.paginasComFalha) > 0:
            self.__adicionarPendencia(RequestPendente(endpoint, "reviews", autorPR=autorPR, numeroPR=numeroPR))
            # não processa as páginas, refaz aquele PR depois
            return
        for review in resultado.itens:
            self.__processarReview(review, autorPR)
        time.sleep(0.5)

    # Não faz requests, apenas roda pelas issues e mapeia
    def __processarFechamentoIssues(self) -> None:
        for issue in self.__issues:
            if not issue.get("closed_by") or issue.get("pull_request") or issue.get('user') is None:
                continue

            quemFez = issue["closed_by"]["login"]
            autorDaIssue = issue["user"]["login"]

            if (quemFez == autorDaIssue):
                continue;

            # registra os dois usuarios
            self.__mapaUsuarios.buscarOuRegistrar(quemFez)
            self.__mapaUsuarios.buscarOuRegistrar(autorDaIssue)

            # registra a interação
            i = Interacao(quemFez, autorDaIssue, self.PESOS["fechamento_issue"], "fechamento_issue")
            self.__adicionarInteracao(i)

    # Processadores
    # Responsáveis por converter dados em interações
    def __processarComentarioIssue(self, comentario: dict):
        # proteger de comentários fantasma
        if comentario.get("user") is None: return

        autorDoComentario = comentario["user"]["login"]
        numeroDaIssue = comentario['issue_url'].split('issues/')[1]
        autorDaIssue = self.__autoresIssuesPRs.get(numeroDaIssue)

        # Comentário em issue fantasma
        if autorDaIssue is None:
            return

        # caso o comentário seja do autor (seria um loop)
        if (autorDoComentario == autorDaIssue):
            return

        # registra os envolvidos
        self.__mapaUsuarios.buscarOuRegistrar(autorDoComentario)
        self.__mapaUsuarios.buscarOuRegistrar(autorDaIssue)

        # registra a interação
        i = Interacao(autorDoComentario, autorDaIssue, self.PESOS["comentario_issue"], "comentario_issue")
        self.__adicionarInteracao(i)

    def __processarComentarioInlinePR(self, comentario: dict):
        # proteger de comentários fantasma
        if comentario.get("user") is None: return

        autorDoComentario = comentario["user"]["login"]
        autorDoPullRequest = self.__autoresIssuesPRs.get(comentario['pull_request_url'].split('pulls/')[1])

        # Comentário em PR fantasma
        if autorDoPullRequest is None:
            return

        # caso o comentário seja do autor (seria um loop)
        if autorDoComentario == autorDoPullRequest:
            return

        # registra os envolvidos
        self.__mapaUsuarios.buscarOuRegistrar(autorDoComentario)
        self.__mapaUsuarios.buscarOuRegistrar(autorDoPullRequest)

        # registra a interação
        i = Interacao(autorDoComentario, autorDoPullRequest, self.PESOS["comentario_pull_request"], "comentario_pull_request")
        self.__adicionarInteracao(i)

    def __processarReview(self, review: dict, autorPR):
        if not review.get("user") or review["user"]["login"] == autorPR:  # pula revisões sem usuário & verifica loops
            return
        # registra o autor
        self.__mapaUsuarios.buscarOuRegistrar(review["user"]["login"])
        # registra a interação
        interacao = Interacao(review["user"]["login"], autorPR, self.PESOS["revisao_pull"], "revisao_pull")
        self.__adicionarInteracao(interacao)

    def __processarMerge(self, pull: dict, autorPR):
        if not pull.get('merged_by') or pull['merged_by']['login'] == autorPR: # pula merges sem usuário & verifica loops
            return
        # registra quem fez o merge
        self.__mapaUsuarios.buscarOuRegistrar(pull['merged_by']['login'])
        # registra a interação
        interacao = Interacao(pull['merged_by']['login'], autorPR, self.PESOS['merge_pull'], "merge_pull")
        self.__adicionarInteracao(interacao)

    # Processa as requests que ficaram pendentes
    def __processarPendencias(self, sleepTime: float):
        # array para caso ainda sobrem pendências
        # não serão processadas, já houveram muitos retries para ela
        # sendo assim, ocorre uma rodada, quem falhar novamente vira aviso
        novasPendencias = []
        for pendencia in self.__requestsPendentes:
            # garante o fluxo adequado para cada pendência
            match pendencia.tipo:
                case "reviews":
                    resultado = self.__clienteGithub.getPaginado(pendencia.endpoint, opts=MinerarOpcoes(0.5, f"Buscando reviews do pull {pendencia.numeroPR}...", cor="ciano"))
                    if len(resultado.paginasComFalha) > 0:
                        novasPendencias.append(pendencia)
                        continue
                    for review in resultado.itens:
                        self.__processarReview(review, pendencia.autorPR)
                case "merge":
                    resultado = self.__clienteGithub.get(pendencia.endpoint, opts=MinerarOpcoes(desc=f"Buscando merge #{pendencia.numeroPR}...", cor='verde'))
                    if resultado is None:
                        novasPendencias.append(pendencia)
                        continue
                    self.__processarMerge(resultado, pendencia.autorPR)
                case "comentarios_issues":
                    resultado = self.__clienteGithub.get(
                        pendencia.endpoint, 
                        params={"page": pendencia.pagina, "per_page": 100},
                        opts=MinerarOpcoes(desc="Buscando comentários das issues...", cor="amarelo"))
                    if resultado is None:
                        novasPendencias.append(pendencia)
                        continue
                    for comentario in resultado:
                        self.__processarComentarioIssue(comentario)
                case "comentarios_prs":
                    resultado = self.__clienteGithub.get(
                        pendencia.endpoint, 
                        params={"page": pendencia.pagina, "per_page": 100},
                        opts=MinerarOpcoes(desc="Buscando comentários dos pull requests...", cor="azul"))
                    if resultado is None:
                        novasPendencias.append(pendencia)
                        continue
                    for comentario in resultado:
                        self.__processarComentarioInlinePR(comentario)
            time.sleep(sleepTime)
        # Atualiza o array final
        self.__requestsPendentes = novasPendencias

    # Exporta dados que serão utilizados pelo builder
    def exportarDados(self) -> dict | None:
        if (self.__mapaUsuarios.quantidadeDeUsuarios() <= 0 or len(self.__mapaInteracoes) <= 0):
            return None
        # retorna cópia dos dados, evitando acesso por referência aos dados internos do minerador
        return {
            "usuarios": self.__mapaUsuarios.exportarUsuarios(),
            "interacoes": [
                {
                    "origem": interacao.origem,
                    "destino": interacao.destino,
                    "peso": interacao.peso,
                    "tipo": interacao.tipo,
                }
                for interacao in self.__mapaInteracoes.values()
            ]
        }

