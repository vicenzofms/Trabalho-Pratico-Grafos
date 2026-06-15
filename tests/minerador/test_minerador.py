import os

import pytest

from trabalho_pratico_grafos.minerador.minerador import Interacao, Minerador, RequestPendente
from trabalho_pratico_grafos.minerador.cliente_github import ResultadoPaginado, ErroTokensInutilizaveis, ErroRequestObrigatoria

# Para rodar escrever no terminal na raiz do projeto: pytest -v

# Substitui o ClienteGithub nos testes que mineram/processam (nenhum teste acessa a rede)
class ClienteFake:
    def __init__(self, respostaGet=None, respostaPaginada=None, respostaCursor=None):
        self.respostaGet = respostaGet
        self.respostaPaginada = respostaPaginada
        self.respostaCursor = respostaCursor

    def get(self, endpoint, params=None, obrigatorio=False, opts=None):
        return self.respostaGet

    def getPaginado(self, endpoint, params=None, opts=None, obrigatorio=False):
        return self.respostaPaginada

    def getPaginadoCursor(self, endpoint, params=None, opts=None, obrigatorio=False):
        return self.respostaCursor

# Inicio dos testes em __init__()
def test_init_tokens_vazios_levanta_erro():
    # Arrange and Act and Assert: lista de tokens vazia é inválida
    with pytest.raises(ValueError):
        Minerador("dono/repo", [])
# Fim dos testes em __init__()

# Inicio dos testes em adicionarInteracao()
def test_adicionarInteracao_cria_uma_interacao():
    # Arrange: crio um minerador
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act: chamo a função que quero testar
    minerador._Minerador__adicionarInteracao(Interacao("ana", "bob", 2, "comentario_issue"))

    # Assert
    assert minerador.quantidadeInteracoes() == 1
    assert minerador._Minerador__mapaInteracoes[("ana", "bob", "comentario_issue")].peso == 2

def test_adicionarInteracao_soma_peso_quando_repete():
    # Arrange: crio minerador
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act: chamo a função duas vezes com a mesma chave
    minerador._Minerador__adicionarInteracao(Interacao("ana", "bob", 2, "comentario_issue"))
    minerador._Minerador__adicionarInteracao(Interacao("ana", "bob", 2, "comentario_issue"))

    # Assert
    assert minerador.quantidadeInteracoes() == 1
    assert minerador._Minerador__mapaInteracoes[("ana", "bob", "comentario_issue")].peso == 4

def test_adicionarInteracao_chaves_diferentes():
    # Arrange: crio minerador
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act: chamo a função duas vezes com diferentes chaves, mesmos usuários, mas tipos diferentes
    minerador._Minerador__adicionarInteracao(Interacao("ana", "bob", 2, "comentario_issue"))
    minerador._Minerador__adicionarInteracao(Interacao("ana", "bob", 1, "fechamento_issue"))

    # Assert
    assert minerador.quantidadeInteracoes() == 2
    assert minerador._Minerador__mapaInteracoes[("ana", "bob", "comentario_issue")].peso == 2
    assert minerador._Minerador__mapaInteracoes[("ana", "bob", "fechamento_issue")].peso == 1

def test_adicionarInteracao_contador_interacoes_registradas():
    # Arrange: crio minerador
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act: chamo a função X vezes passando qualquer chave
    minerador._Minerador__adicionarInteracao(Interacao("ana", "bob", 2, "comentario_issue"))
    minerador._Minerador__adicionarInteracao(Interacao("cecilia", "diego", 1, "fechamento_issue"))
    minerador._Minerador__adicionarInteracao(Interacao("ana", "bob", 5, "merge_pull"))

    # Assert
    assert minerador.quantidadeInteracoesRegistradas() == 3
    assert minerador.quantidadeInteracoes() == 3
# Fim dos testes em adicionarInteracao()

# Inicio dos testes em adicionarPendencia()
def test_adicionarPendencia_registra_na_lista():
    # Arrange: crio minerador
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act
    minerador._Minerador__adicionarPendencia(RequestPendente("repos/dono/repo/pulls/7", "merge", autorPR="ana", numeroPR=7))

    # Assert
    assert len(minerador._Minerador__requestsPendentes) == 1
    assert minerador._Minerador__requestsPendentes[0].tipo == "merge"
    assert minerador._Minerador__requestsPendentes[0].numeroPR == 7
