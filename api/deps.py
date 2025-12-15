# api/deps.py
import sqlite3
from config.settings import DB_PATH

def get_db():
    """
    Dependency FastAPI para obter conexão SQLite.
    Read-only neste MVP.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
