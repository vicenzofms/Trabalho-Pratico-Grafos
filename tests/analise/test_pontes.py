import pytest

from trabalho_pratico_grafos.grafos import GrafoMatrizAdjacencia
from trabalho_pratico_grafos.analise.pontes import (
    pontes_locais,
    arestas_intercomunidade,
    pontes_classicas,
)

# Para rodar: pytest tests/analise/test_pontes.py -v
#
# Ponte local: aresta {u, v} cujos extremos NÃO têm vizinho em comum — o único
# atalho entre os dois "mundos" (remover faz a distância u-v ir de 1 para >2).
# Trabalha sobre o grafo subjacente (não-dirigido), então:
#   - dentro de um triângulo/clique nada é ponte (todo par compartilha vizinho);
#   - numa árvore (caminho, estrela) TODA aresta é ponte (sem triângulos);
#   - o retorno é um par não-dirigido na forma canônica (u, v) com u < v,
#     independente de como a aresta estava orientada no grafo original.
# Os gabaritos abaixo saem na mão; comparo como conjunto pois a ordem não é parte
# do contrato.


def _dois_triangulos_ligados() -> GrafoMatrizAdjacencia:
    """Triângulo {0,1,2} + triângulo {3,4,5}, ligados pela ponte 2-3."""
    grafo = GrafoMatrizAdjacencia(6)
    for u, v in [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (2, 3)]:
        grafo.adicionarAresta(u, v)
    return grafo


def _caminho(n: int) -> GrafoMatrizAdjacencia:
    """Caminho 0-1-2-...-(n-1). Sem triângulos → toda aresta é ponte local."""
    grafo = GrafoMatrizAdjacencia(n)
    for u in range(n - 1):
        grafo.adicionarAresta(u, u + 1)
    return grafo


def _estrela(n: int) -> GrafoMatrizAdjacencia:
    """Estrela: centro 0 ligado a 1..n-1. Sem triângulos → toda aresta é ponte."""
    grafo = GrafoMatrizAdjacencia(n)
    for folha in range(1, n):
        grafo.adicionarAresta(0, folha)
    return grafo


def _completo(n: int) -> GrafoMatrizAdjacencia:
    """Grafo completo: toda aresta dirigida u -> v com u != v."""
    grafo = GrafoMatrizAdjacencia(n)
    for u in range(n):
        for v in range(n):
            if u != v:
                grafo.adicionarAresta(u, v)
    return grafo


def _quadrado() -> GrafoMatrizAdjacencia:
    """Ciclo 0-1-2-3-0. Toda aresta está num ciclo → NENHUMA é ponte clássica
    (mas todas são pontes locais — é o caso que separa as duas leituras)."""
    grafo = GrafoMatrizAdjacencia(4)
    for u, v in [(0, 1), (1, 2), (2, 3), (0, 3)]:
        grafo.adicionarAresta(u, v)
    return grafo


# Inicio dos testes em pontes_locais()
def test_pontes_locais_dois_triangulos_so_a_ponte():
    # Dentro de cada triângulo todo par de vizinhos compartilha o terceiro
    # vértice; só a aresta 2-3 liga dois mundos sem vizinho em comum.
    grafo = _dois_triangulos_ligados()

    pontes = pontes_locais(grafo)

    assert set(pontes) == {(2, 3)}


def test_pontes_locais_triangulo_isolado_nao_tem_ponte():
    # Em um triângulo, cada aresta {u,v} tem o terceiro vértice como vizinho
    # comum → nenhuma ponte local.
    grafo = GrafoMatrizAdjacencia(3)
    for u, v in [(0, 1), (1, 2), (0, 2)]:
        grafo.adicionarAresta(u, v)

    pontes = pontes_locais(grafo)

    assert pontes == []


def test_pontes_locais_completo_nao_tem_ponte():
    # Em um completo (n >= 3), todo par de vértices compartilha os outros n-2
    # vértices como vizinhos → nenhuma ponte local.
    grafo = _completo(4)

    pontes = pontes_locais(grafo)

    assert pontes == []


