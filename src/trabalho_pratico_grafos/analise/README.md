# Pacote `analise`

Aplica algoritmos e métricas de redes complexas sobre um grafo já construído. É o
núcleo analítico do projeto: recebe um `GrafoAbstrato` e produz números e
estruturas (rankings de centralidade, partições em comunidades, coeficientes de
coesão e listas de pontes). Todas as métricas foram implementadas do zero, usando
apenas a biblioteca padrão de Python.

## Como funciona

Cada métrica é uma função que recebe o grafo e usa apenas a API pública dele, sem
saber se a representação interna é matriz ou lista. Os utilitários de caminhos
mínimos ficam centralizados em um único arquivo e são reaproveitados pelas
métricas de distância.

Algumas métricas são definidas para grafos não direcionados. Nesses casos
(agrupamento, assortatividade, comunidades e pontes locais e clássicas) o cálculo
é feito sobre o grafo subjacente, que é a versão não direcionada e ponderada do
grafo original, em que o peso entre dois vértices é a soma dos pesos das duas
direções. As centralidades, por sua vez, respeitam o sentido das arestas.

A classe `AnalisadorRede` serve de fachada: executa todas as métricas de uma vez
e devolve um relatório consolidado, reaproveitando o resultado caro do Louvain.

## Arquivos

### `caminhos.py`

Utilitários de caminhos mínimos, base para as centralidades de distância.

- **`ResultadoBrandes`** (NamedTuple): empacota os três dados que o algoritmo de
  Brandes precisa, a pilha de vértices em ordem de visita, a lista de
  predecessores em caminho mínimo e o número de caminhos mínimos até cada
  vértice.
- **`bfs_distancias(grafo, origem)`**: busca em largura que devolve a distância em
  número de arestas da origem até cada vértice, ignorando pesos. Vértices
  inalcançáveis ficam com infinito.
- **`dijkstra_distancias(grafo, origem)`**: menor distância somando os pesos das
  arestas, usando uma fila de prioridade (`heapq`). Assume pesos positivos.
- **`bfs_brandes(grafo, origem)`**: busca em largura que coleta a pilha, os
  predecessores e a contagem de caminhos mínimos, devolvendo um
  `ResultadoBrandes`. É executada uma vez por vértice dentro do cálculo de
  intermediação.

### `centralidade.py`

Mede a importância de cada colaborador na rede.

- **`centralidade_grau(grafo)`**: devolve um dicionário com as centralidades de
  grau de entrada e de saída, cada uma normalizada por `n-1`. Mede quão conectado
  o vértice é.
- **`centralidade_proximidade(grafo)`**: mede quão perto um vértice está dos
  demais. Para cada vértice roda uma busca em largura, soma as distâncias aos
  alcançáveis e aplica a normalização de Wasserman-Faust, que pondera pela fração
  de nós alcançáveis e trata grafos desconexos sem dividir por zero.
- **`centralidade_intermediacao(grafo)`**: fração dos caminhos mínimos entre todos
  os pares que passa por cada vértice, identificando os que atuam como pontes.
  Implementa o algoritmo de Brandes, propagando os créditos de cada caminho
  mínimo do vértice mais distante para o mais próximo, com normalização para
  grafo direcionado.
- **`pagerank(grafo, d=0.85)`**: mede influência considerando a importância de
  quem aponta para o vértice. Usa iteração de potência com fator de amortecimento
  e trata os nós sem saída, redistribuindo a massa deles entre todos.
- **`centralidade_autovetor(grafo)`**: variante espectral da influência, também
  por iteração de potência. Um vértice é importante se vértices importantes
  apontam para ele. Para quando os valores estabilizam ou após cem iterações.

### `coesao.py`

Propriedades estruturais da rede como um todo.

- **`densidade(grafo)`**: razão entre o número de arestas existentes e o máximo
  possível para um grafo direcionado simples. Varia de 0 a 1.
