# Código Completo do Projeto

*Gerado automaticamente em 11/12/2025 às 09:30*

Total de arquivos: 9

---

## Arquivo: `config/settings.py`

```python
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

PDFS_DIR = BASE_DIR / "pdfs"
OUTPUT_DIR = BASE_DIR / "outputs"
PROMPTS_DIR = BASE_DIR / "prompts"
DB_PATH = BASE_DIR / "banco_destaques.db"

OPENAI_MODEL = "gpt-5-mini"

OUTPUT_DIR.mkdir(exist_ok=True)
```

---

## Arquivo: `core/date_parser.py`

```python
import re
from datetime import datetime

def extrair_data_do_nome(nome_arquivo: str) -> str:
    match = re.search(r"(\d{4})[._-]?(\d{1,2})[._-]?(\d{1,2})", nome_arquivo)
    if not match:
        raise ValueError(f"Data não encontrada no nome: {nome_arquivo}")
    ano, mes, dia = match.groups()
    return f"{ano}-{int(mes):02d}-{int(dia):02d}"
```

---

## Arquivo: `core/openai_client.py`

```python
from openai import OpenAI
from config.settings import OPENAI_MODEL
import json
import time
from utils.logger import log
from dotenv import load_dotenv
import os


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def chamar_gpt(prompt: str, max_retries=3) -> dict:

    if not client.api_key:
         raise ValueError("OPENAI_API_KEY não encontrada! Verifique o arquivo .env")

    for tentativa in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": "Você responde APENAS com JSON válido. Nunca adicione texto fora do JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            conteudo = response.choices[0].message.content.strip()
            return json.loads(conteudo)
        except json.JSONDecodeError:
            if tentativa == max_retries - 1:
                raise
            log("JSON inválido retornado. Tentando novamente...")
            time.sleep(2)
        except Exception as e:
            if tentativa == max_retries - 1:
                raise e
            log(f"Erro na API (tentativa {tentativa+1}): {e}")
            time.sleep(3)
    raise Exception("Falha após várias tentativas")
```

---

## Arquivo: `core/pdf_extractor.py`

```python
from pathlib import Path
import PyPDF2

def extrair_texto(pdf_path: Path) -> str:
    texto = []
    with open(pdf_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            t = page.extract_text()
            if t:
                texto.append(t)
    return "\n".join(texto)
```

---

## Arquivo: `database/models.py`

```python
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
```

---

## Arquivo: `database/repository.py`

```python
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
```

---

## Arquivo: `main.py`

