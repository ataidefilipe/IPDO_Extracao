# agent/tools.py
from queries.common import listar_datas
from queries.operacao import buscar_destaques_operacao
from queries.termica import buscar_termica_por_desvio

def tool_listar_datas():
    return listar_datas()

def tool_buscar_operacao(data: str):
    return buscar_destaques_operacao(data)

def tool_buscar_termica(data: str, limite: int | None = None):
    return buscar_termica_por_desvio(data, limite)
