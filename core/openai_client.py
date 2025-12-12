from openai import OpenAI
from config.settings import OPENAI_MODEL
import json
import time
from utils.logger import log
from dotenv import load_dotenv
import os


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chamar_gpt(prompt: str, max_retries=3) -> dict:

    if not client.api_key:
         raise ValueError("OPENAI_API_KEY não encontrada! Verifique o arquivo .env")

    for tentativa in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Você responde APENAS com JSON válido. Nunca adicione texto fora do JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            conteudo = response.choices[0].message.content.strip()
            return json.loads(conteudo)
        except json.JSONDecodeError:
            if tentativa == max_retries - 1:
                raise
            log("JSON inválido retornado. Tentando novamente...")
            time.sleep(2)
        except Exception as e:
            if tentativa == max_retries - 1:
                raise e
            log(f"Erro na API (tentativa {tentativa+1}): {e}")
            time.sleep(3)
    raise Exception("Falha após várias tentativas")

def chamar_gpt_em_chunks(prompt_template: str, chunks: list) -> list:
    """
    Envia múltiplos prompts ao GPT, um por chunk.
    Cada resposta será tratada como parte do JSON final.
    """
    respostas = []

    for idx, texto in enumerate(chunks, 1):
        log(f"   → Enviando chunk {idx}/{len(chunks)} ao GPT...")

        prompt = prompt_template.replace("{{TEXTO_EXTRAIDO}}", texto)

        resultado = chamar_gpt(prompt)
        respostas.append(resultado)

    return respostas

