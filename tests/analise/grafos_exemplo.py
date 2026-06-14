from trabalho_pratico_grafos.grafos import GrafoMatrizAdjacencia


def grafo_estrela_bidirecional(n: int) -> GrafoMatrizAdjacencia:
    """Vértice 0 é o centro, conectado bidirecionalmente a todos os outros.

    n=5: grau de cada folha = 2 (1 entrada + 1 saída), grau do centro = 2*(n-1).
    """
    grafo = GrafoMatrizAdjacencia(n)
    for folha in range(1, n):
        grafo.adicionarAresta(0, folha)
        grafo.adicionarAresta(folha, 0)
    return grafo


def grafo_completo(n: int) -> GrafoMatrizAdjacencia:
    """Grafo dirigido completo: toda aresta u→v com u != v."""
    grafo = GrafoMatrizAdjacencia(n)
    for u in range(n):
        for v in range(n):
            if u != v:
                grafo.adicionarAresta(u, v)
    return grafo


def dois_triangulos_ligados() -> GrafoMatrizAdjacencia:
    """Triângulo {0,1,2} + triângulo {3,4,5}, ligados pela ponte 2→3.

    7 arestas. Louvain deve achar 2 comunidades. A ponte 2-3 é ponte local e
    intercomunidade.
    """
    grafo = GrafoMatrizAdjacencia(6)
    for u, v in [(0, 1), (1, 2), (0, 2), (3, 4), (4, 5), (3, 5), (2, 3)]:
        grafo.adicionarAresta(u, v)
    return grafo


def grafo_caminho(n: int) -> GrafoMatrizAdjacencia:
    """Linha dirigida: 0→1→2→...→(n-1). Nenhum triângulo → clustering = 0."""
    grafo = GrafoMatrizAdjacencia(n)
    for i in range(n - 1):
        grafo.adicionarAresta(i, i + 1)
    return grafo


def grafo_simetrico(n: int) -> GrafoMatrizAdjacencia:
    """Ciclo bidirecional: 0↔1↔2↔...↔(n-1)↔0.

    Todos os vértices são equivalentes → PageRank e autovetor devem dar valores iguais.
    """
    grafo = GrafoMatrizAdjacencia(n)
    for i in range(n):
        proximo = (i + 1) % n
        grafo.adicionarAresta(i, proximo)
        grafo.adicionarAresta(proximo, i)
    return grafo