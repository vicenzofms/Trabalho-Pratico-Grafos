import heapq
from collections import deque
from typing import NamedTuple
from trabalho_pratico_grafos.grafos import GrafoAbstrato


class ResultadoBrandes(NamedTuple):
    pilha: list[int]
    predecessores: list[list[int]]
    sigma: list[float]


def bfs_distancias(grafo: GrafoAbstrato, origem: int) -> list[float]:
    """Distância (número de arestas) da origem até cada vértice via busca em profundidade.

    Ignora os pesos das arestas. Vértices inalcançáveis ficam com inf.
    """
    n = grafo.getQuantidadeVertices()
    # começa todo mundo como inalcançável
    distancias = [float('inf')] * n
    distancias[origem] = 0.0

    fila = deque([origem])
    while fila:
        u = fila.popleft()
        for v in grafo.getSucessores(u):
            # se v ainda não foi visitado, é alcançado por u
            if distancias[v] == float('inf'):
                distancias[v] = distancias[u] + 1
                fila.append(v)
    return distancias


def dijkstra_distancias(grafo: GrafoAbstrato, origem: int) -> list[float]:
    """Menor distância (somando os pesos) da origem até cada vértice via Dijkstra.

    Assume pesos positivos (garantido por adicionarAresta). Vértices
    inalcançáveis ficam com inf.
    """
    n = grafo.getQuantidadeVertices()
    distancias = [float('inf')] * n
    distancias[origem] = 0.0

    # fila de prioridade com pares (distância acumulada, vértice)
    heap = [(0.0, origem)]
    while heap:
        d, u = heapq.heappop(heap)
        # entrada desatualizada na heap, já tem caminho melhor
        if d > distancias[u]:
            continue
        for v in grafo.getSucessores(u):
            novaDistancia = d + grafo.getPesoAresta(u, v)
            # Se a nova distância for menor, atualiza a aresta u -> v
            if novaDistancia < distancias[v]:
                distancias[v] = novaDistancia
                heapq.heappush(heap, (novaDistancia, v))
    return distancias


def bfs_brandes(grafo: GrafoAbstrato, origem: int) -> ResultadoBrandes:
    """BFS que coleta as informações necessárias para o algoritmo de Brandes.

    --- O que é centralidade de intermediação? ---
    A centralidade de intermediação de um vértice v mede quantas vezes v
    aparece nos caminhos mínimos entre todos os pares (s, t) do grafo.
    Vértices com alta centralidade são "pontes", ou seja, removê-los desconecta
    ou alonga muito os caminhos entre outros vértices.

    --- Como o Brandes usa essa BFS? ---
    O algoritmo de Brandes calcula a centralidade de intermediação em O(VE),
    rodando essa BFS uma vez para cada vértice como origem. Ela retorna três
    estruturas que, juntas, permitem redistribuir os créditos (contribuições)
    de cada caminho mínimo de volta para os vértices intermediários:

        1. pilha  — vértices em ordem de distância crescente à origem.
                    O Brandes percorre a pilha ao contrário (de longe para
                    perto) para propagar os créditos sem reprocessar nada.

        2. predecessores[w] — lista de vértices que chegam a w por um
                    caminho mínimo. Ao propagar o crédito de w de volta,
                    distribuímos apenas entre esses predecessores.

        3. sigma[v] — número de caminhos mínimos da origem até v.
                    Usado para dividir o crédito proporcionalmente: se
                    existem 3 caminhos mínimos até w e 2 passam por u,
                    u recebe 2/3 do crédito de w.

    Retorna:
        ResultadoBrandes(pilha, predecessores, sigma)
    """
    n = grafo.getQuantidadeVertices()
    distancias = [-1] * n            # -1 marca "ainda não visitado"
    predecessores = [[] for _ in range(n)]
    sigma = [0.0] * n                # número de caminhos mínimos
    pilha = []

    distancias[origem] = 0
    sigma[origem] = 1.0

    fila = deque([origem])
    while fila:
        u = fila.popleft()
        pilha.append(u)              # guarda na ordem de visita (distância crescente)
        for v in grafo.getSucessores(u):
            # primeira vez que v é encontrado: define sua distância
            if distancias[v] == -1:
                distancias[v] = distancias[u] + 1
                fila.append(v)
            # u -> v é uma aresta num caminho mínimo: acumula sigma e registra predecessor
            if distancias[v] == distancias[u] + 1:
                sigma[v] += sigma[u]
                predecessores[v].append(u)
    return ResultadoBrandes(pilha, predecessores, sigma)
