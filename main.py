# main.py
from pathlib import Path
import hashlib
from config.settings import PDFS_DIR, OUTPUT_DIR, PROMPTS_DIR
#from core.pdf_extractor import extrair_texto
from core.pdf_extractor_v2 import extrair_texto
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