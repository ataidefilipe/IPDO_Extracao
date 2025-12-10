import re
from datetime import datetime

def extrair_data_do_nome(nome_arquivo: str) -> str:
    match = re.search(r"(\d{4})[._-]?(\d{1,2})[._-]?(\d{1,2})", nome_arquivo)
    if not match:
        raise ValueError(f"Data não encontrada no nome: {nome_arquivo}")
    ano, mes, dia = match.groups()
    return f"{ano}-{int(mes):02d}-{int(dia):02d}"