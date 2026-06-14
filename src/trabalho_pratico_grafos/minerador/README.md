# Pacote `minerador`

Responsável por coletar as interações entre colaboradores de um repositório do
GitHub e convertê-las em um conjunto de dados serializável que alimenta a
construção dos grafos. É a primeira camada do projeto, vindo antes de `grafos`,
`analise` e `gephi`.

## Como funciona

O fluxo geral é o seguinte:

1. O `Minerador` recebe o nome do repositório e uma lista de tokens de acesso.
2. Ele busca todas as issues e pull requests do repositório (informações
   primárias).
3. A partir delas, busca as informações específicas de cada interação
   (comentários, fechamentos, revisões e merges), usando várias threads em
   paralelo para acelerar a coleta.
4. Cada dado bruto é convertido em uma `Interacao` (origem, destino, peso e
   tipo). Interações repetidas entre o mesmo par e do mesmo tipo têm o peso
   acumulado, e auto-interações são descartadas.
5. O resultado pode ser salvo em cache (JSON) e exportado para as próximas
   camadas.

Cada usuário é identificado por um inteiro através do `MapaUsuarios`, porque os
grafos trabalham com índices numéricos. Todo o acesso à rede é isolado no
`ClienteGithub`, que cuida de tokens, rate limit, paginação e novas tentativas.

## Arquivos

### `minerador.py`

Contém a classe principal e as estruturas de dados das interações.

- **`Interacao`** (dataclass): representa uma aresta da rede, com `origem`,
  `destino`, `peso` e `tipo`.
- **`RequestPendente`** (dataclass): representa uma requisição que falhou e
  precisa ser reprocessada depois, guardando o endpoint, o tipo da pendência e
  os dados necessários para repeti-la.
- **`Minerador`**: orquestra toda a coleta. Principais métodos:
  - `__init__(repositorio, tokens, usar_cache)`: inicializa o cliente do
    GitHub, o mapa de usuários, o mapa de interações e os locks de
    concorrência. Lança erro se a lista de tokens estiver vazia.
  - `executar(sleepTime, reprocessar_pendencias)`: ponto de entrada da
    mineração. Tenta o cache primeiro (se habilitado), verifica se o repositório
    existe, busca issues e PRs em paralelo, dispara a coleta de comentários,
    fechamentos, revisões e merges, e ao final reprocessa as pendências e salva o
    cache. Se os tokens ficarem inutilizáveis no meio da coleta
    (`ErroTokensInutilizaveis`), aborta de forma limpa e preserva tudo que já foi
    registrado, salvando o resultado parcial no cache em vez de perdê-lo.
  - `carregarDoCache()` e `salvarNoCache()`: leem e gravam o mapa de interações
    em `data/<owner>_<repo>.json`. Retornam ao estado anterior sem quebrar caso o
    arquivo não exista ou esteja corrompido.
  - `__obterCaminhoCache()`: monta o caminho do arquivo de cache a partir do nome
    do repositório.
  - `__buscarIssues()` e `__buscarPullRequests()`: buscam, com paginação por
    cursor, todas as issues e PRs do repositório. São requisições obrigatórias.
  - `__definirAutoresIssuesPRs()`: monta um dicionário que associa o número de
    cada issue ou PR ao login de quem a abriu, usado depois para ligar
    comentários ao autor correto.
  - `__minerarComentariosIssuesPR()` e
    `__minerarComentariosInlinePullRequest()`: buscam os comentários (paginados),
    registram páginas que falharam como pendências e encaminham cada comentário
    para o processador correspondente.
  - `__minerarReviewsDeUmPR(numeroPR, autorPR)` e
    `__minerarMergeDeUmPR(numeroPR, autorPR)`: buscam as revisões e o merge de um
    PR específico. Em caso de falha, registram uma pendência em vez de processar
    dados parciais.
  - `__processarFechamentoIssues()`: percorre as issues já carregadas (sem novas
    requisições) e cria uma interação de fechamento quando quem fechou é
    diferente de quem abriu.
  - `__processarComentarioIssue()`, `__processarComentarioInlinePR()`,
    `__processarReview()` e `__processarMerge()`: convertem um dado bruto em uma
    `Interacao`. Todos descartam usuários removidos (campo nulo) e auto-loops
    antes de registrar.
  - `__adicionarInteracao(interacao)`: insere a interação no mapa ou soma o peso
    se já existir uma do mesmo par e tipo. Protegido por lock.
  - `__adicionarPendencia(pendencia)`: registra uma pendência na lista. Protegido
    por lock.
  - `__processarPendencias(sleepTime)`: faz uma rodada de reprocessamento das
    pendências, despachando cada uma para o fluxo certo conforme o tipo. O que
    falhar de novo permanece pendente.
  - `exportarDados()`: devolve uma cópia dos usuários e interações em formato de
    dicionário, ou `None` se não houver dados. É a saída consumida pela camada de
    grafos.
  - `quantidadeInteracoes()`, `quantidadeInteracoesRegistradas()` e
    `quantidadeUsuarios()`: contadores de apoio.
  - `exibirInteracoes()`, `exibirUsuarios()` e `exibirRelatorioTokens()`:
    impressões usadas para depuração.

