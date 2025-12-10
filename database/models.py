# database/models.py
import sqlite3
from config.settings import DB_PATH
from utils.logger import log

def criar_tabelas():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Apaga as tabelas antigas para recriar do zero limpo
    cur.execute("DROP TABLE IF EXISTS destaques_operacao")
    cur.execute("DROP TABLE IF EXISTS destaques_geracao")
    cur.execute("DROP TABLE IF EXISTS destaques_geracao_termica")

    # Tabela normalizada para todos os tipos de geração
    cur.execute('''
        CREATE TABLE destaques_geracao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            submercado TEXT NOT NULL,
            tipo_geracao TEXT NOT NULL,
            status TEXT,
            descricao TEXT,
            UNIQUE(data, submercado, tipo_geracao)
        )
    ''')

    # Tabela só com carga, restrições e intercâmbio
    cur.execute('''
        CREATE TABLE destaques_operacao (
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
    ''')

    # Térmica continua igual
    cur.execute('''
        CREATE TABLE destaques_geracao_termica (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            unidade_geradora TEXT NOT NULL,
            desvio TEXT NOT NULL,
            descricao TEXT NOT NULL,
            UNIQUE(data, unidade_geradora, descricao)
        )
    ''')

    conn.commit()
    conn.close()
    log("Banco recriado com sucesso – modelo normalizado e escalável")