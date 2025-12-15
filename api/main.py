# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import datas, operacao, geracao, termica

app = FastAPI(
    title="IPDO API",
    description="""
API de consulta aos destaques do IPDO (ONS).

Esta API expõe dados já processados a partir dos relatórios IPDO,
sem realizar extração de PDF ou chamadas a LLM.

🔹 Escopo MVP  
🔹 Somente leitura  
🔹 Sem autenticação
""",
    version="0.1.0 (MVP)"
)

# ---------------------------------------------------------
# CORS (aberto para MVP)
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # MVP → liberar geral
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------

app.include_router(datas.router)
app.include_router(operacao.router)
app.include_router(geracao.router)
app.include_router(termica.router)

# ---------------------------------------------------------
# Health-check
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    """
    Health-check da API.

    Retorna apenas se o serviço está ativo.
    Não acessa banco nem GPT.
    """
    return {"status": "ok"}
