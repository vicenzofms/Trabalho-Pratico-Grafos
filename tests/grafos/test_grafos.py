import pytest

from trabalho_pratico_grafos.grafos import (
    GrafoListaAdjacencia, GrafoMatrizAdjacencia
)

# Para rodar: pytest tests/grafos/test_grafos.py -v
#
# Os testes são PARAMETRIZADOS sobre as duas implementações concretas
# (lista de adjacência e matriz de adjacência). Como toda a lógica de negócio
# mora no Template Method da GrafoAbstrato e as duas subclasses expõem a mesma
# interface, rodar cada caso nas duas implementações cobre, de uma só vez, a
# classe-base e as duas concretas — e ainda garante que elas se comportam de
# forma idêntica.


@pytest.fixture(params=[GrafoListaAdjacencia, GrafoMatrizAdjacencia],
                ids=["lista", "matriz"])
def Grafo(request):
    # Devolve a CLASSE; cada teste instancia com o nº de vértices que precisar.
    return request.param


def _triangulo(Grafo):
    """Triângulo dirigido 0->1->2->0 (3 arestas, peso 1.0)."""
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)
    grafo.adicionarAresta(1, 2)
    grafo.adicionarAresta(2, 0)
    return grafo


# Inicio dos testes em adicionarAresta()
def test_adicionarAresta_atualiza_graus_e_contagem(Grafo):
    # Arrange
    grafo = Grafo(3)

    # Act
    grafo.adicionarAresta(0, 1, 2.0)

    # Assert: a aresta existe, com grau de saída em u e de entrada em v
    assert grafo.existeAresta(0, 1) is True
    assert grafo.getQuantidadeArestas() == 1
    assert grafo.getGrauSaida(0) == 1
    assert grafo.getGrauEntrada(1) == 1
    assert grafo.getPesoAresta(0, 1) == 2.0


def test_adicionarAresta_eh_idempotente(Grafo):
    # Arrange: adicionar a MESMA aresta duas vezes não pode duplicar nem somar
    grafo = Grafo(3)

    # Act
    grafo.adicionarAresta(0, 1)
    grafo.adicionarAresta(0, 1)

    # Assert: continua sendo uma única aresta, graus inalterados
    assert grafo.getQuantidadeArestas() == 1
    assert grafo.getGrauSaida(0) == 1
    assert grafo.getGrauEntrada(1) == 1


def test_adicionarAresta_peso_invalido_levanta_erro(Grafo):
    # Arrange
    grafo = Grafo(3)

    # Act and Assert: peso <= 0 é inválido
    with pytest.raises(ValueError):
        grafo.adicionarAresta(0, 1, 0.0)
    with pytest.raises(ValueError):
        grafo.adicionarAresta(0, 1, -5.0)


def test_adicionarAresta_laco_levanta_erro(Grafo):
    # Arrange
    grafo = Grafo(3)

    # Act and Assert: u == v é um laço, proibido
    with pytest.raises(ValueError):
        grafo.adicionarAresta(1, 1)


def test_adicionarAresta_indice_invalido_levanta_erro(Grafo):
    # Arrange
    grafo = Grafo(3)

    # Act and Assert: vértice fora dos limites
    with pytest.raises(IndexError):
        grafo.adicionarAresta(0, 5)
    with pytest.raises(IndexError):
        grafo.adicionarAresta(-1, 0)
# Fim dos testes em adicionarAresta()


# Inicio dos testes em removeAresta()
def test_removeAresta_remove_e_atualiza_graus(Grafo):
    # Arrange: grafo com uma aresta
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)

    # Act
    grafo.removeAresta(0, 1)

    # Assert: aresta some, contagem e graus voltam a zero
    assert grafo.existeAresta(0, 1) is False
    assert grafo.getQuantidadeArestas() == 0
    assert grafo.getGrauSaida(0) == 0
    assert grafo.getGrauEntrada(1) == 0


def test_removeAresta_inexistente_eh_idempotente(Grafo):
    # Arrange: remover algo que não existe não pode quebrar nem mexer nos graus
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)

    # Act
    grafo.removeAresta(1, 2)  # essa aresta nunca foi adicionada

    # Assert: nada mudou
    assert grafo.getQuantidadeArestas() == 1
    assert grafo.getGrauSaida(1) == 0


def test_removeAresta_indice_invalido_levanta_erro(Grafo):
    # Arrange
    grafo = Grafo(3)

    # Act and Assert
    with pytest.raises(IndexError):
        grafo.removeAresta(0, 9)
# Fim dos testes em removeAresta()


