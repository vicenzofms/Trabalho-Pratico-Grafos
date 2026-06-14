# Pacote `gephi`

Exporta um grafo para um arquivo que pode ser aberto no GEPHI, o software usado
para visualizar a rede. É a camada final do projeto: recebe um grafo já
construído e analisado e o grava em disco em um dos formatos aceitos pelo GEPHI.
A renderização e a exploração visual do grafo são feitas inteiramente no GEPHI, a
partir do arquivo gerado aqui.

## Como funciona

A exportação foi mantida em um módulo separado, e não como método da classe de
grafo, para preservar a separação de responsabilidades: a classe de grafo cuida
da estrutura e das operações, enquanto a lógica de serialização e escrita em
disco fica isolada neste pacote.

O grafo é gravado como uma lista de arestas em CSV, com uma linha por aresta
existente. Cada linha usa os rótulos dos vértices (os usernames), e não os
índices internos, de modo que o arquivo já vem legível no GEPHI.

## Arquivos

### `gephi.py`

- **`para_gephi(grafo, nome, pasta=None)`**: percorre todas as arestas do grafo e
  grava um arquivo CSV com as colunas `Source`, `Target`, `Weight` e `Type`. A
  origem e o destino são os rótulos dos vértices (ou o índice, caso o vértice não
  tenha rótulo), o peso é o peso da aresta e o tipo é sempre `Directed`, já que o
  grafo é direcionado. Se a pasta de destino não for informada, usa a pasta padrão
  `data/gephi`, criando-a se necessário. Devolve o caminho completo do arquivo
  gerado.

### `__init__.py`

Expõe apenas a função `para_gephi`, que é a interface pública do pacote.
