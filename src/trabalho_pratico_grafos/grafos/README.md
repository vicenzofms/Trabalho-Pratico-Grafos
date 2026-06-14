# Pacote `grafos`

Fornece a estrutura de dados central do projeto: um grafo simples e direcionado,
com pesos e rótulos de vértices, implementado do zero (sem bibliotecas prontas de
grafos). É consumido pelas camadas `analise` e `gephi`, que dependem apenas da
abstração e não de uma implementação concreta.

## Como funciona

O pacote usa herança e abstração. Uma classe abstrata define toda a API comum e
concentra a lógica de alto nível, enquanto duas classes concretas implementam
apenas o armazenamento físico das arestas, uma com matriz de adjacência e outra
com listas de adjacência.

O ponto central é o padrão Template Method. Operações como `adicionarAresta` e
`removeAresta` ficam na classe abstrata e garantem as regras invariantes do grafo
(proibição de laços, idempotência, atualização dos graus, validação de índices).
A manipulação concreta da aresta é delegada a métodos abstratos
(`_inserirAresta`, `_deletarAresta`, `existeAresta`, entre outros), que cada
implementação preenche do seu jeito. Assim, as duas representações compartilham o
mesmo comportamento observável e podem ser trocadas sem afetar quem usa o grafo.

O grafo é direcionado, então cada aresta tem um sentido. Relações bidirecionais
são representadas por duas arestas anti-paralelas. Os vértices são identificados
por índices inteiros de `0` a `n-1`, e operações com índices fora desse intervalo
levantam exceção.

## Arquivos

### `grafo_abstrato.py`

Define a classe **`GrafoAbstrato`**, que estabelece a API e a lógica
compartilhada.

Atributos principais: quantidade de vértices e arestas, rótulos dos vértices,
graus de entrada e saída, e pesos dos vértices, todos inicializados no
construtor.

Métodos de manipulação (Template Method):

- `adicionarAresta(u, v, peso)`: adiciona a aresta após validar. É idempotente
  (adicionar a mesma aresta duas vezes não duplica nem altera os graus) e exige
  peso positivo. Atualiza graus e a contagem de arestas.
- `removeAresta(u, v)`: remove a aresta se ela existir, atualizando graus e
  contagem. Também é idempotente.

Métodos de consulta de propriedades globais:

- `isVazio()`: indica se o grafo não possui arestas.
- `isConexo()`: verifica se o grafo é fracamente conexo, fazendo uma busca em
  largura sobre o grafo subjacente.
- `isCompleto()`: verifica se o número de arestas é o máximo possível para um
  grafo direcionado simples.

Métodos de relação entre arestas e vértices, que exigem que as arestas
informadas existam:

- `isIncidente(u, v, x)`: indica se o vértice `x` é uma das pontas da aresta
  `u -> v`.
- `isConvergente(u1, v1, u2, v2)`: indica se duas arestas distintas chegam no
  mesmo vértice.
- `isDivergente(u1, v1, u2, v2)`: indica se duas arestas distintas saem do mesmo
  vértice.

Métodos auxiliares de validação, usados internamente para garantir consistência:

- `_validarAresta(u, v)`: garante que os vértices existem e que não é um laço.
- `_validarIndices(*args)`: garante que cada índice está dentro dos limites.
- `_exigirAresta(u, v)`: garante que a aresta já existe, levantando exceção caso
  contrário.

Getters e setters, que validam os índices antes de operar:

- `setPesoVertice(u, peso)` e `getPesoVertice(u)`: peso de um vértice.
- `setRotuloVertice(u, rotulo)` e `getRotuloVertice(u)`: rótulo (o username) de
  um vértice.
- `getGrauEntrada(u)` e `getGrauSaida(u)`: graus de entrada e saída.
- `getQuantidadeVertices()` e `getQuantidadeArestas()`: cardinalidades.

Métodos abstratos, implementados pelas subclasses: `setPesoAresta`,
`getPesoAresta`, `isSucessor`, `isPredecessor`, `getPredecessores`,
`getSucessores`, `_inserirAresta`, `_deletarAresta` e `existeAresta`.

### `grafo_matriz.py`

Define **`GrafoMatrizAdjacencia`**, que implementa a API usando uma matriz de
adjacência. A célula `matriz[u][v]` guarda o peso da aresta `u -> v`, e o valor
`0.0` significa ausência de aresta. As linhas usam `array('d')` por eficiência de
memória.

- `setPesoAresta(u, v, peso)`: atualiza o peso de uma aresta existente, exigindo
  peso positivo.
- `getPesoAresta(u, v)`: devolve o peso, ou `0.0` no caso de ausência de aresta.
- `existeAresta(u, v)`: verifica se a célula é diferente de zero.
- `isSucessor(u, v)` e `isPredecessor(u, v)`: consultam linha e coluna para saber
  o sentido da relação.
- `getSucessores(u)` e `getPredecessores(u)`: varrem a linha ou a coluna do
  vértice, custando O(V).
- `_inserirAresta(u, v, peso)` e `_deletarAresta(u, v)`: gravam o peso ou zeram a
  célula. A validação já foi feita no Template Method.

### `grafo_lista.py`

Define **`GrafoListaAdjacencia`**, que implementa a API usando listas de
adjacência. Cada vértice tem um dicionário que mapeia o vértice de destino ao
peso da aresta.

- `setPesoAresta(u, v, peso)`: atualiza o peso de uma aresta existente, exigindo
  peso positivo.
- `getPesoAresta(u, v)`: devolve o peso da aresta, exigindo que ela exista.
- `existeAresta(u, v)`: verifica se o destino está no dicionário da origem.
- `isSucessor(u, v)` e `isPredecessor(u, v)`: usam a existência da aresta no
  sentido correto.
- `getSucessores(u)`: devolve as chaves do dicionário do vértice, custando
  O(grau).
- `getPredecessores(u)`: varre os demais vértices procurando quem aponta para
  `u`.
- `_inserirAresta(u, v, peso)` e `_deletarAresta(u, v)`: inserem ou removem a
  entrada no dicionário.

A diferença prática entre as duas implementações está no custo das operações de
vizinhança. A lista recupera sucessores em tempo proporcional ao grau, enquanto a
matriz sempre varre uma linha ou coluna inteira.

### `__init__.py`

Expõe `GrafoAbstrato`, `GrafoMatrizAdjacencia` e `GrafoListaAdjacencia`.
