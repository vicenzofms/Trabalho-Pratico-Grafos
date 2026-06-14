"""Fixtures do backend — um cache JSON pequeno numa pasta temporária.

Os testes nunca tocam em `src/data/` nem nos dados reais (grandes). A fixture
escreve um repositório `octo/demo` no mesmo formato que o `Minerador` grava (chave
= `str((origem, destino, tipo))`, valor = `{origem, destino, peso, tipo}`), cobrindo
os 5 tipos de interação para que os 4 grafos fiquem não-vazios.
"""

import json

import pytest
from fastapi.testclient import TestClient

from trabalho_pratico_grafos.backend import criar_app
from trabalho_pratico_grafos.backend.config import Settings

# (origem, destino, tipo, peso) — duas "panelinhas" {a,b,c} e {c,d,e} ligadas por c.
INTERACOES = [
    ("a", "b", "comentario_issue", 2),
    ("b", "a", "comentario_issue", 2),
    ("b", "c", "comentario_pull_request", 2),
    ("c", "b", "comentario_pull_request", 2),
    ("c", "d", "fechamento_issue", 1),
    ("d", "e", "revisao_pull", 4),
    ("e", "d", "revisao_pull", 4),
    ("e", "c", "merge_pull", 5),
    ("a", "c", "merge_pull", 5),
]


def _conteudo_cache() -> dict:
    return {
        str((origem, destino, tipo)): {
            "origem": origem,
            "destino": destino,
            "peso": peso,
            "tipo": tipo,
        }
        for origem, destino, tipo, peso in INTERACOES
    }


@pytest.fixture
def dir_dados(tmp_path) -> str:
    """Pasta temporária com o cache de `octo/demo` (arquivo `octo_demo.json`)."""
    pasta = tmp_path / "data"
    pasta.mkdir()
    (pasta / "octo_demo.json").write_text(
        json.dumps(_conteudo_cache(), indent=2), encoding="utf-8"
    )
    return str(pasta)


@pytest.fixture
def caminho_cache(dir_dados) -> str:
    import os

    return os.path.join(dir_dados, "octo_demo.json")


@pytest.fixture
def client(dir_dados) -> TestClient:
    app = criar_app(Settings(diretorio_dados=dir_dados, cors_origins="*"))
    return TestClient(app)