# Fim dos testes em adicionarPendencia()

# Inicio dos testes em definirAutoresIssuesPRs()
def test_definirAutoresIssuesPRs():
    # Arrange: crio o minerador, injeto só os campos que a função lê, number e user.login
    minerador = Minerador("dono/repo", ["token_exemplo"])

    minerador._Minerador__issues = [{"number": 1, "user": {"login": "ana"}}]
    minerador._Minerador__pullRequests = [{"number": 2, "user": {"login": "bob"}}]

    # Act
    minerador._Minerador__definirAutoresIssuesPRs()

    # Assert
    assert minerador._Minerador__autoresIssuesPRs == {"1": "ana", "2": "bob"}

def test_definirAutoresIssuesPRs_ignora_user_nulo():
    # Arrange: issue/PR de usuário deletado vem com user = None
    minerador = Minerador("dono/repo", ["token_exemplo"])

    minerador._Minerador__issues = [{"number": 1, "user": None}]
    minerador._Minerador__pullRequests = [{"number": 2, "user": {"login": "bob"}}]

    # Act
    minerador._Minerador__definirAutoresIssuesPRs()

    # Assert: a issue sem user fica de fora, sem quebrar
    assert minerador._Minerador__autoresIssuesPRs == {"2": "bob"}

def test_definirAutoresIssuesPRs_ignora_pr_sem_user():
    # Arrange: PR de usuário deletado vem com user = None
    minerador = Minerador("dono/repo", ["token_exemplo"])

    minerador._Minerador__issues = [{"number": 1, "user": {"login": "ana"}}]
    minerador._Minerador__pullRequests = [{"number": 2, "user": None}]

    # Act
    minerador._Minerador__definirAutoresIssuesPRs()

    # Assert: o PR sem user fica de fora, sem quebrar
    assert minerador._Minerador__autoresIssuesPRs == {"1": "ana"}
# Fim dos testes em definirAutoresIssuesPRs()

# Inicio dos testes em processarFechamentoIssues()
def test_processarFechamentoIssues_sem_closed_by():
    # Arrange: closed_by = none
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__issues = [{"closed_by": None, "user": {"login": "ana"}}]

    # Act
    minerador._Minerador__processarFechamentoIssues()

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_processarFechamentoIssues_issue_e_um_pull_request():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__issues = [{"closed_by": {"login": "bob"}, "user": {"login": "ana"}, "pull_request": {"url": "https://csfloat.com/"}}]

    # Act
    minerador._Minerador__processarFechamentoIssues()

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_processarFechamentoIssues_quem_fechou_foi_o_autor():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__issues = [{"closed_by": {"login": "astolfo"}, "user": {"login": "astolfo"}}]

    # Act
    minerador._Minerador__processarFechamentoIssues()

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_processarFechamentoIssues_user_nulo():
    # Arrange: issue fechada cujo autor foi deletado
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__issues = [{"closed_by": {"login": "bob"}, "user": None}]

    # Act
    minerador._Minerador__processarFechamentoIssues()

    # Assert: ignora sem quebrar
    assert minerador.quantidadeInteracoes() == 0

def test_processarFechamentoIssues_caso_base_valido():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__issues = [{"closed_by": {"login": "bob"}, "user": {"login": "ana"}}]

    # Act
    minerador._Minerador__processarFechamentoIssues()

    # Assert
    assert minerador.quantidadeInteracoes() == 1
    assert minerador.quantidadeUsuarios() == 2
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "fechamento_issue")].peso == 1
# Fim dos testes em processarFechamentoIssues()

