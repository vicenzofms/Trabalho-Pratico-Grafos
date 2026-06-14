import pytest

from trabalho_pratico_grafos.grafos import GrafoMatrizAdjacencia, GrafoListaAdjacencia
from trabalho_pratico_grafos.analise.centralidade import (
    centralidade_grau,
    pagerank,
    centralidade_autovetor,
)

# Para rodar: pytest tests/analise/test_centralidade.py -v
#
# Testes da centralidade de grau. Em grafo DIRECIONADO o grau se divide em entrada
# (quantos procuram o vértice) e saída (quantos o vértice procura), por isso a
# função devolve {"entrada": [...], "saida": [...]}, cada lista normalizada por
# (n - 1) e indexada pelo id do vértice.
#
# Como libs de grafo são proibidas, todo gabarito é calculado na mão e hardcoded
# no assert.


def _estrela(Classe=GrafoMatrizAdjacencia) -> GrafoMatrizAdjacencia:
    """Estrela com o centro 0 RECEBENDO de todas as folhas: 1->0, 2->0, 3->0.

    n = 4. grau_entrada = [3, 0, 0, 0]; grau_saida = [0, 1, 1, 1].
    O centro é um "ímã de atenção" (entrada máxima, saída zero); as folhas são
    "puras agentes" (saída, sem entrada).
    """
    grafo = Classe(4)
    grafo.adicionarAresta(1, 0)
    grafo.adicionarAresta(2, 0)
    grafo.adicionarAresta(3, 0)
    return grafo


def _caminho(Classe=GrafoMatrizAdjacencia) -> GrafoMatrizAdjacencia:
    """Caminho dirigido 0 -> 1 -> 2.

    n = 3. grau_entrada = [0, 1, 1]; grau_saida = [1, 1, 0].
    Fixture com entrada != saída em todo vértice: pega bug de troca dos dois.
    """
    grafo = Classe(3)
    grafo.adicionarAresta(0, 1)
    grafo.adicionarAresta(1, 2)
    return grafo


def _completo(n: int, Classe=GrafoMatrizAdjacencia) -> GrafoMatrizAdjacencia:
    """Completo dirigido: toda aresta u -> v com u != v.

    Cada vértice manda para n-1 e recebe de n-1, então entrada = saida = 1.0
    para todos depois de normalizar por (n - 1).
    """
    grafo = Classe(n)
    for u in range(n):
        for v in range(n):
            if u != v:
                grafo.adicionarAresta(u, v)
    return grafo


def test_grau_estrela_separa_entrada_e_saida():
    # Arrange
    grafo = _estrela()

    # Act
    r = centralidade_grau(grafo)

    # Assert: centro (0) recebe de 3 folhas -> entrada 3/3 = 1.0, saída 0.
    assert r["entrada"][0] == pytest.approx(1.0)
    assert r["saida"][0] == pytest.approx(0.0)
    # folhas: não recebem nada, mandam 1 aresta -> saída 1/3.
    for folha in (1, 2, 3):
        assert r["entrada"][folha] == pytest.approx(0.0)
        assert r["saida"][folha] == pytest.approx(1 / 3)


def test_grau_caminho_distingue_entrada_de_saida():
    # Arrange: 0 -> 1 -> 2 (n = 3, normaliza por 2)
    grafo = _caminho()

    # Act
    r = centralidade_grau(grafo)

    # Assert: gabarito calculado na mão.
    assert r["entrada"] == pytest.approx([0.0, 0.5, 0.5])
    assert r["saida"] == pytest.approx([0.5, 0.5, 0.0])


def test_grau_completo_tudo_normalizado_em_um():
    # Arrange
    grafo = _completo(3)

    # Act
    r = centralidade_grau(grafo)

    # Assert: no completo todos são equivalentes e o valor bate exatamente em 1.0
    # (prova que a separação entrada/saída mantém a métrica em [0, 1]).
    assert r["entrada"] == pytest.approx([1.0, 1.0, 1.0])
    assert r["saida"] == pytest.approx([1.0, 1.0, 1.0])


