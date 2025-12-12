# 📌 **BACKLOG COMPLETO — Projeto de Extração ONS**

---

# 🧩 **EPIC 01 — Robustez e Qualidade da Extração de PDFs**

---

## **US01 — Substituir PyPDF2 por pypdfium2 para extração confiável**

**Descrição:** Como sistema, quero extrair texto de PDFs com precisão, para que o GPT receba dados limpos e não haja perda de informação crítica.

**Motivação:** PyPDF2 falha em tabelas e PDFs estruturados → baixa qualidade do parsing → GPT devolve resultado incorreto.

### **Critérios de Aceitação**

* A extração deve retornar texto de TODAS as páginas.
* Não deve haver perda perceptível de conteúdo.
* Deve ter fallback se o PDF estiver corrompido.
* Textos devem ser normalizados (quebra de linha padronizada).

### **Subtarefas**

1. Criar novo módulo `pdf_extractor_v2.py` usando **pypdfium2**.
2. Implementar tratamento de erros por página.
3. Implementar limpeza do texto:

   * Remover quebras duplas
   * Remover caracteres invisíveis
   * Converter múltiplos espaços em um
4. Criar testes unitários para três PDFs de exemplo.
5. Substituir chamadas em `main.py`.

### **Definition of Done**

* Testes OK
* 100% dos PDFs exemplo extraídos
* Performance igual ou melhor que PyPDF2
* Código documentado

---

## **US02 — Limitar tamanho do texto enviado ao GPT (chunking)** - desconsiderado

**Descrição:** Como sistema, quero evitar estouro de contexto ao enviar textos longos ao GPT, para garantir resposta confiável.

### **Critérios de Aceitação**

* Nenhum prompt deve exceder o limite de tokens do modelo.
* Sistema divide automaticamente o PDF em blocos inteligíveis.
* Junta as respostas coerentemente antes de salvar JSON.

### **Subtarefas**

1. Implementar função `split_text_by_tokens()`.
2. Criar lógica para *multi-prompt* e *multi-resposta*.
3. Mesclar chunks antes do `salvar_json_com_metadata`.
4. Validar consistência final do JSON.
5. Criar aviso quando chunking for necessário.

### **Definition of Done**

* Nenhuma chamada ao GPT retorna erro 400 (context length).
* Logs mostram divisão inteligente.
* JSON final segue o schema original.

---

# 🧩 **EPIC 02 — Modernização da API OpenAI**

---

## **US03 — Migrar de Chat Completions para Responses API**

**Descrição:** Como desenvolvedor, quero usar a API mais moderna da OpenAI, para ganho de performance, estabilidade e suporte a PDF.

### **Critérios de Aceitação**

* GPT deve ser chamado via `client.responses.create()`.
* Suporte nativo a PDFs deve ser implementado.
* Respostas devem ser parseadas pelo novo formato.
* Retentativas devem permanecer funcionando.

### **Subtarefas**

1. Criar novo módulo `openai_client_v2.py`.
2. Implementar envio de PDF como input binário.
3. Atualizar extractor para usar esse novo fluxo.
4. Ajustar prompt para Responses API.
5. Adicionar timeout explícito (20s).
6. Logging detalhado de cada tentativa.

### **Definition of Done**

* API nova funcionando em ambiente de teste.
* Consistência com JSON atual mantida.
* Modelo `"gpt-5-mini"` utilizado corretamente.

---

# 🧩 **EPIC 03 — Confiabilidade e Resiliência do Sistema**

---

## **US04 — Corrigir bug crítico no main.py (variável e fora do escopo)**

**Descrição:** Como sistema, quero evitar erros de execução por má gestão de escopo, garantindo execução contínua.

### **Critérios de Aceitação**

* Código deve executar sem NameError.
* Bloco de exceção deve ser reposicionado corretamente.

### **Subtarefas**

1. Remover segunda linha duplicada de log.
2. Recolocar o log dentro do `except`.
3. Adicionar testes de execução com cache.

### **Definition of Done**

* Nenhum erro ao processar PDFs com cache.

---

## **US05 — Evitar destruição acidental do banco SQLite** - ok

**Descrição:** Como desenvolvedor, quero evitar que o banco seja apagado a cada execução, preservando histórico.

### **Critérios de Aceitação**

* Tabelas só devem ser criadas se não existirem.
* Reset do banco deve ser uma operação manual separada.

### **Subtarefas**

1. Criar função `init_db()` com `CREATE TABLE IF NOT EXISTS`.
2. Criar script separado `reset_db.py`.
3. Alterar `main.py` para usar `init_db()`.

### **Definition of Done**

* Dados históricos são preservados.
* Reset funciona apenas manualmente.

---

## **US06 — Unificar regras de inserção de dados (REPLACE vs IGNORE)**

**Descrição:** Como mantenedor do sistema, quero consistência nas operações SQL, evitando comportamentos imprevisíveis.

