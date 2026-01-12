# database/migrate_termica_v2.py
import sqlite3
from config.settings import DB_PATH
from utils.logger import log


TABLE = "destaques_geracao_termica"


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    )
    return cur.fetchone() is not None


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cur.fetchall()]


def migrate():
    conn = sqlite3.connect(DB_PATH)
    try:
        if not _table_exists(conn, TABLE):
            log(f"[MIGRATION] Tabela '{TABLE}' não existe. Nada para migrar.")
            return

        cols = _columns(conn, TABLE)

        # Já está no novo padrão?
        if "desvio_mw" in cols and "desvio_status" in cols and "desvio" not in cols:
            log("[MIGRATION] Migração já aplicada (schema novo detectado).")
            return

        # Não é o schema antigo esperado?
        if "desvio" not in cols:
            log(
                "[MIGRATION] Schema inesperado: não existe coluna 'desvio'. "
                "Abortando para não corromper dados."
            )
            return

        log("[MIGRATION] Iniciando migração para termica v2 (desvio_mw/desvio_status)...")

        conn.execute("BEGIN")

        # Renomeia tabela antiga
        conn.execute(f"ALTER TABLE {TABLE} RENAME TO {TABLE}_old")

        # Cria nova tabela
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                unidade_geradora TEXT NOT NULL,
                desvio_mw REAL NULL,
                desvio_status TEXT NOT NULL,
                descricao TEXT NOT NULL,
                UNIQUE(data, unidade_geradora, descricao)
            )
            """
        )

        # Copia dados antigos (desvio_mw vira NULL; desvio_status é mapeado por texto)
        conn.execute(
            f"""
            INSERT OR IGNORE INTO {TABLE}
                (data, unidade_geradora, desvio_mw, desvio_status, descricao)
            SELECT
                data,
                unidade_geradora,
                NULL AS desvio_mw,
                CASE
                    WHEN lower(desvio) LIKE '%acima%' THEN 'Acima'
                    WHEN lower(desvio) LIKE '%abaixo%' THEN 'Abaixo'
                    ELSE 'Sem desvio'
                END AS desvio_status,
                descricao
            FROM {TABLE}_old
            """
        )

        # Remove tabela antiga
        conn.execute(f"DROP TABLE {TABLE}_old")

        conn.commit()
        log("[MIGRATION] Migração concluída com sucesso.")

    except Exception as e:
        conn.rollback()
        log(f"[MIGRATION][ERRO] Falha na migração: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
    