from trabalho_pratico_grafos.grafos import GrafoAbstrato
from trabalho_pratico_grafos.analise.coesao import (
    densidade, coeficiente_agrupamento, assortatividade_grau
)
from trabalho_pratico_grafos.analise.centralidade import (
    centralidade_grau, centralidade_proximidade,
    centralidade_intermediacao, pagerank, centralidade_autovetor
)
from trabalho_pratico_grafos.analise.comunidades import louvain
from trabalho_pratico_grafos.analise.pontes import pontes_locais, arestas_intercomunidade


class AnalisadorRede:
    def __init__(self, grafo: GrafoAbstrato):
        self._grafo = grafo
        self._cache_comunidades = None

    def _comunidades(self) -> list[int]:
        # calcula uma única vez e reutiliza (Louvain é caro)
        if self._cache_comunidades is None:
            self._cache_comunidades = louvain(self._grafo)
        return self._cache_comunidades

    def relatorio_completo(self) -> dict:
        # Executa todas as métricas e devolve um dict serializável para JSON.
        part = self._comunidades()
        return {
            "densidade":       densidade(self._grafo),
            "agrupamento":     coeficiente_agrupamento(self._grafo),
            "assortatividade": assortatividade_grau(self._grafo),
            "centralidades": {
                "grau":          centralidade_grau(self._grafo),
                "proximidade":   centralidade_proximidade(self._grafo),
                "intermediacao": centralidade_intermediacao(self._grafo),
                "pagerank":      pagerank(self._grafo),
                "autovetor":     centralidade_autovetor(self._grafo),
            },
            "comunidades": part,
            "pontes": {
                "locais":          pontes_locais(self._grafo),
                "intercomunidade": arestas_intercomunidade(self._grafo, part),
            },
        }