# Inicio dos testes em processarComentarioIssue()
def test_processarComentarioIssue_user_nulo():
    # Arrange: comentário fantasma (autor deletado)
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__autoresIssuesPRs = {"1": "ana"}

    # Act
    minerador._Minerador__processarComentarioIssue({"user": None, "issue_url": "https://api.github.com/repos/dono/repo/issues/1"})

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_processarComentarioIssue_issue_nao_mapeada():
    # Arrange: comentário em issue que não está no mapa de autores
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__autoresIssuesPRs = {}

    # Act
    minerador._Minerador__processarComentarioIssue({"user": {"login": "bob"}, "issue_url": "https://api.github.com/repos/dono/repo/issues/1"})

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_processarComentarioIssue_comentario_do_proprio_autor():
    # Arrange: autor da issue comentou nela mesma (seria um self-loop)
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__autoresIssuesPRs = {"1": "ana"}

    # Act
    minerador._Minerador__processarComentarioIssue({"user": {"login": "ana"}, "issue_url": "https://api.github.com/repos/dono/repo/issues/1"})

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_processarComentarioIssue_caso_base_valido():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__autoresIssuesPRs = {"1": "ana"}

    # Act
    minerador._Minerador__processarComentarioIssue({"user": {"login": "bob"}, "issue_url": "https://api.github.com/repos/dono/repo/issues/1"})

    # Assert
    assert minerador.quantidadeInteracoes() == 1
    assert minerador.quantidadeUsuarios() == 2
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "comentario_issue")].peso == 2
# Fim dos testes em processarComentarioIssue()

# Inicio dos testes em processarComentarioInlinePR()
def test_processarComentarioInlinePR_user_nulo():
    # Arrange: comentário fantasma (autor deletado)
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__autoresIssuesPRs = {"2": "ana"}

    # Act
    minerador._Minerador__processarComentarioInlinePR({"user": None, "pull_request_url": "https://api.github.com/repos/dono/repo/pulls/2"})

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_processarComentarioInlinePR_pr_nao_mapeado():
    # Arrange: comentário em PR que não está no mapa de autores
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__autoresIssuesPRs = {}

    # Act
    minerador._Minerador__processarComentarioInlinePR({"user": {"login": "bob"}, "pull_request_url": "https://api.github.com/repos/dono/repo/pulls/2"})

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_processarComentarioInlinePR_comentario_do_proprio_autor():
    # Arrange: autor do PR comentou nele mesmo (seria um self-loop)
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__autoresIssuesPRs = {"2": "ana"}

    # Act
    minerador._Minerador__processarComentarioInlinePR({"user": {"login": "ana"}, "pull_request_url": "https://api.github.com/repos/dono/repo/pulls/2"})

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_processarComentarioInlinePR_caso_base_valido():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__autoresIssuesPRs = {"2": "ana"}

    # Act
    minerador._Minerador__processarComentarioInlinePR({"user": {"login": "bob"}, "pull_request_url": "https://api.github.com/repos/dono/repo/pulls/2"})

    # Assert
    assert minerador.quantidadeInteracoes() == 1
    assert minerador.quantidadeUsuarios() == 2
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "comentario_pull_request")].peso == 2
# Fim dos testes em processarComentarioInlinePR()

# Inicio dos testes em processarReview()
def test_processarReview_user_nulo():
    # Arrange: review fantasma (autor deletado)
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act
    minerador._Minerador__processarReview({"user": None}, "ana")

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_processarReview_review_do_proprio_autor():
    # Arrange: autor do PR revisou o próprio PR (seria um self-loop)
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act
    minerador._Minerador__processarReview({"user": {"login": "ana"}}, "ana")

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_processarReview_caso_base_valido():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act
    minerador._Minerador__processarReview({"user": {"login": "bob"}}, "ana")

    # Assert
    assert minerador.quantidadeInteracoes() == 1
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "revisao_pull")].peso == 4
# Fim dos testes em processarReview()

# Inicio dos testes em processarMerge()
def test_processarMerge_sem_merged_by():
    # Arrange: pull sem merged_by
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act
    minerador._Minerador__processarMerge({"merged_by": None}, "ana")

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_processarMerge_merge_do_proprio_autor():
    # Arrange: autor do PR fez o próprio merge (seria um self-loop)
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act
    minerador._Minerador__processarMerge({"merged_by": {"login": "ana"}}, "ana")

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_processarMerge_caso_base_valido():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act
    minerador._Minerador__processarMerge({"merged_by": {"login": "bob"}}, "ana")

    # Assert
    assert minerador.quantidadeInteracoes() == 1
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "merge_pull")].peso == 5
# Fim dos testes em processarMerge()

