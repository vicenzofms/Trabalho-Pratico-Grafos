from dataclasses import dataclass
from threading import Lock
import time
from .cores import Cor, colorir

import requests

@dataclass(frozen=True, slots=True)
class MinerarOpcoes:
    sleepTime: float = 0.8
    desc: str = ""
    cor: Cor = "nenhuma"

@dataclass(frozen=True, slots=True)
class ResultadoPaginado:
    itens: list[dict]
    paginasComFalha: list[int]

@dataclass(slots=True)
class TokenEstado:
    token: str
    usos: int = 0
    invalido: bool = False   
    bloqueadoAte: float = 0.0

class ErroRequestObrigatoria(Exception):
    """Erro em uma request obrigatória! Abortando mineração..."""

class ClienteGithub:
    # Ao falhar em caso de REDE (timeout), são feitas 3 tentativas
    # Ele espera o fator * numeroDaTentativa segundos para a próxima
    __FATOR_SLEEP_FALHA = 7.5

    __tokens: list[TokenEstado]
    __urlBase: str
    __quantidadeRequests: int

    # Locks
    __contadorRequestsLock: Lock
    __tokenLock: Lock

    def __init__(self, tokens: list[str], urlBase: str = "https://api.github.com") -> None:
        # Inicializações
        self.__tokens = [
            TokenEstado(t)
            for t in tokens
        ]
        self.__urlBase = urlBase
        self.__quantidadeRequests = 0
        self.__contadorRequestsLock = Lock()
        self.__tokenLock = Lock()

    # Retorna a respose, usada em get, getPaginado e getPaginadoCursor pelo param page ou por paginação via link/cursor
    def __getResponse(self, url: str, params: dict | None = None, obrigatorio: bool = False, opts: MinerarOpcoes | None = None) -> requests.Response | None:
        tentativas = 0
        while True:
            token = self.__getToken() # pega um token pouco utilizado
            header = self.__getHeader(token.token) # cria um header com o token
            try:
                with self.__contadorRequestsLock:
                    self.__quantidadeRequests += 1

                if opts is not None:
                    print(colorir(opts.desc, opts.cor))

                # faz a request de fato
                req = requests.get(url, params={**(params or {})}, headers=header, timeout=(10, 30))
                
                # trata possíveis resultados
                match req.status_code:
                    case 200: # sucesso
                        return req
                    case 401: # token inválido, marca ele como ruim pra sempre
                        with self.__tokenLock:
                            token.invalido = True
                            continue
                    case 403 | 429: # pode ter dado vários problemas com o rate-limit
                        # acabou o limite do token
                        if req.headers.get("X-RateLimit-Remaining") == "0": # volta como string
                            with self.__tokenLock:
                                token.bloqueadoAte = float(req.headers["X-RateLimit-Reset"]) # marca quando ele libera
                        elif req.headers.get("Retry-After"): # acontece quando atinge o secondary rate-limit
                            with self.__tokenLock:
                                token.bloqueadoAte = time.time() + float(req.headers["Retry-After"]) # marca liberação
                        else:
                            # deu ruim, possivelmente não é culpa do token
                            return self.__requestFalha("Erro 403 desconhecido!", obrigatorio) 
                    case 422:
                        # deu muito ruim, paginação não prevista precisa de cursor
                        # atualmente apenas /issues e /pulls usam cursor
                        body = req.json().get("message", "")
                        if "cursor" in body:
                            return self.__requestFalha(f"{url} excedeu o limite de paginação por página (migrar para cursor)", obrigatorio)
                        return self.__requestFalha(f"Erro HTTP 422 em {url}!", obrigatorio)
                    case _:
                        # qualquer outro erro
                        return self.__requestFalha(f"Erro HTTP {req.status_code} em {url}!", obrigatorio)

            except (requests.Timeout, requests.ConnectionError): # trata falhas de rede
                # cuida das tentativas, até 3, depois falha
                tentativas += 1
                if tentativas >= 3:
                    return self.__requestFalha("Erro de rede/timeout!", obrigatorio)
                time.sleep(tentativas * self.__FATOR_SLEEP_FALHA)

    # get singular
    def get(self, endpoint: str, params: dict | None = None, obrigatorio: bool = False, opts: MinerarOpcoes | None = None):
        res = self.__getResponse(f"{self.__urlBase}/{endpoint}", params, obrigatorio, opts)
        return res.json() if res is not None else None
        
    # get com paginação
    def getPaginado(self, endpoint: str, params: dict | None = None, opts: MinerarOpcoes | None = None, obrigatorio: bool = False) -> ResultadoPaginado:
        opts = opts or MinerarOpcoes()
        desc = opts.desc or f"Fazendo request {endpoint}..."
        pagina = 1
        falhasConsecutivas = 0
        dados = []
        falhas = [] # guarda as páginas que deram ruim para retornar para o minerador como pendência

        while True:
            print(colorir(f"{desc} (página {pagina})", opts.cor))
            data = self.get(endpoint, params={**(params or {}), "per_page":100, "page": pagina}, obrigatorio=obrigatorio)
            if data is None:
                # registra a falha
                # após 3 consecutivas desiste do endpoint (problema externo)
                falhas.append(pagina)
                falhasConsecutivas += 1
                if falhasConsecutivas >= 3:
                    print("Ocorreu um erro no endpoint! Desistindo")
                    break
                pagina += 1 # pula a página que deu problema, pendencia tratada depois pelo minerador
                continue

            # deu certo
            falhasConsecutivas = 0 # reseta
            dados.extend(data)

            if len(data) < 100: #cheguei na ultima página pq tenho menos de 100 itens
                break

            pagina += 1
            time.sleep(opts.sleepTime)

        return ResultadoPaginado(dados, falhas)

    # paginação utilizando o link/cursor
    def getPaginadoCursor(self, endpoint: str, params=None, opts=None, obrigatorio=False) -> list[dict]:
        url = f"{self.__urlBase}/{endpoint}"
        params = {**(params or {}), "per_page": 100}
        dados = []
        while url: # roda até acabar os links
            res = self.__getResponse(url, params, obrigatorio, opts)
            if res is None:
                break
            dados.extend(res.json())
            url = res.links.get("next", {}).get("url") # próxima página
            params = None
            time.sleep(opts.sleepTime if opts else 0.8)
        return dados

    def __getToken(self) -> TokenEstado:
        # precisa por causa da espera
        while True:
            with self.__tokenLock:
                # pega o token com a menor quantidade de usos 
                tokensValidos = list(filter(lambda t: not t.invalido, self.__tokens))
                if len(tokensValidos) <= 0: # it's over aqui
                    raise RuntimeError("Todos os tokens estão inválidos!")

                # filtra pra achar tokens que não tão bloqueados
                tokensDisponiveis = list(filter(lambda t: t.bloqueadoAte <= time.time(), tokensValidos))
                if len(tokensDisponiveis) > 0:
                    # achei um token bom
                    tokenMenosUsado = min(tokensDisponiveis, key=lambda t: t.usos)
                    tokenMenosUsado.usos += 1
                    return tokenMenosUsado

                # todos os tokens são válidos, porém bloqueados
                # vou precisar esperar o minimo possível para que 1 deles libere
                proximoReset = min(t.bloqueadoAte for t in tokensValidos)

            # precisa esperar fora do lock, por isso o while True, e para tentar novamente após a espera
            tempoDeEspera = proximoReset - time.time() + 3 # folga de 3s
            if tempoDeEspera > 900: # mais de 15 minutos n dá pra esperar
                raise RuntimeError("Todos os tokens têm tempo de espera > 15min!")
            if tempoDeEspera > 0: # espera bacana
                print(f"Tokens em rate-limit. Aguardando {tempoDeEspera:.1f}s...")
                time.sleep(tempoDeEspera)
            
    # cria um header a partir de um token
    def __getHeader(self, token: str):
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json"
        }

    # se for request essencial, falha tudo, caso contrário segue o jogo
    def __requestFalha(self, motivo: str, obrigatorio: bool):
        if obrigatorio:
            raise ErroRequestObrigatoria(f"Uma request obrigatória falhou! {motivo}")
        print(f"Alerta! Uma request não obrigatória falhou! {motivo}")
        return None

    def getQuantidadeRequests(self) -> int:
        return self.__quantidadeRequests
        
    def exibirRelatorioTokens(self):
        print("---= Relatório de Tokens =---")
        for i in range(len(self.__tokens)):
            print(f"Token {i+1}: {self.__tokens[i].usos} usos")
        print("---== -----+-----+----- ==---")