```python
# main.py
from pathlib import Path
import hashlib
from config.settings import PDFS_DIR, OUTPUT_DIR, PROMPTS_DIR
from core.pdf_extractor import extrair_texto
from core.date_parser import extrair_data_do_nome
from core.openai_client import chamar_gpt
from database.models import criar_tabelas
from database.repository import salvar_destaques_operacao, salvar_destaques_termica
from utils.logger import log
import json

def calcular_hash_pdf(pdf_path: Path) -> str:
    """Calcula hash do PDF para detectar mudanças"""
    with open(pdf_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def json_existe_e_atual(pdf_path: Path, tipo: str) -> bool:
    """Verifica se o JSON já existe e se o PDF não mudou desde então"""
    json_path = OUTPUT_DIR / f"{pdf_path.stem}_{tipo}.json"
    if not json_path.exists():
        return False
    
    try:
        dados_json = json.loads(json_path.read_text(encoding="utf-8"))
        hash_salvo = dados_json.get("_metadata", {}).get("pdf_hash")
        hash_atual = calcular_hash_pdf(pdf_path)
        return hash_salvo == hash_atual
    except:
        return False

def salvar_json_com_metadata(pdf_path: Path, tipo: str, dados: dict):
    """Salva JSON com hash do PDF pra controle futuro"""
    dados["_metadata"] = {
        "pdf_hash": calcular_hash_pdf(pdf_path),
        "processado_em": Path().cwd().name,  # ou datetime
        "fonte": pdf_path.name
    }
    json_path = OUTPUT_DIR / f"{pdf_path.stem}_{tipo}.json"
    json_path.write_text(json.dumps(dados, indent=4, ensure_ascii=False), encoding="utf-8")

def carregar_prompt(nome: str, data: str, texto: str) -> str:
    template = (PROMPTS_DIR / nome).read_text(encoding="utf-8")
    return template.replace("{{DATA_RELATORIO}}", data).replace("{{TEXTO_EXTRAIDO}}", texto)

def processar_arquivo(pdf_path: Path):
    log(f"Processando → {pdf_path.name}")

    try:
        data = extrair_data_do_nome(pdf_path.name)
    except Exception as e:
        log(f"   Erro ao extrair data do nome: {e}")
        return

    # Verifica se JÁ TEM OS DOIS JSONS e o PDF não mudou
    if json_existe_e_atual(pdf_path, "operacao") and json_existe_e_atual(pdf_path, "termica"):
        log(f"   Arquivos já processados e atualizados → pulando GPT (cache hit)")
        
        # Mesmo assim, salva no banco (caso tenha rodado antes sem banco)
        try:
            for tipo, repo_func in [("operacao", salvar_destaques_operacao), ("termica", salvar_destaques_termica)]:
                json_path = OUTPUT_DIR / f"{pdf_path.stem}_{tipo}.json"
                dados = json.loads(json_path.read_text(encoding="utf-8"))
                if tipo == "operacao":
                    repo_func(data, dados.get("destaques_operacao", []))
                else:
                    repo_func(data, dados.get("destaques_geracao_termica", []))
            log(f"   Dados do cache carregados no banco para {data}")
        except Exception as e:
            log(f"   Erro ao carregar cache no banco: {e}")
        log(f"   Erro ao carregar cache no banco: {e}")
        return

    # Se chegou aqui → precisa rodar GPT
    log(f"   PDF novo ou alterado → enviando para GPT-4o...")
    texto = extrair_texto(pdf_path)

    tarefas = [
        ("destaques_operacao.txt",  "operacao", salvar_destaques_operacao),
        ("destaques_geracao_termica.txt", "termica", salvar_destaques_termica),
    ]

    for arquivo_prompt, tipo, funcao_salvar in tarefas: 
        if json_existe_e_atual(pdf_path, tipo):
            log(f"   {tipo}.json já existe e válido → pulando")
            continue

        log(f"   Extraindo {tipo} com GPT...")
        prompt = carregar_prompt(arquivo_prompt, data, texto)
        try:
            resultado = chamar_gpt(prompt)
            resultado["data"] = data

            # Salva JSON com hash
            salvar_json_com_metadata(pdf_path, tipo, resultado)

            # Salva no banco
            if tipo == "operacao":
                funcao_salvar(data, resultado.get("destaques_operacao", []))
            else:
                funcao_salvar(data, resultado.get("destaques_geracao_termica", []))

            log(f"   {tipo} → salvo (GPT)")

        except Exception as e:
            log(f"   FALHA ao extrair {tipo}: {e}")

def main():
    log("Iniciando sistema de extração ONS (com cache inteligente)")
    criar_tabelas()

    pdfs = sorted(PDFS_DIR.glob("*.pdf"))
    if not pdfs:
        log("Nenhum PDF encontrado em pdfs/")
        return

    log(f"{len(pdfs)} PDF(s) encontrado(s). Verificando cache...")

    for pdf in pdfs:
        processar_arquivo(pdf)

    log("Concluído! Tudo atualizado com cache inteligente")

if __name__ == "__main__":
    main()
```

---

## Arquivo: `utils/logger.py`

```python
from datetime import datetime

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
```

---

## Arquivo: `ver_banco.py`

