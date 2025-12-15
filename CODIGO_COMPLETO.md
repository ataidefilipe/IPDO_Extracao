# Código Completo do Projeto

*Gerado automaticamente em 15/12/2025 às 16:22*

Total de arquivos: 20

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

OPENAI_TIMEOUT = 90  # segundos
```

---

## Arquivo: `core/chunking.py`

```python
# core/chunking.py
"""
Funções utilitárias para divisão de texto (chunking) com limite de tokens.

O objetivo é impedir que textos extraídos do PDF ultrapassem o limite de 
contexto do modelo GPT, evitando erros 400 e análises incompletas.
"""

import re
from utils.logger import log

# Estimativa média: 1 token ≈ 4 caracteres (para modelos GPT modernos)
TOKEN_RATIO = 4


def estimate_tokens(text: str) -> int:
    """Estima número de tokens baseado no tamanho do texto."""
    return max(1, len(text) // TOKEN_RATIO)


def split_text_by_tokens(text: str, max_tokens: int = 6000) -> list:
    """
    Divide o texto em chunks respeitando limite de tokens aproximado.

    - Nunca quebra no meio de parágrafos
    - Se chunk único exceder max_tokens → quebra em sentenças
    - Retorna lista de chunks prontos para envio ao GPT
    """

    total_tokens = estimate_tokens(text)
    log(f"   Texto possui aproximadamente {total_tokens} tokens")

    if total_tokens <= max_tokens:
        log("   Chunking NÃO necessário → texto cabe em um único prompt")
        return [text]

    log("   Chunking necessário → dividindo o texto...")

    # Primeira divisão por parágrafos
    paragraphs = re.split(r"\n\s*\n", text)
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        candidate = current_chunk + "\n\n" + para if current_chunk else para

        if estimate_tokens(candidate) < max_tokens:
            current_chunk = candidate
        else:
            # Chunk cheio → salva e começa outro
            chunks.append(current_chunk.strip())
            current_chunk = para

    # Último pedaço
    if current_chunk:
        chunks.append(current_chunk.strip())

    # Garantia de que nenhum chunk ultrapassa o máximo
    final_chunks = []
    for c in chunks:
        if estimate_tokens(c) <= max_tokens:
            final_chunks.append(c)
        else:
            # Se um parágrafo gigante excede, quebrar em sentenças
            log("   Parágrafo muito grande → realizando divisão por sentenças...")
            sentences = re.split(r"(?<=[.!?])\s+", c)
            sub_chunk = ""
            for s in sentences:
                candidate = sub_chunk + " " + s if sub_chunk else s
                if estimate_tokens(candidate) < max_tokens:
                    sub_chunk = candidate
                else:
                    final_chunks.append(sub_chunk.strip())
                    sub_chunk = s
            if sub_chunk:
                final_chunks.append(sub_chunk.strip())

    log(f"   Chunking finalizado → {len(final_chunks)} chunk(s) gerados")
    return final_chunks
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

## Arquivo: `core/extract_sections.py`

```python
import re
from utils.logger import log


def extrair_trecho(texto: str, inicio: str, fim: str) -> str:
    """
    Extrai o texto entre marcadores específicos.
    Se não encontrar, retorna string vazia.
    """
    pattern = re.compile(
        rf"{re.escape(inicio)}(.*?){re.escape(fim)}",
        flags=re.DOTALL | re.IGNORECASE
    )
    match = pattern.search(texto)
    return match.group(1).strip() if match else ""


def extrair_operacao(texto: str) -> str:
    """
    Extrai seção 4 - Destaques da Operação até antes de 5 - Gerações
    """
    log("   → Extraindo seção: Destaques da Operação")
    return extrair_trecho(texto, "4 - Destaques da Operação", "5 - Gerações")


def extrair_termica(texto: str) -> str:
    """
    Extrai seção 6 - Destaques da Geração Térmica até antes do 7 - Demandas Máximas
    """
    log("   → Extraindo seção: Destaques da Geração Térmica")
    return extrair_trecho(texto, "6 - Destaques da Geração Térmica", "7 - Demandas Máximas")
```

---

## Arquivo: `core/gpt_runner.py`

```python
# core/gpt_runner.py
"""
Camada de orquestração entre prompts, PDFs e OpenAI Responses API.
"""

from core.openai_client_v2 import chamar_gpt_v2
from utils.logger import log


def processar_trecho_com_gpt(trecho: str, prompt_base: str) -> dict:
    """
    Fluxo para trechos textuais (operação e térmica).
    """
    prompt = prompt_base.replace("{{TEXTO_EXTRAIDO}}", trecho)
    print("prompt:\n\n", prompt)
    return chamar_gpt_v2(prompt)


def processar_pdf_com_prompt(pdf_bytes: bytes, prompt: str) -> dict:
    """
    Fluxo para PDFs completos (caso futuro de migração total).
    """
    log("   Enviando PDF completo como input multimodal...")
    return chamar_gpt_v2(prompt, pdf_bytes=pdf_bytes)
```

---

## Arquivo: `core/json_merge.py`

```python
# core/json_merge.py

def merge_respostas(parciais: list, tipo: str) -> dict:
    """
    Junta respostas parciais do GPT em um único JSON final.
    Exemplo:
      - tipo == "operacao" → une listas dentro de "destaques_operacao"
      - tipo == "termica"  → une listas dentro de "destaques_geracao_termica"
    """

    if not parciais:
        raise ValueError("Lista de respostas parciais está vazia")

    final = parciais[0].copy()  # copia campos base (ex: metadata futura)
    
    if tipo == "operacao":
        final["destaques_operacao"] = []
        for p in parciais:
            final["destaques_operacao"] += p.get("destaques_operacao", [])

    elif tipo == "termica":
        final["destaques_geracao_termica"] = []
        for p in parciais:
            final["destaques_geracao_termica"] += p.get("destaques_geracao_termica", [])

    return final
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

def chamar_gpt_em_chunks(prompt_template: str, chunks: list) -> list:
    """
    Envia múltiplos prompts ao GPT, um por chunk.
    Cada resposta será tratada como parte do JSON final.
    """
    respostas = []

    for idx, texto in enumerate(chunks, 1):
        log(f"   → Enviando chunk {idx}/{len(chunks)} ao GPT...")

        prompt = prompt_template.replace("{{TEXTO_EXTRAIDO}}", texto)

        resultado = chamar_gpt(prompt)
        respostas.append(resultado)

    return respostas
```

---

## Arquivo: `core/openai_client_v2.py`

```python
# core/openai_client_v2.py
"""
Cliente OpenAI usando a Responses API (API moderna).
Compatível com:
- JSON-only via prompt
- Retentativas
- Timeout explícito
- Envio opcional de PDF
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import time
from utils.logger import log
from config.settings import OPENAI_MODEL, OPENAI_TIMEOUT

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def _extrair_texto_json(response) -> str:
    """
    Extrai texto consolidado da Responses API de forma segura.
    """
    # Forma mais estável e recomendada
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text.strip()

    # Fallback manual (caso API mude)
    textos = []
    for item in response.output:
        if item["type"] == "message":
            for c in item["content"]:
                if c["type"] == "output_text":
                    textos.append(c["text"])

    return "\n".join(textos).strip()


def chamar_gpt_v2(prompt: str, pdf_bytes: bytes = None, max_retries: int = 3) -> dict:
    """
    Chamada ao GPT usando Responses API.
    Retorna dict (JSON parseado).
    """

    for tentativa in range(1, max_retries + 1):

        log(f"   [GPT] Tentativa {tentativa}/{max_retries} usando Responses API...")

        try:
            # -----------------------------
            # Montagem do input
            # -----------------------------
            if pdf_bytes:
                input_payload = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {
                                "type": "input_file",
                                "mime_type": "application/pdf",
                                "data": pdf_bytes
                            }
                        ]
                    }
                ]
            else:
                input_payload = prompt

            # -----------------------------
            # Chamada OpenAI
            # -----------------------------
            response = client.responses.create(
                model=OPENAI_MODEL,
                input=input_payload,
                timeout=OPENAI_TIMEOUT
            )

            texto = _extrair_texto_json(response)

            if not texto:
                raise ValueError("Resposta vazia da OpenAI Responses API.")

            return json.loads(texto)

        except json.JSONDecodeError:
            log("   [ERRO] JSON inválido retornado. Retentando...")
            time.sleep(2)

        except Exception as e:
            log(f"   [ERRO] OpenAI Responses API: {e}")
            time.sleep(2)

    raise RuntimeError("Falha após múltiplas tentativas com Responses API.")
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

## Arquivo: `core/pdf_extractor_v2.py`

```python
# core/pdf_extractor_v2.py
"""
Módulo de extração de texto usando pypdfium2 (compatível com todas as versões atuais).
"""

from pathlib import Path
import pypdfium2 as pdfium
import re
from utils.logger import log


def _clean_text(text: str) -> str:
    """Normaliza texto extraído para reduzir ruído que atrapalha o GPT."""
    text = text.replace("\u200b", "").replace("\ufeff", "")
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ ]+\n", "\n", text)
    return text.strip()


