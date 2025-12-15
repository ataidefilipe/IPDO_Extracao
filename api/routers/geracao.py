# api/routers/geracao.py
from fastapi import APIRouter, Depends, Query, HTTPException
import sqlite3
from api.deps import get_db

router = APIRouter(
    prefix="/geracao",
    tags=["Geração"]
)

@router.get("")
def consultar_geracao(
    data: str = Query(..., description="Data no formato YYYY-MM-DD"),
    submercado: str | None = Query(None, description="SE, S, NE, N"),
    tipo: str | None = Query(None, description="Hidráulica, Térmica, Eólica, Solar, Nuclear"),
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Consulta geração por data, com filtros opcionais de submercado e tipo.
    """

    cur = db.cursor()

    # -------------------------
    # 1. Montar SQL dinâmico
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
    # 2. Executar consulta
    # -------------------------
    cur.execute(sql, params)
    rows = cur.fetchall()

    # -------------------------
    # 3. Data inválida (nenhum registro no dia)
    # -------------------------
    if not rows:
        # checa se a data existe no banco
        cur.execute(
            "SELECT 1 FROM destaques_geracao WHERE data = ? LIMIT 1",
            (data,)
        )
        existe = cur.fetchone()
        if not existe:
            raise HTTPException(
                status_code=404,
                detail=f"Nenhum dado de geração encontrado para {data}"
            )

    # -------------------------
    # 4. Montar resposta
    # -------------------------
    geracao = [
        {
            "submercado": row["submercado"],
            "tipo": row["tipo_geracao"],
            "status": row["status"],
            "descricao": row["descricao"]
        }
        for row in rows
    ]

    return {
        "data": data,
        "filtros": {
            "submercado": submercado,
            "tipo": tipo
        },
        "geracao": geracao
    }