def test_grau_retorna_uma_entrada_por_vertice():
    # Protege o contrato: uma posição por vértice em cada lista, chaves certas.
    grafo = _completo(5)

    r = centralidade_grau(grafo)

    assert set(r.keys()) == {"entrada", "saida"}
    assert len(r["entrada"]) == grafo.getQuantidadeVertices()
    assert len(r["saida"]) == grafo.getQuantidadeVertices()


def test_grau_um_unico_vertice_nao_divide_por_zero():
    # Caso especial n = 1: (n - 1) = 0 quebraria a divisão; deve devolver 0.0.
    grafo = GrafoMatrizAdjacencia(1)

    r = centralidade_grau(grafo)

    assert r == {"entrada": [0.0], "saida": [0.0]}


def test_grau_grafo_vazio_devolve_listas_vazias():
    # n = 0: sem vértices, sem valores, sem explosão.
    grafo = GrafoMatrizAdjacencia(0)

    r = centralidade_grau(grafo)

    assert r == {"entrada": [], "saida": []}


@pytest.mark.parametrize("Classe", [GrafoMatrizAdjacencia, GrafoListaAdjacencia])
def test_grau_independe_da_implementacao_do_grafo(Classe):
    # A "regra de ouro": a análise usa só a API abstrata, então matriz e lista
    # de adjacência têm que dar exatamente o mesmo resultado.
    r = centralidade_grau(_estrela(Classe))

    assert r["entrada"] == pytest.approx([1.0, 0.0, 0.0, 0.0])
    assert r["saida"] == pytest.approx([0.0, 1 / 3, 1 / 3, 1 / 3])


# ---------------------------------------------------------------------------
# Testes do PageRank (iteração de potência com d = 0.85).
#
# Propriedade que vale em QUALQUER grafo: os valores somam 1 (é uma
# distribuição de probabilidade - a fração do tempo do "navegador aleatório"
# em cada nó). Os gabaritos exatos foram calculados na mão.
# ---------------------------------------------------------------------------


def _ciclo(n: int, Classe=GrafoMatrizAdjacencia) -> GrafoMatrizAdjacencia:
    """Ciclo dirigido 0 -> 1 -> ... -> (n-1) -> 0. Totalmente simétrico."""
    grafo = Classe(n)
    for u in range(n):
        grafo.adicionarAresta(u, (u + 1) % n)
    return grafo


def test_pagerank_ciclo_simetrico_todos_iguais():
    # Num ciclo todos os vértices são equivalentes -> PageRank igual = 1/n.
    pr = pagerank(_ciclo(3))

    assert pr == pytest.approx([1 / 3, 1 / 3, 1 / 3])


def test_pagerank_sempre_soma_um():
    # A massa total se conserva (incl. com sumidouro) -> Σ PR = 1.
    assert sum(pagerank(_ciclo(5))) == pytest.approx(1.0)
    assert sum(pagerank(_completo(4))) == pytest.approx(1.0)
    assert sum(pagerank(_estrela())) == pytest.approx(1.0)


def test_pagerank_dangling_redistribui_a_massa():
    # 0 -> 1, e o nó 1 é sumidouro (grau de saída 0). Resolvendo o sistema na
    # mão com d = 0.85: PR[0] = 1/(2 + d) = 1/2.85, PR[1] = 1 - PR[0].
    # Se a massa do sumidouro não fosse redistribuída, a soma cairia abaixo de 1.
    grafo = GrafoMatrizAdjacencia(2)
    grafo.adicionarAresta(0, 1)

    pr = pagerank(grafo)

    assert pr[0] == pytest.approx(1 / 2.85)
    assert pr[1] == pytest.approx(1 - 1 / 2.85)
    assert sum(pr) == pytest.approx(1.0)


def test_pagerank_quem_recebe_mais_e_mais_central():
    # A->B, A->C, B->C, C->A. O nó C (2) recebe de dois; B (1) só de A e ainda
    # dividido (A tem 2 saídas). Então PR[C] > PR[A] > PR[B].
    grafo = GrafoMatrizAdjacencia(3)
    for u, v in [(0, 1), (0, 2), (1, 2), (2, 0)]:
        grafo.adicionarAresta(u, v)

    pr = pagerank(grafo)

    assert pr[2] > pr[0] > pr[1]
    assert sum(pr) == pytest.approx(1.0)