def test_pontes_locais_caminho_todas_as_arestas():
    # Caminho 0-1-2-3: nenhuma aresta fecha triângulo, logo toda aresta é ponte.
    grafo = _caminho(4)

    pontes = pontes_locais(grafo)

    assert set(pontes) == {(0, 1), (1, 2), (2, 3)}


def test_pontes_locais_estrela_todas_as_arestas():
    # Estrela com centro 0 e folhas 1,2,3: as folhas só conhecem o centro e não
    # têm vizinho em comum com ele → toda aresta centro-folha é ponte.
    grafo = _estrela(4)

    pontes = pontes_locais(grafo)

    assert set(pontes) == {(0, 1), (0, 2), (0, 3)}


def test_pontes_locais_aresta_anti_paralela_conta_uma_vez():
    # 0 <-> 1 (anti-paralela). No subjacente vira uma única ligação não-dirigida;
    # a ponte deve aparecer UMA vez como (0, 1), não duas (nem (1, 0)).
    grafo = GrafoMatrizAdjacencia(2)
    grafo.adicionarAresta(0, 1)
    grafo.adicionarAresta(1, 0)

    pontes = pontes_locais(grafo)

    assert pontes == [(0, 1)]
    assert len(pontes) == 1


def test_pontes_locais_orientacao_canonica_independe_da_direcao():
    # Única aresta existe SÓ como 3 -> 1 no grafo original. Como ponte local é
    # não-dirigida, ela sai na forma canônica (1, 3) com u < v — e não (3, 1).
    grafo = GrafoMatrizAdjacencia(4)
    grafo.adicionarAresta(3, 1)

    pontes = pontes_locais(grafo)

    assert pontes == [(1, 3)]


def test_pontes_locais_grafo_sem_arestas_eh_vazio():
    # Sem arestas não há ligação nenhuma para ser ponte.
    grafo = GrafoMatrizAdjacencia(3)

    pontes = pontes_locais(grafo)

    assert pontes == []
# Fim dos testes em pontes_locais()


# ---------------------------------------------------------------------------
# Testes de arestas_intercomunidade.
#
# Leitura "macro" da ponte: arestas DIRIGIDAS cujos extremos caíram em
# comunidades diferentes. Recebe a partição por parâmetro (não roda o Louvain).
# Como o retorno é dirigido, (u, v) e (v, u) são distintos e ambos podem
# aparecer — ao contrário da pontes_locais, que devolve o par não-dirigido uma
# vez só na forma u < v. Comparo como conjunto, pois a ordem não é contratual.
# ---------------------------------------------------------------------------


# Inicio dos testes em arestas_intercomunidade()
def test_arestas_intercomunidade_dois_triangulos_so_a_ponte():
    # Partição natural (cada triângulo uma comunidade): a única aresta que cruza
    # a fronteira é a ponte 2->3.
    grafo = _dois_triangulos_ligados()
    particao = [0, 0, 0, 1, 1, 1]

    arestas = arestas_intercomunidade(grafo, particao)

    assert set(arestas) == {(2, 3)}


def test_arestas_intercomunidade_tudo_numa_comunidade_eh_vazio():
    # Todos na mesma comunidade → nenhuma aresta cruza fronteira.
    grafo = _dois_triangulos_ligados()
    particao = [0, 0, 0, 0, 0, 0]

    arestas = arestas_intercomunidade(grafo, particao)

    assert arestas == []


