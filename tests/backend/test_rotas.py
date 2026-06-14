"""Testes das rotas via TestClient (httpx) — cobre o contrato HTTP do MVP."""


def test_health(client):
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_listar_repositorios(client):
    resposta = client.get("/api/repositorios")
    assert resposta.status_code == 200
    repos = resposta.json()
    assert len(repos) == 1
    assert repos[0]["nome"] == "octo/demo"
    assert repos[0]["estado"] == "disponivel"
    assert repos[0]["quantidade_usuarios"] == 5
    assert repos[0]["quantidade_interacoes"] == 9


def test_resumo_repositorio_disponivel(client):
    resposta = client.get("/api/repositorios/octo/demo")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["estado"] == "disponivel"
    assert corpo["quantidade_usuarios"] == 5


def test_resumo_repositorio_ausente_responde_200_com_estado(client):
    # O resumo é a rota que reporta o estado; AUSENTE não vira 404 aqui.
    resposta = client.get("/api/repositorios/fantasma/repo")
    assert resposta.status_code == 200
    assert resposta.json()["estado"] == "ausente"


def test_resumo_dos_grafos(client):
    resposta = client.get("/api/repositorios/octo/demo/grafos")
    assert resposta.status_code == 200
    grafos = {g["tipo"]: g for g in resposta.json()}
    assert set(grafos) == {"integrado", "comentarios", "fechamento", "prs"}
    assert grafos["integrado"]["vertices"] == 5
    assert grafos["integrado"]["arestas"] == 9
    assert isinstance(grafos["integrado"]["densidade"], float)  # parte A entregue


def test_detalhe_grafo_tipo_invalido_422(client):
    resposta = client.get("/api/repositorios/octo/demo/grafos/inexistente")
    assert resposta.status_code == 422
    assert "tipos_validos" in resposta.json()


def test_grafo_de_repo_ausente_404(client):
    resposta = client.get("/api/repositorios/fantasma/repo/grafos/integrado")
    assert resposta.status_code == 404


def test_download_gephi(client):
    resposta = client.get("/api/repositorios/octo/demo/grafos/integrado/gephi")
    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("text/csv")
    assert resposta.text.splitlines()[0] == "Source,Target,Weight,Type"


def test_analise_completa(client):
    resposta = client.get("/api/repositorios/octo/demo/analise")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert set(corpo["centralidades"]) == {
        "grau_entrada",
        "grau_saida",
        "autovetor",
        "pagerank",
        "proximidade",
        "intermediacao",
    }
    assert isinstance(corpo["densidade"], float)
    assert corpo["modularidade"] is not None
    assert corpo["comunidades"]


def test_analise_subrecursos(client):
    base = "/api/repositorios/octo/demo/analise"

    cent = client.get(f"{base}/centralidades")
    assert cent.status_code == 200
    assert "pagerank" in cent.json()["centralidades"]

    com = client.get(f"{base}/comunidades")
    assert com.status_code == 200
    assert com.json()["modularidade"] is not None

    pontes = client.get(f"{base}/pontes")
    assert pontes.status_code == 200
    assert set(pontes.json()) == {"locais", "classicas", "intercomunidade"}

    coesao = client.get(f"{base}/coesao")
    assert coesao.status_code == 200
    corpo_coesao = coesao.json()
    assert set(corpo_coesao) == {"densidade", "clustering", "assortatividade"}
    assert all(isinstance(valor, float) for valor in corpo_coesao.values())


def test_ranking_top_n_ordenado(client):
    resposta = client.get("/api/repositorios/octo/demo/analise/ranking/pagerank?top=3")
    assert resposta.status_code == 200
    ranking = resposta.json()
    assert len(ranking) == 3
    valores = [item["valor"] for item in ranking]
    assert valores == sorted(valores, reverse=True)


def test_ranking_metrica_invalida_404(client):
    resposta = client.get("/api/repositorios/octo/demo/analise/ranking/inexistente")
    assert resposta.status_code == 404
    assert "metricas_validas" in resposta.json()


def test_mineracao_sem_token_indisponivel_e_status_404(client):
    # O `client` padrão usa o gerenciador real SEM GITHUB_TOKENS configurado:
    # o disparo de mineração responde 503 (implementada, porém indisponível).
    assert client.post("/api/repositorios/octo/demo/minerar").status_code == 503
    assert client.post("/api/repositorios/octo/demo/atualizar").status_code == 503
    # status de um job inexistente -> 404
    assert client.get("/api/repositorios/octo/demo/minerar/status?job_id=abc").status_code == 404
