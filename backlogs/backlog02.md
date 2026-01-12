# 🧱 BACKLOG — MVP Conversacional IPDO

### Objetivo

Permitir que um usuário **pergunte em linguagem natural** sobre os dados do IPDO já carregados no SQLite e receba respostas consistentes.

📌 Escopo:

* **Somente leitura**
* PDF já foi carregado
* Sem chunking
* Sem segurança
* Uso interno

---

## 🔷 EPIC 1 — Consulta aos Dados Extraídos

Usuário deve conseguir consultar as informações essenciais armazenadas no banco.

---

### US01 — Listar datas disponíveis (baseline) - ok

**Como** usuário
**Quero** saber quais datas existem
**Para** poder selecionar qual consultar

**Tarefas**

* Criar função `listar_datas()` (se já existir, manter)
* Validar que retorna lista não vazia ou vazia corretamente
* Documentar formato retornado

**Pronto quando**

* Chamando a função retorna uma lista decrescente de datas
* Sem erro mesmo se o banco estiver vazio

---

### US02 — Obter destaques de operação por data - ok

**Como** usuário
**Quero** ver os destaques operacionais do dia
**Para** entender a condição do sistema naquele dia

**Tarefas**

* Criar (ou validar) consulta única por data
* Retornar submercados + status de carga, restrições, intercâmbio, geração agregada
* Retornar lista vazia caso não exista

**Pronto quando**

* Função retorna um array de submercados e dados relacionados
* **Nenhum campo obrigatório vem faltando**
* Data inexistente retorna lista vazia

---

### US03 — Buscar geração por submercado e tipo - ok

**Como** usuário
**Quero** filtrar geração por submercado e tipo
**Para** ir direto ao foco do interesse

**Tarefas**

* Implementar (ou garantir) filtros opcionais:

  * `submercado`
  * `tipo`
* Garantir que a ordem seja previsível

**Pronto quando**

* Função retorna lista filtrada coerente
* Chamada sem filtros retorna tudo do dia
* Chamada com filtros não quebra

---

### US04 — Consultar destaques térmicos - ok

**Como** usuário
**Quero** saber se houve problemas térmicos
**Para** identificar desvios relevantes

**Tarefas**

* Criar (ou validar) consulta ordenada por desvio
* Suportar parâmetro opcional de limite
* Devolver lista vazia caso não exista registro

**Pronto quando**

* Retorno consistente contendo unidade, desvio e descrição
* Limite funciona corretamente
* Estrutura de lista nunca muda

---

## 🔷 EPIC 2 — Agente Conversacional

### US05 — Criar prompt governante do agente - ok

**Como** agente
**Quero** saber minhas regras de comportamento
**Para** responder com dados confiáveis

**Tarefas**

* Criar `system_prompt.txt`
* Instruir:

  * só responder baseado no banco
  * nunca inventar dados
  * indicar quando não houver dados
  * não chamar GPT para interpretar PDFs
  * não assumir causas operacionais

**Pronto quando**

* Prompt está versionado em arquivo dedicado
* Linguagem clara e objetiva
* Leitura no agente funciona

---

### US06 — Agente interpreta pergunta e identifica intenção

**Como** usuário
**Quero** perguntar de forma natural
**Para** obter resposta sem SQL

**Tarefas**

* Mapear intenções para ferramentas:

  * listar datas
  * buscar operação
  * buscar térmica
  * buscar geração
* Registrar funções como ferramentas
* Retornar JSON estruturado apenas

**Pronto quando**

* Perguntas simples acionam a função correta
* Erro amigável caso intenção não exista
* Nada explode se input vier estranho

---

### US07 — Formatação da resposta do agente

**Como** usuário
**Quero** ler a resposta de forma clara
**Para** entender sem estrutura interna do banco

**Tarefas**

* Validar JSON retornado pelo tool
* Formatá-lo apenas se necessário
* Padronizar mensagens:

  * “Nenhum dado encontrado”
  * “Não entendi a pergunta”

**Pronto quando**

* Todas respostas seguem o mesmo padrão
* Sem logs ou stacktrace expostos ao usuário final

---

### US08 — CLI simples para conversar com o agente

**Como** usuário interno
**Quero** fazer perguntas pela linha de comando
**Para** testar rapidamente o agente

**Tarefas**

* Criar script de CLI
* Loop:

  * input
  * agente responde
* Palavra-chave para sair: `sair`, `quit`, `exit`

**Pronto quando**

* Rodando `python cli.py` o usuário interage com perguntas sucessivas
* Respostas aparecem no terminal
* Nenhum crash com inputs inesperados

---

## 🔷 EPIC 3 — Qualidade e Operação

### US09 — Logging simples e consistente

**Como** operador
**Quero** entender o que está acontecendo
**Para** debugar comportamentos inesperados

**Tarefas**

* Reutilizar `utils.logger.log()`
* Logar as chamadas detectadas pelo agente
* Logar erros silenciosos de forma amigável

**Pronto quando**

* Logs aparecem no terminal durante operação do agente
* Sem spam desnecessário

---

### US10 — README interno mínimo

**Como** colega desenvolvedor
**Quero** saber como executar o sistema
**Para** conseguir rodar sem te perguntar nada

**Tarefas**

* Criar README.md
* Inclui:

  * requisitos
  * como ativar venv
  * como rodar extração
  * como iniciar CLI
  * como iniciar API

**Pronto quando**

* Novo membro da equipe consegue usar sem ajuda
* Nenhum passo crítico está faltando

---

# 🎯 Critério de aceite final do MVP

O MVP está **entregue** quando:

✔ PDF já processado está no banco
✔ Usuário abre CLI e faz perguntas como:

* “Quais datas existem?”
* “O que aconteceu no dia 2025-05-10?”
* “Houve problemas térmicos ontem?”
* “Como estava a geração no Sudeste no dia 2025-05-10?”

✔ Agente responde usando **apenas os dados existentes**
✔ API segue funcionando sem interferir
✔ Tudo roda local e offline

---

# 🚀 Pronto para executar

Esse backlog é mínimo, executável e cobre apenas:

* Consultar dados
* Conversar sobre os dados
* Não inventar nada
* Ser útil imediatamente

Quando quiser expandir, podemos criar o **backlog da fase 2**:
comparações, painel web, scheduler automático, chunking etc.