def test_arestas_intercomunidade_cada_vertice_sozinho_todas_as_arestas():
    # Cada vértice em sua própria comunidade → TODA aresta dirigida cruza.
    grafo = _dois_triangulos_ligados()
    particao = [0, 1, 2, 3, 4, 5]

    arestas = arestas_intercomunidade(grafo, particao)

    assert set(arestas) == {(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (2, 3)}


def test_arestas_intercomunidade_anti_paralela_conta_as_duas_direcoes():
    # Ponte anti-paralela (2<->3) entre comunidades distintas. Como o retorno é
    # dirigido, as DUAS arestas aparecem: (2,3) e (3,2) — exatamente o ponto que
    # diferencia esta função da pontes_locais (que devolveria {2,3} uma vez só).
    grafo = _dois_triangulos_ligados()
    grafo.adicionarAresta(3, 2)  # torna a ponte 2-3 anti-paralela
    particao = [0, 0, 0, 1, 1, 1]

    arestas = arestas_intercomunidade(grafo, particao)

    assert set(arestas) == {(2, 3), (3, 2)}
# Fim dos testes em arestas_intercomunidade()


# ---------------------------------------------------------------------------
# Testes de pontes_classicas.
#
# Ponte clássica (aresta de corte): aresta que NÃO está em ciclo nenhum — cortá-la
# aumenta o nº de componentes (separa a subárvore de um lado do resto). É a leitura
# mais ESTRITA: toda ponte clássica é ponte local, mas nem toda ponte local é
# clássica. Detectada via DFS iterativa (Tarjan, low-link). Retorno não-dirigido,
# par canônico (u, v) com u < v — igual à pontes_locais. Comparo como conjunto.
# ---------------------------------------------------------------------------


# Inicio dos testes em pontes_classicas()
def test_pontes_classicas_dois_triangulos_so_a_ponte():
    # A ponte 2-3 é a única aresta fora de ciclo; cortá-la separa os triângulos.
    grafo = _dois_triangulos_ligados()

    pontes = pontes_classicas(grafo)

    assert set(pontes) == {(2, 3)}


def test_pontes_classicas_quadrado_nao_tem_ponte():
    # O DISCRIMINANTE: num ciclo toda aresta tem rota alternativa dando a volta →
    # nenhuma é ponte clássica. (A pontes_locais devolveria as 4 — ver teste abaixo.)
    grafo = _quadrado()

    pontes = pontes_classicas(grafo)

    assert pontes == []


def test_pontes_classicas_caminho_todas_as_arestas():
    # Caminho é uma árvore: nenhuma aresta está em ciclo → todas são pontes.
    grafo = _caminho(4)

    pontes = pontes_classicas(grafo)

    assert set(pontes) == {(0, 1), (1, 2), (2, 3)}


def test_pontes_classicas_triangulo_isolado_nao_tem_ponte():
    # Triângulo é um ciclo → nenhuma aresta é ponte clássica.
    grafo = GrafoMatrizAdjacencia(3)
    for u, v in [(0, 1), (1, 2), (0, 2)]:
        grafo.adicionarAresta(u, v)

    pontes = pontes_classicas(grafo)

    assert pontes == []


def test_pontes_classicas_grafo_desconexo():
    # Dois triângulos SEM ponte entre eles: exercita o laço motor externo (uma DFS
    # por componente). Cada triângulo é um ciclo → nenhuma ponte em componente algum.
    grafo = GrafoMatrizAdjacencia(6)
    for u, v in [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5)]:
        grafo.adicionarAresta(u, v)

    pontes = pontes_classicas(grafo)

    assert pontes == []


def test_pontes_classicas_aresta_anti_paralela_conta_uma_vez():
    # Ponte 2<->3 anti-paralela. No subjacente vira uma ligação não-dirigida só;
    # a ponte sai UMA vez como (2, 3), não duas (resultado não-dirigido).
    grafo = _dois_triangulos_ligados()
    grafo.adicionarAresta(3, 2)  # torna a ponte anti-paralela

    pontes = pontes_classicas(grafo)

    assert pontes == [(2, 3)]


def test_pontes_classicas_grafo_sem_arestas_eh_vazio():
    # Sem arestas não há ligação para ser ponte (e cobre o caso de borda).
    grafo = GrafoMatrizAdjacencia(3)

    pontes = pontes_classicas(grafo)

    assert pontes == []


def test_pontes_classicas_e_locais_divergem_no_quadrado():
    # Capstone da hierarquia "clássica ⊊ local": no ciclo, TODA aresta é ponte
    # local (vértices opostos não se conhecem), mas NENHUMA é clássica (há rota
    # dando a volta). É o que prova que as duas leituras medem coisas diferentes.
    grafo = _quadrado()

    assert set(pontes_locais(grafo)) == {(0, 1), (1, 2), (2, 3), (0, 3)}
    assert pontes_classicas(grafo) == []
# Fim dos testes em pontes_classicas()
