import time

import pytest
import requests

from trabalho_pratico_grafos.minerador import cliente_github
from trabalho_pratico_grafos.minerador.cliente_github import ClienteGithub, ErroRequestObrigatoria

# Para rodar escrever no terminal na raiz do projeto: pytest -v

# Infraestrutura dos testes: nenhum teste aqui acessa a rede.
# RespostaFake imita o requests.Response (só os campos que o cliente lê)
# e RequestsFake substitui o requests.get, devolvendo as respostas na ordem
# e gravando cada chamada para os asserts.
class RespostaFake:
    def __init__(self, status_code=200, corpo=None, headers=None, links=None):
        self.status_code = status_code
        self.__corpo = corpo if corpo is not None else {}
        self.headers = headers or {}
        self.links = links or {}

    def json(self):
        return self.__corpo

class RequestsFake:
    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def __call__(self, url, params=None, headers=None, timeout=None):
        self.chamadas.append({"url": url, "params": params, "headers": headers})
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

def prepararCliente(monkeypatch, fake, tokens):
    # troca o requests.get pelo fake e anula os sleeps para o teste não esperar de verdade
    monkeypatch.setattr(cliente_github.requests, "get", fake)
    monkeypatch.setattr(cliente_github.time, "sleep", lambda segundos: None)
    return ClienteGithub(tokens)

# Inicio dos testes em get()
def test_get_sucesso_retorna_json(monkeypatch):
    # Arrange
    fake = RequestsFake(RespostaFake(200, corpo={"name": "repo"}))
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act
    resultado = cliente.get("repos/dono/repo")

    # Assert
    assert resultado == {"name": "repo"}
    assert fake.chamadas[0]["url"] == "https://api.github.com/repos/dono/repo"
    assert fake.chamadas[0]["headers"]["Authorization"] == "Bearer token_a"

def test_get_falha_nao_obrigatoria_retorna_none(monkeypatch):
    # Arrange: erro 500 sem obrigatorio
    fake = RequestsFake(RespostaFake(500))
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act
    resultado = cliente.get("repos/dono/repo")

    # Assert
    assert resultado is None

def test_get_falha_obrigatoria_levanta_excecao(monkeypatch):
    # Arrange: erro 500 com obrigatorio
    fake = RequestsFake(RespostaFake(500))
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act and Assert
    with pytest.raises(ErroRequestObrigatoria):
        cliente.get("repos/dono/repo", obrigatorio=True)

def test_get_401_invalida_token_e_usa_o_proximo(monkeypatch):
    # Arrange: primeira resposta 401 (token inválido), segunda 200
    fake = RequestsFake(RespostaFake(401), RespostaFake(200, corpo={"ok": True}))
    cliente = prepararCliente(monkeypatch, fake, ["token_a", "token_b"])

    # Act
    resultado = cliente.get("repos/dono/repo")

    # Assert: a request foi refeita com o outro token e o primeiro ficou marcado
    assert resultado == {"ok": True}
    assert fake.chamadas[1]["headers"]["Authorization"] == "Bearer token_b"
    assert cliente._ClienteGithub__tokens[0].invalido is True

def test_get_todos_tokens_invalidos_levanta_runtime_error(monkeypatch):
    # Arrange: token único respondendo 401
    fake = RequestsFake(RespostaFake(401))
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act and Assert
    with pytest.raises(RuntimeError):
        cliente.get("repos/dono/repo")

def test_get_403_rate_limit_bloqueia_token_e_usa_o_proximo(monkeypatch):
    # Arrange: 403 com rate limit zerado e reset no futuro, depois 200
    reset = time.time() + 60
    fake = RequestsFake(
        RespostaFake(403, headers={"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": str(reset)}),
        RespostaFake(200, corpo={"ok": True}),
    )
    cliente = prepararCliente(monkeypatch, fake, ["token_a", "token_b"])

    # Act
    resultado = cliente.get("repos/dono/repo")

    # Assert: o token sobrecarregado ficou bloqueado até o reset e a request seguiu com o outro
    assert resultado == {"ok": True}
    assert cliente._ClienteGithub__tokens[0].bloqueadoAte == reset
    assert fake.chamadas[1]["headers"]["Authorization"] == "Bearer token_b"

def test_get_429_retry_after_bloqueia_token(monkeypatch):
    # Arrange: 429 com Retry-After, depois 200 com o outro token
    fake = RequestsFake(
        RespostaFake(429, headers={"Retry-After": "30"}),
        RespostaFake(200, corpo={"ok": True}),
    )
    cliente = prepararCliente(monkeypatch, fake, ["token_a", "token_b"])

    # Act
    resultado = cliente.get("repos/dono/repo")

    # Assert
    assert resultado == {"ok": True}
    assert cliente._ClienteGithub__tokens[0].bloqueadoAte > time.time()

def test_get_403_sem_headers_nao_culpa_o_token(monkeypatch):
    # Arrange: 403 sem headers de rate limit é erro da request, não do token
    fake = RequestsFake(RespostaFake(403))
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act
    resultado = cliente.get("repos/dono/repo")

    # Assert: falhou, mas o token continua utilizável
    assert resultado is None
    assert cliente._ClienteGithub__tokens[0].invalido is False
    assert cliente._ClienteGithub__tokens[0].bloqueadoAte == 0.0

