# core/chunking.py
"""
Funções utilitárias para divisão de texto (chunking) com limite de tokens.

O objetivo é impedir que textos extraídos do PDF ultrapassem o limite de 
contexto do modelo GPT, evitando erros 400 e análises incompletas.
"""

import re
from utils.logger import log

# Estimativa média: 1 token ≈ 4 caracteres (para modelos GPT modernos)
TOKEN_RATIO = 4


def estimate_tokens(text: str) -> int:
    """Estima número de tokens baseado no tamanho do texto."""
    return max(1, len(text) // TOKEN_RATIO)


def split_text_by_tokens(text: str, max_tokens: int = 6000) -> list:
    """
    Divide o texto em chunks respeitando limite de tokens aproximado.

    - Nunca quebra no meio de parágrafos
    - Se chunk único exceder max_tokens → quebra em sentenças
    - Retorna lista de chunks prontos para envio ao GPT
    """

    total_tokens = estimate_tokens(text)
    log(f"   Texto possui aproximadamente {total_tokens} tokens")

    if total_tokens <= max_tokens:
        log("   Chunking NÃO necessário → texto cabe em um único prompt")
        return [text]

    log("   Chunking necessário → dividindo o texto...")

    # Primeira divisão por parágrafos
    paragraphs = re.split(r"\n\s*\n", text)
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        candidate = current_chunk + "\n\n" + para if current_chunk else para

        if estimate_tokens(candidate) < max_tokens:
            current_chunk = candidate
        else:
            # Chunk cheio → salva e começa outro
            chunks.append(current_chunk.strip())
            current_chunk = para

    # Último pedaço
    if current_chunk:
        chunks.append(current_chunk.strip())

    # Garantia de que nenhum chunk ultrapassa o máximo
    final_chunks = []
    for c in chunks:
        if estimate_tokens(c) <= max_tokens:
            final_chunks.append(c)
        else:
            # Se um parágrafo gigante excede, quebrar em sentenças
            log("   Parágrafo muito grande → realizando divisão por sentenças...")
            sentences = re.split(r"(?<=[.!?])\s+", c)
            sub_chunk = ""
            for s in sentences:
                candidate = sub_chunk + " " + s if sub_chunk else s
                if estimate_tokens(candidate) < max_tokens:
                    sub_chunk = candidate
                else:
                    final_chunks.append(sub_chunk.strip())
                    sub_chunk = s
            if sub_chunk:
                final_chunks.append(sub_chunk.strip())

    log(f"   Chunking finalizado → {len(final_chunks)} chunk(s) gerados")
    return final_chunks
