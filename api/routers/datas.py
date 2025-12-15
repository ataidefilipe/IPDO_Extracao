# api/routers/datas.py
from fastapi import APIRouter, Depends
import sqlite3
from api.deps import get_db

router = APIRouter(
    prefix="/datas",
    tags=["Datas"]
)

@router.get("")
def listar_datas(db: sqlite3.Connection = Depends(get_db)):
    """
    Retorna todas as datas disponíveis no banco de dados.

    As datas são retornadas em ordem decrescente (mais recente primeiro).
    """

    cursor = db.cursor()

    cursor.execute("""
        SELECT DISTINCT data
        FROM destaques_operacao
        ORDER BY data DESC
    """)

    datas = [row["data"] for row in cursor.fetchall()]

    return {"datas": datas}
