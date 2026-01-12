# 🧱 BACKLOG — MVP Conversacional IPDO (Revisado)

## Objetivo do MVP

Permitir que o usuário pergunte em **linguagem natural** sobre os dados do IPDO já carregados no SQLite e receba respostas **consistentes, curtas e legíveis**, sem inventar nada.

## Escopo

* Somente leitura
* Banco SQLite já populado (via extração)
* CLI local para teste
* Sem autenticação / sem segurança
* Sem dashboard
* Sem consulta a PDFs

---

# ✅ Definição de Pronto Global (DoD)

Um item está pronto quando:

* Passa em teste manual (passo a passo documentado no item)
* Não expõe JSON cru ao usuário final (a menos que explicitamente solicitado em modo debug)
* Não inventa dados fora do banco
* Logs não poluem a resposta do usuário (logs só em debug)
* Erros são amigáveis e padronizados

---

# 🔷 EPIC 1 — Qualidade dos Dados Persistidos (pós-ajuste de prompts)

> Justificativa: se o banco estiver “inconsistente” com o que o agente precisa responder (ex.: rótulos, campos faltando), o agente vira um gerador de confusão.

## US01 — Validar compatibilidade do prompt “Operação” com os dados reais

**Justificativa:** seu banco já contém submercados fora dos 4 clássicos (ex.: Sudeste/Centro-Oeste, Sistema Isolado). O prompt ajustado deve preservar nomes.

**Atividades**

1. Processar 1–3 PDFs representativos após ajuste do prompt
2. Conferir se `destaques_operacao.submercado` preserva o texto do relatório (sem normalização indevida)
3. Conferir que `restricoes` vem como lista (nunca `null`), mesmo vazia
4. Conferir que `transferencia_energia` sempre contém chaves esperadas (origem/destino/status/descricao), com `null` quando aplicável

**Definição de pronto**

* Para pelo menos 3 datas, o banco contém `destaques_operacao` com estrutura consistente
* Nenhum submercado foi “forçado” para valores inválidos
* Não há crash no pipeline de extração/repositório

---

## US02 — Validar compatibilidade do prompt “Térmica” com o banco e ordenação

**Justificativa:** query/API ordena por desvio; o prompt precisa produzir algo ordenável/consistente (mesmo que seja “status” e não MW).

**Atividades**

1. Processar 1–3 PDFs com térmicas presentes
2. Conferir que cada registro tem:

   * `unidade_geradora` preenchido
   * `desvio` coerente com o modelo (texto/enum conforme prompt atual)
   * `descricao` preenchida
3. Rodar query de térmica e validar ordenação “estável” (mesmo que não numérica), e validar que `LIMIT` funciona

**Definição de pronto**

* Banco contém registros térmicos com estrutura consistente em 3 datas
* Query de térmica não quebra e retorna lista vazia quando não há registros

> Nota: se “desvio” permanecer textual, você aceita uma ordenação imperfeita. Se isso for problema, vira “fase 2” (migração para desvio numérico).

---

# 🔷 EPIC 2 — Camada de Consulta (Queries/Tools) orientada a intenção

> Justificativa: “operação do tipo eólica” é intenção de filtro; sem tools específicas, o agente sempre devolve o pacotão.

## US03 — Criar query “buscar_geracao” como ferramenta do agente

**Justificativa:** suporta perguntas por tipo/submercado e evita despejar JSON gigante.

**Atividades**

1. Expor `queries/geracao.buscar_geracao()` no `agent_ipdo/tools.py` como `tool_buscar_geracao`
2. Definir assinatura:

   * `data: str` obrigatório
   * `submercado: Optional[str]`
   * `tipo: Optional[str]`
3. Garantir normalização mínima do tipo:

   * mapear “solar fotovoltaica” ↔ “Solar” (compatível com o que está persistido)
4. Retornar lista (pode ser vazia)

**Definição de pronto**

* Perguntas como “geração eólica no NE em 2025-07-22” acionam a tool e retornam dados corretos do banco
* Sem erro com filtros vazios

---

## US04 — Criar query “buscar_restricoes” (filtro textual em restrições)

**Justificativa:** perguntas “teve restrição eólica?” não são só geração; restrições estão em outra coluna (`restricoes` JSON).

**Atividades**

1. Criar `queries/restricoes.py` com função:

   * `buscar_restricoes(data: str, termo: Optional[str] = None, submercado: Optional[str] = None)`
2. Implementar:

   * carregar `destaques_operacao.restricoes` (json)
   * filtrar por `termo` (case-insensitive substring) quando fornecido
   * filtrar por `submercado` quando fornecido
3. Expor em `agent_ipdo/tools.py` como `tool_buscar_restricoes`

**Definição de pronto**

* Perguntas como “houve restrição eólica em 2025-07-22?” retornam apenas as linhas relevantes
* Se não houver, retorna lista vazia (sem exceção)

---

## US05 — Criar “buscar_operacao_resumo” (compactação server-side opcional)

**Justificativa:** mesmo com resposta natural, às vezes você quer limitar payload e garantir previsibilidade.

**Atividades**

1. Criar função query que retorne apenas:

   * por submercado: carga.status, transferencia.status, geração (tipo->status)
2. Expor como tool opcional

**Definição de pronto**

* Para perguntas “como estava o sistema no dia X?”, retorno é compacto e consistente

---

# 🔷 EPIC 3 — Agente Conversacional (tool loop + resposta natural)

> Justificativa: hoje seu `agent.py` devolve JSON do banco porque não executa “tool output → resposta final”.

## US06 — Implementar loop correto de tool-calling (Responses API)