- **`coeficiente_agrupamento(grafo)`**: média dos coeficientes locais, calculados
  sobre o grafo subjacente. Para cada vértice mede a proporção de arestas que
  existem entre os seus vizinhos em relação ao total possível. Vértices com menos
  de dois vizinhos contribuem com zero.
- **`assortatividade_grau(grafo)`**: correlação de Pearson entre os graus das
  pontas de cada aresta, pela fórmula de Newman. Indica se vértices muito
  conectados tendem a se ligar entre si (valor positivo) ou à periferia (valor
  negativo). Usa acumuladores em uma única passagem pelas arestas.

### `comunidades.py`

Detecção de grupos de colaboração.

- **`modularidade(grafo, particao)`**: função de avaliação que mede a qualidade de
  uma partição em comunidades, no intervalo de -0.5 a 1. Valores entre cerca de
  0.3 e 0.7 indicam estrutura de comunidades significativa.
- **`louvain(grafo)`**: heurística que busca a partição que maximiza a
  modularidade. Alterna duas fases até estabilizar, o movimento local de vértices
  para a comunidade vizinha que mais aumenta a modularidade, e a agregação de cada
  comunidade em um super-vértice, formando um grafo menor para a próxima rodada.
  Devolve um rótulo de comunidade por vértice original.
- **`_construir_grafo_subjacente(grafo)`** (interno): monta a versão não
  direcionada e ponderada do grafo, somando os pesos das duas direções entre cada
  par.
- **`_grausPonderados(subjacente)`** (interno): soma dos pesos das arestas que
  incidem em cada vértice.
- **`_modularidadePeloSubjacente(subjacente, particao)`** (interno): calcula a
  modularidade diretamente sobre o grafo subjacente já construído.
- **`_louvainSubjacente(subjacente)`** (interno): executa a fase de movimento
  local, movendo cada vértice para a comunidade que maximiza o ganho de
  modularidade até não haver mais movimentos.
- **`_agregar(subjacente, comunidades)`** (interno): colapsa cada comunidade em um
  super-vértice, transformando arestas internas em laços e arestas entre
  comunidades em ligações entre super-vértices. Devolve o novo grafo e o mapa de
  ids.

### `pontes.py`

Identifica as ligações que conectam grupos que de outra forma estariam separados.

- **`pontes_locais(grafo)`**: arestas cujas pontas não têm nenhum vizinho em
  comum. Remover uma dessas ligações não desconecta o grafo, mas aumenta muito a
  distância entre as duas pontas. Atua sobre o grafo subjacente e devolve pares
  não direcionados na convenção `u < v`.
- **`arestas_intercomunidade(grafo, particao)`**: arestas cujas pontas estão em
  comunidades diferentes, segundo a partição recebida. Atua sobre o grafo
  direcionado e devolve os pares no sentido da aresta. Não executa o Louvain, o
  que permite avaliar qualquer partição.
- **`pontes_classicas(grafo)`**: arestas cuja remoção desconecta o grafo. Usa uma
  busca em profundidade com pilha explícita (sem recursão, para evitar estouro do
  limite de recursão em grafos profundos) e a técnica de tempos de descoberta e
  menor tempo alcançável. Devolve pares não direcionados na convenção `u < v`.

### `analisador.py`

- **`AnalisadorRede`**: fachada que recebe o grafo uma vez e oferece o relatório
  completo.
  - `__init__(grafo)`: guarda o grafo e prepara o cache de comunidades.
  - `_comunidades()`: executa o Louvain uma única vez e reutiliza o resultado,
    pois é a operação mais cara.
  - `relatorio_completo()`: executa todas as métricas e devolve um dicionário
    serializável com densidade, agrupamento, assortatividade, as cinco
    centralidades, a partição em comunidades, a modularidade e os três tipos de
    ponte. É a saída consumida pela aplicação e pela futura camada de backend.

### `__init__.py`

Expõe as funções de métrica de todos os módulos e a classe `AnalisadorRede`.
