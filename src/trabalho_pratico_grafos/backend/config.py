"""Configuração do backend (pydantic-settings, lê `.env`).

Mantém os segredos (tokens do GitHub) fora do código: no servidor os tokens vêm
sempre do ambiente e são repassados ao gerenciador de mineração.
"""

import os

from pydantic_settings import BaseSettings, SettingsConfigDict


def diretorio_dados_padrao() -> str:
    """Pasta ``src/data`` — mesma que o ``Minerador`` usa para o cache JSON.

    Calculada relativa a este arquivo (``src/trabalho_pratico_grafos/backend/``),
    subindo dois níveis até ``src/`` e entrando em ``data``. Assim a ``FonteCache``
    enxerga exatamente os JSON que o minerador grava (costura 1 do plano).
    """
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Tokens do GitHub, separados por vírgula (ex.: "ghp_xxx,ghp_yyy").
    github_tokens: str = ""

    # Origens permitidas no CORS, separadas por vírgula (origem do front).
    cors_origins: str = "*"

    # Diretório onde estão os caches JSON. Quando vazio, usa `diretorio_dados_padrao()`.
    # Sobrescrito nos testes para apontar para uma pasta temporária.
    diretorio_dados: str = ""

    @property
    def tokens(self) -> list[str]:
        return [t.strip() for t in self.github_tokens.split(",") if t.strip()]

    @property
    def origens_cors(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def caminho_dados(self) -> str:
        return self.diretorio_dados or diretorio_dados_padrao()