# Inicio dos testes em isVazio()
def test_isVazio_grafo_sem_arestas(Grafo):
    # Arrange: grafo recém-criado, com vértices mas nenhuma aresta
    grafo = Grafo(3)

    # Act and Assert
    assert grafo.isVazio() is True


def test_isVazio_com_aresta_eh_falso(Grafo):
    # Arrange
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)

    # Act and Assert
    assert grafo.isVazio() is False
# Fim dos testes em isVazio()


# Inicio dos testes em isConexo()
def test_isConexo_grafo_vazio_de_vertices_eh_conexo(Grafo):
    # Arrange: 0 vértices é trivialmente conexo
    grafo = Grafo(0)

    # Act and Assert
    assert grafo.isConexo() is True


def test_isConexo_caminho_fracamente_conexo(Grafo):
    # Arrange: caminho dirigido 0->1->2; no grafo subjacente todos se alcançam
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)
    grafo.adicionarAresta(1, 2)

    # Act and Assert
    assert grafo.isConexo() is True


def test_isConexo_componente_isolado_nao_eh_conexo(Grafo):
    # Arrange: aresta 0-1 e o vértice 2 solto, sem nenhuma ligação
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)

    # Act and Assert
    assert grafo.isConexo() is False
# Fim dos testes em isConexo()


# Inicio dos testes em isCompleto()
def test_isCompleto_triangulo_dirigido_completo(Grafo):
    # Arrange: completo dirigido = toda aresta u->v com u != v (n*(n-1) arestas)
    grafo = Grafo(3)
    for u in range(3):
        for v in range(3):
            if u != v:
                grafo.adicionarAresta(u, v)

    # Act and Assert: 3*2 = 6 arestas
    assert grafo.isCompleto() is True


def test_isCompleto_faltando_aresta_nao_eh_completo(Grafo):
    # Arrange: triângulo só de ida (3 arestas, falta a volta de cada uma)
    grafo = _triangulo(Grafo)

    # Act and Assert
    assert grafo.isCompleto() is False
# Fim dos testes em isCompleto()


# Inicio dos testes em isIncidente()
def test_isIncidente_vertice_eh_ponta_da_aresta(Grafo):
    # Arrange
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)

    # Act and Assert: 0 e 1 incidem na aresta 0->1; 2 não
    assert grafo.isIncidente(0, 1, 0) is True
    assert grafo.isIncidente(0, 1, 1) is True
    assert grafo.isIncidente(0, 1, 2) is False


def test_isIncidente_aresta_inexistente_levanta_erro(Grafo):
    # Arrange
    grafo = Grafo(3)

    # Act and Assert: consultar relação de aresta que não existe é inconsistente
    with pytest.raises(ValueError):
        grafo.isIncidente(0, 1, 0)
# Fim dos testes em isIncidente()


# Inicio dos testes em isConvergente()
def test_isConvergente_arestas_que_chegam_no_mesmo_vertice(Grafo):
    # Arrange: 0->2 e 1->2 convergem em 2
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 2)
    grafo.adicionarAresta(1, 2)

    # Act and Assert
    assert grafo.isConvergente(0, 2, 1, 2) is True


def test_isConvergente_arestas_que_nao_convergem(Grafo):
    # Arrange: 0->1 e 1->2 não chegam no mesmo destino
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)
    grafo.adicionarAresta(1, 2)

    # Act and Assert
    assert grafo.isConvergente(0, 1, 1, 2) is False


def test_isConvergente_mesma_aresta_levanta_erro(Grafo):
    # Arrange
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 2)

    # Act and Assert: comparar a aresta com ela mesma é inválido
    with pytest.raises(ValueError):
        grafo.isConvergente(0, 2, 0, 2)
# Fim dos testes em isConvergente()


# Inicio dos testes em isDivergente()
def test_isDivergente_arestas_que_saem_do_mesmo_vertice(Grafo):
    # Arrange: 0->1 e 0->2 divergem a partir de 0
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)
    grafo.adicionarAresta(0, 2)

    # Act and Assert
    assert grafo.isDivergente(0, 1, 0, 2) is True


def test_isDivergente_arestas_que_nao_divergem(Grafo):
    # Arrange: 0->1 e 1->2 saem de vértices diferentes
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)
    grafo.adicionarAresta(1, 2)

    # Act and Assert
    assert grafo.isDivergente(0, 1, 1, 2) is False


def test_isDivergente_mesma_aresta_levanta_erro(Grafo):
    # Arrange
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)

    # Act and Assert
    with pytest.raises(ValueError):
        grafo.isDivergente(0, 1, 0, 1)
# Fim dos testes em isDivergente()


