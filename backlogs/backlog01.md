# 🧱 BACKLOG — PRÓXIMA ETAPA DO IPDO (PÓS-MVP)

## Visão da Próxima Etapa

Transformar o MVP atual em um **serviço consultável**, permitindo que:

1. Usuários consultem os dados via **API HTTP**
2. Um **Agente Inteligente** responda perguntas em linguagem natural usando o banco SQLite como fonte de verdade

⚠️ **Premissas importantes**:

* Sistema continuará **interno**
* Não haverá autenticação nesta fase
* Performance e segurança avançada ficam fora do escopo
* Clareza > abstração excessiva

---

# 🔷 ÉPICO 1 — API de Consulta com FastAPI

## Objetivo do Épico

Disponibilizar os dados extraídos do IPDO por meio de **endpoints REST simples**, permitindo consultas diretas por data, submercado, tipo de geração e destaques térmicos.

---

## 🎯 Perguntas principais do usuário (input para design da API)

Essas perguntas **definem os endpoints**, não o contrário:

1. **“O que aconteceu no sistema ontem?”**
2. **“Quais foram os destaques da operação em um dia específico?”**
3. **“Como foi a geração por submercado?”**
4. **“Houve problemas térmicos? Onde?”**
5. **“Quais usinas térmicas tiveram maior desvio?”**
6. **“Comparando dois dias, o que mudou?”** *(futuro)*

Essas perguntas guiam toda a API.

---

## US01 — Criar base da API FastAPI - ok

### Descrição

Como desenvolvedor, quero criar uma API FastAPI com estrutura modular para expor os dados do IPDO sem acoplar lógica de negócio ao `main.py`.

### Tarefas

* Criar pasta `api/`
* Criar `api/main.py`
* Configurar FastAPI
* Adicionar CORS aberto (MVP)
* Criar health-check `/health`

### Definition of Done (DoD)

* API sobe com `uvicorn api.main:app`
* Endpoint `/health` retorna `{ "status": "ok" }`
* Nenhuma lógica de extração é duplicada

---

## US02 — Endpoint: Listar datas disponíveis

### Descrição

Como usuário, quero saber quais datas existem no banco para poder consultar os relatórios disponíveis.

### Endpoint

```
GET /datas
```

### Retorno esperado

```json
{
  "datas": ["2025-05-10", "2025-05-11"]
}
```

### DoD

* Consulta vem do SQLite
* Datas ordenadas desc
* Retorno JSON simples

---

## US03 — Endpoint: Destaques da Operação por data - ok

### Endpoint

```
GET /operacao/{data}
```

### Comportamento

* Retorna todos os submercados daquele dia
* Inclui carga, restrições, intercâmbio e geração

### DoD

* Data inválida retorna 404
* Estrutura JSON consistente com o MVP
* Sem lógica de GPT aqui (somente leitura)

---

## US04 — Endpoint: Geração por tipo e submercado - ok

### Endpoint

```
GET /geracao
```

### Parâmetros

* `data` (obrigatório)
* `submercado` (opcional)
* `tipo` (opcional)

### DoD

* Filtros combináveis
* Consulta simples SQL
* Resposta clara e previsível

---

## US05 — Endpoint: Destaques de Geração Térmica - ok

### Endpoint

```
GET /termica/{data}
```

### DoD

* Lista todas as ocorrências térmicas do dia
* Ordenação por desvio
* Retorna lista vazia se não houver dados

---

## US06 — Documentação automática da API - ok

### Descrição

Como desenvolvedor, quero visualizar e testar os endpoints via Swagger.

### DoD

* Swagger disponível em `/docs`
* Todos endpoints documentados automaticamente
* Exemplos simples nos schemas

---

# 🔷 ÉPICO 2 — Agente Inteligente para Consulta ao Banco

## Objetivo do Épico

Permitir que usuários façam **perguntas em linguagem natural**, como:

> “Teve algum problema térmico no Nordeste ontem?”

E o sistema responda usando **dados reais do banco**, sem improvisação.

---

## ⚠️ Decisão Arquitetural Importante (respondendo sua pergunta)

### ❓ O agente PRECISA chamar a API?

**Resposta curta e sênior:**
👉 **NÃO, nesta fase.**

### Decisão recomendada

| Opção                   | Quando usar                          |
| ----------------------- | ------------------------------------ |
| Acesso direto ao SQLite | **Agora (MVP+)**                     |
| API HTTP                | Quando houver múltiplos consumidores |
| API + Auth              | Quando houver usuários externos      |

👉 Como o agente **roda no mesmo projeto**, o melhor caminho agora é:

> **Agente → repositório → SQLite**

Isso reduz:

* latência
* complexidade
* duplicação de lógica

A API serve para **humanos e sistemas externos**, não para uso interno obrigatório.

---

## US07 — Criar camada de consulta semântica (read-only) - ok

### Descrição

Criar funções Python que traduzem **intenção de consulta** em SQL.

Exemplos:

* `buscar_destaques_operacao(data)`
* `buscar_termica_por_desvio(data, limite)`
* `listar_datas()`

### DoD

* Funções isoladas
* Nenhum SQL dentro do agente
* Testes unitários simples

---

## US08 — Criar Agente com Agent SDK (Query Agent)

### Descrição

Como usuário, quero fazer perguntas em linguagem natural sobre o IPDO e receber respostas baseadas nos dados reais do banco.

### Papel do Agente

* NÃO inventa dados
* NÃO chama GPT para interpretar PDFs
* Apenas:

  1. interpreta a pergunta
  2. decide qual função chamar
  3. formata a resposta

### DoD

* Agente responde corretamente perguntas simples
* Usa funções internas
* Não acessa GPT para “imaginar” respostas

---

## US09 — Prompt de Sistema do Agente (governança)

### Descrição

Criar um prompt claro dizendo ao agente:

* ele só pode responder com base no banco
* se não houver dados, deve dizer isso
* não deve inferir causas técnicas

### DoD

* Prompt versionado
* Linguagem clara
* Sem improvisação narrativa

---

## US10 — Interface simples de teste do Agente

### Opções (escolher uma):

* CLI (`python agente.py`)
* Endpoint `/ask`
* Notebook

### DoD

* Pergunta → resposta
* Logs claros
* Fácil de debugar

---

# 🔚 CONCLUSÃO SÊNIOR

### O que você está construindo agora?

👉 **Um sistema de inteligência operacional**, não apenas um extrator.

### Decisões corretas tomadas:

✔ API para usuários externos
✔ Agente com acesso direto ao banco
✔ Sem overengineering
✔ Evolução incremental

Se quiser, no próximo passo posso:

* desenhar a **arquitetura do Agent**
* escrever o **prompt do agente**
* ou já criar o **esqueleto da FastAPI + Agent convivendo no mesmo projeto**
