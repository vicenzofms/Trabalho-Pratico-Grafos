import pytest

from trabalho_pratico_grafos.grafos import GrafoMatrizAdjacencia, GrafoListaAdjacencia
from trabalho_pratico_grafos.analise.centralidade import centralidade_grau

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
