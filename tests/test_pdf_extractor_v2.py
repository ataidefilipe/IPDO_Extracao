from core.pdf_extractor_v2 import extrair_texto
from pathlib import Path

def test_extração_pdf_simples():
    pdf = Path("tests/pdfs/exemplo1.pdf")
    texto = extrair_texto(pdf)

    assert isinstance(texto, str)
    assert len(texto) > 10  # texto mínimo
    assert "IPDO" in texto or len(texto) > 50


def test_extração_pdf_multiplas_paginas():
    pdf = Path("tests/pdfs/exemplo2.pdf")
    texto = extrair_texto(pdf)

    assert "\n" in texto  # mais de uma página deve gerar contatos
    assert len(texto.splitlines()) > 5


def test_pdf_corrompido_retornar_erro():
    pdf = Path("tests/pdfs/corrompido.pdf")

    try:
        extrair_texto(pdf)
        assert False, "Era esperado erro ao abrir PDF corrompido"
    except RuntimeError:
        assert True