```python
# ver_banco.py
import sqlite3
import pandas as pd
from config.settings import DB_PATH
from utils.logger import log
from datetime import datetime

def mostrar_resumo():
    conn = sqlite3.connect(DB_PATH)
    
    print("\n" + "="*60)
    print("           RESUMO DO BANCO ONS - IPDO")
    print("="*60)
    
    # Total de dias processados
    total_dias = pd.read_sql_query("SELECT COUNT(DISTINCT data) as qtd FROM destaques_operacao", conn).iloc[0]['qtd']
    datas = pd.read_sql_query("SELECT data FROM destaques_operacao ORDER BY data DESC LIMIT 10", conn)['data'].tolist()
    
    print(f"Total de dias no banco: {total_dias}")
    print(f"Últimas datas: {', '.join(datas)}")
    print("-" * 60)

    # Último dia completo
    ultimo_dia = datas[0] if datas else None
    if ultimo_dia:
        print(f"\nDESTAQUES DO DIA: {ultimo_dia}")
        print("\nGeração por Submercado e Tipo:")
        df_ger = pd.read_sql_query("""
            SELECT submercado, tipo_geracao, status, substr(descricao, 1, 70) || '...' as descricao
            FROM destaques_geracao 
            WHERE data = ?
            ORDER BY submercado, 
                     CASE tipo_geracao 
                       WHEN 'Hidráulica' THEN 1 
                       WHEN 'Térmica' THEN 2 
                       WHEN 'Eólica' THEN 3 
                       WHEN 'Solar' THEN 4 
                       WHEN 'Nuclear' THEN 5 ELSE 99 END
        """, conn, params=(ultimo_dia,))
        print(df_ger.to_string(index=False))

        print("\nDestaques Térmicos:")
        df_term = pd.read_sql_query("""
            SELECT unidade_geradora, desvio, substr(descricao, 1, 80) || '...' as descricao
            FROM destaques_geracao_termica 
            WHERE data = ? 
            ORDER BY desvio DESC
        """, conn, params=(ultimo_dia,))
        if len(df_term) == 0:
            print("   Nenhum destaque térmico neste dia")
        else:
            print(df_term.to_string(index=False))

    conn.close()
    print("\n" + "="*60)

def exportar_excel():
    conn = sqlite3.connect(DB_PATH)
    
    # Lê tudo
    df_op = pd.read_sql_query("SELECT data, submercado, carga_status, carga_descricao, restricoes, transferencia_status FROM destaques_operacao ORDER BY data DESC", conn)
    df_ger = pd.read_sql_query("SELECT data, submercado, tipo_geracao, status, descricao FROM destaques_geracao ORDER BY data DESC", conn)
    df_term = pd.read_sql_query("SELECT data, unidade_geradora, desvio, descricao FROM destaques_geracao_termica ORDER BY data DESC", conn)
    
    arquivo = f"IPDO_Destaques_Completo_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    
    with pd.ExcelWriter(arquivo, engine='openpyxl') as writer:
        df_op.to_excel(writer, sheet_name="Operação e Carga", index=False)
        df_ger.to_excel(writer, sheet_name="Geração por Tipo", index=False)
        df_term.to_excel(writer, sheet_name="Destaques Térmicos", index=False)
    
    conn.close()
    print(f"\nExcel gerado com sucesso: {arquivo}")
    print("   3 abas: Operação e Carga | Geração por Tipo | Destaques Térmicos")

if __name__ == "__main__":
    print("\nEscolha uma opção:\n")
    print("1 → Ver resumo no terminal (recomendado)")
    print("2 → Exportar TUDO para Excel agora")
    print("3 → Ambos")
    
    try:
        op = input("\nDigite 1, 2 ou 3: ").strip()
        if op == "1":
            mostrar_resumo()
        elif op == "2":
            exportar_excel()
        elif op == "3":
            mostrar_resumo()
            exportar_excel()
        else:
            print("Opção inválida!")
    except KeyboardInterrupt:
        print("\nTchau!")
```

---

