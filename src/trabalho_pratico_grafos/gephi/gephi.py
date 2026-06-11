import csv
import os
from trabalho_pratico_grafos.grafos.grafo_abstrato import GrafoAbstrato


def para_gephi(grafo: GrafoAbstrato, nome: str, pasta: str | None = None) -> str:
    """Exporta o grafo para um CSV de arestas no formato esperado pelo Gephi em data/gephi/.

    Args:
        grafo: instância de GrafoAbstrato a ser exportada.
        nome: nome do arquivo gerado (ex: "meu_grafo" → "meu_grafo.csv").
    """
    if pasta is None:
        pasta = os.path.join(os.path.dirname(__file__), "../..", "data", "gephi")
    os.makedirs(pasta, exist_ok=True)

    caminho = os.path.join(pasta, f"{nome}.csv")
    n = grafo.getQuantidadeVertices()

    with open(caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Source", "Target", "Weight", "Type"])
        for u in range(n):
            for v in range(n):
                if u != v and grafo.existeAresta(u, v):
                    source = grafo.getRotuloVertice(u) or str(u)
                    target = grafo.getRotuloVertice(v) or str(v)
                    peso = grafo.getPesoAresta(u, v)
                    writer.writerow([source, target, peso, "Directed"])

    return caminho
