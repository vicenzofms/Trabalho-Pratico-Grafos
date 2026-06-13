from collections.abc import Iterator
from trabalho_pratico_grafos.analise.comunidades import _construir_grafo_subjacente
from trabalho_pratico_grafos.grafos.grafo_abstrato import GrafoAbstrato


def pontes_locais(grafo: GrafoAbstrato) -> list[tuple[int, int]]:
    """
    Atua sobre o grafo subjacente
    Encontra arestas tal que, existe uma ligação entre u e v, e eles não possuem
    vizinhos em comum, o único atalho entre os dois mundos é a aresta não direcionada u-v
    ---
    Retorna uma lista de pares não-direcionados (u, v) na convenção u < v
    """
    # caso exista a ligação u-v, independente se no grafo original
    # a representação é u->v ou v->u ou as duas em anti-paralelas
    # remover essa ligação não necessariamente desconecta o grafo (ponte clássica)
    # apenas faz a distância entre u e v ir de 1 para > 2, já que não há caminho de tamanho 2 (via vizinho compartilhado)
    subjacente = _construir_grafo_subjacente(grafo)
    pontes = []
    for u in subjacente:
        vizinhosU = set(subjacente[u].keys()) # vizinhança de u
        for v in subjacente[u].keys():
            # u<v (por convenção para a tupla) e não processa o par (v, u) por economia
            if (u > v): continue
            vizinhosV = set(subjacente[v].keys()) # vizinhança de v
            # não temos vizinhos em comum (interseção entre vizinhanças)
            # importante que a interseção entre vizinhosU e vizinhosV nunca vai
            # conter u e v, já que vizinhosV não tem v e vizinhosU não tem u (não pode laços)
            if (vizinhosU.isdisjoint(vizinhosV)):
                pontes.append((u, v))
    return pontes

def arestas_intercomunidade(grafo: GrafoAbstrato, particao: list[int]) -> list[tuple[int, int]]:
    """
    Encontra arestas que tem extremos em comunidades diferentes
    ---
    Retorna uma lista de pares DIRECIONADOS (u, v), ou seja, arestas u->v
    """
    # Lembrete: particao[i] retorna a comunidade em que o vértice i está localizado
    # a função não roda louvain, seria muito caro além de fixar a resposta para um grafo, dessa forma conseguimos
    # tratar qualquer configuração de comunidades, independente se tem a modularidade maximizada

    # diferente de pontes_locais, aqui a direção importa, estamos atuando em cima do grafo direcionado
    # ou seja, o par (u, v) representa a aresta u->v e o par (v, u) a aresta v->u, diferente do retorno de pontes_locais
    # dessa forma, o par sempre representa uma aresta existente no grafo original, a resposta final pode conter (u,v) e (v,u)
    arestas = []
    for u in range(grafo.getQuantidadeVertices()):
        for v in grafo.getSucessores(u):
            if particao[u] != particao[v]:
                arestas.append((u, v))
    return arestas

def pontes_classicas(grafo: GrafoAbstrato) -> list[tuple[int, int]]:
    """
    Encontra pontes clássicas, que se removidas, desconectam o grafo
    ---
    Retorna uma lista de pares não-direcionados (u, v) na convenção u < v
    """
    # Utiliza uma DFS, porém não implementada de maneira recursiva, devido a grafos que podem ser muito profundos e estourar
    # o limite de recursão do Python, ao implementar a pilha manualmente não temos essa limitação de RecursionError
    subjacente = _construir_grafo_subjacente(grafo)
    pontes = []

    # representa quando o vértice foi descoberto
    temposDescoberta = [-1] *  grafo.getQuantidadeVertices() 
    # é o menor tempo de descoberta que o vértice consegue alcançar (diretamente via aresta de retorno ou por filho)
    menorTempoAlcancavel = [-1] *  grafo.getQuantidadeVertices()
    tempoAtual = 0

    # guarda o vértice sendo processado, seu pai e o Iterator dos seus vizinhos
    # precisa ser um Iterator e não uma lista pois quando um break ocorre para que
    # o processamento de um filho comece, o Iterator lembra de onde eu parei
    # e continua a partir dali quando voltar
    pilha: list[tuple[int, int, Iterator]] 

    for u in subjacente:
        # se o vértice já foi descoberto antes, pula
        if temposDescoberta[u] >= 0: continue

        # marca o tempo do vertice atual e o menor que consegue alcançar é si próprio
        temposDescoberta[u] = menorTempoAlcancavel[u] = tempoAtual
        tempoAtual += 1
        # adiciona o vértice para ser processado
        pilha = [(u, -1, iter(subjacente[u].keys()))]

        # até esgotar a pilha
        # cada iteração é um passo de trabalho no vértice do topo
        while len(pilha) > 0:
            # desconstrói o topo da pilha
            atual, pai, vizinhos = pilha[len(pilha)-1]
            desceu = False
            # percorre os vizinhos
            for v in vizinhos:
                if v == pai: continue # não volto pela aresta que vim
                if temposDescoberta[v] < 0: # aresta de árvore
                    # marca a descoberta do vizinho v
                    temposDescoberta[v] = menorTempoAlcancavel[v] = tempoAtual
                    tempoAtual += 1
                    # coloca o vizinho v para ser o próximo a ser processado
                    pilha.append((v, atual, iter(subjacente[v].keys())))
                    desceu = True
                    break # vai processar o vizinho imediatamente
                else: # aresta de retorno
                    # marca o maior retorno possível, o mais antigo que eu consigo voltar entre o que eu já conseguia ou o meu vizinho
                    menorTempoAlcancavel[atual] = min(menorTempoAlcancavel[atual], temposDescoberta[v])
            if not desceu:
                # já processei todos os vizinhos do atual
                pilha.pop()
                # preciso propagar o menorTempoAlcancavel que encontrei no atual para o pai
                if pai != -1: # não sou a raiz
                    menorTempoAlcancavel[pai] = min(menorTempoAlcancavel[pai], menorTempoAlcancavel[atual])
                    # se o vértice com o menor tempo de descoberta que eu consigo alcançar (diretamente ou por sub-arvore) 
                    # é estritamente mais novo que meu pai, então a aresta pai-atual é uma ponte, já que eu não consigo
                    # voltar por outro caminho, se a ligação for cortada eu estou separado do resto (grafo desconectado)
                    if menorTempoAlcancavel[atual] > temposDescoberta[pai]:
                        pontes.append((min(atual, pai), max(atual, pai)))
    return pontes