**Justificativa:** sem isso, o modelo não recebe o resultado da tool e você só consegue “printar” o retorno bruto.

**Atividades**

1. Refatorar `agent_ipdo/agent.py` para:

   * chamar `client.responses.create(...)`
   * detectar `function_call`
   * executar tool local
   * enviar `function_call_output` com `call_id`
   * repetir até vir `message/output_text`
2. Limitar iterações (ex.: max 3) para evitar loop infinito

**Definição de pronto**

* Após uma tool call, o agente retorna uma resposta em PT-BR natural e curta
* Não retorna JSON bruto por padrão

---

## US07 — Registrar tools com schema correto (required / optional)

**Justificativa:** no seu dump apareceu `buscar_termica` com `limite` requerido em runtime — isso quebra a tool.

**Atividades**

1. Revisar `TOOLS` em `agent.py`:

   * `limite` deve ser opcional (não estar em required)
   * `buscar_geracao` deve ter required apenas `data`
   * `buscar_restricoes` required apenas `data`
2. Adicionar descrições claras e exemplos curtos (na description) para orientar o modelo

**Definição de pronto**

* Modelo chama tools sem erro de schema
* `buscar_termica` funciona com e sem limite

---

## US08 — Resolver datas relativas com [AGORA] no código (guardrail)

**Justificativa:** hoje você “confia” no system_prompt para resolver hoje/ontem, mas é frágil e gera tool calls com data errada.

**Atividades**

1. Implementar parser leve em Python:

   * extrair `[AGORA=...]` do input
   * substituir “hoje/ontem/anteontem” na pergunta por data absoluta
   * detectar datas DD/MM/YYYY e converter
2. Rodar antes de enviar ao modelo

**Definição de pronto**

* “ontem” sempre vira YYYY-MM-DD correto antes do modelo decidir tool
* Modelo para de errar datas por interpretação

---

## US09 — Resposta natural padronizada (templates)

**Justificativa:** consistência e leitura rápida.

**Atividades**

1. Definir padrões de saída por intenção:

   * listar datas: “Tenho dados para: …”
   * operação: bullets por submercado (carga, intercâmbio, geração)
   * geração (filtro): listar só os itens filtrados
   * restrições: listar restrições encontradas
   * térmica: listar top N (ou tudo)
2. Implementar “modo compacto” padrão e “modo detalhado” quando usuário pedir

**Definição de pronto**

* Respostas seguem um estilo consistente e não despejam estrutura interna
* Listas grandes são resumidas automaticamente

---

## US10 — Tratamento de ausência de dados (mensagens oficiais)

**Justificativa:** evita “parece bug” quando o banco está vazio.

**Atividades**

1. Padronizar 3 mensagens:

   * sem registro: “Não há registros no banco para essa consulta.”
   * intenção fora das tools: “Essa informação não está disponível nas ferramentas atuais.”
   * data ausente: “Informe uma data (YYYY-MM-DD) para eu consultar.”
2. Garantir que o código retorna isso antes de tentar tool com parâmetro faltando

**Definição de pronto**

* Para qualquer caso de erro comum, a resposta é amigável e consistente

---

# 🔷 EPIC 4 — Observabilidade e Operação (logs sem poluir usuário)

> Justificativa: você precisa debugar tool calls, mas o usuário não pode ver “dump gigante”.

## US11 — Logging controlado por DEBUG

**Justificativa:** separar log técnico de resposta do usuário.

**Atividades**

1. Adicionar `DEBUG=1` no `.env` (opcional)
2. `agent.py` usa `utils.logger.log()` apenas se `DEBUG`
3. Remover prints diretos de objetos gigantes (ou truncar)

**Definição de pronto**

* Em produção local (DEBUG=0), nenhuma linha de log aparece para o usuário
* Em debug, logs mostram tool chamada, args, tamanho do retorno, e iteração do loop

---

# 🔷 EPIC 5 — Documentação e Testes Manuais

> Justificativa: MVP só é “usável” se qualquer dev conseguir rodar.

## US12 — README mínimo com comandos copy/paste

**Justificativa:** reduz suporte e acelera onboarding.

**Atividades**

1. Criar `README.md` com:

   * pré-requisitos
   * venv + deps
   * como colocar PDFs
   * como rodar extração (`python main.py`)
   * como rodar CLI (`python -m agent_ipdo.cli` ou `python agent_ipdo/cli.py`)
   * como rodar API (`uvicorn api.main:app --reload`)
2. Adicionar exemplo de perguntas

**Definição de pronto**

* Um colega roda do zero seguindo README sem pedir ajuda

---

## US13 — Roteiro de testes manuais (smoke tests)

**Justificativa:** você valida rápido regressões.

**Atividades**

1. Criar checklist de 10 perguntas:

   * datas
   * operação por data
   * térmica por data
   * térmica top N
   * geração por tipo
   * geração por submercado+tipo
   * restrições por termo
   * hoje/ontem/anteontem
2. Definir saída esperada (não exata, mas estrutura)

**Definição de pronto**

* Checklist executado sem falhas após cada ajuste no agente

---

# Ajustes necessários no seu backlog antigo (mudanças de requisito)

* Trocar US06: de “Retornar JSON estruturado apenas” → para **“Retornar resposta natural baseada nas tools”**
* Manter JSON somente como:

  * modo debug, ou
  * ferramenta auxiliar, ou
  * endpoint da API

---

Se você quiser, eu também posso transformar isso em **formato Jira** (Epic → Story → Tasks → Acceptance Criteria) ou em **Kanban pronto** com “Prioridade / Estimativa / Dependências”.
