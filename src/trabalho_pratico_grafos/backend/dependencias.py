"""Injeção de dependência — expõe os serviços guardados em `app.state`.

Os serviços (e os caches em memória que eles carregam) são criados uma única vez
em `criar_app()` e ficam em `app.state`. Estas funções apenas os recuperam, o que
torna o app testável: cada `TestClient` cria um app com sua própria fonte de dados
(pasta temporária), sem singletons globais nem `lru_cache` a limpar.
"""

from fastapi import Request

from .mineracao import GerenciadorMineracao
from .servicos import AnaliseServico, GrafoServico, RepositorioServico


def get_repositorio_servico(request: Request) -> RepositorioServico:
    return request.app.state.repositorio_servico


def get_grafo_servico(request: Request) -> GrafoServico:
    return request.app.state.grafo_servico


def get_analise_servico(request: Request) -> AnaliseServico:
    return request.app.state.analise_servico


def get_gerenciador_mineracao(request: Request) -> GerenciadorMineracao:
    return request.app.state.gerenciador_mineracao
