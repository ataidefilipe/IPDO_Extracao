from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

PDFS_DIR = BASE_DIR / "pdfs"
OUTPUT_DIR = BASE_DIR / "outputs"
PROMPTS_DIR = BASE_DIR / "prompts"
DB_PATH = BASE_DIR / "banco_destaques.db"

OPENAI_MODEL = "gpt-5-mini"

OUTPUT_DIR.mkdir(exist_ok=True)

OPENAI_TIMEOUT = 90  # segundos