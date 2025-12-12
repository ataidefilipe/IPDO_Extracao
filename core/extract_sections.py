import re
from utils.logger import log


def extrair_trecho(texto: str, inicio: str, fim: str) -> str:
    """
    Extrai o texto entre marcadores específicos.
    Se não encontrar, retorna string vazia.
    """
    pattern = re.compile(
        rf"{re.escape(inicio)}(.*?){re.escape(fim)}",
        flags=re.DOTALL | re.IGNORECASE
    )
    match = pattern.search(texto)
    return match.group(1).strip() if match else ""


def extrair_operacao(texto: str) -> str:
    """
    Extrai seção 4 - Destaques da Operação até antes de 5 - Gerações
    """
    log("   → Extraindo seção: Destaques da Operação")
    return extrair_trecho(texto, "4 - Destaques da Operação", "5 - Gerações")


def extrair_termica(texto: str) -> str:
    """
    Extrai seção 6 - Destaques da Geração Térmica até antes do 7 - Demandas Máximas
    """
    log("   → Extraindo seção: Destaques da Geração Térmica")
    return extrair_trecho(texto, "6 - Destaques da Geração Térmica", "7 - Demandas Máximas")
