from pathlib import Path
from config.settings import PDFS_DIR, OUTPUT_DIR, PROMPTS_DIR
from core.pdf_extractor import extrair_texto
from core.date_parser import extrair_data_do_nome
from core.openai_client import chamar_gpt
from database.models import criar_tabelas
from database.repository import salvar_destaques_operacao, salvar_destaques_termica
from utils.logger import log
import json

def carregar_prompt(nome: str, data: str, texto: str) -> str:
    template = (PROMPTS_DIR / nome).read_text(encoding="utf-8")
    return template.replace("{{DATA_RELATORIO}}", data).replace("{{TEXTO_EXTRAIDO}}", texto)

def processar_arquivo(pdf_path: Path):
    log(f"Processando → {pdf_path.name}")

    data = extrair_data_do_nome(pdf_path.name)
    texto = extrair_texto(pdf_path)

    tarefas = [
        ("destaques_operacao.txt", "operacao", salvar_destaques_operacao),
        ("destaques_geracao_termica.txt", "termica", salvar_destaques_termica),
    ]

    for arquivo_prompt, tipo, funcao_salvar in tarefas:
        prompt = carregar_prompt(arquivo_prompt, data, texto)
        try:
            resultado = chamar_gpt(prompt)
            resultado["data"] = data  # garantia

            # Salva JSON (opcional)
            json_path = OUTPUT_DIR / f"{pdf_path.stem}_{tipo}.json"
            json_path.write_text(json.dumps(resultado, indent=4, ensure_ascii=False), encoding="utf-8")

            # Salva no banco
            if tipo == "operacao":
                funcao_salvar(data, resultado.get("destaques_operacao", []))
            else:
                funcao_salvar(data, resultado.get("destaques_geracao_termica", []))

        except Exception as e:
            log(f"   Falha em {tipo}: {e}")

def main():
    log("Iniciando sistema de extração ONS")
    criar_tabelas()

    pdfs = sorted(PDFS_DIR.glob("*.pdf"))
    if not pdfs:
        log("Nenhum PDF encontrado em pdfs/")
        return

    for pdf in pdfs:
        processar_arquivo(pdf)

    log("Concluído! Tudo salvo no banco e em outputs/")

if __name__ == "__main__":
    main()