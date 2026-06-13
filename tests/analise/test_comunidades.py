import pytest

from trabalho_pratico_grafos.grafos import GrafoMatrizAdjacencia
from trabalho_pratico_grafos.analise.comunidades import modularidade, louvain

# Para rodar: pytest tests/analise/test_comunidades.py -v
#
# Testes de sanidade da modularidade (a "função de avaliação").
# Os valores esperados foram calculados na mão pela forma "por comunidade":
#   Q = Σ_c [ Σin(c)/2m − (Σtot(c)/2m)² ]
# Como libs de grafo são proibidas, o gabarito é hardcoded no assert.


def _dois_triangulos_ligados() -> GrafoMatrizAdjacencia:
    """Triângulo {0,1,2} + triângulo {3,4,5}, ligados pela ponte 2-3.

    7 arestas, cada uma adicionada em uma única direção (peso 1.0). No grafo
    subjacente isso vira peso 1 em cada ponta, então k(i) = grau de i e m = 7.
    Graus: k = [2, 2, 3, 3, 2, 2] (os vértices 2 e 3 carregam a ponte).
    """
    grafo = GrafoMatrizAdjacencia(6)
    # triângulo 1
    grafo.adicionarAresta(0, 1)
    grafo.adicionarAresta(1, 2)
    grafo.adicionarAresta(0, 2)
    # triângulo 2
    grafo.adicionarAresta(3, 4)
    grafo.adicionarAresta(4, 5)
    grafo.adicionarAresta(3, 5)
    # ponte entre os dois triângulos
    grafo.adicionarAresta(2, 3)
    return grafo


def test_modularidade_tudo_numa_comunidade_eh_zero():
    # Arrange: qualquer grafo, com todos os vértices na mesma comunidade
    grafo = _dois_triangulos_ligados()
    particao = [0, 0, 0, 0, 0, 0]

    # Act
    q = modularidade(grafo, particao)

    # Assert: Σin = 2m e Σtot = 2m → Q = 1 − 1 = 0 (exato)
    assert q == pytest.approx(0.0, abs=1e-12)


def test_modularidade_cada_vertice_sozinho_eh_negativa():
    # Arrange: partição trivial, cada vértice na própria comunidade
    grafo = _dois_triangulos_ligados()
    particao = [0, 1, 2, 3, 4, 5]

    # Act
    q = modularidade(grafo, particao)

    # Assert: Σin(c) = 0 para todo c → Q = −Σ(k(i)/2m)².
    # k = [2,2,3,3,2,2], m = 7 → Q = −(4+4+9+9+4+4)/196 = −34/196 = −17/98
    assert q == pytest.approx(-17 / 98)
    assert q < 0


def test_modularidade_dois_triangulos_particao_correta():
    # Arrange: a partição "natural", cada triângulo é uma comunidade
    grafo = _dois_triangulos_ligados()
    particao = [0, 0, 0, 1, 1, 1]

    # Act
    q = modularidade(grafo, particao)

    # Assert: m = 7; cada triângulo tem Σin = 6 (3 arestas × 2 direções) e
    # Σtot = 7 (graus 2+2+3) → Q = 2·[6/14 − (7/14)²] = 5/14 ≈ 0.357
    assert q == pytest.approx(5 / 14)


# ---------------------------------------------------------------------------
# Testes do Louvain.
#
# Os ids de comunidade são ARBITRÁRIOS (poderia ser [0,0,0,1,1,1] ou
# [1,1,1,0,0,0]), então os asserts verificam a ESTRUTURA da partição — quais
# vértices caem juntos — e não os valores dos rótulos. Para isso comparamos
# rótulos entre si (p[i] == p[j]) em vez de fixar números.
# ---------------------------------------------------------------------------


def _completo(n: int) -> GrafoMatrizAdjacencia:
    """Grafo completo: toda aresta dirigida u -> v com u != v."""
    grafo = GrafoMatrizAdjacencia(n)
    for u in range(n):
        for v in range(n):
            if u != v:
                grafo.adicionarAresta(u, v)
    return grafo


def test_louvain_retorna_um_rotulo_por_vertice():
    # Protege contra o bug de composição: a saída tem que ter um rótulo por
    # vértice ORIGINAL, não um por comunidade.
    grafo = _dois_triangulos_ligados()

    particao = louvain(grafo)

    assert len(particao) == grafo.getQuantidadeVertices()


def test_louvain_acha_os_dois_triangulos():
    # Arrange
    grafo = _dois_triangulos_ligados()

    # Act
    particao = louvain(grafo)

    # Assert: cada triângulo é uma comunidade, e elas são distintas
    assert particao[0] == particao[1] == particao[2]   # triângulo {0,1,2} junto
    assert particao[3] == particao[4] == particao[5]   # triângulo {3,4,5} junto
    assert particao[0] != particao[3]                  # e separados entre si
    assert len(set(particao)) == 2
    # a modularidade da partição encontrada bate com o gabarito calculado na mão
    assert modularidade(grafo, particao) == pytest.approx(5 / 14)


def test_louvain_grafo_completo_uma_comunidade():
    # Num completo, qualquer divisão tem Q < 0 → o ótimo é todos juntos.
    grafo = _completo(5)

    particao = louvain(grafo)

    assert len(set(particao)) == 1


def test_louvain_nao_funde_componentes_desconexos():
    # Dois triângulos SEM ponte: componentes sem nenhuma aresta entre si.
    grafo = GrafoMatrizAdjacencia(6)
    for u, v in [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5)]:
        grafo.adicionarAresta(u, v)

    particao = louvain(grafo)

    # Jamais coloca vértices de componentes desconexos na mesma comunidade.
    assert particao[0] != particao[3]
    assert len(set(particao)) >= 2


def test_louvain_independe_da_numeracao_dos_vertices():
    # Mesmos dois triângulos, mas com os vértices INTERCALADOS:
    # triângulo A = {0,2,4}, triângulo B = {1,3,5}, ponte 4-1.
    # A saída tem que vir intercalada ([0,1,0,1,0,1]-like), provando que o
    # agrupamento segue o vértice, não a ordem dos ids.
    grafo = GrafoMatrizAdjacencia(6)
    for u, v in [(0, 2), (2, 4), (0, 4), (1, 3), (3, 5), (1, 5), (4, 1)]:
        grafo.adicionarAresta(u, v)

    particao = louvain(grafo)

    assert particao[0] == particao[2] == particao[4]   # triângulo A junto
    assert particao[1] == particao[3] == particao[5]   # triângulo B junto
    assert particao[0] != particao[1]
    assert len(set(particao)) == 2


def test_louvain_nao_e_pior_que_particoes_triviais():
    # Invariante: o Louvain nunca devolve algo pior que as partições triviais
    # (tudo junto, Q = 0; cada um sozinho, Q < 0).
    grafo = _dois_triangulos_ligados()
    n = grafo.getQuantidadeVertices()

    q_louvain = modularidade(grafo, louvain(grafo))

    assert q_louvain >= modularidade(grafo, [0] * n)            # tudo junto (Q = 0)
    assert q_louvain >= modularidade(grafo, list(range(n)))     # cada um sozinho (Q < 0)