@pytest.mark.parametrize("Classe", [GrafoMatrizAdjacencia, GrafoListaAdjacencia])
def test_pagerank_independe_da_implementacao_do_grafo(Classe):
    # Regra de ouro: matriz e lista de adjacência dão o mesmo resultado.
    pr = pagerank(_ciclo(3, Classe))

    assert pr == pytest.approx([1 / 3, 1 / 3, 1 / 3])


# ---------------------------------------------------------------------------
# Testes da centralidade de autovetor (iteração de potência + normalização).
#
# IMPORTANTE: o autovetor "balança" e não converge em grafos BIPARTIDOS
# (estrela, ciclos pares) nem em alguns dirigidos. Por isso todas as fixtures
# aqui são NÃO-bipartidas (têm triângulos) e simétricas, onde o gabarito é
# limpo. O resultado vem normalizado em L2, então a norma do vetor é ~1.
# ---------------------------------------------------------------------------


def _norma_l2(vetor: list[float]) -> float:
    return sum(v * v for v in vetor) ** 0.5


def _triangulo_bidirecional(Classe=GrafoMatrizAdjacencia) -> GrafoMatrizAdjacencia:
    """Triângulo 0-1-2 com as duas direções de cada aresta. Não-bipartido."""
    grafo = Classe(3)
    for u, v in [(0, 1), (1, 0), (1, 2), (2, 1), (0, 2), (2, 0)]:
        grafo.adicionarAresta(u, v)
    return grafo


def _dois_triangulos_bidirecional(Classe=GrafoMatrizAdjacencia) -> GrafoMatrizAdjacencia:
    """Triângulo {0,1,2} + triângulo {2,3,4}, compartilhando o vértice-ponte 2.

    O vértice 2 participa dos dois triângulos, então é o mais central.
    """
    grafo = Classe(5)
    arestas = [(0, 1), (0, 2), (1, 2),  # triângulo da esquerda
               (2, 3), (2, 4), (3, 4)]  # triângulo da direita
    for u, v in arestas:
        grafo.adicionarAresta(u, v)
        grafo.adicionarAresta(v, u)     # nas duas direções
    return grafo


def test_autovetor_triangulo_simetrico_todos_iguais():
    # Triângulo é simétrico -> todos têm a mesma importância. Normalizado em L2,
    # cada um vale 1/raiz(3) ≈ 0.577.
    x = centralidade_autovetor(_triangulo_bidirecional())

    assert x == pytest.approx([1 / 3 ** 0.5, 1 / 3 ** 0.5, 1 / 3 ** 0.5])


def test_autovetor_completo_todos_iguais():
    # No completo K4 todos são equivalentes -> 1/raiz(4) = 0.5.
    x = centralidade_autovetor(_completo(4))

    assert x == pytest.approx([0.5, 0.5, 0.5, 0.5])


def test_autovetor_resultado_normalizado_em_l2():
    # A normalização garante que o vetor de saída tem "tamanho" (norma L2) ~1.
    x = centralidade_autovetor(_dois_triangulos_bidirecional())

    assert _norma_l2(x) == pytest.approx(1.0)


def test_autovetor_ponte_e_a_mais_central():
    # O vértice 2 está nos dois triângulos -> tem que ser o de maior pontuação,
    # e os outros quatro (simétricos entre si) ficam iguais e menores.
    x = centralidade_autovetor(_dois_triangulos_bidirecional())

    assert x[2] == max(x)
    assert x[2] > x[0]
    assert x[0] == pytest.approx(x[1]) == pytest.approx(x[3]) == pytest.approx(x[4])


@pytest.mark.parametrize("Classe", [GrafoMatrizAdjacencia, GrafoListaAdjacencia])
def test_autovetor_independe_da_implementacao_do_grafo(Classe):
    # Regra de ouro: matriz e lista de adjacência dão o mesmo resultado.
    x = centralidade_autovetor(_triangulo_bidirecional(Classe))

    assert x == pytest.approx([1 / 3 ** 0.5, 1 / 3 ** 0.5, 1 / 3 ** 0.5])
