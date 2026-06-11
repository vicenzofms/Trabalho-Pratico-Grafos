# Script para testes dos grafos
# Não dê commit nos seus tokens!
from trabalho_pratico_grafos.gephi.gephi import para_gephi
from trabalho_pratico_grafos.minerador import Minerador
from trabalho_pratico_grafos.grafos import *

def agregarAresta(grafo: GrafoAbstrato, u: int, v: int, peso: float):
    if (grafo.existeAresta(u, v)):
        peso = grafo.getPesoAresta(u, v) + peso
        grafo.setPesoAresta(u, v, peso)
    else:
        grafo.adicionarAresta(u, v, peso)

def definirRotulos(grafo: GrafoAbstrato, rotulos: list[str]):
    if (grafo.getQuantidadeVertices() != len(rotulos)):
        raise ValueError("O grafo não possui a mesma quantidade de vértices passados")
    for i in range(len(rotulos)):
        grafo.setRotuloVertice(i, rotulos[i])

def construirGrafoPorTipo(dados: dict, tipos: set[str]) -> GrafoAbstrato:
    interacoesFiltradas =  [
        interacao
        for interacao in dados['interacoes']
        if interacao['tipo'] in tipos
    ] if len(tipos) > 0 else dados['interacoes']
    usernames: list[str] = []
    mapaIds: dict[str, int] = {}
    for interacao in interacoesFiltradas:
        for nome in (interacao['origem'], interacao['destino']):
            if nome not in usernames:
                mapaIds[nome] = len(usernames)
                usernames.append(nome)
    
    grafo = GrafoMatrizAdjacencia(len(usernames))
    for interacao in interacoesFiltradas:
        indiceU = mapaIds[interacao['origem']]
        indiceV = mapaIds[interacao['destino']]
        agregarAresta(grafo, indiceU, indiceV, interacao['peso'])
    definirRotulos(grafo, usernames)
    return grafo

# Definições Gerais
minerador = Minerador("discordjs/discord.js", ["TOKEN1", "TOKEN2"], True)
minerador.executar()
dados = minerador.exportarDados()
if dados is None:
    raise ValueError("Não foi possível carregar os dados")

grafoGeral = construirGrafoPorTipo(dados, set())
grafoComentarios = construirGrafoPorTipo(dados, {"comentario_issue", "comentario_pull_request"})
grafoFechamento = construirGrafoPorTipo(dados, {"fechamento_issue"})
grafoPR_Interacoes = construirGrafoPorTipo(dados, {"revisao_pull", "merge_pull"})

# Prints / Local de uso & testes
print("---- Grafos ----")
print(f"Geral: {grafoGeral.qntdVertices} vertices / {grafoGeral.qntdArestas} arestas")
print(f"Comentários: {grafoComentarios.qntdVertices} vertices / {grafoComentarios.qntdArestas} arestas")
print(f"Fechamento: {grafoFechamento.qntdVertices} vertices / {grafoFechamento.qntdArestas} arestas")
print(f"PR Interações: {grafoPR_Interacoes.qntdVertices} vertices / {grafoPR_Interacoes.qntdArestas} arestas")
print("---- Grafos ----")

para_gephi(grafoGeral, "grafo_geral_discordjs")
        