# Inicio dos testes em processarPendencias()
def test_processarPendencias_merge_resolvida():
    # Arrange: pendência de merge e cliente respondendo com sucesso
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__clienteGithub = ClienteFake(respostaGet={"merged_by": {"login": "bob"}})
    minerador._Minerador__adicionarPendencia(RequestPendente("repos/dono/repo/pulls/7", "merge", autorPR="ana", numeroPR=7))

    # Act
    minerador._Minerador__processarPendencias(0)

    # Assert: pendência resolvida sai da lista e vira interação
    assert len(minerador._Minerador__requestsPendentes) == 0
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "merge_pull")].peso == 5

def test_processarPendencias_falha_de_novo_permanece_na_lista():
    # Arrange: pendência de merge e cliente falhando de novo
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__clienteGithub = ClienteFake(respostaGet=None)
    minerador._Minerador__adicionarPendencia(RequestPendente("repos/dono/repo/pulls/7", "merge", autorPR="ana", numeroPR=7))

    # Act
    minerador._Minerador__processarPendencias(0)

    # Assert: continua na lista (dados parciais) e nada é registrado
    assert len(minerador._Minerador__requestsPendentes) == 1
    assert minerador.quantidadeInteracoes() == 0

def test_processarPendencias_comentarios_issues_despacha_para_o_processador_correto():
    # Arrange: página de comentários de issue recuperada no retry
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__autoresIssuesPRs = {"1": "ana"}
    minerador._Minerador__clienteGithub = ClienteFake(respostaGet=[{"user": {"login": "bob"}, "issue_url": "https://api.github.com/repos/dono/repo/issues/1"}])
    minerador._Minerador__adicionarPendencia(RequestPendente("repos/dono/repo/issues/comments", "comentarios_issues", pagina=3))

    # Act
    minerador._Minerador__processarPendencias(0)

    # Assert: a interação sai com o tipo certo
    assert len(minerador._Minerador__requestsPendentes) == 0
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "comentario_issue")].peso == 2

def test_processarPendencias_comentarios_prs_despacha_para_o_processador_correto():
    # Arrange: página de comentários inline de PR recuperada no retry
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__autoresIssuesPRs = {"2": "ana"}
    minerador._Minerador__clienteGithub = ClienteFake(respostaGet=[{"user": {"login": "bob"}, "pull_request_url": "https://api.github.com/repos/dono/repo/pulls/2"}])
    minerador._Minerador__adicionarPendencia(RequestPendente("repos/dono/repo/pulls/comments", "comentarios_prs", pagina=3))

    # Act
    minerador._Minerador__processarPendencias(0)

    # Assert: a interação sai com o tipo certo (e não como comentario_issue)
    assert len(minerador._Minerador__requestsPendentes) == 0
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "comentario_pull_request")].peso == 2

def test_processarPendencias_reviews_resolvida():
    # Arrange: reviews do PR recuperadas inteiras no retry
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__clienteGithub = ClienteFake(respostaPaginada=ResultadoPaginado([{"user": {"login": "bob"}}], []))
    minerador._Minerador__adicionarPendencia(RequestPendente("repos/dono/repo/pulls/7/reviews", "reviews", autorPR="ana", numeroPR=7))

    # Act
    minerador._Minerador__processarPendencias(0)

    # Assert
    assert len(minerador._Minerador__requestsPendentes) == 0
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "revisao_pull")].peso == 4

def test_processarPendencias_reviews_com_pagina_falha_nao_processa_nada():
    # Arrange: retry das reviews falhou em uma página — tudo ou nada (evita peso duplicado)
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__clienteGithub = ClienteFake(respostaPaginada=ResultadoPaginado([{"user": {"login": "bob"}}], [2]))
    minerador._Minerador__adicionarPendencia(RequestPendente("repos/dono/repo/pulls/7/reviews", "reviews", autorPR="ana", numeroPR=7))

    # Act
    minerador._Minerador__processarPendencias(0)

    # Assert: permanece pendente e nenhum item parcial é registrado
    assert len(minerador._Minerador__requestsPendentes) == 1
    assert minerador.quantidadeInteracoes() == 0

