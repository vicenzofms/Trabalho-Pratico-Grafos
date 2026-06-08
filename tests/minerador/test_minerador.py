from trabalho_pratico_grafos.minerador.minerador import Interacao, Minerador

# Para rodar escrever no terminal na raiz do projeto: pytest -v

# Inicio dos testes em addInteraction()
def test_addInteraction_cria_uma_interacao():
    # Arrange: crio um minerador
    minerador = Minerador("dono/repo", "token_exemplo")

    # Act: chamo a função que quero testar
    minerador.addInteraction(Interacao("ana", "bob", 2, "comentario_issue"))

    # Assert
    assert minerador.quantidadeInteracoes() == 1
    assert minerador.mapaInteracoes[("ana", "bob", "comentario_issue")].peso == 2

def test_addInteraction_soma_peso_quando_repete():
    # Arrange: crio minerador
    minerador = Minerador("dono/repo", "token_exemplo")

    # Act: chamo a função duas vezes com a mesma chave
    minerador.addInteraction(Interacao("ana", "bob", 2, "comentario_issue"))
    minerador.addInteraction(Interacao("ana", "bob", 2, "comentario_issue"))

    # Assert
    assert minerador.quantidadeInteracoes() == 1
    assert minerador.mapaInteracoes[("ana", "bob", "comentario_issue")].peso == 4

def test_addInteraction_chaves_diferentes():
    # Arrange: crio minerador
    minerador = Minerador("dono/repo", "token_exemplo")

    # Act: chamo a função duas vezes com diferentes chaves, mesmo usuários, mas tipos diferentes
    minerador.addInteraction(Interacao("ana", "bob", 2, "comentario_issue"))
    minerador.addInteraction(Interacao("ana", "bob", 1, "fechamento_issue"))

    # Assert
    assert minerador.quantidadeInteracoes() == 2
    assert minerador.mapaInteracoes[("ana", "bob", "comentario_issue")].peso == 2
    assert minerador.mapaInteracoes[("ana", "bob", "fechamento_issue")].peso == 1

def test_addInteraction_contador_geral_interacoes():
    # Arrange: crio minerador
    minerador = Minerador("dono/repo", "token_exemplo")

    # Act: chamo a função X vezes passando qualquer chave
    minerador.addInteraction(Interacao("ana", "bob", 2, "comentario_issue"))
    minerador.addInteraction(Interacao("cecilia", "diego", 1, "fechamento_issue"))
    minerador.addInteraction(Interacao("ana", "bob", 5, "merge_pull"))

    # Assert
    assert minerador.contadorGeralInteracoes == 3
    assert minerador.quantidadeInteracoes() == 3
# Fim dos teste em addInteraction()

# Início dos teste em definirAutoresIssuesPRs()
def test_definirAutoresIssuesPRs():
    # Arrange: crio o minerador, injeto só os campos que a função lê, number e user.login
    minerador = Minerador("dono/repo", "token_exemplo")

    minerador._Minerador__issues = [{"number": 1, "user": {"login": "ana"}}]
    minerador._Minerador__pullRequests = [{"number": 2, "user": {"login": "bob"}}]

    # Act
    minerador.definirAutoresIssuesPRs()

    # Assert
    assert minerador._Minerador__autoresIssuesPRs == {"1": "ana", "2": "bob"}
# Fim dos teste em definirAutoresIssuesPRs()

# Início dos teste em minerarFechamentoIssues()
def test_minerarFechamentoIssues_sem_closed_by():
    # Arrange: closed_by = none
    minerador = Minerador("dono/repo", "token_exemplo")
    minerador._Minerador__issues = [{"closed_by": None, "user": {"login": "ana"}}]

    # Act
    minerador.minerarFechamentoIssues(0)

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_minerarFechamentoIssues_issue_e_um_pull_request():
    # Arrange
    minerador = Minerador("dono/repo", "token_exemplo")
    minerador._Minerador__issues = [{"closed_by": {"login": "bob"}, "user": {"login": "ana"}, "pull_request": {"url": "https://csfloat.com/"}}]

    # Act
    minerador.minerarFechamentoIssues(0)

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_minerarFechamentoIssues_quem_fechou_foi_o_autor():
    # Arrange
    minerador = Minerador("dono/repo", "token_exemplo")
    minerador._Minerador__issues = [{"closed_by": {"login": "astolfo"}, "user": {"login": "astolfo"}}]

    # Act
    minerador.minerarFechamentoIssues(0)

    # Assert
    assert minerador.quantidadeInteracoes() == 0

def test_minerarFechamentoIssues_caso_base_valido():
    # Arrange
    minerador = Minerador("dono/repo", "token_exemplo")
    minerador._Minerador__issues = [{"closed_by": {"login": "bob"}, "user": {"login": "ana"}}]

    # Act
    minerador.minerarFechamentoIssues(0)

    # Assert
    assert minerador.quantidadeInteracoes() == 1
    assert minerador.quantidadeUsuarios() == 2
    assert minerador.mapaInteracoes[("bob", "ana", "fechamento_issue")].peso == 1
# Fim dos teste em minerarFechamentoIssues()

# Início dos teste em aumentarContadorRequest()
def test_aumentarContadorRequest():
    # Arrange
    minerador = Minerador("dono/repo", "token_exemplo")

    # Act
    minerador.aumentarContadorRequest()
    minerador.aumentarContadorRequest()
    minerador.aumentarContadorRequest()

    # Assert
    assert minerador._Minerador__contadorRequests == 3
# Fim dos teste em aumentarContadorRequest()
