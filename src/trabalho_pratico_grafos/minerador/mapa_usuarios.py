class MapaUsuarios:
    # Os grafos usam int então precisamos de uma forma de mapear cada usuário para um número
    # Com a lista e dicionário abaixo, os usuários são guardados e seu respectivo id é facilmente
    # recuperável.

    def __init__(self) -> None:
        self.__usuarios: dict[str, int] = {} # guarda keyvalue pairs "nome do usuario": id
        self.__ids: list[str] = [] # mapeia os ids pra um usuario

    def buscarOuRegistrar(self, username: str) -> int: # Caso usuário não esteja registrado, registra e retorna o id
        # podemos fazer a adição apenas alocando o próximo id por que não teremos remoção do usuário
        # dessa forma não tem problema ser incremental
        if username not in self.__usuarios: # usuário ainda não tá na lista
            novoId = len(self.__ids)
            self.__usuarios[username] = novoId
            self.__ids.append(username)
        return self.__usuarios[username]

    def buscarNome(self, id: int) -> str:
        return self.__ids[id]

    def quantidadeDeUsuarios(self) -> int:
        return len(self.__ids)

    def listarUsuarios(self) -> None:
        for u in self.__ids:
            print(u)