def test_processarPendencias_comentarios_issues_falha_permanece():
    # Arrange: retry de comentários de issue falha de novo (cliente devolve None)
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__clienteGithub = ClienteFake(respostaGet=None)
    minerador._Minerador__adicionarPendencia(RequestPendente("repos/dono/repo/issues/comments", "comentarios_issues", pagina=3))

    # Act
    minerador._Minerador__processarPendencias(0)

    # Assert: continua na lista e nada é registrado
    assert len(minerador._Minerador__requestsPendentes) == 1
    assert minerador.quantidadeInteracoes() == 0

def test_processarPendencias_comentarios_prs_falha_permanece():
    # Arrange: retry de comentários inline de PR falha de novo (cliente devolve None)
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__clienteGithub = ClienteFake(respostaGet=None)
    minerador._Minerador__adicionarPendencia(RequestPendente("repos/dono/repo/pulls/comments", "comentarios_prs", pagina=3))

    # Act
    minerador._Minerador__processarPendencias(0)

    # Assert: continua na lista e nada é registrado
    assert len(minerador._Minerador__requestsPendentes) == 1
    assert minerador.quantidadeInteracoes() == 0
# Fim dos testes em processarPendencias()

# Inicio dos testes em exportarDados()
def test_exportarDados_sem_dados_retorna_none():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act and Assert
    assert minerador.exportarDados() is None

def test_exportarDados_estrutura():
    # Arrange: registro uma interação válida
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__mapaUsuarios.buscarOuRegistrar("ana")
    minerador._Minerador__processarMerge({"merged_by": {"login": "bob"}}, "ana")

    # Act
    exportado = minerador.exportarDados()

    # Assert
    assert exportado["interacoes"] == [{"origem": "bob", "destino": "ana", "peso": 5, "tipo": "merge_pull"}]
    assert exportado["usuarios"]["quantidade"] == 2
# Fim dos testes em exportarDados()

# Inicio dos testes em obterCaminhoCache()
def test_obterCaminhoCache_usa_o_nome_do_repositorio():
    # Arrange: o caminho do cache troca a barra do repo por _ e aponta para data/
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act
    caminho = minerador._Minerador__obterCaminhoCache()

    # Assert
    assert caminho.endswith("dono_repo.json")
    assert "data" in caminho
# Fim dos testes em obterCaminhoCache()

# Inicio dos testes em salvarNoCache() e carregarDoCache()
def test_cache_salva_e_recarrega_round_trip(tmp_path):
    # Arrange: minerador com uma interação, com o cache redirecionado para um tmp
    caminho = str(tmp_path / "cache.json")
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__processarMerge({"merged_by": {"login": "bob"}}, "ana")
    minerador._Minerador__obterCaminhoCache = lambda: caminho

    # Act: salva e recarrega num minerador novo apontando para o mesmo arquivo
    minerador.salvarNoCache()
    outro = Minerador("dono/repo", ["token_exemplo"])
    outro._Minerador__obterCaminhoCache = lambda: caminho
    sucesso = outro.carregarDoCache()

    # Assert: a interação volta idêntica e os dois usuários são re-registrados
    assert sucesso is True
    assert outro.quantidadeInteracoes() == 1
    assert outro.quantidadeUsuarios() == 2
    assert outro._Minerador__mapaInteracoes[("bob", "ana", "merge_pull")].peso == 5

def test_carregarDoCache_arquivo_inexistente_retorna_false(tmp_path):
    # Arrange: caminho que não existe
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__obterCaminhoCache = lambda: str(tmp_path / "nao_existe.json")

    # Act and Assert
    assert minerador.carregarDoCache() is False

def test_carregarDoCache_arquivo_corrompido_retorna_false(tmp_path):
    # Arrange: arquivo com JSON inválido
    caminho = tmp_path / "cache.json"
    caminho.write_text("{ isso nao e json valido")
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__obterCaminhoCache = lambda: str(caminho)

    # Act and Assert: cai no except e devolve False, sem quebrar
    assert minerador.carregarDoCache() is False
# Fim dos testes em salvarNoCache() e carregarDoCache()

