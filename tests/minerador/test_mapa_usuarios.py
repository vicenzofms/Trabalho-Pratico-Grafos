from trabalho_pratico_grafos.minerador.mapa_usuarios import MapaUsuarios

# Para rodar escrever no terminal na raiz do projeto: pytest -v

# Início dos testes em buscarOuRegistrar()
def test_buscarOuRegistrar_novo_usuario():
    # Arrange
    mapa = MapaUsuarios()

    # Act
    id = mapa.buscarOuRegistrar("ana")

    # Assert
    assert id == 0

def test_buscarOuRegistrar_ids_sequenciais():
    # Arrange
    mapa = MapaUsuarios()

    # Act
    id0 = mapa.buscarOuRegistrar("ana")
    id1 = mapa.buscarOuRegistrar("bob")
    id2 = mapa.buscarOuRegistrar("cecilia")

    # Assert
    assert id0 == 0
    assert id1 == 1
    assert id2 == 2

def test_buscarOuRegistrar_usuario_repetido():
    # Arrange
    mapa = MapaUsuarios()

    # Act
    id1 = mapa.buscarOuRegistrar("ana")
    id2 = mapa.buscarOuRegistrar("ana")

    # Assert
    assert id1 == id2

def test_buscarNome_retorna_username():
    # Arrange
    mapa = MapaUsuarios()

    # Act
    mapa.buscarOuRegistrar("ana")

    # Assert
    assert mapa.buscarNome(0) == "ana"

def test_quantidadeDeUsuarios_vazio():
    # Arrange
    mapa = MapaUsuarios()
    # Act and Assert
    assert mapa.quantidadeDeUsuarios() == 0

def test_quantidadeDeUsuarios_apos_registros():
    # Arrange
    mapa = MapaUsuarios()

    # Act
    mapa.buscarOuRegistrar("ana")
    mapa.buscarOuRegistrar("bob")
    mapa.buscarOuRegistrar("bob")

    # Assert
    assert mapa.quantidadeDeUsuarios() == 2

# Início dos testes em exportarUsuarios()
def test_exportarUsuarios_estrutura():
    # Arrange
    mapa = MapaUsuarios()
    mapa.buscarOuRegistrar("ana")
    mapa.buscarOuRegistrar("bob")

    # Act
    exportado = mapa.exportarUsuarios()

    # Assert
    assert exportado["ids_por_username"] == {"ana": 0, "bob": 1}
    assert exportado["usernames_por_id"] == ["ana", "bob"]
    assert exportado["quantidade"] == 2

def test_exportarUsuarios_retorna_copias():
    # Arrange
    mapa = MapaUsuarios()
    mapa.buscarOuRegistrar("ana")

    # Act: altero o dado exportado
    exportado = mapa.exportarUsuarios()
    exportado["ids_por_username"]["intruso"] = 99
    exportado["usernames_por_id"].append("intruso")

    # Assert: o mapa interno não pode ser afetado
    assert mapa.quantidadeDeUsuarios() == 1
    assert mapa.buscarNome(0) == "ana"
# Fim dos testes em exportarUsuarios()
