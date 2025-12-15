# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="IPDO API",
    description="API de consulta aos destaques do IPDO (ONS)",
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
# Health-check
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    """
    Endpoint simples para verificar se a API está no ar.
    Não depende de banco nem de GPT.
    """
    return {"status": "ok"}
