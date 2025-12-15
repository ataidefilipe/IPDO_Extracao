from queries.termica import buscar_termica_por_desvio

def test_buscar_termica_sem_limite():
    resultado = buscar_termica_por_desvio("1900-01-01")
    assert isinstance(resultado, list)
