"""Interface `FonteDeDados` (costura 1).

Todo o backend consome os dados por esta interface — nunca lendo `src/data/`
espalhado pelo código nem chamando o `Minerador` direto. No MVP a única
implementação é `FonteCache`; na Fase 6 a mineração apenas grava um novo JSON e a
`FonteCache` passa a enxergá-lo sem nenhuma mudança a jusante.
"""

from abc import ABC, abstractmethod


class FonteDeDados(ABC):
    @abstractmethod
    def listar(self) -> list[str]:
        """Nomes ("owner/repo") de todos os repositórios disponíveis na fonte."""

    @abstractmethod
    def carregar(self, repo: str) -> dict | None:
        """Dados de um repositório no formato `{usuarios, interacoes}`.

        Mesmo formato que `Minerador.exportarDados()`. Retorna `None` quando o
        repositório não existe na fonte (estado AUSENTE).
        """

    @abstractmethod
    def versao(self, repo: str) -> float | None:
        """Versão atual dos dados do repositório (ex.: mtime do JSON).

        Usada como parte da chave do cache de análise (costura 4): ao atualizar
        (re-minerar) um repo, a versão muda e o cache invalida sozinho. `None`
        quando o repositório não existe.
        """
