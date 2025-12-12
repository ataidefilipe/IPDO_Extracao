# core/openai_client_v2.py
"""
Cliente OpenAI usando a Responses API (API moderna).
Compatível com:
- JSON-only via prompt
- Retentativas
- Timeout explícito
- Envio opcional de PDF
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import time
from utils.logger import log
from config.settings import OPENAI_MODEL, OPENAI_TIMEOUT

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _extrair_texto_json(response) -> str:
    """
    Extrai texto consolidado da Responses API de forma segura.
    """
    # Forma mais estável e recomendada
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text.strip()

    # Fallback manual (caso API mude)
    textos = []
    for item in response.output:
        if item["type"] == "message":
            for c in item["content"]:
                if c["type"] == "output_text":
                    textos.append(c["text"])

    return "\n".join(textos).strip()


def chamar_gpt_v2(prompt: str, pdf_bytes: bytes = None, max_retries: int = 3) -> dict:
    """
    Chamada ao GPT usando Responses API.
    Retorna dict (JSON parseado).
    """

    for tentativa in range(1, max_retries + 1):

        log(f"   [GPT] Tentativa {tentativa}/{max_retries} usando Responses API...")

        try:
            # -----------------------------
            # Montagem do input
            # -----------------------------
            if pdf_bytes:
                input_payload = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {
                                "type": "input_file",
                                "mime_type": "application/pdf",
                                "data": pdf_bytes
                            }
                        ]
                    }
                ]
            else:
                input_payload = prompt

            # -----------------------------
            # Chamada OpenAI
            # -----------------------------
            response = client.responses.create(
                model=OPENAI_MODEL,
                input=input_payload,
                timeout=OPENAI_TIMEOUT
            )

            texto = _extrair_texto_json(response)

            if not texto:
                raise ValueError("Resposta vazia da OpenAI Responses API.")

            return json.loads(texto)

        except json.JSONDecodeError:
            log("   [ERRO] JSON inválido retornado. Retentando...")
            time.sleep(2)

        except Exception as e:
            log(f"   [ERRO] OpenAI Responses API: {e}")
            time.sleep(2)

    raise RuntimeError("Falha após múltiplas tentativas com Responses API.")
