# core/pdf_extractor_v2.py
"""
Módulo de extração de texto usando pypdfium2 (compatível com todas as versões atuais).
"""

from pathlib import Path
import pypdfium2 as pdfium
import re
from utils.logger import log


def _clean_text(text: str) -> str:
    """Normaliza texto extraído para reduzir ruído que atrapalha o GPT."""
    text = text.replace("\u200b", "").replace("\ufeff", "")
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ ]+\n", "\n", text)
    return text.strip()


def extrair_texto(pdf_path: Path) -> str:
    """
    Extrai texto de todas as páginas do PDF usando pypdfium2.
    Compatível com versões antigas e recentes da biblioteca.
    """

    log(f"   Iniciando extração pypdfium2 → {pdf_path.name}")

    try:
        pdf = pdfium.PdfDocument(str(pdf_path))
    except Exception as e:
        raise RuntimeError(f"Falha ao abrir PDF '{pdf_path}': {e}")

    paginas = len(pdf)  # ← número de páginas correto nessa versão
    texto_final = []

    for page_number in range(paginas):
        try:
            page = pdf[page_number]  # ← forma correta de acessar página
            textpage = page.get_textpage()
            texto = textpage.get_text_range()
            texto_final.append(texto)
        except Exception as e:
            log(f"   [WARN] Falha ao extrair página {page_number+1}/{paginas}: {e}")
            texto_final.append(f"\n[Página {page_number+1} não pôde ser extraída]\n")

    texto = "\n".join(texto_final)
    texto = _clean_text(texto)

    log(f"   Extração concluída ({paginas} páginas)")
    return texto