def test_get_422_de_cursor_tem_mensagem_especifica(monkeypatch):
    # Arrange: o 422 de limite de paginação (ver D3.1 do plano)
    corpo = {"message": "Pagination with the page parameter is not supported for large datasets, please use cursor based pagination (after/before)"}
    fake = RequestsFake(RespostaFake(422, corpo=corpo))
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act and Assert: a exceção identifica o problema de cursor
    with pytest.raises(ErroRequestObrigatoria, match="cursor"):
        cliente.get("repos/dono/repo/issues", obrigatorio=True)

def test_get_timeout_desiste_apos_3_tentativas(monkeypatch):
    # Arrange: rede sempre estourando timeout
    fake = RequestsFake(requests.Timeout(), requests.Timeout(), requests.Timeout())
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act
    resultado = cliente.get("repos/dono/repo")

    # Assert: 3 tentativas e desiste sem exceção
    assert resultado is None
    assert len(fake.chamadas) == 3

def test_get_timeout_recupera_na_segunda_tentativa(monkeypatch):
    # Arrange: um timeout seguido de sucesso
    fake = RequestsFake(requests.Timeout(), RespostaFake(200, corpo={"ok": True}))
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act
    resultado = cliente.get("repos/dono/repo")

    # Assert
    assert resultado == {"ok": True}
    assert len(fake.chamadas) == 2
# Fim dos testes em get()

# Inicio dos testes em getQuantidadeRequests()
def test_getQuantidadeRequests_conta_as_requests(monkeypatch):
    # Arrange
    fake = RequestsFake(RespostaFake(200), RespostaFake(200))
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act
    cliente.get("repos/dono/repo")
    cliente.get("repos/dono/repo")

    # Assert
    assert cliente.getQuantidadeRequests() == 2
# Fim dos testes em getQuantidadeRequests()

# Inicio dos testes em getPaginado()
def test_getPaginado_para_na_ultima_pagina(monkeypatch):
    # Arrange: página cheia (100 itens) seguida de página incompleta
    pagina1 = [{"id": i} for i in range(100)]
    pagina2 = [{"id": 100}]
    fake = RequestsFake(RespostaFake(200, corpo=pagina1), RespostaFake(200, corpo=pagina2))
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act
    resultado = cliente.getPaginado("repos/dono/repo/issues/comments")

    # Assert
    assert len(resultado.itens) == 101
    assert resultado.paginasComFalha == []
    assert fake.chamadas[0]["params"]["page"] == 1
    assert fake.chamadas[1]["params"]["page"] == 2

def test_getPaginado_registra_pagina_com_falha_e_continua(monkeypatch):
    # Arrange: página 1 falha, página 2 responde e encerra
    fake = RequestsFake(RespostaFake(500), RespostaFake(200, corpo=[{"id": 1}]))
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act
    resultado = cliente.getPaginado("repos/dono/repo/issues/comments")

    # Assert: a falha vira pendência de página e a mineração segue
    assert resultado.paginasComFalha == [1]
    assert resultado.itens == [{"id": 1}]

def test_getPaginado_desiste_apos_3_falhas_consecutivas(monkeypatch):
    # Arrange: três páginas seguidas falhando
    fake = RequestsFake(RespostaFake(500), RespostaFake(500), RespostaFake(500))
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act
    resultado = cliente.getPaginado("repos/dono/repo/issues/comments")

    # Assert
    assert resultado.paginasComFalha == [1, 2, 3]
    assert resultado.itens == []
# Fim dos testes em getPaginado()

# Inicio dos testes em getPaginadoCursor()
def test_getPaginadoCursor_segue_o_link_next(monkeypatch):
    # Arrange: primeira resposta com link next, segunda sem (última página)
    urlNext = "https://api.github.com/repositories/1/issues?per_page=100&after=cursor_abc"
    fake = RequestsFake(
        RespostaFake(200, corpo=[{"id": 1}], links={"next": {"url": urlNext}}),
        RespostaFake(200, corpo=[{"id": 2}]),
    )
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act
    resultado = cliente.getPaginadoCursor("repos/dono/repo/issues", params={"state": "all"})

    # Assert: juntou as páginas e a segunda request usou a URL do next, sem params duplicados
    assert resultado == [{"id": 1}, {"id": 2}]
    assert fake.chamadas[0]["params"] == {"state": "all", "per_page": 100}
    assert fake.chamadas[1]["url"] == urlNext
    assert not fake.chamadas[1]["params"] # nenhum param extra: a URL do next já carrega o cursor

def test_getPaginadoCursor_falha_nao_obrigatoria_devolve_parcial(monkeypatch):
    # Arrange: primeira página ok, segunda falha sem obrigatorio
    urlNext = "https://api.github.com/repositories/1/issues?per_page=100&after=cursor_abc"
    fake = RequestsFake(
        RespostaFake(200, corpo=[{"id": 1}], links={"next": {"url": urlNext}}),
        RespostaFake(500),
    )
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act
    resultado = cliente.getPaginadoCursor("repos/dono/repo/issues")

    # Assert: devolve o que conseguiu
    assert resultado == [{"id": 1}]

def test_getPaginadoCursor_falha_obrigatoria_levanta_excecao(monkeypatch):
    # Arrange: falha com obrigatorio (caso das listagens de issues/pulls)
    fake = RequestsFake(RespostaFake(500))
    cliente = prepararCliente(monkeypatch, fake, ["token_a"])

    # Act and Assert
    with pytest.raises(ErroRequestObrigatoria):
        cliente.getPaginadoCursor("repos/dono/repo/issues", obrigatorio=True)
# Fim dos testes em getPaginadoCursor()
