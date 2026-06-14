from trabalho_pratico_grafos.grafos import GrafoAbstrato
from math import sqrt

def centralidade_grau(grafo: GrafoAbstrato) -> dict[str, list[float]]:
    n = grafo.getQuantidadeVertices()

    if n == 1:
        return {"entrada": [0.0], "saida": [0.0]}

    centralidadesGrauEntrada = []
    centralidadesGrauSaida = []
    for vertice in range(n):
        centralidadesGrauEntrada.append(grafo.getGrauEntrada(vertice) / (n - 1))
        centralidadesGrauSaida.append(grafo.getGrauSaida(vertice) / (n - 1))

    return {"entrada": centralidadesGrauEntrada, "saida": centralidadesGrauSaida}

def centralidade_autovetor(grafo: GrafoAbstrato) -> list[float]:
    # Aqui a gente mede a importância de um nó olhando QUEM aponta pra ele, não quantos.
    # Ser apontado por um nó importante vale mais do que ser apontado por vários nós fracos.
    # Resumo: você fica importante se nós importantes apontam pra você.

    n = grafo.getQuantidadeVertices()

    # todo mundo começa com a mesma importância
    x = [1 / n] * n

    # repete a conta até os valores pararem de mudar (no máximo 100 vezes)
    for i in range(100):

        # cada nó junta a importância de todos os que apontam pra ele
        x_adicional = [0.0] * n
        for v in range(n):
            for u in grafo.getPredecessores(v):
                x_adicional[v] += x[u]

        # mede o tamanho geral dos valores (a cada volta eles crescem, isso serve pro ajuste abaixo)
        soma = 0.0
        for j in range(n):
            soma += x_adicional[j]*x_adicional[j]
        norma = sqrt(soma)

        # se deu tudo zero, não dá pra dividir, então para por aqui
        if norma == 0:
            break

        # encolhe todos os valores na mesma proporção pra eles não dispararem
        for j in range(n):
            x_adicional[j] /= norma

        # vê qual nó mudou mais de uma volta pra outra
        diff = 0.0
        for j in range(n):
            valor_absoluto = abs(x_adicional[j] - x[j])
            if valor_absoluto > diff:
                diff = valor_absoluto

        # guarda os valores novos pra próxima volta usar
        x = x_adicional

        # se quase ninguém mudou, já estabilizou, pode parar
        if diff < 0.000001:
            break

    return x

def pagerank(grafo: GrafoAbstrato, d = 0.85) -> list[float]:
    # A explicação de o que é o pagerank é o seguinte:
    #
    # Imagina uma pessoa clicando à toa na internet. Ela está numa página e faz uma de duas coisas a cada passo:
    # - Com 85% de chance (d = 0.85): clica num link aleatório da página atual (segue uma seta que sai do nó).
    # - Com 15% de chance (1 − d = 0.15): enjoa e pula pra uma página qualquer do grafo, escolhida ao acaso (isso é o "teletransporte").
    #
    # Agora a pergunta-chave:
    #    Se essa pessoa ficar clicando assim pra sempre, em quais páginas ela passa mais tempo?
    # O PageRank de um nó é exatamente isso: a fração do tempo que o navegador passa nele.
    #
    # E por que uma página recebe muita visita? Porque muitas páginas importantes apontam pra ela. É
    # circular de propósito: você é importante se gente importante te aponta. O algoritmo resolve essa
    # circularidade repetindo a conta até estabilizar.
    #
    # Guarda esses dois "fluxos de visita" pra um nó v:
    # 1. Visitas que chegam por teletransporte (alguém enjoou e caiu em v por sorte).
    # 2. Visitas que chegam por clique (alguém estava num nó u que aponta pra v e clicou justo naquele link).

    n = grafo.getQuantidadeVertices()
    # todos começam com a mesma importância
    PR = [1 / n] * n

    # repete a conta até estabilizar (no máximo 100 vezes)
    for i in range(100):

        # acumula a importância dos vértices que não têm saídas
        s = 0.0
        for u in range(n):
            if grafo.getGrauSaida(u) == 0:
                s += PR[u]

        # calcula os valores novos num vetor separado
        PR_adicional = [0.0] * n
        for v in range(n):
            soma_cliques = 0.0
            for u in grafo.getPredecessores(v):
                soma_cliques += PR[u] / grafo.getGrauSaida(u)

            # acumula a contribuição, essa é a fórmula
            PR_adicional[v] =  (1 - d) / n + d * s / n + d * soma_cliques

        # mede o quanto mudou desta rodada pra anterior
        diff = 0.0
        for j in range(n):
            # abs converte os número negativos e matém os positivos
            diff += abs(PR_adicional[j] - PR[j])

        # adota os valores novos
        PR = PR_adicional

        # se mal mudou, estabilizou, para o for
        if diff < 0.000001:
            break

    return PR
