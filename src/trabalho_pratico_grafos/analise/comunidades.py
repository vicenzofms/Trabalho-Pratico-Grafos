from collections import defaultdict
from trabalho_pratico_grafos.grafos import GrafoAbstrato

def _construir_grafo_subjacente(grafo: GrafoAbstrato):
    subjacente = {i: {} for i in range(grafo.getQuantidadeVertices())}
    for u in range(grafo.getQuantidadeVertices()):
        for v in grafo.getSucessores(u):
            peso = grafo.getPesoAresta(u, v)
            # o get com (x, y) diz: se a chave x não existir, retorne o valor y
            subjacente[u][v] = subjacente[u].get(v, 0.0) + peso
            subjacente[v][u] = subjacente[v].get(u, 0.0) + peso
    # O grafo subjacente[u] está representando a vizinhança de u
    # com cada subjacente[u][v] sendo o peso de u->v e v->u juntos
    # do grafo original. Ou seja: subjacente[u][v] == subjacente[v][u]
    return subjacente

def modularidade(grafo: GrafoAbstrato, particao: list[int]):
    subjacente = _construir_grafo_subjacente(grafo)
    pesos = {
        i: sum(subjacente[i].values())
        for i in subjacente
    }
    pesoTotalGrafo = sum(pesos.values()) / 2
    somatorioEntrada = defaultdict(float)
    somatorioTotal = defaultdict(float)
    
    # particao[i] = id da comunidade do vértice i
    # ou seja, particao tem |V| de tamanho
    for vertice in range(grafo.getQuantidadeVertices()):
        # pega a comunidade daquele vertice
        comunidade = particao[vertice]
        somatorioTotal[comunidade] += pesos[vertice]
        for (u, peso) in subjacente[vertice].items():
            if (particao[u] == comunidade):
                # esse passo vai contar os pesos dobrado
                # um quando i, j e novamente quando j, i
                somatorioEntrada[comunidade] += peso
    return sum([
        (somatorioEntrada[comunidade]/(2*pesoTotalGrafo) - (somatorioTotal[comunidade]/(2*pesoTotalGrafo))**2)
        for comunidade in list(dict.fromkeys(particao))
    ])
    
