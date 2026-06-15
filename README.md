# Trabalho-Pratico-Grafos

Biblioteca em Python para análise de repositórios do GitHub utilizando grafos,
acompanhada de uma API HTTP (FastAPI) e de um frontend (Angular) para
visualização dos resultados e do grafo.

## Sobre

O projeto modela as interações entre colaboradores de um repositório (comentários
em issues e pull requests, fechamentos, revisões e merges) como um **grafo
direcionado e ponderado**, implementado do zero — sem bibliotecas prontas de
grafos — e roda sobre ele um conjunto de métricas de redes complexas.

O fluxo de dados percorre quatro pacotes, em camadas:

| Pacote | Papel |
| --- | --- |
| [`minerador`](src/trabalho_pratico_grafos/minerador/) | Coleta as interações de um repositório via API do GitHub e salva em cache JSON. |
| [`grafos`](src/trabalho_pratico_grafos/grafos/) | Estrutura de dados central: grafo direcionado e ponderado (matriz e lista de adjacência). |
| [`analise`](src/trabalho_pratico_grafos/analise/) | Métricas de rede: centralidades, comunidades (Louvain), coesão e pontes. |
| [`gephi`](src/trabalho_pratico_grafos/gephi/) | Exporta o grafo para o formato do Gephi. |

Em cima desses pacotes, o **backend** (FastAPI) expõe os dados minerados, as
métricas, a visualização do grafo e a exportação via HTTP, e o **frontend**
(Angular) consome essa API e renderiza o grafo com a biblioteca vis.js.
Todas as métricas usam apenas a biblioteca padrão de Python.

## Requisitos

- Python `>= 3.12`
- Node.js + npm (apenas para o frontend)

## Início rápido

### 1. Clonar e preparar o ambiente

```bash
git clone https://github.com/vicenzofms/Trabalho-Pratico-Grafos.git
cd Trabalho-Pratico-Grafos

# (recomendado) ambiente virtual
python -m venv .venv
# Windows (PowerShell):  .venv\Scripts\Activate.ps1
# Linux/macOS:           source .venv/bin/activate
```

### 2. Instalar a biblioteca

```bash
# biblioteca de grafos/análise (núcleo)
pip install -e .

# com as dependências do backend (FastAPI)
pip install -e ".[backend]"

# com as ferramentas de desenvolvimento e testes
pip install -e ".[dev]"
```

### 3. Rodar o backend (FastAPI)

A camada HTTP **orquestra** os pacotes existentes e expõe os dados minerados, as
métricas de rede, a visualização do grafo (nós e arestas em JSON) e a exportação
GEPHI.

Por padrão (sem `GITHUB_TOKENS`), o backend é **cache-only**: lê os repositórios já
minerados em `src/data/` e as rotas de mineração respondem `503`. Com
`GITHUB_TOKENS` configurado, a mineração fica ativa: as rotas disparam a coleta em
segundo plano (`202` com um `JobMineracao`), acompanhada pela rota de status.

```bash
pip install -e ".[backend]"

# (opcional) configurar variáveis — veja a seção Configuração (.env)
cp .env.example .env

uvicorn trabalho_pratico_grafos.backend.main:app --reload
# docs interativas em http://localhost:8000/docs
```

### 4. Rodar o frontend (Angular)

```bash
cd frontend
npm install
npm start
# app em http://localhost:4200
```

## Configuração (`.env`)

O backend lê suas configurações de variáveis de ambiente (ou de um arquivo
`.env` na raiz do projeto). Copie o modelo e ajuste o que precisar:

```bash
cp .env.example .env
```

Para uso cache-only **nenhuma variável é obrigatória** — os defaults bastam;
`GITHUB_TOKENS` só é necessário para minerar pela API.

| Variável | Descrição | Default |
| --- | --- | --- |
| `GITHUB_TOKENS` | Tokens do GitHub separados por vírgula. Usados pela mineração (rotas `/minerar` e `/atualizar`); sem eles, essas rotas respondem `503`. | vazio |
| `CORS_ORIGINS` | Origens permitidas no CORS (origem do front), separadas por vírgula. Ex.: `http://localhost:4200`. | `*` |
| `DIRETORIO_DADOS` | Pasta dos caches JSON. Vazio = usa `src/data` (mesma do minerador). | `src/data` |

> O arquivo `.env` é git-ignored. **Nunca** faça commit dos seus tokens.

## Minerando um repositório

A mineração coleta as interações de um repositório e grava um cache JSON em
`src/data/<owner>_<repo>.json`. Exemplo de uso direto do pacote `minerador`
(veja também [`src/trabalho_pratico_grafos/scripts/builder.py`](src/trabalho_pratico_grafos/scripts/builder.py)):

```python
from trabalho_pratico_grafos.minerador import Minerador

# nome do repositório e lista de tokens do GitHub
minerador = Minerador("discordjs/discord.js", ["SEU_TOKEN"], usar_cache=True)
minerador.executar()
dados = minerador.exportarDados()
```

> Não dê commit nos seus tokens.

## Testes

```bash
pip install -e ".[dev]"

# todos os testes
pytest

# apenas o backend
pytest tests/backend -v
```

## Estrutura do projeto

```
.
├── src/trabalho_pratico_grafos/
│   ├── minerador/   # coleta de interações via API do GitHub
│   ├── grafos/      # estrutura de dados de grafo (matriz e lista)
│   ├── analise/     # métricas de redes complexas
│   ├── gephi/       # exportação para o Gephi
│   ├── backend/     # API HTTP (FastAPI)
│   └── scripts/     # scripts auxiliares
├── frontend/        # aplicação Angular
├── tests/           # testes (pytest)
└── .env.example     # modelo de configuração do backend
```

Cada pacote tem um `README.md` próprio com a documentação detalhada de seus
módulos.

## Autores

- Vicenzo Fonseca de Mello Souza
- Renato Douglas Nascimento Silva de Oliveira
- Ana Luiza de Freitas Rodrigues
- Kayke Emanoel de Souza Santos

## Licença

[MIT](LICENSE).