# Inicio dos testes em buscarPullRequests() e buscarIssues()
def test_buscarPullRequests_armazena_resultado_do_cliente():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__clienteGithub = ClienteFake(respostaCursor=[{"number": 1, "user": {"login": "ana"}}])

    # Act
    minerador._Minerador__buscarPullRequests(0)

    # Assert
    assert minerador._Minerador__pullRequests == [{"number": 1, "user": {"login": "ana"}}]

def test_buscarIssues_armazena_resultado_do_cliente():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__clienteGithub = ClienteFake(respostaCursor=[{"number": 2, "user": {"login": "bob"}}])

    # Act
    minerador._Minerador__buscarIssues(0)

    # Assert
    assert minerador._Minerador__issues == [{"number": 2, "user": {"login": "bob"}}]
# Fim dos testes em buscarPullRequests() e buscarIssues()

# Inicio dos testes em minerarComentariosIssuesPR()
def test_minerarComentariosIssuesPR_processa_itens_e_registra_pendencias():
    # Arrange: uma página recuperada (vira interação) e uma com falha (vira pendência)
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__autoresIssuesPRs = {"1": "ana"}
    minerador._Minerador__clienteGithub = ClienteFake(respostaPaginada=ResultadoPaginado(
        [{"user": {"login": "bob"}, "issue_url": "https://api.github.com/repos/dono/repo/issues/1"}],
        [4],
    ))

    # Act
    minerador._Minerador__minerarComentariosIssuesPR(0)

    # Assert: item virou interação e a página com falha virou pendência
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "comentario_issue")].peso == 2
    assert len(minerador._Minerador__requestsPendentes) == 1
    assert minerador._Minerador__requestsPendentes[0].tipo == "comentarios_issues"
    assert minerador._Minerador__requestsPendentes[0].pagina == 4
# Fim dos testes em minerarComentariosIssuesPR()

# Inicio dos testes em minerarComentariosInlinePullRequest()
def test_minerarComentariosInlinePullRequest_processa_itens_e_registra_pendencias():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__autoresIssuesPRs = {"2": "ana"}
    minerador._Minerador__clienteGithub = ClienteFake(respostaPaginada=ResultadoPaginado(
        [{"user": {"login": "bob"}, "pull_request_url": "https://api.github.com/repos/dono/repo/pulls/2"}],
        [5],
    ))

    # Act
    minerador._Minerador__minerarComentariosInlinePullRequest(0)

    # Assert
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "comentario_pull_request")].peso == 2
    assert len(minerador._Minerador__requestsPendentes) == 1
    assert minerador._Minerador__requestsPendentes[0].tipo == "comentarios_prs"
    assert minerador._Minerador__requestsPendentes[0].pagina == 5
# Fim dos testes em minerarComentariosInlinePullRequest()

# Inicio dos testes em minerarReviewsDeUmPR()
def test_minerarReviewsDeUmPR_processa_reviews(monkeypatch):
    # Arrange: reviews recuperadas inteiras (sem página com falha); evita o sleep real
    monkeypatch.setattr("time.sleep", lambda *_: None)
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__clienteGithub = ClienteFake(respostaPaginada=ResultadoPaginado([{"user": {"login": "bob"}}], []))

    # Act
    minerador._Minerador__minerarReviewsDeUmPR(7, "ana")

    # Assert: registra o autor do PR e a interação de revisão
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "revisao_pull")].peso == 4
    assert len(minerador._Minerador__requestsPendentes) == 0

def test_minerarReviewsDeUmPR_pagina_com_falha_vira_pendencia(monkeypatch):
    # Arrange: página falhou -> tudo ou nada, não processa nada e vira pendência
    monkeypatch.setattr("time.sleep", lambda *_: None)
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__clienteGithub = ClienteFake(respostaPaginada=ResultadoPaginado([{"user": {"login": "bob"}}], [2]))

    # Act
    minerador._Minerador__minerarReviewsDeUmPR(7, "ana")

    # Assert
    assert len(minerador._Minerador__requestsPendentes) == 1
    assert minerador._Minerador__requestsPendentes[0].tipo == "reviews"
    assert minerador.quantidadeInteracoes() == 0
# Fim dos testes em minerarReviewsDeUmPR()