# Inicio dos testes em getPesoVertice() e setPesoVertice()
def test_peso_vertice_round_trip(Grafo):
    # Arrange
    grafo = Grafo(3)

    # Act
    grafo.setPesoVertice(1, 3.5)

    # Assert
    assert grafo.getPesoVertice(1) == 3.5


def test_peso_vertice_indice_invalido_levanta_erro(Grafo):
    # Arrange
    grafo = Grafo(3)

    # Act and Assert
    with pytest.raises(IndexError):
        grafo.setPesoVertice(9, 1.0)
    with pytest.raises(IndexError):
        grafo.getPesoVertice(9)
# Fim dos testes em getPesoVertice() e setPesoVertice()


# Inicio dos testes em getRotuloVertice() e setRotuloVertice()
def test_rotulo_vertice_round_trip(Grafo):
    # Arrange
    grafo = Grafo(3)

    # Act
    grafo.setRotuloVertice(2, "ana")

    # Assert
    assert grafo.getRotuloVertice(2) == "ana"


def test_rotulo_vertice_indice_invalido_levanta_erro(Grafo):
    # Arrange
    grafo = Grafo(3)

    # Act and Assert
    with pytest.raises(IndexError):
        grafo.setRotuloVertice(9, "x")
# Fim dos testes em getRotuloVertice() e setRotuloVertice()


# Inicio dos testes em setPesoAresta()
def test_setPesoAresta_atualiza_o_peso(Grafo):
    # Arrange
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1, 1.0)

    # Act
    grafo.setPesoAresta(0, 1, 4.0)

    # Assert
    assert grafo.getPesoAresta(0, 1) == 4.0


def test_setPesoAresta_aresta_inexistente_levanta_erro(Grafo):
    # Arrange
    grafo = Grafo(3)

    # Act and Assert
    with pytest.raises(ValueError):
        grafo.setPesoAresta(0, 1, 2.0)


def test_setPesoAresta_peso_invalido_levanta_erro(Grafo):
    # Arrange
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)

    # Act and Assert
    with pytest.raises(ValueError):
        grafo.setPesoAresta(0, 1, 0.0)
# Fim dos testes em setPesoAresta()


# Inicio dos testes em getPesoAresta()
def test_getPesoAresta_inexistente_lista_levanta_erro():
    # Arrange: na lista, peso de aresta inexistente é inconsistente -> erro
    grafo = GrafoListaAdjacencia(3)

    # Act and Assert
    with pytest.raises(ValueError):
        grafo.getPesoAresta(0, 1)


def test_getPesoAresta_inexistente_matriz_retorna_zero():
    # Arrange: na matriz, célula vazia é 0.0 por construção
    grafo = GrafoMatrizAdjacencia(3)

    # Act and Assert
    assert grafo.getPesoAresta(0, 1) == 0.0
# Fim dos testes em getPesoAresta()


# Inicio dos testes em isSucessor() e isPredecessor()
def test_isSucessor_e_isPredecessor(Grafo):
    # Arrange: aresta 0->1
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)

    # Act and Assert: 1 é sucessor de 0; 0 é predecessor de 1
    assert grafo.isSucessor(0, 1) is True
    assert grafo.isPredecessor(1, 0) is True
    # e o contrário não vale (grafo dirigido)
    assert grafo.isSucessor(1, 0) is False
    assert grafo.isPredecessor(0, 1) is False


def test_isSucessor_e_isPredecessor_mesmo_vertice_eh_falso(Grafo):
    # Arrange: relação de um vértice consigo mesmo é sempre falsa
    grafo = Grafo(3)

    # Act and Assert
    assert grafo.isSucessor(1, 1) is False
    assert grafo.isPredecessor(1, 1) is False
# Fim dos testes em isSucessor() e isPredecessor()


# Inicio dos testes em getSucessores() e getPredecessores()
def test_getSucessores_e_getPredecessores(Grafo):
    # Arrange: 0->1, 0->2 e 1->2
    grafo = Grafo(3)
    grafo.adicionarAresta(0, 1)
    grafo.adicionarAresta(0, 2)
    grafo.adicionarAresta(1, 2)

    # Act and Assert (ordenados para não depender da ordem interna)
    assert sorted(grafo.getSucessores(0)) == [1, 2]
    assert grafo.getSucessores(2) == []
    assert sorted(grafo.getPredecessores(2)) == [0, 1]
    assert grafo.getPredecessores(0) == []


def test_getSucessores_indice_invalido_levanta_erro(Grafo):
    # Arrange
    grafo = Grafo(3)

    # Act and Assert
    with pytest.raises(IndexError):
        grafo.getSucessores(9)
    with pytest.raises(IndexError):
        grafo.getPredecessores(9)
# Fim dos testes em getSucessores() e getPredecessores()
