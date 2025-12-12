# database/models.py
import sqlite3
from config.settings import DB_PATH
from utils.logger import log


def reset_db():
    """
    APAGA COMPLETAMENTE o banco de dados.
    Use APENAS de forma manual.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS destaques_operacao")
    cur.execute("DROP TABLE IF EXISTS destaques_geracao")
    cur.execute("DROP TABLE IF EXISTS destaques_geracao_termica")

    conn.commit()
    conn.close()

    log("⚠️ Banco RESETADO manualmente")
