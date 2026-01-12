# database/init_db.py
import sqlite3
from config.settings import DB_PATH
from utils.logger import log


def init_db():
    """
    Inicializa o banco SQLite sem apagar dados existentes.
    Cria tabelas apenas se não existirem.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # -------------------------
    # destaques_geracao
    # -------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS destaques_geracao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            submercado TEXT NOT NULL,
            tipo_geracao TEXT NOT NULL,
            status TEXT,
            descricao TEXT,
            UNIQUE(data, submercado, tipo_geracao)
        )
    """)

    # -------------------------
    # destaques_operacao
    # -------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS destaques_operacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            submercado TEXT NOT NULL,
            carga_status TEXT,
            carga_descricao TEXT,
            restricoes TEXT,
            transferencia_origem TEXT,
            transferencia_destino TEXT,
            transferencia_status TEXT,
            transferencia_descricao TEXT,
            UNIQUE(data, submercado)
        )
    """)

    # -------------------------
    # destaques_geracao_termica
    # -------------------------
    cur.execute("""
        CREATE TABLE IF NOT EXISTS destaques_geracao_termica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            unidade_geradora TEXT NOT NULL,
            desvio_mw REAL NULL,
            desvio_status TEXT NOT NULL,
            descricao TEXT NOT NULL,
            UNIQUE(data, unidade_geradora, descricao)
        )
    """)

    conn.commit()
    conn.close()

    log("Banco inicializado com segurança (sem apagar dados)")
