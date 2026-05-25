class Minerador:
    url: str
    auth_token: str

    def __init__(self, url: str, token: str) -> None:
        self.url = url
        self.auth_token = token

    def minerarComentariosIssues(self):
        pass

    def minerarComentariosPullRequests(self):
        pass

    def minerarFechamentoIssues(self):
        pass

    def minerarPullRequests(self):
        pass
