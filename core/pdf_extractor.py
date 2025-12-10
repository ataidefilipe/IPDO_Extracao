from pathlib import Path
import PyPDF2

def extrair_texto(pdf_path: Path) -> str:
    texto = []
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                texto.append(t)
    return "\n".join(texto)