"""Testes do GrafoServico — construção dos 4 grafos a partir do cache."""

import pytest

from trabalho_pratico_grafos.backend.erros import (
    RepositorioAusenteError,
    TipoGrafoInvalidoError,
)
from trabalho_pratico_grafos.backend.fontes import FonteCache
from trabalho_pratico_grafos.backend.servicos import GrafoServico


def _servico(dir_dados: str) -> GrafoServico:
    return GrafoServico(FonteCache(dir_dados))


def test_constroi_os_quatro_grafos_com_vertices_e_arestas_esperados(dir_dados):
    grafos = _servico(dir_dados).construir_todos("octo/demo")

    assert set(grafos) == {"integrado", "comentarios", "fechamento", "prs"}

    # integrado = todas as interações: 5 usuários, 9 pares dirigidos distintos.
    assert grafos["integrado"].getQuantidadeVertices() == 5
    assert grafos["integrado"].getQuantidadeArestas() == 9
    # comentários (issue + PR): a-b, b-c -> {a,b,c}, 4 arestas.
    assert grafos["comentarios"].getQuantidadeVertices() == 3
    assert grafos["comentarios"].getQuantidadeArestas() == 4
    # fechamento: só c->d.
    assert grafos["fechamento"].getQuantidadeVertices() == 2
    assert grafos["fechamento"].getQuantidadeArestas() == 1
    # prs (revisão + merge): d-e, e->c, a->c -> {a,c,d,e}, 4 arestas.
    assert grafos["prs"].getQuantidadeVertices() == 4
    assert grafos["prs"].getQuantidadeArestas() == 4


def test_agrega_peso_de_interacoes_no_mesmo_par(dir_dados):
    # No integrado, a aresta a->c vem só do merge (peso 5). Confirma rótulos + peso.
    grafo = _servico(dir_dados).construir("octo/demo", "integrado")
    rotulos = [grafo.getRotuloVertice(i) for i in range(grafo.getQuantidadeVertices())]
    a, c = rotulos.index("a"), rotulos.index("c")
    assert grafo.getPesoAresta(a, c) == 5


def test_repositorio_ausente_levanta_erro(dir_dados):
    with pytest.raises(RepositorioAusenteError):
        _servico(dir_dados).construir("fantasma/repo", "integrado")


def test_tipo_invalido_levanta_erro(dir_dados):
    with pytest.raises(TipoGrafoInvalidoError):
        _servico(dir_dados).construir("octo/demo", "inexistente")


def test_resumo_traz_densidade_calculada(dir_dados):
    # Com `coesao.densidade` entregue (parte A), a densidade é plumbada no resumo.
    resumo = _servico(dir_dados).resumir("octo/demo", "integrado")
    assert resumo.vertices == 5
    assert resumo.arestas == 9
    assert isinstance(resumo.densidade, float)
    assert 0 < resumo.densidade <= 1
