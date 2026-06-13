from trabalho_pratico_grafos.grafos import GrafoAbstrato

def centralidade_grau(grafo: GrafoAbstrato) -> dict[str, list[float]]:
    quantidadeVertices = grafo.getQuantidadeVertices()

    if quantidadeVertices == 1:
        return {"entrada": [0.0], "saida": [0.0]}

    centralidadesGrauEntrada = []
    centralidadesGrauSaida = []
    for vertice in range(quantidadeVertices):
        centralidadesGrauEntrada.append(grafo.getGrauEntrada(vertice) / (quantidadeVertices - 1))
        centralidadesGrauSaida.append(grafo.getGrauSaida(vertice) / (quantidadeVertices - 1))

    return {"entrada": centralidadesGrauEntrada, "saida": centralidadesGrauSaida}

def centralidade_autovetor(grafo: GrafoAbstrato):

    y = 0

def pagerank(grafo: GrafoAbstrato, d=0.85):

    z = 0

