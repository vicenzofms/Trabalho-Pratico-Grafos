"""Costura 3 — gerência de jobs de mineração (interface + stub + implementação real)."""

from .base import GerenciadorMineracao
from .real import GerenciadorMineracaoReal
from .stub import GerenciadorMineracaoStub

__all__ = ["GerenciadorMineracao", "GerenciadorMineracaoStub", "GerenciadorMineracaoReal"]
