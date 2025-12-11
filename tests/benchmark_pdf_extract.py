from core.pdf_extractor_v2 import extrair_texto
from time import time
from pathlib import Path

def test_benchmark_extraction_speed():
    pdf = Path("tests/pdfs/exemplo1.pdf")
    t0 = time()
    extrair_texto(pdf)
    t1 = time()

    assert (t1 - t0) < 1.5  # tempo aceitável para PDFs típicos do IPDO
