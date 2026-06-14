import pytest

from trabalho_pratico_grafos.grafos import GrafoMatrizAdjacencia, GrafoListaAdjacencia
from trabalho_pratico_grafos.analise.caminhos import (
    bfs_distancias,
    dijkstra_distancias,
    bfs_brandes,
)

def _caminho(Classe=GrafoMatrizAdjacencia):
    """Grafo simples: 0 -> 1 -> 2."""
    g = Classe(3)
    g.adicionarAresta(0, 1)
    g.adicionarAresta(1, 2)
    return g


def _ponderado(Classe=GrafoMatrizAdjacencia):
    """Caminhos com pesos diferentes: rota indireta é mais barata."""
    g = Classe(3)
    g.adicionarAresta(0, 1, 10.0)
    g.adicionarAresta(0, 2, 1.0)
    g.adicionarAresta(2, 1, 1.0)
    return g


def _diamante(Classe=GrafoMatrizAdjacencia):
    """Dois caminhos mínimos entre 0 e 3."""
    g = Classe(4)
    g.adicionarAresta(0, 1)
    g.adicionarAresta(0, 2)
    g.adicionarAresta(1, 3)
    g.adicionarAresta(2, 3)
    return g

def test_bfs_calcula_distancia_por_niveis():
    # BFS mede quantidade de arestas até cada vértice.
    assert bfs_distancias(_caminho(), 0) == pytest.approx([0.0, 1.0, 2.0])


def test_bfs_ignora_pesos_das_arestas():
    # Mesmo com pesos diferentes, BFS considera apenas a quantidade de saltos.
    d = bfs_distancias(_ponderado(), 0)

    assert d == pytest.approx([0.0, 1.0, 1.0])


def test_bfs_vertice_inalcancavel_tem_distancia_infinita():
    # Sem caminho até o vértice, a distância permanece infinita.
    g = GrafoMatrizAdjacencia(3)
    g.adicionarAresta(0, 1)

    assert bfs_distancias(g, 0)[2] == float("inf")


@pytest.mark.parametrize("Classe", [GrafoMatrizAdjacencia, GrafoListaAdjacencia])
def test_bfs_funciona_nas_duas_estruturas(Classe):
    # Matriz e lista de adjacência devem produzir o mesmo resultado.
    assert bfs_distancias(_caminho(Classe), 0) == pytest.approx(
        [0.0, 1.0, 2.0]
    )

def test_dijkstra_escolhe_menor_custo():
    # O caminho 0->2->1 (custo 2) é escolhido no lugar de 0->1 (custo 10).
    d = dijkstra_distancias(_ponderado(), 0)

    assert d[1] == pytest.approx(2.0)
    assert d[2] == pytest.approx(1.0)


def test_dijkstra_diferencia_bfs_em_grafo_ponderado():
    # BFS e Dijkstra retornam resultados diferentes quando pesos importam.
    bfs = bfs_distancias(_ponderado(), 0)
    dijkstra = dijkstra_distancias(_ponderado(), 0)

    assert bfs[1] != pytest.approx(dijkstra[1])


def test_dijkstra_vertice_inalcancavel_tem_distancia_infinita():
    # Vértices sem caminho continuam com distância infinita.
    g = GrafoMatrizAdjacencia(3)
    g.adicionarAresta(0, 1)

    assert dijkstra_distancias(g, 0)[2] == float("inf")


@pytest.mark.parametrize("Classe", [GrafoMatrizAdjacencia, GrafoListaAdjacencia])
def test_dijkstra_funciona_nas_duas_estruturas(Classe):
    # O algoritmo deve ser independente da representação do grafo.
    assert dijkstra_distancias(_caminho(Classe), 0) == pytest.approx(
        [0.0, 1.0, 2.0]
    )

def test_brandes_conta_caminhos_minimos():
    # No diamante existem dois caminhos mínimos de 0 até 3.
    _, _, sigma = bfs_brandes(_diamante(), 0)

    assert sigma[3] == pytest.approx(2.0)


def test_brandes_armazena_predecessores_dos_caminhos():
    # Cada vértice guarda de onde veio no caminho mínimo.
    _, pred, _ = bfs_brandes(_caminho(), 0)

    assert pred[1] == [0]
    assert pred[2] == [1]


@pytest.mark.parametrize("Classe", [GrafoMatrizAdjacencia, GrafoListaAdjacencia])
def test_brandes_funciona_nas_duas_estruturas(Classe):
    # O cálculo de caminhos mínimos deve ser igual em matriz e lista.
    _, _, sigma = bfs_brandes(_diamante(Classe), 0)

    assert sigma[3] == pytest.approx(2.0)