# Inicio dos testes em minerarMergeDeUmPR()
def test_minerarMergeDeUmPR_processa_merge(monkeypatch):
    # Arrange: merge recuperado com sucesso; evita o sleep real
    monkeypatch.setattr("time.sleep", lambda *_: None)
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__clienteGithub = ClienteFake(respostaGet={"merged_by": {"login": "bob"}})

    # Act
    minerador._Minerador__minerarMergeDeUmPR(7, "ana")

    # Assert
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "merge_pull")].peso == 5
    assert len(minerador._Minerador__requestsPendentes) == 0

def test_minerarMergeDeUmPR_falha_vira_pendencia(monkeypatch):
    # Arrange: cliente devolve None (falhou)
    monkeypatch.setattr("time.sleep", lambda *_: None)
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__clienteGithub = ClienteFake(respostaGet=None)

    # Act
    minerador._Minerador__minerarMergeDeUmPR(7, "ana")

    # Assert
    assert len(minerador._Minerador__requestsPendentes) == 1
    assert minerador._Minerador__requestsPendentes[0].tipo == "merge"
    assert minerador.quantidadeInteracoes() == 0
# Fim dos testes em minerarMergeDeUmPR()

# Inicio dos testes dos métodos de exibição (debug, só imprimem)
def test_exibirInteracoes_nao_quebra():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__processarMerge({"merged_by": {"login": "bob"}}, "ana")

    # Act and Assert: roda sem levantar exceção
    minerador.exibirInteracoes()

def test_exibirUsuarios_nao_quebra():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__mapaUsuarios.buscarOuRegistrar("ana")

    # Act and Assert
    minerador.exibirUsuarios()

def test_exibirRelatorioTokens_nao_quebra():
    # Arrange
    minerador = Minerador("dono/repo", ["token_exemplo"])

    # Act and Assert
    minerador.exibirRelatorioTokens()
# Fim dos testes dos métodos de exibição

# Inicio dos testes em executar()
def test_executar_usa_cache_e_retorna_cedo(tmp_path):
    # Arrange: salva um cache previamente; com usar_cache=True, executar deve
    # carregá-lo e encerrar sem tocar na rede
    caminho = str(tmp_path / "cache.json")
    semente = Minerador("dono/repo", ["token_exemplo"])
    semente._Minerador__processarMerge({"merged_by": {"login": "bob"}}, "ana")
    semente._Minerador__obterCaminhoCache = lambda: caminho
    semente.salvarNoCache()

    minerador = Minerador("dono/repo", ["token_exemplo"], usar_cache=True)
    minerador._Minerador__obterCaminhoCache = lambda: caminho

    # Act
    minerador.executar()

    # Assert: os dados vieram do cache, sem nenhuma request
    assert minerador.quantidadeInteracoes() == 1
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "merge_pull")].peso == 5


# Cliente que passa na verificação do repo e nas listagens, mas esgota os tokens
# (ErroTokensInutilizaveis) em qualquer mineração específica (comentários/merges).
class ClienteTokensEsgotam:
    def __init__(self, issues, pulls):
        self.__issues = issues
        self.__pulls = pulls

    def get(self, endpoint, params=None, obrigatorio=False, opts=None):
        # "repos/dono/repo" (verificação do repo) passa; o resto (merge) esgota
        if endpoint.count("/") == 2:
            return {"full_name": endpoint}
        raise ErroTokensInutilizaveis("tokens esgotados (fake)")

    def getPaginadoCursor(self, endpoint, params=None, opts=None, obrigatorio=False):
        if endpoint.endswith("/issues"): return self.__issues
        if endpoint.endswith("/pulls"): return self.__pulls
        return []

    def getPaginado(self, endpoint, params=None, opts=None, obrigatorio=False):
        raise ErroTokensInutilizaveis("tokens esgotados (fake)")

    def getQuantidadeRequests(self):
        return 0

