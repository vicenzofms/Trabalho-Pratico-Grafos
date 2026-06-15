"""`FonteCache` — lê os JSON minerados de `src/data/` (costura 1, MVP).

O JSON em disco é o mapa de interações que o `Minerador.salvarNoCache()` grava:
cada chave é a tupla `(origem, destino, tipo)` serializada como string e cada
valor tem `{origem, destino, peso, tipo}`. Esta fonte transforma esse formato no
contrato `{usuarios, interacoes}` que o `grafo_servico` consome — sem depender do
`Minerador` (logo, sem exigir token) e sem usar `eval` na chave (os valores já
trazem origem/destino/tipo).
"""

import json
import os

from .base import FonteDeDados


class FonteCache(FonteDeDados):
    def __init__(self, diretorio: str) -> None:
        self._diretorio = diretorio

    def _caminho(self, repo: str) -> str:
        # "owner/repo" -> "owner_repo.json" (mesma convenção do Minerador).
        return os.path.join(self._diretorio, f"{repo.replace('/', '_')}.json")

    def listar(self) -> list[str]:
        if not os.path.isdir(self._diretorio):
            return []
        repos: list[str] = []
        for nome in sorted(os.listdir(self._diretorio)):
            if not nome.endswith(".json"):
                continue
            # "owner_repo.json" -> "owner/repo". Logins do GitHub não contêm "_",
            # então o PRIMEIRO "_" é sempre a barra (nomes de repo podem ter "_").
            repos.append(nome[: -len(".json")].replace("_", "/", 1))
        return repos

    def carregar(self, repo: str) -> dict | None:
        caminho = self._caminho(repo)
        if not os.path.isfile(caminho):
            return None

        with open(caminho, "r", encoding="utf-8") as f:
            bruto = json.load(f)

        interacoes = [
            {
                "origem": v["origem"],
                "destino": v["destino"],
                "peso": v["peso"],
                "tipo": v["tipo"],
            }
            for v in bruto.values()
        ]

        # Deriva os usuários a partir das interações (mesma contagem que o
        # `Minerador.carregarDoCache()` produz: usuários distintos que aparecem
        # como origem ou destino de alguma interação).
        ids_por_username: dict[str, int] = {}
        usernames_por_id: list[str] = []
        for interacao in interacoes:
            for nome in (interacao["origem"], interacao["destino"]):
                if nome not in ids_por_username:
                    ids_por_username[nome] = len(usernames_por_id)
                    usernames_por_id.append(nome)

        return {
            "usuarios": {
                "ids_por_username": ids_por_username,
                "usernames_por_id": usernames_por_id,
                "quantidade": len(usernames_por_id),
            },
            "interacoes": interacoes,
        }

    def versao(self, repo: str) -> float | None:
        caminho = self._caminho(repo)
        if not os.path.isfile(caminho):
            return None
        return os.path.getmtime(caminho)

    def remover(self, repo: str) -> bool:
        caminho = self._caminho(repo)
        if not os.path.isfile(caminho):
            return False
        os.remove(caminho)
        return True
