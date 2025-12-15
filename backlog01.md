Abaixo está um **backlog de MVP em FastAPI** para expor os dados do seu SQLite (IPDO), com **histórias descritivas, tarefas técnicas, boas práticas** e **Definition of Done** por item. Vou partir da **estrutura atual do banco**:

* `destaques_operacao` (por `data` + `submercado`)
* `destaques_geracao` (por `data` + `submercado` + `tipo_geracao`)
* `destaques_geracao_termica` (por `data` + `unidade_geradora` + `descricao`)

E dos acessos principais que um usuário tende a pedir no MVP:

* “Quais dias existem?”
* “Me dê o resumo do dia X”
* “Me dê os detalhes do submercado Y no dia X”
* “Quais foram os desvios térmicos no período?”
* “Quero filtrar por usina térmica”
* “Me dê a evolução por tipo de geração em um período”
* “Exporta em JSON (e opcionalmente CSV)”

> Escopo MVP: **sem preocupação com performance, auth, rate limit, paginação avançada, caching**. Mas com estrutura limpa, validação mínima e respostas previsíveis.

---

# Backlog MVP — FastAPI para consulta do IPDO (SQLite)

## EP01 — Base do Projeto e Infra de API

### US01 — Criar projeto FastAPI com estrutura modular

**Descrição:** Como desenvolvedor, quero uma estrutura de pastas clara para crescer a API sem virar “main.py gigante”.

**Sugestão de estrutura:**

```
api/
  main.py
  deps.py
  db.py
  routers/
    health.py
    dates.py
    operacao.py
    geracao.py
    termica.py
  schemas/
    operacao.py
    geracao.py
    termica.py
    common.py
```

**Tarefas:**

* Criar `api/main.py` com FastAPI e inclusão de routers
* Criar `api/db.py` com conexão SQLite (simples)
* Criar `api/deps.py` para dependency `get_db()`
* Configurar CORS aberto (MVP)
* Adicionar `uvicorn` no requirements (se ainda não tiver)

**Boas práticas:**

* Routers separados por domínio
* Prefixos e tags por router
* Response models (Pydantic) para contrato estável

**Definition of Done:**

* `uvicorn api.main:app --reload` sobe a API
* `/docs` acessível
* Projeto organizado em módulos/routers

---

### US02 — Endpoint de healthcheck e info do banco

**Descrição:** Como usuário, quero saber se a API está no ar e qual a última data disponível no banco.

**Endpoint(s):**

* `GET /health`

  * Retorna: `status`, `db_path`, `dias_no_banco`, `ultima_data`

**Tarefas:**

* Implementar consulta `COUNT(DISTINCT data)` e `MAX(data)` na tabela `destaques_operacao` (fonte principal de dias processados)
* Model Pydantic `HealthResponse`

**DoD:**

* `/health` retorna JSON válido com campos esperados
* Se banco vazio, retorna `dias_no_banco=0` e `ultima_data=null`

---

## EP02 — Navegação por Datas e Resumos

### US03 — Listar datas disponíveis

**Descrição:** Como usuário, quero listar as datas existentes para navegar pelos relatórios.

**Endpoint:**

* `GET /dates`

  * Query opcional: `limit` (default 30), `offset` (default 0)
  * Retorna lista de datas em ordem desc

**Tarefas:**

* Query: `SELECT DISTINCT data FROM destaques_operacao ORDER BY data DESC LIMIT ? OFFSET ?`
* Schema `DatesResponse`

**DoD:**

* Retorna lista consistente
* Parâmetros opcionais funcionando

---

### US04 — Obter “visão geral do dia”

**Descrição:** Como usuário, quero um resumo agregado do dia (submercados, carga, intercâmbio, geração e térmica) em uma resposta única.

**Endpoint:**

* `GET /days/{date}/overview`

**Retorno sugerido (MVP):**

```json
{
  "data": "2025-05-10",
  "submercados": [
    {
      "submercado": "Sul",
      "carga": {...},
      "transferencia_energia": {...},
      "restricoes": [...],
      "geracao": [...]
    }
  ],
  "termica": [
    { "unidade_geradora": "...", "desvio": "...", "descricao": "..." }
  ]
}
```

**Tarefas:**

* Buscar `destaques_operacao` por data
* Buscar `destaques_geracao` por data e agrupar por submercado
* Buscar `destaques_geracao_termica` por data
* Deserializar `restricoes` (JSON string) em lista
* Unir num schema único `DayOverviewResponse`

**DoD:**

* Retorna overview completo para uma data existente
* Para data inexistente: HTTP 404 com mensagem clara
* `restricoes` retorna como lista (não string JSON)

---

## EP03 — Operação (carga, restrições, intercâmbio)

### US05 — Consultar operação por data e submercado

**Descrição:** Como usuário, quero pegar apenas o recorte de “Destaques da Operação” para um submercado específico.

**Endpoint:**

* `GET /operacao`

  * Query obrigatória: `date`
  * Query opcional: `submercado` (se omitido retorna todos do dia)

**Tarefas:**

* Query base por data, filtro opcional por submercado
* Retornar `restricoes` como lista
* Schema `OperacaoItem`, `OperacaoResponse`

**DoD:**

* Funciona com e sem `submercado`
* Retorna 404 se data não existe
* Resposta segue contrato Pydantic

---

### US06 — Listar submercados disponíveis em uma data

**Descrição:** Como usuário, quero saber quais submercados têm registro em um dia.

**Endpoint:**

* `GET /days/{date}/submercados`

**Tarefas:**

* Query: `SELECT submercado FROM destaques_operacao WHERE data = ? ORDER BY submercado`