### `cliente_github.py`

Isola todo o acesso HTTP à API do GitHub.

- **`MinerarOpcoes`** (dataclass): agrupa opções de uma requisição, como o tempo
  de espera entre páginas, a descrição exibida e a cor do log.
- **`ResultadoPaginado`** (dataclass): resultado de uma busca paginada, com a
  lista de itens e a lista de páginas que falharam.
- **`TokenEstado`** (dataclass): estado interno de cada token, incluindo número
  de usos, se está inválido e até quando está bloqueado por rate limit.
- **`ErroRequestObrigatoria`** (exceção): levantada quando uma requisição
  marcada como obrigatória falha, abortando a mineração.
- **`ErroTokensInutilizaveis`** (exceção): levantada quando não há mais nenhum
  token utilizável, seja porque todos ficaram inválidos, seja porque todos estão
  em rate limit com espera superior a quinze minutos. Sinaliza ao minerador que
  deve abortar a coleta.
- **`ClienteGithub`**: principais métodos:
  - `get(endpoint, ...)`: faz uma única requisição e devolve o JSON, ou `None` em
    caso de falha não obrigatória.
  - `getPaginado(endpoint, ...)`: percorre as páginas de um endpoint usando o
    parâmetro `page`, acumula os itens e reporta as páginas que falharam.
    Desiste após três falhas consecutivas.
  - `getPaginadoCursor(endpoint, ...)`: percorre as páginas seguindo o link de
    próxima página (cursor) presente no cabeçalho da resposta, usado em issues e
    PRs.
  - `__getResponse(...)`: núcleo das requisições. Escolhe um token, monta o
    cabeçalho, executa a chamada e trata os códigos de status (sucesso, token
    inválido, rate limit, limite de paginação e erros de rede com novas
    tentativas).
  - `__getToken()`: seleciona o token válido menos usado e, se todos estiverem
    bloqueados, espera o mínimo necessário até um liberar. Quando não há token
    utilizável (todos inválidos ou com espera maior que quinze minutos), levanta
    `ErroTokensInutilizaveis`.
  - `__getHeader(token)`: monta o cabeçalho de autenticação.
  - `__requestFalha(motivo, obrigatorio)`: centraliza o tratamento de falha,
    levantando exceção se a requisição for obrigatória ou apenas avisando caso
    contrário.
  - `getQuantidadeRequests()` e `exibirRelatorioTokens()`: métricas de uso.

### `mapa_usuarios.py`

- **`MapaUsuarios`**: faz a ponte entre o login textual de um usuário e o índice
  inteiro usado nos grafos. Não há remoção, então os ids são incrementais.
  - `buscarOuRegistrar(username)`: devolve o id do usuário, registrando-o se for
    a primeira vez.
  - `buscarNome(id)`: devolve o login a partir do id.
  - `quantidadeDeUsuarios()`: total de usuários registrados.
  - `listarUsuarios()`: imprime todos os logins (depuração).
  - `exportarUsuarios()`: devolve os mapeamentos (login para id e id para login)
    e a contagem, em cópia, para a exportação dos dados.

### `cores.py`

Utilitário de apoio para colorir as mensagens de log no terminal.

- **`colorir(texto, cor)`**: envolve o texto nos códigos ANSI da cor escolhida.
- **`CORES`** e **`RESET`**: tabela de códigos de cor e o código de reset.

### `__init__.py`

Expõe apenas a classe `Minerador`, que é a interface pública do pacote.
