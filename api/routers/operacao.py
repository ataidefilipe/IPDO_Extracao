# api/routers/operacao.py
from fastapi import APIRouter, Depends, HTTPException
import sqlite3
import json
from api.deps import get_db

router = APIRouter(
    prefix="/operacao",
    tags=["Operação"]
)

@router.get("/{data}")
def obter_destaques_operacao(
    data: str,
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Retorna os destaques da operação por data.
    """

    cur = db.cursor()

    # -------------------------
    # 1. Buscar operação
    # -------------------------
    cur.execute("""
        SELECT *
        FROM destaques_operacao
        WHERE data = ?
        ORDER BY submercado
    """, (data,))

    rows = cur.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum destaque de operação encontrado para {data}"
        )

    # -------------------------
    # 2. Montar resposta
    # -------------------------
    destaques = []

    for row in rows:
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

        destaques.append({
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

    return {
        "data": data,
        "destaques_operacao": destaques
    }
