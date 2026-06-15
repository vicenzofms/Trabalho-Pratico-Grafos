"""Testes da Fase 6 (mineração pela API) com um Minerador FALSO.

Nenhum teste toca a rede ou usa token: a criação do `Minerador` é injetada
(`criar_miner`), e o fake apenas grava um JSON no diretório que a `FonteCache` lê.
Assim os estados (executando/concluido/erro), as pré-condições (409), o estado
`MINERANDO`/`ERRO` e a invalidação por mtime são todos determinísticos.
"""

import json
import os

import pytest
from fastapi.testclient import TestClient

from trabalho_pratico_grafos.backend import criar_app
from trabalho_pratico_grafos.backend.config import Settings
from trabalho_pratico_grafos.backend.erros import ConflitoMineracaoError
from trabalho_pratico_grafos.backend.fontes import FonteCache
from trabalho_pratico_grafos.backend.mineracao import GerenciadorMineracao
from trabalho_pratico_grafos.backend.schemas.repositorio import EstadoRepositorio
from trabalho_pratico_grafos.backend.servicos import RepositorioServico

# Interações que o minerador falso "descobre" (2 usuários, 2 interações).
INTERACOES_NOVAS = [
    ("ana", "bia", "comentario_issue", 2),
    ("bia", "ana", "merge_pull", 5),
]


