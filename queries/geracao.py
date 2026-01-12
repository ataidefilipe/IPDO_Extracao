# queries/geracao.py
import sqlite3
from config.settings import DB_PATH


def buscar_geracao(
    data: str,
    submercado: str | None = None,
    tipo: str | None = None
) -> list[dict]:
    """
    Consulta geração para uma data específica, com filtros opcionais.

    Args:
        data (str): Data no formato YYYY-MM-DD
        submercado (str | None): SE, S, NE, N (opcional)
        tipo (str | None): Hidráulica, Térmica, Eólica, Solar, Nuclear (opcional)

    Returns:
        list[dict]: Cada item inclui:
            - submercado
            - tipo
            - status
            - descricao

        Retorna lista vazia se nenhum registro corresponder.
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        # -------------------------
        # 1. SQL com filtros opcionais
        # -------------------------
        sql = """
            SELECT data, submercado, tipo_geracao, status, descricao
            FROM destaques_geracao
            WHERE data = ?
        """
        params = [data]

        if submercado:
            sql += " AND submercado = ?"
            params.append(submercado)

        if tipo:
            sql += " AND tipo_geracao = ?"
            params.append(tipo)

        sql += " ORDER BY submercado, tipo_geracao"

        # -------------------------
        # 2. Execução e mapeamento
        # -------------------------
        cur.execute(sql, params)

        resultados = [
            {
                "submercado": row["submercado"],
                "tipo": row["tipo_geracao"],
                "status": row["status"],
                "descricao": row["descricao"]
            }
            for row in cur.fetchall()
        ]

        return resultados

    finally:
        conn.close()
