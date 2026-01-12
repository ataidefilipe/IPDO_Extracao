# queries/termica.py
import sqlite3
from config.settings import DB_PATH


def buscar_termica_por_desvio(
    data: str,
    limite: int | None = None,
    desvio_status: str | None = None,
) -> list[dict]:
    """
    Retorna destaques térmicos para uma data específica, ordenados por:
      - desvio_mw DESC (NULL por último)

    Args:
        data (str): YYYY-MM-DD
        limite (int | None): máximo de itens
        desvio_status (str | None): 'Acima' | 'Abaixo' | 'Sem desvio' (opcional)

    Returns:
        list[dict]: unidade_geradora, desvio_mw, desvio_status, descricao
    """

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        sql = """
            SELECT unidade_geradora, desvio_mw, desvio_status, descricao
            FROM destaques_geracao_termica
            WHERE data = ?
        """
        params = [data]

        if desvio_status:
            sql += " AND desvio_status = ?"
            params.append(desvio_status)

        # NULLS LAST em SQLite:
        # (desvio_mw IS NULL) => 0 para número, 1 para NULL. Ordena NULL por último.
        sql += """
            ORDER BY (desvio_mw IS NULL) ASC, desvio_mw DESC
        """

        if limite is not None:
            sql += " LIMIT ?"
            params.append(limite)

        cur.execute(sql, params)

        return [
            {
                "unidade_geradora": row["unidade_geradora"],
                "desvio_mw": row["desvio_mw"],
                "desvio_status": row["desvio_status"],
                "descricao": row["descricao"],
            }
            for row in cur.fetchall()
        ]

    finally:
        conn.close()
