from queries.operacao import buscar_destaques_operacao

def test_buscar_operacao_data_inexistente():
    resultado = buscar_destaques_operacao("1900-01-01")
    assert resultado == []
