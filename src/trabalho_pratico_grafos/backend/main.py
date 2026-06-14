"""App FastAPI do backend — fábrica, CORS, routers, /health e tradução de erros.

`criar_app()` monta o app com uma `Settings` (default ou injetada nos testes) e
guarda os serviços em `app.state` (ver `dependencias.py`). O entrypoint do uvicorn
é o `app` no fim deste módulo:

    uvicorn trabalho_pratico_grafos.backend.main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import Settings
from .erros import (
    MetricaInvalidaError,
    MineracaoIndisponivelError,
    RepositorioAusenteError,
    TipoGrafoInvalidoError,
)
from .fontes import FonteCache
from .mineracao import GerenciadorMineracaoStub
from .routers import analise, grafos, repositorios
from .servicos import AnaliseServico, GrafoServico, RepositorioServico


def _registrar_erros(app: FastAPI) -> None:
    """Mapeia as exceções de domínio para os códigos do contrato (seção 6)."""

    @app.exception_handler(RepositorioAusenteError)
    def _repo_ausente(request: Request, exc: RepositorioAusenteError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(TipoGrafoInvalidoError)
    def _tipo_invalido(request: Request, exc: TipoGrafoInvalidoError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": str(exc), "tipos_validos": exc.validos},
        )

    @app.exception_handler(MetricaInvalidaError)
    def _metrica_invalida(request: Request, exc: MetricaInvalidaError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": str(exc), "metricas_validas": exc.validas},
        )

    @app.exception_handler(MineracaoIndisponivelError)
    def _mineracao_indisponivel(request: Request, exc: MineracaoIndisponivelError) -> JSONResponse:
        return JSONResponse(status_code=501, content={"detail": str(exc)})


def criar_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    app = FastAPI(
        title="Trabalho Prático de Grafos — Backend",
        description="API que orquestra mineração, grafos e análise de rede.",
        version="0.0.1",
    )

    # Serviços e caches compartilhados (criados uma vez por app).
    fonte = FonteCache(settings.caminho_dados)
    grafo_servico = GrafoServico(fonte)
    app.state.settings = settings
    app.state.fonte = fonte
    app.state.repositorio_servico = RepositorioServico(fonte)
    app.state.grafo_servico = grafo_servico
    app.state.analise_servico = AnaliseServico(grafo_servico, fonte)
    app.state.gerenciador_mineracao = GerenciadorMineracaoStub()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origens_cors,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["infra"])
    def health() -> dict:
        return {"status": "ok"}

    app.include_router(repositorios.router, prefix="/api")
    app.include_router(grafos.router, prefix="/api")
    app.include_router(analise.router, prefix="/api")

    _registrar_erros(app)
    return app


app = criar_app()
