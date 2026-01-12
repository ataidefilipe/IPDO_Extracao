# queries/common.py
import sqlite3
from config.settings import DB_PATH

def listar_datas() -> list[str]:
    """
    Retorna todas as datas processadas e existentes no banco.

    Returns:
        list[str]: Lista de datas no formato YYYY-MM-DD, ordenadas
                   do mais recente para o mais antigo.
                   Retorna lista vazia se não houver registros.

    Comportamento:
        ✔ Nunca lança erro se o banco estiver vazio
        ✔ Não duplica datas
        ✔ Ordena decrescente no SQL
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT DISTINCT data
            FROM destaques_operacao
            ORDER BY data DESC
        """)
        datas = [row["data"] for row in cur.fetchall()]
    finally:
        conn.close()

    return datas
