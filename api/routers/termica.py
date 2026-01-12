# api/routers/termica.py
from fastapi import APIRouter, Depends, HTTPException
import sqlite3
from api.deps import get_db

router = APIRouter(
    prefix="/termica",
    tags=["Geração Térmica"]
)

@router.get("/{data}")
def obter_destaques_termica(
    data: str,
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Retorna os destaques de geração térmica por data (v2).
    """

    cur = db.cursor()

    # Verifica se existe qualquer dado no dia (operação OU térmica)
    cur.execute("SELECT 1 FROM destaques_operacao WHERE data = ? LIMIT 1", (data,))
    existe_oper = cur.fetchone()

    cur.execute("SELECT 1 FROM destaques_geracao_termica WHERE data = ? LIMIT 1", (data,))
    existe_term = cur.fetchone()

    if not existe_oper and not existe_term:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum dado encontrado para a data {data}"
        )

    cur.execute("""
        SELECT unidade_geradora, desvio_mw, desvio_status, descricao
        FROM destaques_geracao_termica
        WHERE data = ?
        ORDER BY (desvio_mw IS NULL) ASC, desvio_mw DESC
    """, (data,))

    rows = cur.fetchall()

    destaques = [
        {
            "unidade_geradora": row["unidade_geradora"],
            "desvio_mw": row["desvio_mw"],
            "desvio_status": row["desvio_status"],
            "descricao": row["descricao"]
        }
        for row in rows
    ]

    return {
        "data": data,
        "destaques_geracao_termica": destaques
    }
