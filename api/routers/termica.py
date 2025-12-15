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
    Retorna os destaques de geração térmica por data.
    """

    cur = db.cursor()

    # -------------------------
    # 1. Verificar se a data existe no banco
    # -------------------------
    cur.execute(
        "SELECT 1 FROM destaques_operacao WHERE data = ? LIMIT 1",
        (data,)
    )
    existe_data = cur.fetchone()

    if not existe_data:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum dado encontrado para a data {data}"
        )

    # -------------------------
    # 2. Buscar destaques térmicos
    # -------------------------
    cur.execute("""
        SELECT unidade_geradora, desvio, descricao
        FROM destaques_geracao_termica
        WHERE data = ?
        ORDER BY desvio DESC
    """, (data,))

    rows = cur.fetchall()

    destaques = [
        {
            "unidade_geradora": row["unidade_geradora"],
            "desvio": row["desvio"],
            "descricao": row["descricao"]
        }
        for row in rows
    ]

    return {
        "data": data,
        "destaques_geracao_termica": destaques
    }
