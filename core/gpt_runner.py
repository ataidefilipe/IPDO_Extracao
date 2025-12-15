# core/gpt_runner.py
"""
Camada de orquestração entre prompts, PDFs e OpenAI Responses API.
"""

from core.openai_client_v2 import chamar_gpt_v2
from utils.logger import log


def processar_trecho_com_gpt(trecho: str, prompt_base: str) -> dict:
    """
    Fluxo para trechos textuais (operação e térmica).
    """
    prompt = prompt_base.replace("{{TEXTO_EXTRAIDO}}", trecho)
    print("prompt:\n\n", prompt)
    return chamar_gpt_v2(prompt)


def processar_pdf_com_prompt(pdf_bytes: bytes, prompt: str) -> dict:
    """
    Fluxo para PDFs completos (caso futuro de migração total).
    """
    log("   Enviando PDF completo como input multimodal...")
    return chamar_gpt_v2(prompt, pdf_bytes=pdf_bytes)
