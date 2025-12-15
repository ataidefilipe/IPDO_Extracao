from queries.common import listar_datas

def test_listar_datas_retorna_lista():
    datas = listar_datas()
    assert isinstance(datas, list)