class _MineradorFake:
    """Imita o contrato do Minerador usado pelo gerenciador: executar + salvarNoCache."""

    def __init__(self, repo: str, dir_dados: str) -> None:
        self._repo = repo
        self._dir = dir_dados

    def executar(self, sleepTime: float = 0.8, reprocessar_pendencias: bool = True) -> None:
        pass  # "minera" sem fazer nada

    def salvarNoCache(self) -> None:
        caminho = os.path.join(self._dir, f"{self._repo.replace('/', '_')}.json")
        conteudo = {
            str((o, d, t)): {"origem": o, "destino": d, "peso": p, "tipo": t}
            for o, d, t, p in INTERACOES_NOVAS
        }
        os.makedirs(self._dir, exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(conteudo, f)

    def quantidadeUsuarios(self) -> int:
        return len({u for it in INTERACOES_NOVAS for u in (it[0], it[1])})

    def quantidadeInteracoes(self) -> int:
        return len(INTERACOES_NOVAS)


class _MineradorQuebrado:
    def executar(self, sleepTime: float = 0.8, reprocessar_pendencias: bool = True) -> None:
        raise RuntimeError("falha simulada de rede")

    def salvarNoCache(self) -> None:  # pragma: no cover - nunca chega aqui
        pass


def _gerenciador(miner_cls):
    def criar(fonte, settings):
        return GerenciadorMineracao(
            fonte,
            ["fake-token"],
            criar_miner=lambda repo, tokens: miner_cls(repo, settings.caminho_dados)
            if miner_cls is _MineradorFake
            else miner_cls(),
        )

    return criar


@pytest.fixture
def client_fake(dir_dados) -> TestClient:
    app = criar_app(Settings(diretorio_dados=dir_dados), criar_gerenciador=_gerenciador(_MineradorFake))
    return TestClient(app)


@pytest.fixture
def client_quebrado(dir_dados) -> TestClient:
    app = criar_app(Settings(diretorio_dados=dir_dados), criar_gerenciador=_gerenciador(_MineradorQuebrado))
    return TestClient(app)


# --- Rotas (HTTP) -----------------------------------------------------------
def test_minerar_repo_novo_fluxo_completo(client_fake):
    # dispara: 202 + job "executando"
    resposta = client_fake.post("/api/repositorios/novo/repo/minerar")
    assert resposta.status_code == 202
    job = resposta.json()
    assert job["estado"] == "executando"

    # o BackgroundTask roda síncrono no TestClient -> job concluído e cache escrito
    status = client_fake.get(f"/api/repositorios/novo/repo/minerar/status?job_id={job['job_id']}")
    assert status.status_code == 200
    assert status.json()["estado"] == "concluido"

    # repo agora está DISPONIVEL com os dados minerados
    resumo = client_fake.get("/api/repositorios/novo/repo").json()
    assert resumo["estado"] == "disponivel"
    assert resumo["quantidade_interacoes"] == len(INTERACOES_NOVAS)


def test_minerar_repo_existente_conflita_409(client_fake):
    # octo/demo já existe no cache -> minerar deve recusar (use atualizar)
    assert client_fake.post("/api/repositorios/octo/demo/minerar").status_code == 409


def test_atualizar_repo_ausente_conflita_409(client_fake):
    assert client_fake.post("/api/repositorios/fantasma/repo/atualizar").status_code == 409


def test_excluir_durante_mineracao_conflita_409(dir_dados):
    # Inicia (registra job "executando") sem rodar o BackgroundTask: repo MINERANDO.
    fonte = FonteCache(dir_dados)
    gerenciador = GerenciadorMineracao(
        fonte, ["fake"], criar_miner=lambda repo, tokens: _MineradorFake(repo, dir_dados)
    )
    servico = RepositorioServico(fonte, gerenciador)

    gerenciador.iniciar("novo/repo")  # job ativo, ainda não executado
    with pytest.raises(ConflitoMineracaoError):
        servico.remover("novo/repo")


def test_atualizar_repo_existente_regrava_o_cache(client_fake, caminho_cache):
    mtime_antes = os.path.getmtime(caminho_cache)

    resposta = client_fake.post("/api/repositorios/octo/demo/atualizar")
    assert resposta.status_code == 202

    # o cache foi regravado pelo minerador falso (mtime muda; dados = os do fake)
    assert os.path.getmtime(caminho_cache) >= mtime_antes
    resumo = client_fake.get("/api/repositorios/octo/demo").json()
    assert resumo["quantidade_interacoes"] == len(INTERACOES_NOVAS)


def test_erro_na_mineracao_vira_estado_erro(client_quebrado):
    resposta = client_quebrado.post("/api/repositorios/novo/repo/minerar")
    assert resposta.status_code == 202
    job_id = resposta.json()["job_id"]

    status = client_quebrado.get(f"/api/repositorios/novo/repo/minerar/status?job_id={job_id}").json()
    assert status["estado"] == "erro"
    assert "falha simulada" in (status["detalhe"] or "")

    # o repo reflete ERRO no resumo
    assert client_quebrado.get("/api/repositorios/novo/repo").json()["estado"] == "erro"


# --- Gerenciador (unidade, sem HTTP) ----------------------------------------
def test_estado_minerando_antes_de_executar_o_job(dir_dados):
    fonte = FonteCache(dir_dados)
    gerenciador = GerenciadorMineracao(
        fonte, ["fake"], criar_miner=lambda repo, tokens: _MineradorFake(repo, dir_dados)
    )
    servico = RepositorioServico(fonte, gerenciador)

    job = gerenciador.iniciar("novo/repo")
    assert job.estado == "executando"
    # enquanto o job não roda, o repo aparece como MINERANDO
    assert servico.obter("novo/repo").estado == EstadoRepositorio.MINERANDO

    gerenciador.executar_job(job.job_id)
    assert gerenciador.status(job.job_id).estado == "concluido"
    assert servico.obter("novo/repo").estado == EstadoRepositorio.DISPONIVEL


def test_disparo_com_job_em_andamento_conflita(dir_dados):
    fonte = FonteCache(dir_dados)
    gerenciador = GerenciadorMineracao(
        fonte, ["fake"], criar_miner=lambda repo, tokens: _MineradorFake(repo, dir_dados)
    )
    gerenciador.iniciar("novo/repo")  # job ativo, ainda não executado
    with pytest.raises(ConflitoMineracaoError):
        gerenciador.iniciar("novo/repo")
