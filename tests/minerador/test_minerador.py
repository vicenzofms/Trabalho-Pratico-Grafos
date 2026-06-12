from trabalho_pratico_grafos.minerador.minerador import Interacao, Minerador, RequestPendente
from trabalho_pratico_grafos.minerador.cliente_github import ResultadoPaginado

# Para rodar escrever no terminal na raiz do projeto: pytest -v

# Substitui o ClienteGithub nos testes de processarPendencias (nenhum teste acessa a rede)
class ClienteFake:
    def __init__(self, respostaGet=None, respostaPaginada=None):
        self.respostaGet = respostaGet
        self.respostaPaginada = respostaPaginada

    def get(self, endpoint, params=None, obrigatorio=False, opts=None):
        return self.respostaGet

    def getPaginado(self, endpoint, params=None, opts=None, obrigatorio=False):
        return self.respostaPaginada

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
