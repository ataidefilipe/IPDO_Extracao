# queries/termica.py
import sqlite3
from config.settings import DB_PATH

def buscar_termica_por_desvio(
    data: str,
    limite: int | None = None
) -> list[dict]:
    """
    Retorna destaques térmicos ordenados por desvio (desc).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql = """
        SELECT unidade_geradora, desvio, descricao
        FROM destaques_geracao_termica
        WHERE data = ?
        ORDER BY desvio DESC
    """
    params = [data]

    if limite:
        sql += " LIMIT ?"
        params.append(limite)

    cur.execute(sql, params)

    resultados = [
        {
            "unidade_geradora": row["unidade_geradora"],
            "desvio": row["desvio"],
            "descricao": row["descricao"]
        }
        for row in cur.fetchall()
    ]

    conn.close()
    return resultados
