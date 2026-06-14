import pytest

from trabalho_pratico_grafos.grafos import GrafoMatrizAdjacencia, GrafoListaAdjacencia
from trabalho_pratico_grafos.analise.coesao import (
    densidade,
    coeficiente_agrupamento,
    assortatividade_grau,
)
from grafos_exemplo import (
    grafo_completo,
    grafo_caminho,
    dois_triangulos_ligados,
    grafo_estrela_bidirecional,
)

# =============================================================================
# densidade()
# =============================================================================

def test_densidade_grafo_completo_eh_um():
    # Arrange: completo de 4 vértices → 12 arestas, máximo = 4*3 = 12
    grafo = grafo_completo(4)

    assert densidade(grafo) == pytest.approx(1.0)


def test_densidade_grafo_vazio_eh_zero():
    grafo = GrafoMatrizAdjacencia(5)  # sem arestas

    assert densidade(grafo) == pytest.approx(0.0)


def test_densidade_grafo_com_um_vertice_eh_zero():
    grafo = GrafoMatrizAdjacencia(1)

    assert densidade(grafo) == pytest.approx(0.0)


def test_densidade_caminho_valor_correto():
    # 0→1→2: 2 arestas, máximo = 3*2 = 6 → D = 1/3
    grafo = grafo_caminho(3)

    assert densidade(grafo) == pytest.approx(1 / 3)


@pytest.mark.parametrize("Classe", [GrafoMatrizAdjacencia, GrafoListaAdjacencia])
def test_densidade_independe_da_implementacao(Classe):
    # A "regra de ouro": análise usa só a API abstrata
    grafo = grafo_completo(3)
    # recria com a classe parametrizada
    g = Classe(3)
    for u in range(3):
        for v in range(3):
            if u != v:
                g.adicionarAresta(u, v)

    assert densidade(g) == pytest.approx(1.0)



def test_agrupamento_grafo_completo_eh_um():
    # Num completo, todo triângulo está fechado
    grafo = grafo_completo(4)

    assert coeficiente_agrupamento(grafo) == pytest.approx(1.0)


def test_agrupamento_grafo_caminho_eh_zero():
    # Linha: nenhum triângulo possível
    grafo = grafo_caminho(4)

    assert coeficiente_agrupamento(grafo) == pytest.approx(0.0)


def test_agrupamento_grafo_vazio_eh_zero():
    grafo = GrafoMatrizAdjacencia(5)

    assert coeficiente_agrupamento(grafo) == pytest.approx(0.0)


def test_agrupamento_dois_triangulos_entre_zero_e_um():
    # Dois triângulos ligados: coef. alto nos vértices internos, menor nos extremos
    grafo = dois_triangulos_ligados()
    resultado = coeficiente_agrupamento(grafo)

    assert 0.0 < resultado < 1.0


# =============================================================================
# assortatividade_grau()
# =============================================================================

def test_assortatividade_grafo_completo_eh_zero():
    # Todos os graus iguais → variância zero → correlação indefinida → retorna 0.0
    grafo = grafo_completo(4)

    assert assortatividade_grau(grafo) == pytest.approx(0.0)


def test_assortatividade_grafo_vazio_eh_zero():
    grafo = GrafoMatrizAdjacencia(5)

    assert assortatividade_grau(grafo) == pytest.approx(0.0)


def test_assortatividade_estrela_eh_negativa():
    # Hub de alto grau conectado a folhas de grau 1 → correlação negativa
    grafo = grafo_estrela_bidirecional(5)
    resultado = assortatividade_grau(grafo)

    assert resultado < 0.0


def test_assortatividade_retorna_entre_menos_um_e_um():
    # Invariante: correlação de Pearson sempre em [-1, 1]
    grafo = dois_triangulos_ligados()
    resultado = assortatividade_grau(grafo)

    assert -1.0 <= resultado <= 1.0
