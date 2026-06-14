import pytest

from trabalho_pratico_grafos.analise import AnalisadorRede
from grafos_exemplo import dois_triangulos_ligados, grafo_caminho

# Para rodar: pytest tests/analise/test_analisador.py -v
#
# A AnalisadorRede é só uma FACHADA: orquestra as métricas dos outros módulos
# (que já têm seus próprios testes) e cacheia o Louvain. Aqui não re-validamos
# os valores de cada métrica, e sim que a fachada (a) monta o dicionário com a
# estrutura combinada esperada e (b) calcula as comunidades uma única vez.


# Inicio dos testes em relatorio_completo()
def test_relatorio_completo_tem_a_estrutura_esperada():
    # Arrange
    analisador = AnalisadorRede(dois_triangulos_ligados())

    # Act
    relatorio = analisador.relatorio_completo()

    # Assert: chaves de primeiro nível
    assert set(relatorio.keys()) == {
        "densidade", "agrupamento", "assortatividade",
        "centralidades", "comunidades", "pontes",
    }
    # subestrutura das centralidades
    assert set(relatorio["centralidades"].keys()) == {
        "grau", "proximidade", "intermediacao", "pagerank", "autovetor",
    }
    # subestrutura das pontes
    assert set(relatorio["pontes"].keys()) == {"locais", "intercomunidade"}


def test_relatorio_completo_comunidades_um_rotulo_por_vertice():
    # Arrange: o grafo tem 6 vértices
    grafo = dois_triangulos_ligados()
    analisador = AnalisadorRede(grafo)

    # Act
    relatorio = analisador.relatorio_completo()

    # Assert: a partição traz um rótulo por vértice original
    assert len(relatorio["comunidades"]) == grafo.getQuantidadeVertices()


def test_relatorio_completo_e_serializavel_em_json():
    # Arrange: a fachada promete um dict serializável para JSON
    import json
    analisador = AnalisadorRede(grafo_caminho(4))

    # Act and Assert: serializar não pode levantar exceção
    json.dumps(analisador.relatorio_completo())
# Fim dos testes em relatorio_completo()


# Inicio dos testes em _comunidades() (cache)
def test_comunidades_calcula_uma_unica_vez(monkeypatch):
    # Arrange: conta quantas vezes o Louvain é de fato chamado
    import trabalho_pratico_grafos.analise.analisador as mod
    chamadas = {"n": 0}
    original = mod.louvain

    def louvain_espiao(grafo):
        chamadas["n"] += 1
        return original(grafo)

    monkeypatch.setattr(mod, "louvain", louvain_espiao)
    analisador = AnalisadorRede(dois_triangulos_ligados())

    # Act: chama duas vezes
    primeira = analisador._comunidades()
    segunda = analisador._comunidades()

    # Assert: Louvain rodou só uma vez e o resultado cacheado é reaproveitado
    assert chamadas["n"] == 1
    assert primeira is segunda
# Fim dos testes em _comunidades() (cache)
