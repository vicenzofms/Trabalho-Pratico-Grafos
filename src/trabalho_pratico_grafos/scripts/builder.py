# Script para testes dos grafos
# Não dê commit nos seus tokens!
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

# Definições Gerais
minerador = Minerador("discordjs/discord.js", ["TOKEN1", "TOKEN2"], True)
minerador.executar()
dados = minerador.exportarDados()
if dados is None:
    raise ValueError("Não foi possível carregar os dados")

grafoGeral: GrafoAbstrato = GrafoMatrizAdjacencia(dados["usuarios"]['quantidade'])
grafoComentarios: GrafoAbstrato = GrafoMatrizAdjacencia(dados["usuarios"]['quantidade'])
grafoFechamento: GrafoAbstrato = GrafoMatrizAdjacencia(dados["usuarios"]['quantidade'])
grafoPR_Interacoes: GrafoAbstrato = GrafoMatrizAdjacencia(dados["usuarios"]['quantidade']) # reviews/merges

# Mapear Interacoes -> Aresta
for interacao in dados['interacoes']:
    indiceU: int = dados['usuarios']['ids_por_login'][interacao['origem']]
    indiceV: int = dados['usuarios']['ids_por_login'][interacao['destino']]
    agregarAresta(grafoGeral, indiceU, indiceV, interacao['peso'])
    if (interacao['tipo'] == 'comentario_issue' or interacao['tipo'] == 'comentario_pull_request'):
        agregarAresta(grafoComentarios, indiceU, indiceV, interacao['peso'])
    elif (interacao['tipo'] == "fechamento_issue"):
        agregarAresta(grafoFechamento, indiceU, indiceV, interacao['peso'])
    else:
        agregarAresta(grafoPR_Interacoes, indiceU, indiceV, interacao['peso'])


definirRotulos(grafoGeral, dados['usuarios']['logins_por_id'])
definirRotulos(grafoFechamento, dados['usuarios']['logins_por_id'])
definirRotulos(grafoComentarios, dados['usuarios']['logins_por_id'])
definirRotulos(grafoPR_Interacoes, dados['usuarios']['logins_por_id'])

# Prints / Local de uso & testes
print("---- Grafos ----")
print(f"Geral: {grafoGeral.qntdVertices} vertices / {grafoGeral.qntdArestas} arestas")
print(f"Comentários: {grafoComentarios.qntdVertices} vertices / {grafoComentarios.qntdArestas} arestas")
print(f"Fechamento: {grafoFechamento.qntdVertices} vertices / {grafoFechamento.qntdArestas} arestas")
print(f"PR Interações: {grafoPR_Interacoes.qntdVertices} vertices / {grafoPR_Interacoes.qntdArestas} arestas")
print("---- Grafos ----")

        

