# core/pdf_extractor_v2.py
"""
Módulo de extração de texto usando pypdfium2.
Mais robusto que PyPDF2 e ideal para relatórios estruturados (como o IPDO).
"""

from pathlib import Path
import pypdfium2 as pdfium
import re
from utils.logger import log


def _clean_text(text: str) -> str:
    """Normaliza texto extraído para reduzir ruído que atrapalha o GPT."""

    # Remove caracteres invisíveis
    text = text.replace("\u200b", "").replace("\ufeff", "")

    # Substitui múltiplos espaços
    text = re.sub(r"[ ]{2,}", " ", text)

    # Remove quebras múltiplas
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove espaços antes de quebras de linha
    text = re.sub(r"[ ]+\n", "\n", text)

    return text.strip()


def extrair_texto(pdf_path: Path) -> str:
    """
    Extrai texto de todas as páginas do PDF usando pypdfium2.
    
    Requisitos atendidos:
    - Extrai todas as páginas
    - Fallback por página caso falhe
    - Limpeza do texto
    """

    log(f"   Iniciando extração pypdfium2 → {pdf_path.name}")

    try:
        pdf = pdfium.PdfDocument(str(pdf_path))
    except Exception as e:
        raise RuntimeError(f"Falha ao abrir PDF '{pdf_path}': {e}")

    paginas = pdf.get_page_count()
    texto_final = []

    for num in range(paginas):
        try:
            page = pdf.get_page(num)
            texto = page.get_textpage().get_text_range()
            texto_final.append(texto)
        except Exception as e:
            log(f"   [WARN] Falha ao extrair página {num+1}/{paginas}: {e}")
            texto_final.append(f"\n[Página {num+1} não pôde ser extraída]\n")

    texto = "\n".join(texto_final)
    texto = _clean_text(texto)

    log(f"   Extração concluída ({paginas} páginas)")

    return texto
