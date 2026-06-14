import csv
import os
import pytest

from trabalho_pratico_grafos.grafos import GrafoMatrizAdjacencia, GrafoListaAdjacencia
from trabalho_pratico_grafos.gephi.gephi import para_gephi

def _triangulo(Classe=GrafoMatrizAdjacencia):
    """Grafo em forma de triângulo para executar os testes."""
    g = Classe(3)
    g.adicionarAresta(0, 1, 1.0)
    g.adicionarAresta(1, 2, 2.0)
    g.adicionarAresta(0, 2, 3.0)
    return g


def _ler_csv(caminho: str) -> list[dict]:
    with open(caminho, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def test_para_gephi_cria_arquivo(tmp_path):
    grafo = _triangulo()

    caminho = para_gephi(grafo, "teste", pasta=str(tmp_path))

    assert os.path.isfile(caminho)


def test_para_gephi_retorna_caminho_correto(tmp_path):
    grafo = _triangulo()

    caminho = para_gephi(grafo, "meu_grafo", pasta=str(tmp_path))

    assert caminho == os.path.join(str(tmp_path), "meu_grafo.csv")

def test_para_gephi_numero_de_arestas(tmp_path):
    # O triângulo tem 3 arestas; o CSV deve ter exatamente 3 linhas de dados.
    grafo = _triangulo()

    caminho = para_gephi(grafo, "teste", pasta=str(tmp_path))
    linhas = _ler_csv(caminho)

    assert len(linhas) == 3

def test_para_gephi_pesos_corretos(tmp_path):
    # Os pesos exportados devem bater com os definidos no grafo.
    grafo = _triangulo()

    caminho = para_gephi(grafo, "teste", pasta=str(tmp_path))
    linhas = _ler_csv(caminho)

    pesos_exportados = {(l["Source"], l["Target"]): float(l["Weight"]) for l in linhas}
    assert pesos_exportados[("0", "1")] == pytest.approx(1.0)
    assert pesos_exportados[("1", "2")] == pytest.approx(2.0)
    assert pesos_exportados[("0", "2")] == pytest.approx(3.0)

@pytest.mark.parametrize("Classe", [GrafoMatrizAdjacencia, GrafoListaAdjacencia])
def test_para_gephi_independe_da_implementacao(tmp_path, Classe):
    grafo = _triangulo(Classe)

    caminho = para_gephi(grafo, "impl", pasta=str(tmp_path))
    linhas = _ler_csv(caminho)

    assert len(linhas) == 3