def test_executar_aborta_e_preserva_parciais_quando_tokens_esgotam(tmp_path):
    # Arrange: o fechamento de issue é processado sem rede, então fica registrado
    # antes de os tokens esgotarem na mineração de comentários.
    caminho = str(tmp_path / "cache.json")
    minerador = Minerador("dono/repo", ["token_exemplo"], usar_cache=True)
    minerador._Minerador__obterCaminhoCache = lambda: caminho
    issues = [{"number": 1, "user": {"login": "ana"}, "closed_by": {"login": "bob"}}]
    minerador._Minerador__clienteGithub = ClienteTokensEsgotam(issues, [])

    # Act: executar não pode levantar exceção, deve abortar de forma limpa
    minerador.executar(sleepTime=0)

    # Assert: a interação de fechamento foi preservada apesar do aborto e persistida no cache
    assert minerador.quantidadeInteracoes() == 1
    assert minerador._Minerador__mapaInteracoes[("bob", "ana", "fechamento_issue")].peso == 1
    assert os.path.exists(caminho)
    # e o aborto por tokens marcou a coleta como parcial
    assert minerador.houveDadosParciais() is True


# Cliente em que a verificação do repo ("repos/dono/repo") falha.
class ClienteRepoIndisponivel:
    def __init__(self, erro):
        self.__erro = erro

    def get(self, endpoint, params=None, obrigatorio=False, opts=None):
        raise self.__erro

    def getPaginadoCursor(self, endpoint, params=None, opts=None, obrigatorio=False):  # pragma: no cover
        return []

    def getPaginado(self, endpoint, params=None, opts=None, obrigatorio=False):  # pragma: no cover
        return ResultadoPaginado([], [])

    def getQuantidadeRequests(self):  # pragma: no cover
        return 0


@pytest.mark.parametrize(
    "erro",
    [ErroRequestObrigatoria("repo nao existe (fake)"), ErroTokensInutilizaveis("tokens (fake)")],
)
def test_executar_repo_indisponivel_levanta_e_nao_salva(tmp_path, erro):
    # Arrange: a verificação obrigatória do repo falha logo no começo
    caminho = str(tmp_path / "cache.json")
    minerador = Minerador("dono/repo", ["token_exemplo"], usar_cache=True)
    minerador._Minerador__obterCaminhoCache = lambda: caminho
    minerador._Minerador__clienteGithub = ClienteRepoIndisponivel(erro)

    # Act + Assert: erro fatal propaga e nada é salvo
    with pytest.raises(type(erro)):
        minerador.executar(sleepTime=0)
    assert not os.path.exists(caminho)


# Cliente em que o repo existe, mas a listagem obrigatória de issues/PRs falha.
class ClienteListagemFalha:
    def get(self, endpoint, params=None, obrigatorio=False, opts=None):
        return {"full_name": endpoint}  # verificação do repo passa

    def getPaginadoCursor(self, endpoint, params=None, opts=None, obrigatorio=False):
        raise ErroRequestObrigatoria("listagem obrigatória falhou (fake)")

    def getPaginado(self, endpoint, params=None, opts=None, obrigatorio=False):  # pragma: no cover
        return ResultadoPaginado([], [])

    def getQuantidadeRequests(self):  # pragma: no cover
        return 0


def test_executar_listagem_obrigatoria_falha_levanta_e_nao_salva(tmp_path):
    # Arrange: repo existe, mas a listagem de issues/PRs (obrigatória) falha
    caminho = str(tmp_path / "cache.json")
    minerador = Minerador("dono/repo", ["token_exemplo"], usar_cache=True)
    minerador._Minerador__obterCaminhoCache = lambda: caminho
    minerador._Minerador__clienteGithub = ClienteListagemFalha()

    # Act + Assert: erro fatal propaga e nada é salvo
    with pytest.raises(ErroRequestObrigatoria):
        minerador.executar(sleepTime=0)
    assert not os.path.exists(caminho)


def test_salvarNoCache_sem_interacoes_nao_grava_arquivo(tmp_path):
    # Arrange: minerador sem nenhuma interação coletada
    caminho = str(tmp_path / "cache.json")
    minerador = Minerador("dono/repo", ["token_exemplo"])
    minerador._Minerador__obterCaminhoCache = lambda: caminho

    # Act
    minerador.salvarNoCache()

    # Assert: cache vazio não é persistido
    assert not os.path.exists(caminho)


def test_minerador_novo_nao_e_parcial():
    # Arrange + Assert: por padrão, uma coleta nova não está marcada como parcial
    minerador = Minerador("dono/repo", ["token_exemplo"])
    assert minerador.houveDadosParciais() is False
# Fim dos testes em executar()
