# agent_ipdo/agent.py
"""
Agente IPDO (LLM + Tools + SQLite)

✅ Ajustes principais:
- Implementa o LOOP correto de tool-calling da Responses API:
  1) modelo pede tool
  2) executamos tool
  3) devolvemos function_call_output
  4) modelo gera resposta FINAL em linguagem natural

- Adiciona tools com filtros (submercado/tipo/status/limite/termo)
- Logs detalhados e legíveis
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from openai import OpenAI

# --- Queries diretas no SQLite (sem depender de FastAPI) ---
from queries.common import listar_datas as q_listar_datas
from queries.operacao import buscar_destaques_operacao as q_buscar_operacao
from queries.operacao import buscar_operacao_resumo as q_buscar_operacao_resumo
from queries.termica import buscar_termica_por_desvio as q_buscar_termica
from queries.geracao import buscar_geracao as q_buscar_geracao



# ------------------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------------------

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

prompt_path = Path(__file__).parent / "system_prompt.txt"
SYSTEM_PROMPT = prompt_path.read_text(encoding="utf-8")


def _log(msg: str):
    print(f"[AGENT LOG] {msg}")


def _safe_json_dumps(obj: Any) -> str:
    """Converte saída de tool para string JSON estável."""
    return json.dumps(obj, ensure_ascii=False, default=str)


def _normalize_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, str):
        s = v.strip()
        return s or None
    return str(v).strip() or None


def _normalize_int(v: Any) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(v)
    except Exception:
        return None


# ------------------------------------------------------------------------------
# Tools (funções reais)
# ------------------------------------------------------------------------------

def tool_listar_datas() -> list[str]:
    return q_listar_datas()


def tool_buscar_operacao(data: str, submercado: str | None = None) -> list[dict]:
    """
    Retorna destaques de operação por data.
    Filtro opcional por submercado (case-insensitive, contém).
    """
    data = _normalize_str(data) or ""
    submercado = _normalize_str(submercado)

    itens = q_buscar_operacao(data)

    if submercado:
        sm = submercado.lower()
        itens = [i for i in itens if sm in (i.get("submercado", "").lower())]

    return itens


def tool_buscar_geracao(
    data: str,
    submercado: str | None = None,
    tipo: str | None = None,
    status: str | None = None,
    limite: int | None = None,
) -> list[dict]:
    """
    Retorna destaques de geração (tabela destaques_geracao) com filtros.
    - submercado/tipo são filtros direto na query
    - status é filtro pós-query (porque não existe filtro no SQL da função atual)
    - limite é aplicado ao final
    """
    data = _normalize_str(data) or ""
    submercado = _normalize_str(submercado)
    tipo = _normalize_str(tipo)
    status = _normalize_str(status)
    limite = _normalize_int(limite)

    itens = q_buscar_geracao(data=data, submercado=submercado, tipo=tipo)

    if status:
        st = status.lower()
        itens = [i for i in itens if st == (i.get("status", "") or "").lower()]

    if limite is not None and limite >= 0:
        itens = itens[:limite]

    return itens


def tool_buscar_termica(
    data: str,
    limite: int | None = None,
    unidade: str | None = None,
    termo: str | None = None,
    desvio_status: str | None = None,
) -> list[dict]:
    """
    Retorna destaques térmicos por data com filtros opcionais:
    - limite: aplicado na query
    - desvio_status: aplicado na query ('Acima'|'Abaixo'|'Sem desvio')
    - unidade: filtro pós-query (contém) em unidade_geradora
    - termo: filtro pós-query (contém) em descricao
    """
    data = _normalize_str(data) or ""
    limite = _normalize_int(limite)
    unidade = _normalize_str(unidade)
    termo = _normalize_str(termo)
    desvio_status = _normalize_str(desvio_status)

    itens = q_buscar_termica(data=data, limite=limite, desvio_status=desvio_status)

    if unidade:
        u = unidade.lower()
        itens = [i for i in itens if u in (i.get("unidade_geradora", "").lower())]

    if termo:
        t = termo.lower()
        itens = [i for i in itens if t in (i.get("descricao", "").lower())]

    return itens


def tool_buscar_restricoes(
    data: str,
    submercado: str | None = None,
    termo: str | None = None,
    limite: int | None = None,
) -> list[dict]:
    """
    Retorna restrições (strings) extraídas dos destaques de operação.
    Útil quando usuário pede só "restrições" / "limitações" e quer filtrar por palavra.
    """
    data = _normalize_str(data) or ""
    submercado = _normalize_str(submercado)
    termo = _normalize_str(termo)
    limite = _normalize_int(limite)

    itens = tool_buscar_operacao(data=data, submercado=submercado)

    out: list[dict] = []
    for it in itens:
        sm = it.get("submercado")
        for r in (it.get("restricoes") or []):
            if not isinstance(r, str):
                continue
            out.append({"submercado": sm, "restricao": r})

    if termo:
        tl = termo.lower()
        out = [x for x in out if tl in (x.get("restricao", "").lower())]

    if limite is not None and limite >= 0:
        out = out[:limite]

    return out

def tool_buscar_operacao_resumo(
    data: str,
    submercado: str | None = None,
    limite_itens: int | None = None,
) -> list[dict]:
    """
    Retorna resumo compacto da operação por data.
    Filtro opcional por submercado (case-insensitive, contém).
    limite_itens limita tamanho de listas internas do resumo.
    """
    data = _normalize_str(data) or ""
    submercado = _normalize_str(submercado)
    limite_itens = _normalize_int(limite_itens)

    return q_buscar_operacao_resumo(data=data, submercado=submercado, limite_itens=limite_itens)


# ------------------------------------------------------------------------------
# Tool schemas (para o modelo)
# ------------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "name": "listar_datas",
        "description": "Lista as datas disponíveis no banco IPDO (SQLite).",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "buscar_operacao",
        "description": (
            "Busca destaques da operação por data. "
            "Opcionalmente filtra por submercado (ex: 'Nordeste', 'Sudeste', 'Sul', 'Norte')."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Data no formato YYYY-MM-DD"},
                "submercado": {"type": "string", "description": "Filtro opcional por submercado"},
            },
            "required": ["data"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "buscar_geracao",
        "description": (
            "Busca destaques de geração (tabela destaques_geracao) por data, "
            "com filtros opcionais de submercado, tipo e status. "
            "Use quando o usuário pedir algo como 'eólica', 'solar', 'hidráulica' etc."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Data no formato YYYY-MM-DD"},
                "submercado": {"type": "string", "description": "Filtro opcional (SE, S, NE, N ou nome)"},
                "tipo": {"type": "string", "description": "Filtro opcional (Hidráulica, Térmica, Eólica, Solar, Nuclear)"},
                "status": {"type": "string", "description": "Filtro opcional (Acima, Inferior, Sem desvio, etc.)"},
                "limite": {"type": "integer", "description": "Máximo de itens a retornar (opcional)"},
            },
            "required": ["data"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "buscar_termica",
        "description": (
            "Busca destaques de geração térmica por data. "
            "Pode limitar a quantidade (limite) e filtrar por unidade/termo."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Data no formato YYYY-MM-DD"},
                "limite": {"type": "integer", "description": "Máximo de itens (opcional)"},
                "unidade": {"type": "string", "description": "Filtrar por unidade_geradora (contém, opcional)"},
                "termo": {"type": "string", "description": "Filtrar por palavra na descrição (contém, opcional)"},
                "desvio_status": {"type": "string", "description": "Filtro opcional: Acima | Abaixo | Sem desvio"},
            },
            "required": ["data"],  # ✅ limite é opcional de verdade
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "buscar_restricoes",
        "description": (
            "Busca restrições/limitações reportadas na operação por data, "
            "com filtros opcionais de submercado e termo (ex: 'eólica', 'solar', 'frequência')."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Data no formato YYYY-MM-DD"},
                "submercado": {"type": "string", "description": "Filtro opcional por submercado"},
                "termo": {"type": "string", "description": "Filtro opcional por palavra/trecho (contém)"},
                "limite": {"type": "integer", "description": "Máximo de itens (opcional)"},
            },
            "required": ["data"],
            "additionalProperties": False,
        },
    },
        {
        "type": "function",
        "name": "buscar_operacao_resumo",
        "description": (
            "Busca um RESUMO compacto da operação por data (menos texto e mais previsível). "
            "Retorna por submercado: carga_status, transferencia_status, contagem de restrições, "
            "amostra de restrições e lista curta de geração (tipo+status). "
            "Use por padrão quando o usuário perguntar 'como estava o sistema no dia X?'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "data": {"type": "string", "description": "Data no formato YYYY-MM-DD"},
                "submercado": {"type": "string", "description": "Filtro opcional por submercado (contém)"},
                "limite_itens": {"type": "integer", "description": "Limita tamanho de listas internas (opcional)"},
            },
            "required": ["data"],
            "additionalProperties": False,
        },
    },

]


# ------------------------------------------------------------------------------
# Dispatcher de tools
# ------------------------------------------------------------------------------

def _executar_tool(nome: str, args: dict) -> Any:
    """Executa uma tool e retorna um objeto serializável."""
    if nome == "listar_datas":
        return tool_listar_datas()

    if nome == "buscar_operacao":
        data = _normalize_str(args.get("data"))
        if not data:
            return {"erro": "Parâmetro 'data' é obrigatório (YYYY-MM-DD)."}
        return tool_buscar_operacao(data=data, submercado=args.get("submercado"))

    if nome == "buscar_geracao":
        data = _normalize_str(args.get("data"))
        if not data:
            return {"erro": "Parâmetro 'data' é obrigatório (YYYY-MM-DD)."}
        return tool_buscar_geracao(
            data=data,
            submercado=args.get("submercado"),
            tipo=args.get("tipo"),
            status=args.get("status"),
            limite=args.get("limite"),
        )

    if nome == "buscar_termica":
        data = _normalize_str(args.get("data"))
        if not data:
            return {"erro": "Parâmetro 'data' é obrigatório (YYYY-MM-DD)."}
        return tool_buscar_termica(
            data=data,
            limite=args.get("limite"),
            unidade=args.get("unidade"),
            termo=args.get("termo"),
            desvio_status=args.get("desvio_status"),
        )


    if nome == "buscar_restricoes":
        data = _normalize_str(args.get("data"))
        if not data:
            return {"erro": "Parâmetro 'data' é obrigatório (YYYY-MM-DD)."}
        return tool_buscar_restricoes(
            data=data,
            submercado=args.get("submercado"),
            termo=args.get("termo"),
            limite=args.get("limite"),
        )
    
    if nome == "buscar_operacao_resumo":
        data = _normalize_str(args.get("data"))
        if not data:
            return {"erro": "Parâmetro 'data' é obrigatório (YYYY-MM-DD)."}
        return tool_buscar_operacao_resumo(
            data=data,
            submercado=args.get("submercado"),
            limite_itens=args.get("limite_itens"),
        )

    return {"erro": f"Tool desconhecida: {nome}"}


# ------------------------------------------------------------------------------
# Loop do agente (Responses API)
# ------------------------------------------------------------------------------

def responder_pergunta(pergunta: str) -> str:
    """
    Executa o loop de tool-calling até obter resposta final em linguagem natural.
    """
    if not client.api_key:
        return "[ERRO] OPENAI_API_KEY não encontrada no ambiente/.env"

    _log(f"Pergunta recebida: {pergunta}")

    # input é uma lista de itens (mensagens + outputs da API)
    input_items: list[Any] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": pergunta},
    ]

    max_turnos = 6

    for turno in range(1, max_turnos + 1):
        _log(f"--- Turno {turno}/{max_turnos}: chamando Responses API ---")

        response = client.responses.create(
            model="gpt-5.2",
            input=input_items,
            tools=TOOLS,
            tool_choice="auto",
        )

        # Log “resumo” do retorno
        _log(f"Response status={getattr(response, 'status', None)} id={getattr(response, 'id', None)}")
        _log(f"Output_text(len)={len(getattr(response, 'output_text', '') or '')}")

        # IMPORTANTÍSSIMO: manter histórico do que o modelo retornou
        if getattr(response, "output", None):
            input_items += response.output

        # Verifica tool calls
        tool_calls = []
        for idx, item in enumerate(getattr(response, "output", []) or []):
            _log(f"[output#{idx}] type={getattr(item, 'type', None)}")
            if getattr(item, "type", None) == "function_call":
                tool_calls.append(item)

        # Se não tem tool call, é a resposta final
        if not tool_calls:
            final = (getattr(response, "output_text", None) or "").strip()
            if final:
                _log("Resposta final em linguagem natural gerada (sem tool calls).")
                return final

            # fallback: tenta coletar mensagem manualmente
            _log("[WARN] Sem tool calls, mas output_text vazio. Tentando extrair manualmente...")
            textos = []
            for item in getattr(response, "output", []) or []:
                if getattr(item, "type", None) == "message":
                    for c in getattr(item, "content", []) or []:
                        if getattr(c, "type", None) in ("output_text", "text"):
                            textos.append(getattr(c, "text", "") or "")
            final2 = "\n".join([t for t in textos if t]).strip()
            return final2 or "Não foi possível interpretar a resposta do modelo."

        # Executa cada tool call e devolve output para o modelo
        _log(f"{len(tool_calls)} tool call(s) detectada(s). Executando...")

        for call in tool_calls:
            nome = getattr(call, "name", "")
            raw_args = getattr(call, "arguments", "") or ""
            call_id = getattr(call, "call_id", None)

            _log(f"Tool call → name={nome} call_id={call_id}")
            _log(f"Tool args(raw)={raw_args}")

            try:
                args = json.loads(raw_args) if raw_args else {}
            except Exception:
                args = {}

            _log(f"Tool args(parsed)={args}")

            try:
                result = _executar_tool(nome, args)
            except Exception as e:
                _log(f"[ERRO] Falha executando tool '{nome}': {e}")
                result = {"erro": f"Falha executando tool '{nome}': {str(e)}"}

            result_json = _safe_json_dumps(result)
            _log(f"Tool result(len)={len(result_json)}")

            # Devolve o output pro modelo (continua o loop)
            input_items.append(
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": result_json,
                }
            )

    return "Não foi possível completar a solicitação (muitas iterações de ferramenta)."
