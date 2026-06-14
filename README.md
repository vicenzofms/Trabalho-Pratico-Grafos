# Trabalho-Pratico-Grafos
Criação de uma lib em python para análise de um repositório utilizando grafos

## Backend (FastAPI)

Camada HTTP que **orquestra** os pacotes existentes (`grafos`, `analise`,
`gephi`, `minerador`) e expõe os dados minerados, as métricas de rede e a
exportação GEPHI. Veja o plano em [`plano-backend-fastapi.md`](plano-backend-fastapi.md).

No MVP é **cache-only**: lê os repositórios já minerados em `src/data/`. As rotas
de mineração existem, mas respondem `501` (ativadas na Fase 6).

```bash
# instalar as dependências do backend
pip install -e ".[backend]"

# (opcional) configurar variáveis: cp .env.example .env
uvicorn trabalho_pratico_grafos.backend.main:app --reload
# docs interativas em http://localhost:8000/docs
```

Testes do backend:

```bash
pip install -e ".[dev]"
pytest tests/backend -v
```
