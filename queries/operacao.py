# queries/operacao.py
import sqlite3
import json
from config.settings import DB_PATH

def buscar_destaques_operacao(data: str) -> list[dict]:
    """
    Retorna os destaques da operação para uma data específica.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Operação
    cur.execute("""
        SELECT *
        FROM destaques_operacao
        WHERE data = ?
        ORDER BY submercado
    """, (data,))

    rows = cur.fetchall()
    if not rows:
        conn.close()
        return []

    resultados = []

    for row in rows:
        submercado = row["submercado"]

        # Geração
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

    conn.close()
    return resultados