def extrair_texto(pdf_path: Path) -> str:
    """
    Extrai texto de todas as páginas do PDF usando pypdfium2.
    Compatível com versões antigas e recentes da biblioteca.
    """

    log(f"   Iniciando extração pypdfium2 → {pdf_path.name}")

    try:
        pdf = pdfium.PdfDocument(str(pdf_path))
    except Exception as e:
        raise RuntimeError(f"Falha ao abrir PDF '{pdf_path}': {e}")

    paginas = len(pdf)  # ← número de páginas correto nessa versão
    texto_final = []

    for page_number in range(paginas):
        try:
            page = pdf[page_number]  # ← forma correta de acessar página
            textpage = page.get_textpage()
            texto = textpage.get_text_range()
            texto_final.append(texto)
        except Exception as e:
            log(f"   [WARN] Falha ao extrair página {page_number+1}/{paginas}: {e}")
            texto_final.append(f"\n[Página {page_number+1} não pôde ser extraída]\n")

    texto = "\n".join(texto_final)
    texto = _clean_text(texto)

    log(f"   Extração concluída ({paginas} páginas)")
    return texto
```

---

## Arquivo: `database/init_db.py`

```python
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
            desvio TEXT NOT NULL,
            descricao TEXT NOT NULL,
            UNIQUE(data, unidade_geradora, descricao)
        )
    """)

    conn.commit()
    conn.close()

    log("Banco inicializado com segurança (sem apagar dados)")
```

---

## Arquivo: `database/models.py`

```python
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
import json

from config.settings import PDFS_DIR, OUTPUT_DIR, PROMPTS_DIR

from core.pdf_extractor_v2 import extrair_texto
from core.date_parser import extrair_data_do_nome
from core.gpt_runner import processar_trecho_com_gpt
from core.extract_sections import extrair_operacao, extrair_termica

from database.init_db import init_db
from database.repository import salvar_destaques_operacao, salvar_destaques_termica

from utils.logger import log


# ---------------------------------------------------------
# Funções de suporte
# ---------------------------------------------------------

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
        "processado_em": Path().cwd().name,
        "fonte": pdf_path.name
    }
    json_path = OUTPUT_DIR / f"{pdf_path.stem}_{tipo}.json"
    json_path.write_text(json.dumps(dados, indent=4, ensure_ascii=False), encoding="utf-8")


def carregar_prompt_base(nome_prompt: str, data: str) -> str:
    """Carrega o template sem texto ainda"""
    template = (PROMPTS_DIR / nome_prompt).read_text(encoding="utf-8")
    return template.replace("{{DATA_RELATORIO}}", data)


# ---------------------------------------------------------
# Processamento principal de cada PDF
# ---------------------------------------------------------

def processar_arquivo(pdf_path: Path):
    log(f"Processando → {pdf_path.name}")

    # -------------------------
    # 1. Extrair data
    # -------------------------
    try:
        data = extrair_data_do_nome(pdf_path.name)
    except Exception as e:
        log(f"   Erro ao extrair data do nome: {e}")
        return

    # -------------------------
    # 2. Cache – evitar GPT
    # -------------------------
    if json_existe_e_atual(pdf_path, "operacao") and json_existe_e_atual(pdf_path, "termica"):
        log(f"   Cache HIT → JSONs já atualizados, pulando GPT")

        try:
            for tipo, repo_func in [
                ("operacao", salvar_destaques_operacao),
                ("termica", salvar_destaques_termica)
            ]:
                json_path = OUTPUT_DIR / f"{pdf_path.stem}_{tipo}.json"
                dados = json.loads(json_path.read_text(encoding="utf-8"))

                if tipo == "operacao":
                    repo_func(data, dados.get("destaques_operacao", []))
                else:
                    repo_func(data, dados.get("destaques_geracao_termica", []))

            log(f"   Dados carregados do cache para o banco")
        except Exception as e:
            log(f"   Erro ao carregar cache no banco: {e}")

        return

    # -------------------------
    # 3. Extrair TEXTO COMPLETO
    # -------------------------
    log("   Extraindo texto bruto do PDF...")
    texto = extrair_texto(pdf_path)

    # -------------------------
    # 4. Definição de tarefas (operacao / termica)
    # -------------------------
    tarefas = [
        ("destaques_operacao.txt",  "operacao", extrair_operacao, salvar_destaques_operacao),
        ("destaques_geracao_termica.txt", "termica", extrair_termica, salvar_destaques_termica),
    ]

    # -------------------------
    # 5. Rodar cada tipo de destaque
    # -------------------------
    for nome_prompt, tipo, func_extrair_trecho, func_salvar in tarefas:

        if json_existe_e_atual(pdf_path, tipo):
            log(f"   {tipo}.json já válido → pulando")
            continue

        log(f"   → Preparando extração de {tipo}...")

        # 5.1 Extrair apenas o trecho relevante
        trecho = func_extrair_trecho(texto)

        if not trecho:
            log(f"   [WARN] Não foi possível localizar a seção relevante para {tipo}.")
            continue

        # 5.2 Carregar prompt base (sem o texto ainda)
        prompt = (PROMPTS_DIR / nome_prompt).read_text(encoding="utf-8")
        prompt = prompt.replace("{{DATA_RELATORIO}}", data)
        prompt = prompt.replace("{{TEXTO_EXTRAIDO}}", trecho)

        try:
            # 5.3 Chamada simples ao GPT (sem chunking)
            resultado = processar_trecho_com_gpt(trecho, prompt)
            resultado["data"] = data

            # 5.4 Salvar o JSON com metadata
            salvar_json_com_metadata(pdf_path, tipo, resultado)

            # 5.5 Salvar no banco
            if tipo == "operacao":
                func_salvar(data, resultado.get("destaques_operacao", []))
            else:
                func_salvar(data, resultado.get("destaques_geracao_termica", []))

            log(f"   {tipo} → salvo com sucesso")

        except Exception as e:
            log(f"   ERRO ao extrair {tipo}: {e}")


# ---------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------

def main():
    log("Iniciando sistema de extração ONS (com cache e corte de seções)")

    init_db()

    pdfs = sorted(PDFS_DIR.glob("*.pdf"))
    if not pdfs:
        log("Nenhum PDF encontrado em pdfs/")
        return

    log(f"{len(pdfs)} PDF(s) encontrado(s). Iniciando processamento...")

    for pdf in pdfs:
        processar_arquivo(pdf)

    log("Concluído! Tudo atualizado com sucesso.")


if __name__ == "__main__":
    main()
```

---

## Arquivo: `reset_db.py`

```python
# reset_db.py
from database.models import reset_db

if __name__ == "__main__":
    print("\n⚠️ ATENÇÃO ⚠️")
    print("Você está prestes a APAGAR TODO O BANCO DE DADOS.")
    print("Esta ação é IRREVERSÍVEL.\n")

    confirm = input("Digite 'RESETAR' para confirmar: ").strip()

    if confirm == "RESETAR":
        reset_db()
        print("Banco apagado com sucesso.")
    else:
        print("Operação cancelada.")
```

---

## Arquivo: `tests/benchmark_pdf_extract.py`

```python
from core.pdf_extractor_v2 import extrair_texto
from time import time
from pathlib import Path

def test_benchmark_extraction_speed():
    pdf = Path("tests/pdfs/exemplo1.pdf")
    t0 = time()
    extrair_texto(pdf)
    t1 = time()

    assert (t1 - t0) < 1.5  # tempo aceitável para PDFs típicos do IPDO
```

---

## Arquivo: `tests/test_openai_client_v2.py`

```python
from core.openai_client_v2 import chamar_gpt_v2

def test_mock_responses_api(monkeypatch):
    class FakeResp:
        output_text = '{"ok": true}'

    class FakeClient:
        def responses(self):
            return self
        def create(self, **kwargs):
            return FakeResp()

    monkeypatch.setattr("core.openai_client_v2.client", FakeClient())

    out = chamar_gpt_v2("teste")
    assert out["ok"] is True
```

---

## Arquivo: `tests/test_pdf_extractor_v2.py`

```python
from core.pdf_extractor_v2 import extrair_texto
from pathlib import Path

def test_extração_pdf_simples():
    pdf = Path("tests/pdfs/exemplo1.pdf")
    texto = extrair_texto(pdf)

    assert isinstance(texto, str)
    assert len(texto) > 10  # texto mínimo
    assert "IPDO" in texto or len(texto) > 50


def test_extração_pdf_multiplas_paginas():
    pdf = Path("tests/pdfs/exemplo2.pdf")
    texto = extrair_texto(pdf)

    assert "\n" in texto  # mais de uma página deve gerar contatos
    assert len(texto.splitlines()) > 5


def test_pdf_corrompido_retornar_erro():
    pdf = Path("tests/pdfs/corrompido.pdf")

    try:
        extrair_texto(pdf)
        assert False, "Era esperado erro ao abrir PDF corrompido"
    except RuntimeError:
        assert True
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

