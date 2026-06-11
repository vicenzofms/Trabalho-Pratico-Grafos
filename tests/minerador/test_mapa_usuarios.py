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
