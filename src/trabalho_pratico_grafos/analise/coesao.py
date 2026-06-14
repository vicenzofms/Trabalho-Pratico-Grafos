from trabalho_pratico_grafos.grafos import GrafoAbstrato

def densidade(grafo: GrafoAbstrato) -> float: # A função retorna um valor que varia de 0 a 1, indicando a intensidade da densidade do grafo.
    verticesnum = grafo.getQuantidadeVertices()
    if verticesnum <= 1:
        return 0.0

    return grafo.getQuantidadeArestas()/ (verticesnum * (verticesnum - 1))

def coeficiente_agrupamento(grafo: GrafoAbstrato) -> float:
    #Calcula a média dos coeficientes de agrupamento de cada vertice calculados sob o grafo subjacente. Vertices com menos de 2 vizinhos contribuem em 0 para a media.
    coeficientes = []
    for v in range(grafo.getQuantidadeVertices()):
        #Cálculo da vizinhança local de cada vértice, considerando o grafo subjacente (direcionamento das arestas não importa.)
        vizinhos = set(grafo.getSucessores(v)) | set(grafo.getPredecessores(v))
        vizinhos.discard(v)
        k = len(vizinhos)

        if k < 2:
            coeficientes.append(0.0)
            continue

        arestas_entre_vizinhos = 0
        lista_vizinhos = list(vizinhos)
        for i in range(len(lista_vizinhos)):
            for j in range(i + 1, len(lista_vizinhos)):
                u, w = lista_vizinhos[i], lista_vizinhos[j]
                if grafo.isSucessor(u, w) or grafo.isSucessor(w, u):
                    arestas_entre_vizinhos += 1

        # C(k,2) = k*(k-1)/2 é o número máximo de arestas entre k vizinhos
        coeficientes.append(arestas_entre_vizinhos / (k * (k - 1) / 2))

    return sum(coeficientes) / len(coeficientes) if coeficientes else 0.0

def assortatividade_grau(grafo: GrafoAbstrato) -> float:
    #Define se vértices de alto grau tendem a se conectar com outros de alto grau ou com vértices de baixo grau. Correlação de Pearson entre os graus nas pontas de cada aresta (fórmula de Newman)."
    soma_xy = soma_x = soma_y = soma_x2 = soma_y2 = 0.0
    n = 0

    for u in range(grafo.getQuantidadeVertices()):
        grau_u = grafo.getGrauSaida(u)
        for v in grafo.getSucessores(u):
            grau_v = grafo.getGrauEntrada(v)
            soma_xy += grau_u * grau_v
            soma_x  += grau_u
            soma_y  += grau_v
            soma_x2 += grau_u ** 2
            soma_y2 += grau_v ** 2
            n += 1

    if n == 0:
        return 0.0

    numerador = n * soma_xy - soma_x * soma_y
    denom_x   = n * soma_x2 - soma_x ** 2
    denom_y   = n * soma_y2 - soma_y ** 2

    if denom_x <= 0 or denom_y <= 0:
        return 0.0   # todos os graus iguais → correlação indefinida

    return numerador / (denom_x * denom_y) ** 0.5