# 🧱 BACKLOG — Pendências MVP Conversacional IPDO

## 🎯 Objetivo

Fechar as lacunas restantes para o MVP funcionar de ponta a ponta com os **prompts ajustados** (principalmente Térmica), com **robustez mínima**, **logs controlados** e **documentação/teste**.

---

## 🔥 EPIC 0 — Bloqueadores de compatibilidade (DADOS ↔ BANCO ↔ API ↔ AGENTE)

### US-P0-01 — Adequar modelo “Térmica” ao novo prompt (desvio_mw/desvio_status) - ok

**Justificativa**: hoje o pipeline espera `desvio` e a tabela tem `desvio TEXT NOT NULL`; com o prompt novo vai quebrar e/ou ordenar errado.
**Atividades**

1. **Definir contrato alvo** para térmica no banco (colunas e tipos):

   * `desvio_mw REAL NULL`
   * `desvio_status TEXT NOT NULL` (Acima/Abaixo/Sem desvio)
   * manter `descricao TEXT NOT NULL`, `unidade_geradora TEXT NOT NULL`
2. Criar **migração simples** (script) para atualizar schema:

   * `ALTER TABLE` (ou recriar tabela e copiar dados, se necessário)
3. Ajustar `database/init_db.py` para criar tabela no novo padrão.
4. Ajustar `database/repository.py` (`salvar_destaques_termica`) para ler:

   * `i.get("desvio_mw")`
   * `i["desvio_status"]`
5. Ajustar `queries/termica.py`:

   * ordenar por **desvio_mw DESC NULLS LAST** (em SQLite: `ORDER BY (desvio_mw IS NULL), desvio_mw DESC`)
   * permitir filtro opcional por `desvio_status` (opcional, se você quiser já fechar filtro de agente)
6. Ajustar `api/routers/termica.py` para retornar os novos campos e ordenar corretamente.
7. Ajustar `agent_ipdo/agent.py` tool `buscar_termica` para refletir o novo contrato (campos, filtros).
   **Definição de pronto**

* Rodar extração com prompt novo **não quebra** e salva registros térmicos.
* `/termica/{data}` retorna `unidade_geradora`, `desvio_mw`, `desvio_status`, `descricao`.
* Consulta térmica ordena corretamente (maiores desvios primeiro; null por último).
* Agente consegue responder “top desvios térmicos” com consistência.

---

## 🧠 EPIC 1 — Robustez de interpretação de data (não depender só do prompt)

### US-P1-01 — Implementar parser de data no código do agente (absoluta e relativa)

**Justificativa**: hoje o comportamento depende do LLM seguir o prompt; um parser reduz erro e tool calls inválidas.
**Atividades**

1. Criar util `agent_ipdo/date_utils.py` com funções:

   * `parse_agora(marker: str) -> datetime`
   * `resolve_relative_date(text: str, agora: datetime) -> Optional[str]` (hoje/ontem/anteontem)
   * `normalize_date_formats(text: str) -> Optional[str]` (DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD)
2. No `responder_pergunta()`, extrair `[AGORA=...]` e disponibilizar `agora_date`.
3. Pré-processar a pergunta para:

   * injetar data resolvida (quando for inequívoco)
   * ou guardar a data resolvida em variável para tool args (quando o modelo pedir)
4. Adicionar log quando ocorrer conversão (“ontem → 2026-01-07”).
   **Definição de pronto**

* Perguntas com “hoje/ontem/anteontem” resultam em tool calls com `data=YYYY-MM-DD`.
* Perguntas com DD/MM/YYYY ou DD-MM-YYYY são normalizadas.
* Se não der para resolver, agente pede data (sem chamar tool com data vazia).

---

## 🧰 EPIC 2 — Ferramentas e cobertura de consulta (o que falta para “consultas comuns”)

### US-P2-01 — Expor e documentar tool `buscar_restricoes` no system_prompt - ok

**Justificativa**: tool existe, mas o modelo não foi instruído explicitamente a usá-la; reduz acerto de intenção.
**Atividades**

1. Atualizar `agent_ipdo/system_prompt.txt`:

   * incluir `buscar_restricoes(data, submercado?, termo?, limite?)`
   * exemplos de quando usar (“restrições”, “limitações”, “corte”, “indisponibilidade”, “restrição elétrica”)
2. Incluir política de resposta para restrições (listar itens + oferecer filtros).
   **Definição de pronto**

* Perguntas “quais restrições no NE ontem?” acionam `buscar_restricoes`.
* Se não houver restrições, resposta padronizada (“Não há registros…”).

---

### US-P2-02 — Criar tool “operacao_resumo” (compacta server-side) - ok

**Justificativa**: reduz custo/ruído e dá previsibilidade; evita o LLM ter que resumir listas grandes “na unha”.
**Atividades**