**DoD:**

* Retorna lista de submercados do dia
* 404 se dia inexistente

---

## EP04 — Geração (hidráulica/térmica/eólica/solar/nuclear)

### US07 — Consultar geração por data

**Descrição:** Como usuário, quero consultar a geração por tipo e submercado em um dia.

**Endpoint:**

* `GET /geracao`

  * Query obrigatória: `date`
  * Query opcional: `submercado`, `tipo`

**Tarefas:**

* Query com filtros opcionais
* Schema `GeracaoRow`, `GeracaoResponse`

**DoD:**

* Filtra corretamente
* Retorna lista ordenada (por submercado, tipo)
* 404 se data inexistente

---

### US08 — Série histórica de geração (período)

**Descrição:** Como usuário, quero ver a evolução dos status/descrições por tipo de geração em um período.

**Endpoint:**

* `GET /geracao/series`

  * Query obrigatória: `start_date`, `end_date`
  * Query opcional: `submercado`, `tipo`

**Retorno MVP:**

* Lista de linhas (sem agregação complexa), ex:

```json
[
  {"data":"2025-05-10","submercado":"Sul","tipo_geracao":"Hidráulica","status":"Inferior","descricao":"..."}
]
```

**Tarefas:**

* Query BETWEEN em `data`
* Ordenar por `data ASC`

**DoD:**

* Intervalo funciona
* Retorno ordenado
* Validação simples: `start_date <= end_date` (senão 400)

---

## EP05 — Térmica (desvios por unidade)

### US09 — Consultar destaques térmicos por data

**Descrição:** Como usuário, quero listar os desvios térmicos de um dia.

**Endpoint:**

* `GET /termica`

  * Query obrigatória: `date`
  * Query opcional: `desvio` (Acima/Abaixo/Sem)

**Tarefas:**

* Query por data e filtro opcional por desvio
* Schema `TermicaItem`, `TermicaResponse`

**DoD:**

* Retorna lista do dia
* Filtro por desvio funciona
* 404 se data inexistente

---

### US10 — Buscar térmicas por unidade geradora (contains)

**Descrição:** Como usuário, quero buscar por nome de usina (ex: “Angra”) e ver em quais datas ela apareceu.

**Endpoint:**

* `GET /termica/search`

  * Query obrigatória: `q` (texto)
  * Query opcional: `start_date`, `end_date`

**Tarefas:**

* Query: `WHERE unidade_geradora LIKE ?`
* Se intervalo informado, aplicar BETWEEN
* Retornar linhas com data + unidade + desvio + descrição

**DoD:**

* Busca funciona com LIKE
* Retorna datas onde apareceu
* Se nada encontrado, retorna lista vazia (200)

---

## EP06 — Export e Usabilidade (MVP)

### US11 — Export simples em CSV (opcional, mas útil)

**Descrição:** Como usuário, quero exportar os resultados em CSV para análise rápida.

**Endpoint(s):**

* `GET /export/operacao.csv?date=...`
* `GET /export/geracao.csv?date=...`
* `GET /export/termica.csv?date=...`

**Tarefas:**

* Gerar CSV na resposta (streaming opcional; no MVP pode ser string)
* `Content-Type: text/csv`

**DoD:**

* CSV baixa corretamente
* Cabeçalho com nomes de colunas
* Respeita filtros básicos

---

### US12 — Padronizar erros e mensagens (DX/UX)

**Descrição:** Como usuário, quero erros previsíveis (404 para inexistente, 400 para parâmetro inválido).

**Tarefas:**

* Criar helpers de erro (`HTTPException`)
* Centralizar validações de data (regex simples `YYYY-MM-DD`)

**DoD:**

* Mensagens de erro consistentes
* Sem tracebacks expostos no response

---

## EP07 — Qualidade mínima e documentação

### US13 — Documentar endpoints no README e exemplos de uso

**Descrição:** Como usuário, quero exemplos de curl e payloads de resposta.

**Tarefas:**

* Atualizar README: como rodar API, exemplos `/days/{date}/overview`, `/termica/search`
* Inserir exemplos de resposta

**DoD:**

* README contém passos + exemplos
* `/docs` mostra tags e descrições básicas

---

### US14 — Testes básicos de API (smoke tests)

**Descrição:** Como dev, quero testes mínimos garantindo que endpoints principais estão OK.

**Tarefas:**

* Adicionar `pytest` + `httpx` (TestClient)
* Testar: `/health`, `/dates`, `/days/{date}/overview` (com banco de teste ou banco real pequeno)

**DoD:**

* `pytest` passa com pelo menos 3 testes
* Testes rodam localmente

---

# Principais contratos (schemas) recomendados

Para o MVP, vale garantir que:

* `restricoes` seja sempre `list`
* `transferencia_energia` sempre exista com defaults
* `geracao` sempre seja `list`

Isso evita que o front ou outro consumidor quebre.

---

# Sequência recomendada de implementação (ordem ótima de entrega)

1. **US01, US02** (API sobe e health)
2. **US03** (lista datas)
3. **US04** (overview do dia — maior valor)
4. **US05/US07/US09** (consultas por domínio)
5. **US10** (busca por unidade térmica)
6. **US08** (série por período)
7. **US11** (export CSV)
8. **US12/US13/US14** (polimento e qualidade mínima)

---

Se você quiser, eu já posso entregar o **código do MVP inteiro (FastAPI)** com essa estrutura e endpoints (pronto pra rodar), usando **sqlite3 puro** (mais simples) ou **SQLAlchemy** (mais “padrão”). Para MVP, eu recomendo **sqlite3 puro** pra ser rápido e direto.