### **Critérios de Aceitação**

* Regras uniformes para todas as tabelas.
* Documentação de quando usar `REPLACE` e quando usar `IGNORE`.

### **Subtarefas**

1. Definir padrão global (REPLACE recomendado).
2. Atualizar todos os SQLs.
3. Revisar UNIQUE constraints.
4. Testes: inserir duplicata e validar comportamento.

### **Definition of Done**

* Comportamento uniforme para todas inserções.

---

# 🧩 **EPIC 04 — Manutenção e Arquitetura Limpa**

---

## **US07 — Criar tratamento centralizado de logs**

**Descrição:** Como operador, quero logs padronizados e com níveis (INFO/WARN/ERROR), para melhor depuração.

### **Critérios de Aceitação**

* logger deve suportar:

  * INFO
  * WARNING
  * ERROR
  * SUCCESS
* Saída deve ter timestamp + módulo.

### **Subtarefas**

1. Criar classe `Logger` com níveis.
2. Criar formato: `[HH:MM:SS] [LEVEL] [MODULE] mensagem`.
3. Substituir todas as chamadas existentes.

### **Definition of Done**

* Logs padronizados em todo o projeto.

---

## **US08 — Criar máquina de estados para processamento de PDFs**

**Descrição:** Como dev, quero que cada PDF tenha estados claros:
→ encontrado
→ cache hit
→ cache miss
→ extraído
→ salvo
→ erro
Isso facilita telemetria, debugging e automações.

### **Critérios de Aceitação**

* Cada PDF deve gerar um relatório de estados.
* Erros devem ser rastreáveis por estado.

### **Subtarefas**

1. Criar enum `ProcessingState`.
2. Integrar ao `processar_arquivo`.
3. Criar função `emit_state(pdf, state)`.

### **Definition of Done**

* Cada PDF tem seu histórico completo nos logs.

---

## **US09 — Criar serviço de processamento paralelo**

**Descrição:** Como usuário avançado, quero processar múltiplos PDFs simultaneamente, acelerando processamento.

### **Critérios de Aceitação**

* Uso de `concurrent.futures`.
* Limite configurável de workers.
* Garantir integridade do banco mesmo com concorrência.

### **Subtarefas**

1. Implementar fila de execução.
2. Uso de `ThreadPoolExecutor` ou `ProcessPoolExecutor`.
3. Lock para acesso ao banco SQLite.
4. Testes de stress com 50 PDFs.

### **Definition of Done**

* Performance aumenta proporcionalmente ao número de workers.

---

# 🧩 **EPIC 05 — Qualidade dos Dados e Inteligência do Sistema**

---

## **US10 — Criar validador do JSON retornado pelo GPT**

**Descrição:** Como sistema, quero validar os campos obrigatórios do JSON antes de gravar no banco.

### **Critérios de Aceitação**

* JSON inválido → erro claro.
* Ausência de campo obrigatório → rejeitar.
* Tipos corretos (lista, str, dict).

### **Subtarefas**

1. Criar schema Pydantic.
2. Implementar validação no `chamar_gpt`.
3. Criar exemplos de JSON válido e inválido.

### **Definition of Done**

* JSON só é gravado após validação.

---

# 📌 **PRIORITIZAÇÃO (MOSCOW)**

### MUST HAVE

* US01 (pypdfium2)
* US03 (Responses API)
* US04 (bug crítico)
* US05 (não destruir o banco)
* US10 (validação do JSON)

### SHOULD HAVE

* US02 (chunking)
* US06 (uniformizar SQL)
* US07 (novo logger)

### COULD HAVE

* US08 (máquina de estados)
* US09 (paralelismo)

### WON’T HAVE (por enquanto)

Nenhum item identificado como desnecessário.

---

# 📊 **MATRIZ IMPACTO X COMPLEXIDADE**

| US   | Impacto | Complexidade | Prioridade |
| ---- | ------- | ------------ | ---------- |
| US04 | ⭐⭐⭐⭐⭐   | ⭐            | **Alta**   |
| US01 | ⭐⭐⭐⭐⭐   | ⭐⭐⭐          | **Alta**   |
| US03 | ⭐⭐⭐⭐⭐   | ⭐⭐⭐⭐         | **Alta**   |
| US05 | ⭐⭐⭐⭐    | ⭐            | **Alta**   |
| US10 | ⭐⭐⭐⭐    | ⭐⭐           | **Alta**   |
| US02 | ⭐⭐⭐     | ⭐⭐⭐⭐         | Média      |
| US06 | ⭐⭐⭐     | ⭐⭐           | Média      |
| US07 | ⭐⭐      | ⭐⭐           | Média      |
| US09 | ⭐⭐⭐     | ⭐⭐⭐⭐         | Baixa      |
| US08 | ⭐⭐      | ⭐⭐⭐          | Baixa      |
