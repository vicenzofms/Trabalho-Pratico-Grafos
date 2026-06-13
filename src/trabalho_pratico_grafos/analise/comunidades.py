from collections import defaultdict
from trabalho_pratico_grafos.grafos import GrafoAbstrato
# OH MY GOD, que trem doido

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

def _grausPonderados(subjacente: dict):
    # retorna o dicionário de graus ponderados
    # ou seja para o vértice v -> a soma dos pesos de todas as arestas que incidem em v
    return {
        i: sum(subjacente[i].values())
        for i in subjacente
    }

def modularidade(grafo: GrafoAbstrato, particao: list[int]):
    subjacente = _construir_grafo_subjacente(grafo)
    return _modularidadePeloSubjacente(subjacente, particao)

def _modularidadePeloSubjacente(subjacente: dict, particao: list[int]):
    # para cada vértice soma os pesos de todas as arestas que incidem nele
    pesos = _grausPonderados(subjacente)
    # precisa dividir por 2 por causa da regra do aperto de mão
    pesoTotalGrafo = sum(pesos.values()) / 2

    # mede os pesos de cada comunidade
    somatorioEntrada = defaultdict(float)
    # mede os pesos em caso de ligações aleatórias porém mantendo os graus
    somatorioTotal = defaultdict(float)
    
    # particao[i] = id da comunidade do vértice i
    # ou seja, particao tem |V| de tamanho
    for vertice in range(len(subjacente)):
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
    
def louvain(grafo: GrafoAbstrato) -> list[int]:
    # cada vértice começa isolado em sua própria comunidade
    subjacente = _construir_grafo_subjacente(grafo)
    comunidades = [u for u in range(len(subjacente))]
    while True:
        # roda a 1a fase
        novasComunidades = _louvainSubjacente(subjacente)
        # len(subjacente) sempre mostra a quantidade de comunidades
        # no inicio é |V|, depois vai aglomerando
        if len(set(novasComunidades)) == len(subjacente): break # não houve nenhuma nova comunidade, solução está ótima
        # houve melhora, precisamos agregar para considerar as novas comunidades criadas
        # pode ser uma nova comunidade (1a execução) ou uma junção de comunidades (2a+ execução)
        # super vértices (representando comunidades) são também convertido em super vértices maiores
        # quando comunidades se juntam
        subjacente, novosIds = _agregar(subjacente, novasComunidades)
        # ajusta a referencia global de comunidades
        # essa sempre tem a quantidade original de vértices
        # assim, comunidades[u] sempre mostrando a comunidade atual que o vértice u pertence
        comunidades = [
            # o fluxo é sempre:
            # novasComunidades[c] -> comunidade que a iteração da fase 1 deu
            # novosIds[...] -> super-vértice que a nova comunidade foi compactada em
            novosIds[novasComunidades[c]]
            for c in comunidades
        ]
    # retorna a configuração ótima de comunidades
    return comunidades
    
def _louvainSubjacente(subjacente: dict):
    # Fase 1 (roda em loop durante a Fase 2)
    comunidades = [u for u in range(len(subjacente))]
    pesos = _grausPonderados(subjacente)
    # precisa dividir por 2 por causa da regra do aperto de mão
    pesoTotalGrafo = sum(pesos.values()) / 2
    # somatorioTotal[c] representa a soma total dos pesos que estão na comunidade c
    # como cada vértice começa em sua própria comunidade, no início somatorioTotal = pesos
    somatorioTotal = pesos.copy()
    # repete até não haver movimentações
    while True:
        movimento = 0
        # verificar se caso u for para a comunidade de um dos seus vizinhos
        # se a modularidade melhora
        for u in range(len(subjacente)):
            # remover o u de sua comunidade atual
            comunidadeAtual = comunidades[u]
            proximaComunidade = comunidadeAtual
            somatorioTotal[comunidadeAtual] -= pesos[u] # remove o u

            # vai conter o peso de todas ligações de u com todas as comunidades de seus vizinhos
            pesosLigacoesPorComunidade = defaultdict(float)
            # 0.0 garante que a comunidadeAtual sempre seja uma opção, com maiorVariacao = -inf
            # estabelecendo a base de comparação
            pesosLigacoesPorComunidade[comunidadeAtual] = 0.0 
            for (v, peso) in subjacente[u].items():
                if v == u: continue # não conta o laço subjacente[u][u] que ocorre na fase 2
                # aumenta o peso da ligação u->v na lista da comunidade de v
                # se v percence a comunidadeAtual, o peso é atualizado também (muda o 0.0 ali de cima)
                pesosLigacoesPorComunidade[comunidades[v]] += peso

            # mede a maior variação de modularidade encontrada
            # assim, conseguimos determinar qual a comunidade que maximiza variação
            maiorVariacao = float('-inf')
            for possivelComunidade in pesosLigacoesPorComunidade.keys():
                # calcula a variação
                # ligações reais de u com a possivelComunidade - ligações esperadas por acaso (dado o tamanho da comunidade e o grau de u)
                # comunidades grandes + u com alto grau = penalidade por inflação
                variacao = (pesosLigacoesPorComunidade[possivelComunidade] / pesoTotalGrafo)-((somatorioTotal[possivelComunidade]*pesos[u])/(2*pesoTotalGrafo**2))
                if variacao > maiorVariacao:
                    maiorVariacao = variacao
                    proximaComunidade = possivelComunidade

            # se a melhor comunidade for a que já estava, não é um movimento
            if proximaComunidade != comunidadeAtual:
                movimento += 1

            # muda a comunidade de u (se proximaComunidade == comunidadeAtual ele readiciona u)
            # já que foi removido de lá no inicio
            somatorioTotal[proximaComunidade] += pesos[u]
            comunidades[u] = proximaComunidade

        # nenhum vértice mudou de comunidade, a modularidade está ótima
        if movimento == 0: break
    # fim da 1a fase
    return comunidades

def _agregar(subjacente: dict, comunidades: list[int]) -> tuple[dict, dict]:
    # recebe um subjacente e uma lista com as comunidades já realocadas
    # agora, vai criar um novo subjacente, de maneira que cada comunidade vira um vértice
    # arestas internas da comunidade viram laços (preservando o peso do vértice)
    # arestas entre comunidades agora são superU->superV onde
    # superU = vértice da comunidade 1 e superV = vértice da comunidade 2

    # cria um dicionário com as novas comunidades e as enumera
    # ex: lista [1,1,4,4,4] vira {1: 0, 4:1}
    # comunidade 1 = super_vértice 0 e comunidade 4 = super_vértice 1
    novosIds = {c: i for i, c in enumerate(dict.fromkeys(comunidades))}
    # o novo subjacente, com os super vértices (1/comunidade)
    novoSubjacente = {i: {} for i in range(len(novosIds))}
    # remapeamento das antigas arestas
    for u in subjacente:
        for (v, peso) in subjacente[u].items():
            superU = novosIds[comunidades[u]] # vértice da comunidade de U
            superV = novosIds[comunidades[v]] # vértice da comunidade de V
            # nova aresta do novo grafo subjacente
            # no caso de u e v serem da mesma comunidade superU == superV, portanto, um laço
            # caso contrário é uma ponte entre comunidades/super-vértices
            novoSubjacente[superU][superV] = novoSubjacente[superU].get(superV, 0.0) + peso
            # detalhe que os pesos internos são contados duas vezes, já que ocorre em
            # subjacente[u][v] e subjacente[v][u], isso que mantém o peso total do grafo igual
    # devolve o novo grafo de super vértices e o mapa de ids
    return (novoSubjacente, novosIds)

