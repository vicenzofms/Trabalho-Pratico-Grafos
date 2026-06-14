"""Backend FastAPI do Trabalho Prático de Grafos.

Camada HTTP que **orquestra** os pacotes existentes (`grafos`, `analise`,
`gephi`, `minerador`) — não calcula métrica nenhuma por conta própria. Veja o
plano em ``plano-backend-fastapi.md`` para a arquitetura e as fases.
"""

from .main import criar_app

__all__ = ["criar_app"]
