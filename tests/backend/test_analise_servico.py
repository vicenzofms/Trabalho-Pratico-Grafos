"""Testes do AnaliseServico — fallback, serialização por username e cache."""

import os
import time

from trabalho_pratico_grafos.backend.fontes import FonteCache
from trabalho_pratico_grafos.backend.servicos import AnaliseServico, GrafoServico


def _servico(dir_dados: str) -> AnaliseServico:
    fonte = FonteCache(dir_dados)
    return AnaliseServico(GrafoServico(fonte), fonte)


def test_centralidades_disponiveis_sao_rankings_ordenados_por_username(dir_dados):
    rel = _servico(dir_dados).relatorio("octo/demo")
    centralidades = rel["centralidades"]

    # Além de grau/autovetor/pagerank (parte C), proximidade e intermediação
    # (parte B) já foram entregues e o adaptador as detecta e serializa.
    assert set(centralidades) == {
        "grau_entrada",
        "grau_saida",
        "autovetor",
        "pagerank",
        "proximidade",
        "intermediacao",
    }

    pagerank = centralidades["pagerank"]
    assert {item["username"] for item in pagerank} == {"a", "b", "c", "d", "e"}
    valores = [item["valor"] for item in pagerank]
    assert valores == sorted(valores, reverse=True)


def test_coesao_comunidades_e_pontes_presentes(dir_dados):
    rel = _servico(dir_dados).relatorio("octo/demo")

    # parte A (coesao) entregue: densidade/clustering/assortatividade já têm valor.
    # O backend só plumba o que o `analise` devolve, então aqui validamos o tipo
    # (o valor numérico em si é coberto pelos testes do pacote `analise`).
    for metrica in ("densidade", "assortatividade", "clustering"):
        assert isinstance(rel[metrica], float)
    # comunidades/pontes (parte D) e modularidade.
    assert rel["modularidade"] is not None
    assert rel["comunidades"]
    assert set(rel["pontes"]) == {"locais", "classicas", "intercomunidade"}


def test_cache_por_mtime_reaproveita_e_invalida_ao_mudar(dir_dados, caminho_cache):
    servico = _servico(dir_dados)

    primeiro = servico.relatorio("octo/demo")
    segundo = servico.relatorio("octo/demo")
    assert primeiro is segundo  # mesma versão (mtime) -> reaproveita o cache

    # Simula uma re-mineração mudando o mtime do JSON (costura 4).
    futuro = time.time() + 10
    os.utime(caminho_cache, (futuro, futuro))

    terceiro = servico.relatorio("octo/demo")
    assert terceiro is not primeiro  # mtime mudou -> recomputado


def test_grafo_de_tipo_sem_interacoes_nao_quebra(dir_dados, tmp_path):
    # Um repo cujo tipo "fechamento" só tem 1 aresta; mas testamos um grafo vazio
    # de verdade montando um cache só de comentários e pedindo o relatório de "prs".
    import json

    pasta = tmp_path / "vazio"
    pasta.mkdir()
    (pasta / "x_y.json").write_text(
        json.dumps(
            {
                "('a', 'b', 'comentario_issue')": {
                    "origem": "a",
                    "destino": "b",
                    "peso": 2,
                    "tipo": "comentario_issue",
                }
            }
        ),
        encoding="utf-8",
    )
    fonte = FonteCache(str(pasta))
    servico = AnaliseServico(GrafoServico(fonte), fonte)

    rel = servico.relatorio("x/y", "prs")  # nenhuma interação de PR -> grafo vazio
    assert rel["centralidades"] == {}
    assert rel["comunidades"] == {}
    assert rel["modularidade"] is None
