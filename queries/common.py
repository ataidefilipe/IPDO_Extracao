# queries/common.py
import sqlite3
from config.settings import DB_PATH

def listar_datas() -> list[str]:
    """
    Retorna todas as datas disponíveis no banco (ordem desc).
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT data
        FROM destaques_operacao
        ORDER BY data DESC
    """)

    datas = [row["data"] for row in cur.fetchall()]
    conn.close()

    return datas
