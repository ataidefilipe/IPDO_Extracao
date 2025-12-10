# database/repository.py
import sqlite3
import json
from config.settings import DB_PATH
from utils.logger import log

def _get_conn():
    return sqlite3.connect(DB_PATH)

def salvar_destaques_operacao(data: str, itens: list):
    if not itens:
        log("   Nenhum destaque de operação para salvar")
        return
    
    conn = _get_conn()
    cur = conn.cursor()
    total_geracoes = 0

    log(f"   Processando {len(itens)} submercado(s)...")

    for idx, item in enumerate(itens, 1):
        submercado = item.get("submercado", "Desconhecido")
        log(f"     [{idx}/{len(itens)}] Submercado: {submercado}")

        try:
            # 1. Salva carga + restrições + intercâmbio
            cur.execute('''
                INSERT OR REPLACE INTO destaques_operacao
                (data, submercado, carga_status, carga_descricao, restricoes,
                 transferencia_origem, transferencia_destino, transferencia_status, transferencia_descricao)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data,
                submercado,
                item.get("carga", {}).get("status"),
                item.get("carga", {}).get("descricao"),
                json.dumps(item.get("restricoes", []), ensure_ascii=False),
                item.get("transferencia_energia", {}).get("submercado_origem"),
                item.get("transferencia_energia", {}).get("submercado_destino"),
                item.get("transferencia_energia", {}).get("status"),
                item.get("transferencia_energia", {}).get("descricao"),
            ))

            # 2. Salva cada tipo de geração
            for ger in item.get("geracao", []):
                tipo = ger["tipo"]
                if tipo == "Solar Fotovoltaica":
                    tipo = "Solar"
                
                cur.execute('''
                    INSERT OR REPLACE INTO destaques_geracao
                    (data, submercado, tipo_geracao, status, descricao)
                    VALUES (?, ?, ?, ?, ?)
                ''', (data, submercado, tipo, ger["status"], ger["descricao"]))
                total_geracoes += 1

        except Exception as e:
            log(f"   ERRO ao salvar submercado {submercado}: {e}")
            raise

    conn.commit()
    conn.close()
    log(f"   SUCESSO → {len(itens)} submercado(s) + {total_geracoes} linha(s) de geração salvos para {data}")

def salvar_destaques_termica(data: str, itens: list):
    if not itens:
        log("   Nenhum destaque térmico para salvar")
        return
    
    conn = _get_conn()
    cur = conn.cursor()
    cur.executemany('''
        INSERT OR IGNORE INTO destaques_geracao_termica
        (data, unidade_geradora, desvio, descricao)
        VALUES (?, ?, ?, ?)
    ''', [(data, i["unidade_geradora"], i["desvio"], i["descricao"]) for i in itens])
    conn.commit()
    conn.close()
    log(f"   SUCESSO → {len(itens)} destaque(s) térmico(s) salvo(s) para {data}")