"""Análise da rede (Fase 4) — o núcleo do backend.

Enquanto a fachada `AnalisadorRede` (parte A) não existe, este serviço usa um
**adaptador de fallback** que chama diretamente as funções já entregues do pacote
`analise` (`centralidade_*`, `pagerank`, `louvain`, `modularidade`, `pontes_*`).
As funções ainda pendentes das partes A/B (proximidade, intermediação, densidade,
clustering, assortatividade) são detectadas em tempo de import e ficam `None`
até existirem — quando entrarem, populam sozinhas, sem mudar este arquivo.

Responsabilidades:
- cachear o relatório por `(repo, tipo, versão_do_json)` (costura 4: re-minerar
  muda o mtime e invalida o cache sozinho);
- converter os resultados indexados por id de vértice para `{username: valor}`,
  montando rankings já ordenados (o front quer nomes, não índices).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from trabalho_pratico_grafos.analise import centralidade as _centralidade_mod
from trabalho_pratico_grafos.analise.centralidade import (
    centralidade_autovetor,
    centralidade_grau,
    pagerank,
)
from trabalho_pratico_grafos.analise.comunidades import louvain, modularidade
from trabalho_pratico_grafos.analise.pontes import (
    arestas_intercomunidade,
    pontes_classicas,
    pontes_locais,
)
from trabalho_pratico_grafos.grafos import GrafoAbstrato

from ..fontes import FonteDeDados

if TYPE_CHECKING:  # evita ciclo de import com grafo_servico em tempo de execução
    from .grafo_servico import GrafoServico


# --- Detecção das funções ainda não entregues (partes A/B) -----------------
# `coesao.py` (parte A) pode nem existir ainda → import tolerante a falha.
try:
    from trabalho_pratico_grafos.analise import coesao as _coesao_mod
except ImportError:
    _coesao_mod = None


def _funcao_opcional(modulo, nome: str) -> Callable | None:
    """Retorna a função `nome` do módulo, ou `None` se ela ainda não existe."""
    return getattr(modulo, nome, None) if modulo is not None else None


def _escalar_opcional(modulo, nome: str, grafo: GrafoAbstrato, *args) -> float | None:
    fn = _funcao_opcional(modulo, nome)
    return fn(grafo, *args) if fn is not None else None


def densidade_opcional(grafo: GrafoAbstrato) -> float | None:
    """Densidade via `coesao.densidade` (parte A); `None` enquanto não existir.

    Exposta para o `grafo_servico` preencher `GrafoResumo.densidade` sem que o
    backend calcule a métrica — segue a regra "o backend só orquestra".
    """
    return _escalar_opcional(_coesao_mod, "densidade", grafo)


def _lista_opcional(modulo, nome: str, grafo: GrafoAbstrato) -> list[float] | None:
    fn = _funcao_opcional(modulo, nome)
    return fn(grafo) if fn is not None else None


# --- Adaptador de fallback: produz o relatório indexado por id de vértice ----
def _relatorio_indexado(grafo: GrafoAbstrato) -> dict:
    grau = centralidade_grau(grafo)
    centralidades: dict[str, list[float]] = {
        "grau_entrada": grau["entrada"],
        "grau_saida": grau["saida"],
        "autovetor": centralidade_autovetor(grafo),
        "pagerank": pagerank(grafo),
    }
    # contagens brutas de arestas (in/out), por id de vértice — o front mostra na
    # tabela de centralidades ao lado do valor da métrica selecionada.
    graus = [
        {"entrada": grafo.getGrauEntrada(i), "saida": grafo.getGrauSaida(i)}
        for i in range(grafo.getQuantidadeVertices())
    ]
    # parte B (entram quando existirem):
    proximidade = _lista_opcional(_centralidade_mod, "centralidade_proximidade", grafo)
    if proximidade is not None:
        centralidades["proximidade"] = proximidade
    intermediacao = _lista_opcional(_centralidade_mod, "centralidade_intermediacao", grafo)
    if intermediacao is not None:
        centralidades["intermediacao"] = intermediacao

    particao = louvain(grafo)

    return {
        "densidade": densidade_opcional(grafo),
        "assortatividade": _escalar_opcional(_coesao_mod, "assortatividade_grau", grafo),
        "clustering": _escalar_opcional(_coesao_mod, "coeficiente_agrupamento", grafo),
        "modularidade": modularidade(grafo, particao),
        "centralidades": centralidades,
        "graus": graus,
        "comunidades": particao,
        "pontes": {
            "locais": pontes_locais(grafo),
            "classicas": pontes_classicas(grafo),
            "intercomunidade": arestas_intercomunidade(grafo, particao),
        },
    }


# --- Serialização: id de vértice -> username --------------------------------
def _rotulo(grafo: GrafoAbstrato, i: int) -> str:
    return grafo.getRotuloVertice(i) or str(i)


def _ranking(grafo: GrafoAbstrato, valores: list[float]) -> list[dict]:
    pares = [(_rotulo(grafo, i), valor) for i, valor in enumerate(valores)]
    pares.sort(key=lambda par: par[1], reverse=True)
    return [{"username": username, "valor": valor} for username, valor in pares]


def _ranking_arestas_por_peso(grafo: GrafoAbstrato) -> list[dict]:
    arestas = [
        {
            "origem": _rotulo(grafo, u),
            "destino": _rotulo(grafo, v),
            "peso": grafo.getPesoAresta(u, v),
        }
        for u in range(grafo.getQuantidadeVertices())
        for v in grafo.getSucessores(u)
    ]
    arestas.sort(key=lambda aresta: aresta["peso"], reverse=True)
    return arestas


def _agrupar_comunidades(grafo: GrafoAbstrato, particao: list[int]) -> dict[str, list[str]]:
    grupos: dict[str, list[str]] = {}
    for vertice, comunidade in enumerate(particao):
        grupos.setdefault(str(comunidade), []).append(_rotulo(grafo, vertice))
    return grupos


def _nomear_pares(grafo: GrafoAbstrato, pares: list[tuple[int, int]]) -> list[tuple[str, str]]:
    return [(_rotulo(grafo, u), _rotulo(grafo, v)) for u, v in pares]


def _nomear_graus(grafo: GrafoAbstrato, graus: list[dict]) -> dict[str, dict]:
    return {_rotulo(grafo, i): grau for i, grau in enumerate(graus)}


def _relatorio_vazio() -> dict:
    """Relatório de um grafo sem vértices/arestas (ex.: tipo sem interações)."""
    return {
        "densidade": None,
        "assortatividade": None,
        "clustering": None,
        "modularidade": None,
        "centralidades": {},
        "graus": {},
        "arestas_mais_pesadas": [],
        "comunidades": {},
        "pontes": {"locais": [], "classicas": [], "intercomunidade": []},
    }


def relatorio_do_grafo(grafo: GrafoAbstrato) -> dict:
    """Calcula e serializa (por username) o relatório completo de um grafo."""
    # Grafo sem arestas não tem métricas a calcular (e evita divisão por zero nos
    # algoritmos). Como o minerador nunca gera laços, todo grafo construído tem
    # ou 0 vértices (tipo sem interações) ou >= 2 vértices com >= 1 aresta.
    if grafo.getQuantidadeVertices() == 0 or grafo.getQuantidadeArestas() == 0:
        return _relatorio_vazio()

    indexado = _relatorio_indexado(grafo)
    return {
        "densidade": indexado["densidade"],
        "assortatividade": indexado["assortatividade"],
        "clustering": indexado["clustering"],
        "modularidade": indexado["modularidade"],
        "centralidades": {
            metrica: _ranking(grafo, valores)
            for metrica, valores in indexado["centralidades"].items()
        },
        "graus": _nomear_graus(grafo, indexado["graus"]),
        "arestas_mais_pesadas": _ranking_arestas_por_peso(grafo),
        "comunidades": _agrupar_comunidades(grafo, indexado["comunidades"]),
        "pontes": {
            categoria: _nomear_pares(grafo, pares)
            for categoria, pares in indexado["pontes"].items()
        },
    }


class AnaliseServico:
    def __init__(self, grafo_servico: "GrafoServico", fonte: FonteDeDados) -> None:
        self._grafos = grafo_servico
        self._fonte = fonte
        # cache em memória por (repo, tipo, representacao, versão do json) — costura 4.
        self._cache: dict[tuple[str, str, str, float | None], dict] = {}

    def relatorio(self, repo: str, tipo: str = "integrado", representacao: str = "matriz") -> dict:
        versao = self._fonte.versao(repo)
        chave = (repo, tipo, representacao, versao)
        if chave in self._cache:
            return self._cache[chave]
        # construir() valida o repo (404) e o tipo (422) antes de calcular.
        grafo = self._grafos.construir(repo, tipo, representacao)
        resultado = relatorio_do_grafo(grafo)
        self._cache[chave] = resultado
        return resultado

    def invalidar(self, repo: str) -> None:
        """Descarta as entradas em memória de um repo (ex.: após exclusão)."""
        for chave in [c for c in self._cache if c[0] == repo]:
            del self._cache[chave]
