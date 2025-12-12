# main.py
from pathlib import Path
import hashlib
import json

from config.settings import PDFS_DIR, OUTPUT_DIR, PROMPTS_DIR

from core.pdf_extractor_v2 import extrair_texto
from core.date_parser import extrair_data_do_nome
from core.gpt_runner import processar_trecho_com_gpt
from core.extract_sections import extrair_operacao, extrair_termica

from database.models import criar_tabelas
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

    criar_tabelas()

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