1. Criar `queries/operacao_resumo.py` (ou função em `queries/operacao.py`) que retorne:

   * por submercado: carga_status, transferencia_status e contagem de restrições, lista curta de geração com status
2. Registrar tool `buscar_operacao_resumo(data, submercado?, limite_itens?)`
3. Adicionar no `system_prompt.txt` quando preferir resumo vs detalhado.
   **Definição de pronto**

* Perguntas “como estava o sistema no dia X?” usam resumo por padrão.
* O usuário pode pedir “detalhe completo” e aí usar `buscar_operacao`.

---

## 🧾 EPIC 3 — Padronização de respostas e erros (determinismo mínimo)

### US-P3-01 — Padronizar respostas “sem dados” e “intenção não suportada”

**Justificativa**: hoje depende do LLM; queremos consistência mínima.
**Atividades**

1. Criar `agent_ipdo/response_templates.py` com funções:

   * `msg_sem_dados(contexto: str) -> str`
   * `msg_nao_disponivel() -> str`
   * `msg_pedir_data() -> str`
2. No loop do agente:

   * se tool retornar `{"erro": ...}` → responder com template apropriado
   * se tool retornar lista vazia → responder com template “sem dados”
3. Garantir que não vaze stack trace para usuário (somente log).
   **Definição de pronto**

* Casos sem dados sempre retornam exatamente “Não há registros no banco para essa consulta.”
* Casos não suportados retornam exatamente “Essa informação não está disponível nas ferramentas atuais.”
* Erros internos não aparecem no texto final ao usuário.

---

## 📈 EPIC 4 — Observabilidade (logs úteis sem poluir)

### US-P4-01 — Adicionar flag DEBUG para logs do agente

**Justificativa**: hoje o agente imprime tudo sempre; em uso normal isso atrapalha.
**Atividades**

1. Criar config via env: `AGENT_DEBUG=true/false`
2. Ajustar `_log()` para respeitar debug (ou níveis: INFO/DEBUG).
3. Logar sempre apenas:

   * tool escolhida
   * data resolvida
   * contagem de itens retornados
     (detalhes completos só em DEBUG)
     **Definição de pronto**

* Em modo normal, logs são curtos e operacionais.
* Em DEBUG, logs atuais continuam disponíveis.

---

### US-P4-02 — Remover/evitar duplicidade de tools (`agent_ipdo/tools.py`)

**Justificativa**: arquivo está desatualizado e pode confundir manutenção.
**Atividades**

1. Escolher padrão:

   * (A) remover `agent_ipdo/tools.py` e centralizar no `agent.py`, ou
   * (B) mover tools para `tools.py` e importar no `agent.py`
2. Atualizar imports e garantir que a versão “oficial” tenha todas as tools.
   **Definição de pronto**

* Existe **um único** lugar “fonte da verdade” para tools.
* Nenhum arquivo obsoleto sugere ferramenta incompleta.

---

## 📚 EPIC 5 — Documentação e testes mínimos

### US-P5-01 — Criar README.md mínimo (execução local)

**Justificativa**: reduz dependência do autor e facilita repasse para time.
**Atividades**

1. Incluir requisitos (Python, venv, deps)
2. Como rodar:

   * extração `python main.py`
   * ver banco `python ver_banco.py`
   * API `uvicorn api.main:app --reload`
   * CLI `python -m agent_ipdo.cli`
3. Variáveis de ambiente relevantes (`OPENAI_API_KEY`, `AGENT_DEBUG`, modelo)
   **Definição de pronto**

* Um dev novo consegue rodar extração, API e CLI só com o README.

---

### US-P5-02 — Smoke tests manuais (roteiro) + dados de exemplo

**Justificativa**: garante regressão mínima e valida o “MVP entregue”.
**Atividades**

1. Criar `tests/SMOKE_TESTS.md` com checklist:

   * listar datas
   * operação por data
   * térmica por data
   * geração por data + filtro
   * restrições por termo
2. Definir perguntas padrão com `[AGORA=...]` e o resultado esperado (em termos de “não vazio / vazio / mensagem padrão”).
   **Definição de pronto**

* Qualquer pessoa executa o roteiro e valida o MVP em 10–15 minutos.
* Casos sem dados e casos com dados estão cobertos.

---

# ✅ Ordem recomendada de execução

1. **US-P0-01 (Térmica — bloqueador)**
2. **US-P1-01 (parser de data)**
3. **US-P3-01 (mensagens padrão)**
4. **US-P4-01 (DEBUG logs)**
5. **US-P2-01 + US-P2-02 (tools e cobertura)**
6. **US-P5-01 + US-P5-02 (docs e smoke tests)**
7. **US-P4-02 (limpeza/organização tools)**

Se você quiser, eu também posso converter isso em **issues estilo GitHub/Jira** (com labels, prioridade, estimativa e critérios de aceite) sem mudar o conteúdo.
