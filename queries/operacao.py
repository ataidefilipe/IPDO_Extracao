# queries/operacao.py
import sqlite3
import json
from config.settings import DB_PATH


def buscar_destaques_operacao(data: str) -> list[dict]:
    """
    Retorna os destaques da operação para uma data específica.

    Args:
        data (str): Data no formato YYYY-MM-DD.

    Returns:
        list[dict]: Lista de destaques por submercado, contendo:
            - submercado (str) — SEMPRE presente
            - carga: {status, descricao}
            - restricoes (list[str])
            - transferencia_energia: {submercado_origem, submercado_destino, status, descricao}
            - geracao (list[dict]) — tipo, status, descricao

        Retorna uma lista vazia caso não exista nenhum dado para a data.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        # -------------------------
        # 1. Buscar destaques operacionais do dia
        # -------------------------
        cur.execute("""
            SELECT *
            FROM destaques_operacao
            WHERE data = ?
            ORDER BY submercado
        """, (data,))

        oper_rows = cur.fetchall()

        # Sem operação naquele dia → lista vazia
        if not oper_rows:
            return []

        resultados = []

        # -------------------------
        # 2. Iterar por submercado e buscar geração associada
        # -------------------------
        for row in oper_rows:
            submercado = row["submercado"]

            # Buscar geração por submercado
            cur.execute("""
                SELECT tipo_geracao, status, descricao
                FROM destaques_geracao
                WHERE data = ? AND submercado = ?
                ORDER BY tipo_geracao
            """, (data, submercado))

            geracoes = [
                {
                    "tipo": g["tipo_geracao"],
                    "status": g["status"],
                    "descricao": g["descricao"]
                }
                for g in cur.fetchall()
            ]

            # Garantia de consistência de campos
            resultados.append({
                "submercado": submercado,
                "carga": {
                    "status": row["carga_status"],
                    "descricao": row["carga_descricao"]
                },
                "restricoes": json.loads(row["restricoes"]) if row["restricoes"] else [],
                "transferencia_energia": {
                    "submercado_origem": row["transferencia_origem"],
                    "submercado_destino": row["transferencia_destino"],
                    "status": row["transferencia_status"],
                    "descricao": row["transferencia_descricao"]
                },
                "geracao": geracoes
            })

        return resultados

    finally:
        conn.close()



def buscar_destaques_operacao(data: str) -> list[dict]:
    """
    Retorna os destaques da operação para uma data específica.

    Args:
        data (str): Data no formato YYYY-MM-DD.

    Returns:
        list[dict]: Lista de destaques por submercado, contendo:
            - submercado (str) — SEMPRE presente
            - carga: {status, descricao}
            - restricoes (list[str])
            - transferencia_energia: {submercado_origem, submercado_destino, status, descricao}
            - geracao (list[dict]) — tipo, status, descricao

        Retorna uma lista vazia caso não exista nenhum dado para a data.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT *
            FROM destaques_operacao
            WHERE data = ?
            ORDER BY submercado
        """, (data,))

        oper_rows = cur.fetchall()

        if not oper_rows:
            return []

        resultados = []

        for row in oper_rows:
            submercado = row["submercado"]

            cur.execute("""
                SELECT tipo_geracao, status, descricao
                FROM destaques_geracao
                WHERE data = ? AND submercado = ?
                ORDER BY
                  CASE tipo_geracao
                    WHEN 'Hidráulica' THEN 1
                    WHEN 'Térmica' THEN 2
                    WHEN 'Eólica' THEN 3
                    WHEN 'Solar' THEN 4
                    WHEN 'Nuclear' THEN 5
                    ELSE 99
                  END,
                  tipo_geracao
            """, (data, submercado))

            geracoes = [
                {
                    "tipo": g["tipo_geracao"],
                    "status": g["status"],
                    "descricao": g["descricao"]
                }
                for g in cur.fetchall()
            ]

            resultados.append({
                "submercado": submercado,
                "carga": {
                    "status": row["carga_status"],
                    "descricao": row["carga_descricao"]
                },
                "restricoes": json.loads(row["restricoes"]) if row["restricoes"] else [],
                "transferencia_energia": {
                    "submercado_origem": row["transferencia_origem"],
                    "submercado_destino": row["transferencia_destino"],
                    "status": row["transferencia_status"],
                    "descricao": row["transferencia_descricao"]
                },
                "geracao": geracoes
            })

        return resultados

    finally:
        conn.close()


def buscar_operacao_resumo(
    data: str,
    submercado: str | None = None,
    limite_itens: int | None = None,
) -> list[dict]:
    """
    Retorna um resumo compacto da operação por submercado, para reduzir ruído/volume.

    Para cada submercado:
      - carga_status
      - transferencia_status (+ origem/destino, se existirem)
      - restricoes_qtd + restricoes_amostra (limitada)
      - geracao: lista curta com tipo + status (limitada)

    Args:
        data: YYYY-MM-DD
        submercado: filtro opcional (contém, case-insensitive)
        limite_itens: limita tamanho de listas (restricoes_amostra e geracao).
            Se None: restricoes_amostra = até 3, geracao = até 5 (padrão)

    Returns:
        list[dict]: lista por submercado (ou vazia se não existir).
    """
    def _norm_str(v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        return s or None

    def _norm_int(v: int | None) -> int | None:
        if v is None:
            return None
        try:
            return int(v)
        except Exception:
            return None

    submercado = _norm_str(submercado)
    limite_itens = _norm_int(limite_itens)

    # defaults compactos
    restr_lim = 3 if limite_itens is None else max(0, limite_itens)
    ger_lim = 5 if limite_itens is None else max(0, limite_itens)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT *
            FROM destaques_operacao
            WHERE data = ?
            ORDER BY submercado
        """, (data,))
        rows = cur.fetchall()

        if not rows:
            return []

        out: list[dict] = []

        for row in rows:
            sm = row["submercado"] or ""

            if submercado:
                if submercado.lower() not in sm.lower():
                    continue

            restricoes = json.loads(row["restricoes"]) if row["restricoes"] else []
            if not isinstance(restricoes, list):
                restricoes = []

            cur.execute("""
                SELECT tipo_geracao, status
                FROM destaques_geracao
                WHERE data = ? AND submercado = ?
                ORDER BY
                  CASE tipo_geracao
                    WHEN 'Hidráulica' THEN 1
                    WHEN 'Térmica' THEN 2
                    WHEN 'Eólica' THEN 3
                    WHEN 'Solar' THEN 4
                    WHEN 'Nuclear' THEN 5
                    ELSE 99
                  END,
                  tipo_geracao
            """, (data, sm))

            geracoes = [
                {"tipo": g["tipo_geracao"], "status": g["status"]}
                for g in cur.fetchall()
            ]

            if ger_lim is not None:
                geracoes = geracoes[:ger_lim]

            amostra = restricoes[:restr_lim] if restr_lim is not None else restricoes

            out.append({
                "submercado": sm,
                "carga_status": row["carga_status"],
                "transferencia_status": row["transferencia_status"],
                "transferencia_origem": row["transferencia_origem"],
                "transferencia_destino": row["transferencia_destino"],
                "restricoes_qtd": len(restricoes),
                "restricoes_amostra": amostra,
                "geracao": geracoes,
            })

        return out

    finally:
        conn.close()
