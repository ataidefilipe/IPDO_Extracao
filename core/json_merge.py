# core/json_merge.py

def merge_respostas(parciais: list, tipo: str) -> dict:
    """
    Junta respostas parciais do GPT em um único JSON final.
    Exemplo:
      - tipo == "operacao" → une listas dentro de "destaques_operacao"
      - tipo == "termica"  → une listas dentro de "destaques_geracao_termica"
    """

    if not parciais:
        raise ValueError("Lista de respostas parciais está vazia")

    final = parciais[0].copy()  # copia campos base (ex: metadata futura)
    
    if tipo == "operacao":
        final["destaques_operacao"] = []
        for p in parciais:
            final["destaques_operacao"] += p.get("destaques_operacao", [])

    elif tipo == "termica":
        final["destaques_geracao_termica"] = []
        for p in parciais:
            final["destaques_geracao_termica"] += p.get("destaques_geracao_termica", [])

    return final
