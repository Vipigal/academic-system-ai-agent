---
type: Plan
title: Agente, eval e fluxo ponta a ponta
description: Spec-mãe da fase que reorganiza as camadas com o bootstrap, cria o agente LangChain com skills, o histórico, a confirmação de protocolo, o chat com stream, o eval de modelos e as evidências do case.
tags: [plano, agente, langchain, eval, chat, arquitetura]
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
sources:
  - id: arquitetura
    resource: /docs/architecture.md
    title: Arquitetura do agente de atendimento ao aluno (B36 a B41)
  - id: catalogo
    resource: /docs/question-catalog.md
    title: Catálogo de perguntas do aluno
  - id: spec-tools
    resource: /docs/plans/ontologia-e-tools.md
    title: Spec anterior, com as 19 tools e o envelope
---

# Agente, eval e fluxo ponta a ponta

> **Status:** em revisão · **Data:** 2026-11-05
> **Spec vivo:** esta pasta é a fonte única da fase. Este `index.md` é o spec-mãe; cada tarefa tem o seu arquivo.
> Mudanças são editadas aqui e anotadas em "Mudança no spec" na seção Registro; leia o Registro junto do restante.
> **Repos:** só este. `Makefile`, `.importlinter`, `quality.toml`, `ruff.toml`, `.flake8`, `mypy.ini`,
> `pyrightconfig.json`, `tools/quality/` e `tests/lint/` são do dono; tarefa que precisar mudá-los entrega o patch.

## Para o humano

- **O que muda:** a API ganha o agente LangChain com as 19 tools e 7 skills, o histórico no schema `agent`, a
  confirmação de protocolo fora do LLM, a rota `/chat` com stream, a página de chat, o eval de modelos e as evidências
  que o enunciado pede. Antes disso, as camadas são reorganizadas com o `bootstrap/` como composition root.
- **Por quê:** é o que falta para o case rodar de ponta a ponta e ser avaliado: qualidade medida, latência relatada,
  ataques testados.
- **Quanto custa:** 13 tarefas em 5 ondas. Caminho crítico: T1 → T4 → T9 → T11 → T12. O eval da matriz inicial custa
  na faixa de dezenas de dólares, quase tudo no juiz (§6.6).
- **Revisar com atenção:** os contratos da §6 (stream do chat, token da proposta, golden set), as pendentes da §3.2 e o
  corte das ondas da §8.

## 1. Contexto e problema

As 19 tools, as 54 ontologias e o envelope estão prontos e testados, com 609 testes verdes. Nada disso é alcançável:
`src/api/main.py` só expõe `/health`, e a montagem por aluno em `src/api/composition/` só é usada pelos testes. O pacote
nasceu fora dos contratos do linter, e a discussão de arquitetura de 2026-11-05 o transformou no `bootstrap/` (B36 a
B41 da arquitetura).

O enunciado exige, além do código: exemplos de conversa, testes de segurança com tentativas e resultados, medição de
latência e como a qualidade foi avaliada. Nenhum existe ainda.

## 2. Princípios

- **Segurança por construção:** identidade só do token; a sessão nasce pronta; o LLM não grava; o cliente não manda
  histórico em que o servidor confie.
- **Medir antes de escolher:** modelo, skills e prompt mudam por resultado do eval, não por opinião.
- **O desenho mais simples que mantém a garantia:** montagem à mão no bootstrap, sem container de DI; mecanismo de
  skills próprio de poucas linhas; tabelas de histórico mínimas.
- **Uma tarefa, uma fronteira:** tarefas da mesma onda não tocam o mesmo arquivo e se verificam sozinhas.

## 3. Decisões

### 3.1 Batidas (não reabrir)

| # | Decisão | Por quê |
|---|---|---|
| D1 | Escopo: reorganização em camadas, agente, histórico, confirmação de protocolo, chat com stream, front, eval, scripts de banco `02` a `05` e evidências | Decisão do dono; é o que falta para entregar o case |
| D2 | Camadas e composição conforme B36 a B39: `bootstrap/` monta tudo; agente e tools em `application/agent/`; `infrastructure/` para adaptadores técnicos; presentation só com rotas | Discussão de 2026-11-05, conferida contra a literatura; os contratos já estão no `.importlinter` |
| D3 | O agente é montado a cada request com `create_agent`; cada tool é uma closure sobre os services do aluno; o schema de cada tool é calculado uma vez, na subida | Medido com modelo fake: `create_agent` com 20 tools leva 3,3 ms no p50; inferir os schemas a cada vez levaria 25 ms |
| D4 | A sessão é imutável e nasce numa dependência de request (B37) | Sem sessão vazia, a falha é fechada |
| D5 | Skills em `SKILL.md` por área, com `name` e `description`; o prompt lista as descrições e a tool `load_skill(area)` devolve o corpo e `OntologyRenderer.for_skill(area)` | Formato do LangChain e do Deep Agents; o `SkillsMiddleware` do Deep Agents exige backend de arquivos e `read_file`, peso sem ganho para 7 textos |
| D6 | Histórico em `agent.conversation`, `agent.message` e `agent.tool_call` (B41) | Funciona com réplicas, sem segundo driver, com dono testável pelo adapter |
| D7 | A proposta de protocolo é um token assinado, preso ao aluno e com validade; a confirmação valida de novo e grava (B40) | Mesma garantia de B26 sem tabela de rascunho |
| D8 | Front em React com Vite e AI SDK `useChat`, em `src/app/`; o FastAPI emite o protocolo de stream de mensagens do AI SDK | Plug and play, com o card de confirmação como componente da parte da tool |
| D9 | Eval com runner próprio em `src/evals/`; golden set em YAML a partir do catálogo, com fatos amarrados a consultas SQL nomeadas; graders determinísticos e um juiz LLM | Sem serviço externo obrigatório; nenhum número digitado à mão |
| D10 | Observabilidade no Langfuse Cloud, com `CallbackHandler` por request e `@observe` nos casos de uso da application; `user_id` anonimizado | Decisão do dono; evita subir os serviços do self-host |
| D11 | Modelo inicial `gpt-6-luna` pela Responses API (`use_responses_api=True` no `ChatOpenAI`) | Favorita do dono; no Chat Completions, tool calling dessa série só funciona com effort `none` |
| D12 | Matriz do eval depois do primeiro ciclo: `gpt-6-luna` (effort `low` e `medium`), `gpt-5.6-luna`, `gpt-5.4-mini`, `gpt-6.1-terra` e `gpt-6.1-sol` | Cobre a favorita, a geração anterior, uma linha de base e o teto de qualidade |
| D13 | O aviso de negativação fica só na skill financeira; o gabarito de SR-05 usa a cobertura do AVA a partir de 01/02/2023; saldo zero para fatura cancelada ou renegociada está aprovado | Decisões do dono sobre o review da fase anterior |
| D14 | O servidor usa só a última mensagem do aluno e o id da conversa; o histórico vem sempre do banco | Histórico enviado pelo cliente permitiria forjar mensagens do assistente ou de tool |
| D15 | Testes não chamam o provedor de LLM, exceto os marcados `live`, que só rodam com `--live` | `make check` determinístico e sem custo |
| D16 | A sessão guarda só identidades: `person_ids`, CPF (oculto) e `enrollment_keys`. Cada sistema tem uma tabela-raiz (contrato, conta do AVA, protocolo) cuja regra de ownership é o predicado do dialeto sobre as matrículas; as demais tabelas chegam a ela por `Via`. O tipo de pagador é resolvido na consulta | Decisão do dono: com mais sistemas, carregar tudo do aluno na sessão pesa; registros resolvidos na consulta não ficam velhos; a carga cai de 8 para 2 ou 3 consultas por request. É o "AND do dono" traduzido por sistema |
| D17 | Pastas por camada e, dentro, por área (`academic`, `finance`, `lms`, `protocol`, `overview`, `identity`, `shared`), sem o prefixo da área no nome do arquivo; os testes espelham as áreas | Decisão do dono: muitos arquivos soltos por camada; manter a camada no topo preserva os contratos do linter |
| D18 | A API e o código da API nos testes conectam com a role `api`; o oráculo SQL dos testes e do eval usa uma URL de administrador separada | Decisão do dono: prova que o menor privilégio basta; o oráculo lê tabelas que a role não vê |
| D19 | Juiz do eval: Claude, rodado pelo Claude Code em modo headless com um agente dedicado, sem ferramentas, que não sabe qual modelo respondeu. Reserva: `gpt-6.1-terra` pela API | Decisão do dono: usa o plano em vez de crédito de API; Claude não é candidato, então não há autopreferência; `gpt-6-astra` é caro demais |
| D20 | Login simulado em `POST /auth/dev-login` com `marca:RA`, só com `APP_DEV_LOGIN=true` | Decisão do dono |
| D21 | `docker compose down -v` liberado para aplicar os scripts de banco desta fase | Decisão do dono em 2026-11-05 |
| D22 | **Erro ensino:** erro de tool nunca derruba o turno do modelo. Parâmetro inválido esperado volta como resultado da tool, com status `invalid` e um parágrafo que diz qual parâmetro, o que veio, o que é aceito e um exemplo válido. Falha inesperada volta como status `error`, com texto genérico e registro no log | Decisão do dono: o modelo corrige a própria chamada em vez de abandonar a resposta; detalhe interno nunca chega ao modelo |
| D23 | Tool a mais na trajetória não reprova; o grader exige as tools necessárias e a resposta correta, e reprova só tool proibida | Decisão do dono: importa resolver o problema |
| D24 | Janela de histórico de 20 mensagens, sem resumo | Decisão do dono; resumo entra se o eval mostrar perda |

### 3.2 Pendentes (confirmar na revisão)

| # | Proposta | Alternativa | Recomendação |
|---|---|---|---|
| P6 | Teste de carga com Locust e modelo fake (`APP_AGENT_MODEL=fake`) | k6 | A proposta: mesma linguagem do projeto; mede a API sem custo de LLM |
| P7 | Log estruturado com `logging` da biblioteca padrão e formatador JSON | `structlog` | A proposta: uma dependência a menos |

## 4. Escopo

### Dentro

- Reorganização em camadas, sem mudar comportamento.
- Scripts `02_constraints.sql`, `03_indexes.sql`, `04_agent_schema.sql` e `05_roles.sql`, aplicados com volume novo.
- Agente, skills, histórico, identidade, observabilidade, confirmação de protocolo, chat com stream, front.
- Golden set, red team, runner de eval, relatório por modelo.
- Evidências: conversas, segurança, latência, qualidade, carga; instruções para rodar no `README.md`.

### Fora

| Item | Entra quando |
|---|---|
| `get_ontology` como tool | O eval mostrar falha em perguntas de dúvida ou sem dado só com skills (D14 do spec anterior) |
| Resumo de histórico | O eval mostrar perda em conversas longas (D24) |
| Cache da sessão | O teste de carga mostrar que a carga por request pesa (B6) |
| Fallback para outro provedor | Existir chave de outro provedor |
| Login real | Fora do case: a identidade é simulada, como o enunciado permite |
| Escritas além de abrir protocolo | Arquitetura, seção 9 |

## 5. Terreno: como a codebase faz hoje

Estado depois da arrumação (T1, T1b e T2).

- **Tools:** 5 classes em `src/api/application/agent/tools/`, validadas por `ToolRegistry` (`tools/registry.py`), com
  docstring de até 200 caracteres, ontologias declaradas, retorno `ToolResult` e parâmetros de uma lista permitida. O
  registro devolve `RegisteredTool(definition, handler)`. `StudentTools` está em `application/agent/student_tools.py`.
- **Montagem por aluno:** `StudentProviders` (`bootstrap/student_providers.py`) carrega a sessão, cria o `RepositoryAdapter` e
  monta os services (`bootstrap/student_services.py`, `protocol_providers.py`) e as tools (`bootstrap/tool_providers.py`). Só
  os testes o usam até T9 e T11. `Singletons` (`bootstrap/singletons.py`) tem `settings`, `database` e `clock`.
- **App:** `ApiFactory.create` (`bootstrap/app.py`) monta `Database` e o router de health com o padrão
  `HealthRouter.build(service)`, que o chat e a confirmação devem seguir.
- **Settings e relógio:** `Settings` em `bootstrap/settings.py`, já com todos os campos da fase; `ReferenceClock` em
  `infrastructure/clock.py`.
- **Sessão (D16):** `StudentSession` em `domain/identity/session.py`, com `person_ids`, `cpf` e `enrollment_keys`; o port
  `StudentSessionLoader` em `domain/ports/identity.py`; a carga faz 2 consultas. Raízes de ownership: `contract`, `mdl_user`,
  `protocol`. Consulta privada só por `RepositoryAdapter.fetch_declared`.
- **Envelope:** `ToolResult` em `application/shared/tool_result.py`, com `status`, `data`, `page`, `totals`, `caveats`,
  `coverage` e `candidates`.
- **Skills:** `OntologyRenderer.for_skill(area)` em `domain/ontology/renderer.py`, para as 7 áreas de `Area`.
- **Proposta de protocolo:** `ProtocolProposer` em `application/protocol/` valida e devolve `ProtocolProposalDto` sem gravar.
  Não existe código de escrita de protocolo.
- **Oráculo e mapa:** `SqlOracle` em `tests/integration/support/sql_oracle.py`, com conexão própria de administrador por
  `APP_ORACLE_DATABASE_URL`; `tests/agent_map.py` liga as 60 perguntas às tools e ontologias. O eval cria o seu próprio
  oráculo com a mesma variável; a API nunca a lê.
- **Gates:** `.importlinter` com 6 contratos, incluindo LangChain só em `application/agent/`; `quality.toml` com docstring só
  em `application/agent/tools`; marcadores `unit`, `integration`, `sweep`, `slow` e `live` no `pyproject.toml`; `make
  check-fast` para o loop.
- **Banco:** `db/init/` com os scripts `01` a `05` aplicados. Os testes conectam como a role `api`: tabela nova do schema
  `agent` já está coberta pelo grant, mas sequência ou tabela de origem nova exige mudar `05_roles.sh` e recriar o volume.
- **Dependências:** `langchain`, `langchain-openai`, `langfuse` e `pyjwt` nas dependências; `pyyaml` e `locust` no grupo
  `dev`. Para o mypy strict, T3 precisará de `types-pyyaml`.

## 6. Desenho

### 6.1 Camadas

As da arquitetura, seção 5.1. Resumo para quem implementa:

```text
src/api/bootstrap/        app.py (ApiFactory) · settings.py · singletons.py · *_providers.py por área
src/api/presentation/http health.py · auth.py · identity.py · chat.py · ui_stream.py · protocol_confirmation.py
src/api/application/      academic/ finance/ lms/ protocol/ overview/ health/ shared/ (cada área com dto/)
                          chat/ · protocol/confirmation.py
                agent/    tools/ (as 19 + skill_tools) · langchain_tools.py · student_agent.py · skills/<area>/SKILL.md
src/api/domain/           academic/ finance/ lms/ protocol/ identity/ shared/ ontology/ ports/
src/api/persistence/      core/ identity/ sag/ finance/ lms/ secretary/ agent/
src/api/infrastructure/   clock.py · tracing.py · logging.py · proposal_signer.py
src/evals/                golden/ · oracle_queries.py · graders/ · judge/ · runner.py · report.py
src/app/                  front React + Vite
```

Os nomes exatos das pastas e arquivos são os que T1 deixar no código; esta árvore é o alvo.

### 6.2 Grafo por request

Singletons, criados uma vez em `bootstrap/singletons.py`: `Settings`, `Database`, relógio, modelo de chat, biblioteca de
skills, schemas das tools, cliente do Langfuse, assinador de propostas.

Por request, em providers do bootstrap encadeados por `Depends`: identidade (JWT → `person_id`) → `StudentSession`, só com
identidades (D16) →
`RepositoryAdapter` → repositórios → services → tools → agente → `ChatService`. A rota recebe só o provider de que precisa:
`/chat` monta o agente; a confirmação monta só o que grava protocolo.

Regra contra dependência cativa: nenhum singleton guarda método ligado, service, tool, agente ou histórico de um aluno.
O invariante 11 da arquitetura vira teste em T4.

### 6.3 Contrato do chat (T9, consumido por T12)

Pedido: `POST /chat` com `Authorization: Bearer <jwt>` e corpo no formato do AI SDK 7, `{id, messages: [...]}`. O servidor
usa o `id` como id da conversa e só a última mensagem de papel `user`; o resto do corpo é ignorado (D14).

Resposta: `200 text/event-stream` com o header `x-vercel-ai-ui-message-stream: v1`. Cada evento é uma linha
`data: <json>` seguida de linha em branco, nesta ordem possível:

| Evento | Quando |
|---|---|
| `start` | Abertura, com `messageId` |
| `text-start`, `text-delta`, `text-end` | Texto do modelo |
| `tool-input-available` | O modelo pediu uma tool: `toolCallId`, `toolName`, `input` |
| `tool-output-available` | Resultado da tool: `toolCallId`, `output` (o `ToolResult` serializado) |
| `error` | Falha, com `errorText` genérico, sem detalhe interno |
| `finish` | Fim; seguido de `data: [DONE]` |

Os nomes exatos dos eventos são conferidos contra a documentação do AI SDK 7 no início de T9; divergência vira "Mudança no
spec". Conversa de outro aluno ou inexistente: mesma resposta, `404`.

### 6.4 Proposta e confirmação de protocolo (T8)

- `propose_protocol` passa a devolver, além da proposta, um `token`: HMAC-SHA256 com segredo de settings sobre `person_id`,
  matrícula, serviço, mensagem e validade de 15 minutos. O token não aparece no texto do modelo; o front o lê do
  `tool-output-available`.
- `POST /protocols/proposals/confirm` com Bearer e `{token}`. Confere assinatura, validade e que o `person_id` do token é o da
  sessão; reaplica as regras da proposta (taxa, serviço ativo, duplicado); abre o protocolo no domínio e grava 3 linhas numa
  transação (arquitetura, 5.6).
- Respostas: `201 {protocol_number, status, sla_due_at}`; token inválido, expirado ou de outro aluno: `404` uniforme;
  duplicado: `409`; serviço com taxa: `422`. Confirmar duas vezes o mesmo token devolve o mesmo `409` de duplicado.

### 6.5 Histórico (T5)

| Tabela | Colunas | Dono |
|---|---|---|
| `agent.conversation` | `id uuid`, `person_id`, `created_at`, `updated_at` | `person_id` da sessão |
| `agent.message` | `id uuid`, `conversation_id`, `position`, `role` (`user` ou `assistant`), `content`, `model`, `tokens_in`, `tokens_out`, `latency_ms`, `created_at` | `Via` conversation |
| `agent.tool_call` | PK (`message_id`, `id`), em que `id` é o do modelo; `position`, `name`, `arguments jsonb`, `result jsonb`, `status`, `duration_ms`, `created_at` | `Via` message |

Na leitura, a janela das últimas 20 mensagens (D24) nunca separa um `AIMessage` com `tool_calls` dos seus `ToolMessage`.

### 6.6 Eval (T3 e T10)

- **Golden set:** `src/evals/golden/questions.yaml`, um item por pergunta do catálogo (60), e `redteam.yaml`. Campos: `id`,
  `kind` (`answerable`, `no_data`, `refusal`, `attack`), `split` (`dev` ou `holdout`, estratificado por área e `kind`, cerca
  de 30% em holdout), `question`, `student` (`marca:RA`), `tools.expected` e `tools.forbidden`, `facts` (nome da consulta
  SQL, parâmetros e formato: `brl`, `date`, `int`, `percent`, `text`), `forbidden_text`, `rubric` e `reference` (a resposta
  ideal do catálogo).
- **Consultas nomeadas:** `src/evals/oracle_queries.py`, `nome → SQL`, independentes das tools e dos services.
- **Graders:** trajetória (D23); fatos com números normalizados em pt-BR e comparação exata em centavos; recusa
  determinística (nenhuma tool de dado, nenhum texto proibido); vazamento (nenhum identificador de outra pessoa,
  reaproveitando a ideia do invariante do agente comprometido); juiz que aprova ou reprova cada item da rubrica,
  raciocinando antes do veredito.
- **Juiz (D19):** o runner grava os pedidos de julgamento em JSONL, sem o nome do modelo avaliado, e um segundo passo os
  entrega ao Claude Code em modo headless (`claude -p`) com um agente dedicado em `.claude/agents/`, sem ferramentas e com
  saída em JSON validado. Lotes de itens por chamada, para reduzir overhead. Com a opção de reserva, o mesmo pedido vai a
  `gpt-6.1-terra` pela API. O juiz é um port em `src/evals/judge/`, com as duas implementações.
- **Execução:** `python -m evals.run --model gpt-6-luna --split dev --repeat 3`. Chama o agente direto, sem HTTP, com a
  sessão de cada aluno. Registra modelo, effort, versão do prompt, hash das skills e das descrições das tools.
- **Saída:** JSONL por execução e um relatório Markdown com acerto por grader e por área, pass@1 médio, estabilidade entre
  repetições, latência p50 e p95, tokens e custo. Traces no Langfuse com tags `eval`, modelo e versões.
- **Custo estimado da matriz:** 60 perguntas × 3 repetições × 6 configurações ≈ 1.080 execuções; os candidatos custam
  centavos a poucos dólares por rodada, e o juiz sai do plano do Claude Code (D19). Medir o custo real do primeiro ciclo
  antes da matriz.

### 6.7 Agente (T4)

- Prompt de sistema curto e versionado: papel, idioma, regra de só afirmar o que as tools devolvem, recusa para dado de
  terceiros, lista das skills com as descrições, data de referência. Sem ontologias no prompt (D4 do spec anterior).
- Middlewares: limite de chamadas ao modelo e às tools por execução e retry do modelo. Limites em settings.
- **Erro ensino (D22):**
  - O envelope ganha os status `invalid` e `error`, com o campo `explanation`.
  - Erro de validação do schema da tool (tipo errado, enum fora da lista, `limit` fora da faixa) é convertido pelo conversor
    em `invalid`, com uma frase por parâmetro: o que veio, o que é aceito (os valores do enum, o formato, a faixa) e um
    exemplo. A mensagem crua do pydantic não chega ao modelo.
  - Erros esperados dentro da tool, como período em formato errado, levantam exceções tipadas do domínio ou da application
    que já carregam o parágrafo de ensino; o conversor os transforma em `invalid`.
  - Qualquer outra exceção vira `error` com texto genérico ("não consegui consultar agora; tente de novo ou diga ao aluno
    que a consulta falhou"), é registrada com `trace_id` e não interrompe a execução.
  - Os textos ficam em português, junto da definição de cada parâmetro, e são testados.
- Timeout por request e limite de chamadas simultâneas ao provedor, configuráveis.
- Modelo `fake` para testes e carga: um modelo determinístico do LangChain que segue um roteiro de tool calls.

## 7. Consequências

- **Melhora:** o case passa a rodar de ponta a ponta; cada camada tem contrato no linter; a escolha de modelo vira número.
- **Piora ou encarece:** o bootstrap cresce com as áreas (providers divididos por área para caber no linter); o eval com juiz
  tem custo por rodada; a role restrita exige volume novo, que apaga os dados carregados e recarrega.
- **Riscos:**
  - Tool calling da `gpt-6-luna` silenciosamente desligado se a Responses API não estiver ativa. Mitigação: teste `live` em T4
    que exige pelo menos uma tool chamada.
  - Nomes de eventos do AI SDK 7 diferentes do esperado. Mitigação: conferência no início de T9.
  - Juiz enviesado. Mitigação: conferir à mão os primeiros 15 vereditos e registrar a concordância.
  - Escrita de protocolo alterando os dados do eval (R4 da arquitetura). Mitigação: testes de escrita desfazem a transação ou
    usam aluno dedicado; o eval nunca confirma protocolo.
- **Não pode mudar:** os invariantes 1 a 11 da arquitetura; as 19 tools e seus schemas visíveis ao modelo, salvo o `token` em
  `propose_protocol`; os 609 testes atuais, que só mudam de import em T1.

## 8. Plano de implementação

| # | Tarefa | Depende de | Arquivos principais | Fronteira de teste | Arquivo |
|---|---|---|---|---|---|
| T1 | Reorganização em camadas | — | `bootstrap/`, `infrastructure/clock.py`, `application/agent/tools/`, imports dos testes, `Dockerfile`, `compose.yaml`, `pyproject.toml`, `.env.example` | Suíte atual | [t01](/docs/plans/agente/t01-camadas.md) |
| T1b | Sessão só com identidades | T1 | `domain/identity/session.py`, carga da sessão, `ownership.py` de cada sistema, consultas do tipo de pagador | Integração (partição e volumes) | [t01b](/docs/plans/agente/t01b-sessao.md) |
| T2 | Banco: constraints, índices, schema `agent`, role | T1b | `db/init/02` a `05`, `compose.yaml`, `.env.example`, settings do oráculo, teste de role | Integração | [t02](/docs/plans/agente/t02-banco.md) |
| T3 | Golden set e red team | T1 | `src/evals/golden/`, `src/evals/oracle_queries.py`, validador | Unitário e integração | [t03](/docs/plans/agente/t03-golden-set.md) |
| T4 | Agente e skills | T1 | `application/agent/`, `bootstrap/agent_providers.py` | Unitário com modelo fake; `live` | [t04](/docs/plans/agente/t04-agente.md) |
| T5 | Histórico | T1, T2 | `domain/ports/conversation.py`, `persistence/agent/`, `ownership_registry.py`, `bootstrap/history_providers.py` | Integração | [t05](/docs/plans/agente/t05-historico.md) |
| T6 | Identidade e login simulado | T1 | `presentation/http/identity.py`, `auth.py`, `bootstrap/identity_providers.py` | Integração HTTP | [t06](/docs/plans/agente/t06-identidade.md) |
| T7 | Observabilidade | T1 | `infrastructure/tracing.py`, `infrastructure/logging.py`, `bootstrap/observability.py` | Unitário; conferência no Langfuse | [t07](/docs/plans/agente/t07-observabilidade.md) |
| T8 | Confirmação de protocolo | T1, T2, T6 | `domain/protocol/opening.py`, `persistence/secretary/protocol_writer.py`, `application/protocol_confirmation.py`, `infrastructure/proposal_signer.py`, `presentation/http/protocol_confirmation.py`, proposta com token | Integração | [t08](/docs/plans/agente/t08-confirmacao.md) |
| T9 | Chat com stream | T4, T5, T6, T7 | `application/chat/`, `presentation/http/chat.py`, `ui_stream.py`, `bootstrap/chat_providers.py` | Integração HTTP com modelo fake | [t09](/docs/plans/agente/t09-chat.md) |
| T10 | Runner de eval | T3, T4, T7 | `src/evals/` (exceto `golden/`) | Unitário; uma rodada `live` | [t10](/docs/plans/agente/t10-runner-eval.md) |
| T11 | Montagem e ponta a ponta | T8, T9 | `bootstrap/app.py`, `compose.yaml`, `.env.example`, `tests/e2e/` | E2E | [t11](/docs/plans/agente/t11-ponta-a-ponta.md) |
| T12 | Front de chat | T11 | `src/app/` | Navegador | [t12](/docs/plans/agente/t12-front.md) |
| T13 | Evidências e README | T10, T11 | `docs/evidencias.md`, `README.md`, `loadtest/`, resultados do eval | Execuções reais | [t13](/docs/plans/agente/t13-evidencias.md) |

### Ondas e paralelismo

- **Arrumação (sessão de 2026-11-05, em sequência):** T1 → T1b → T2. T1 move e cria o esqueleto; T1b muda as consultas
  de ownership; T2 deriva os índices dessas consultas, aplica a role e recria o volume. Ao fim, o código está organizado e a
  próxima sessão começa pela onda 1.
- **Onda 1:** T3, T4, T5, T6 e T7, cada uma com o seu módulo de providers no bootstrap ou, em T3, só `src/evals/`.
- **Onda 2:** T8, T9 e T10. Cada rota é testada num app de teste; a ligação no `ApiFactory` fica para T11.
- **Onda 3:** T11, que liga as rotas, sobe o Compose e roda o fluxo inteiro.
- **Onda 4:** T12 e T13.
- **Caminho crítico:** T1 → T1b → T2 → T4 → T9 → T11 → T12.

## 9. Para o agente executor

- **Comece por:** T1, depois T1b e T2, em sequência. Depois delas, a onda 1.
- **Leia antes:** `CLAUDE.md`, `docs/architecture.md` (seções 3, 5.1, 5.2, 5.6 e 5.9), este arquivo inteiro com o Registro e o
  arquivo da sua tarefa.
- **Não toque:** os arquivos do dono listados no cabeçalho; a semântica das 19 tools e das ontologias; os dados de origem.
  `docker compose down -v` está liberado para T2 (D21).
- **Gates:** `make check-fast` no loop; `make check` verde ao fechar a tarefa, com a saída como prova. Decisão nova é
  confirmada com o dono, editada aqui e anotada no Registro antes de virar código. Sem commit, salvo numa execução longa,
  em que o condutor commita por tarefa aceita.
- **Iteração:** perguntas ao dono em lote, numeradas, com a recomendação em cada uma.

## Notas de implementação

## Fontes

[^camadas]: Discussão de arquitetura de 2026-11-05, com as fontes da seção B36 da arquitetura: Seemann (*Composition Root*),
    Martin (*Clean Architecture*, caps. 22, 26 e 32), Percival e Gregory (*Architecture Patterns with Python*, cap. 13),
    NestJS (*Injection scopes*).
[^langchain]: Medição com `langchain` 1.4.9 e modelo fake em 2026-11-05: `create_agent` com 20 tools, p50 3,3 ms; skills e
    middlewares conferidos nas skills oficiais do LangChain e em docs.langchain.com.
[^aisdk]: Protocolo de stream de mensagens do AI SDK, ai-sdk.dev/docs/ai-sdk-ui/stream-protocol, lido em 2026-11-05.
[^openai]: Páginas de modelos e preços da OpenAI, lidas em 2026-11-05: `gpt-6-luna` a US$ 0,10 e 0,50 por milhão de tokens
    de entrada e saída; tool calling no Chat Completions só com effort `none`.
[^langfuse]: SDK `langfuse` 5.2.0, com suporte a Python 3.14; plano Hobby do Langfuse Cloud com 50 mil unidades por mês.

## Registro

**Mudança no spec** · 2026-11-05 · D16 a D21, T1, T1b, T2

- **O quê:** sessão só com identidades e ownership por predicado do dialeto (nova T1b); pastas por camada e área em T1; a
  role `api` vale para a API e para o código nos testes, com URL de administrador só para o oráculo; juiz é Claude pelo
  Claude Code headless, com `gpt-6.1-terra` de reserva; login simulado aprovado; `down -v` liberado. T1, T1b e T2 rodam
  nesta sessão, em sequência.
- **Por quê:** decisões do dono na revisão do spec.
- **Seções editadas:** §3.1, §3.2, §6.1, §6.2, §6.6, §8, §9.
- **Impacto na implementação:** T1 ganha a reorganização em pastas; T1b é nova; T2 passa a depender de T1b, troca a URL da
  API para a role e cria a URL do oráculo; T10 implementa o juiz pelo port com as duas opções; T11 deixa de trocar a URL.

**Mudança no spec** · 2026-11-05 · D22 a D24, §6.7, T4

- **O quê:** erro ensino: erro de tool nunca derruba o turno; parâmetro inválido volta como `invalid` com parágrafo que
  explica o erro e mostra um valor aceito; falha inesperada volta como `error` genérico. P4 e P5 viraram D23 e D24.
- **Por quê:** decisão do dono.
- **Seções editadas:** §3.1, §3.2, §6.5, §6.6, §6.7, T4, T10.
- **Impacto na implementação:** T4 ganha os status `invalid` e `error`, o campo `explanation` e os testes por tool; T10
  usa D23 no grader de trajetória.

**Nota de implementação** · 2026-11-05 · T1b

- **O quê:** `StudentSession` com `person_ids`, `cpf` e `enrollment_keys` (cada chave guarda a grafia do SAG e o
  `EnrollmentRef`; `enrollments` e `brands` são propriedades). A carga faz 2 consultas. Raízes: `contract`
  (`FinanceDialect.contract_of`), `mdl_user` (`LmsDialect.account_of`) e `protocol` (`ProtocolRow.id IN` a subconsulta de
  `SecretaryDialect.protocols_of` sobre a tabela privada). Fatura, desconto e acordo passam a `Via` contrato; inscrição,
  tentativa e log passam a `Via` conta. O pagador sai de `RepositoryAdapter.fetch_declared(CONTRACTS_WITH_PAYER)`, que só
  aceita consultas do registro, exige a raiz e aplica o ownership do `FROM`.
- **Fora do spec:** o `NOT EXISTS` da cascata virou `LEFT JOIN ... IS NULL`, mesma semântica (teste da cascata), porque
  dentro do `OR` o planejador estimava custo de 234 mil e ligava o JIT em toda consulta de protocolo (43 ms → 2 ms).
- **Medido** (p50, 100 cargas e 50 pessoas; antes = HEAD, mesmas consultas): carga da sessão 21,0 → 4,8 ms;
  `list_invoices` 23,5 → 25,2 ms; `list_protocols` 45,2 → 50,6 ms; resumo financeiro 29,2 → 33,0 ms. As três mais lentas
  aplicam o predicado do dialeto por varredura; T2 cria os índices de expressão.

**Checkpoint de implementação** · 2026-11-05 · T1

- **Feito:** bootstrap como composition root; infrastructure; tools em `application/agent/`; settings e dependências da fase;
  marcador `live`; pastas por camada e área, incluindo testes (151 arquivos com `git mv`). 615 testes verdes, a mesma contagem
  de antes.
- **Divergiu do spec:** providers em 4 módulos, pelo limite de imports; `ReferenceClock` recebe a data, porque infrastructure
  não importa bootstrap; `academic/term_calendar.py`, porque `calendar.py` sombreava a biblioteca padrão.
- **Próximo:** T1b.

**Checkpoint de implementação** · 2026-11-05 · T1b

- **Feito:** conforme a nota de implementação acima, revisada pelo condutor. 622 testes verdes, sem asserção alterada.
- **Divergiu do spec:** nada além da nota.
- **Próximo:** T2.

**Checkpoint de implementação** · 2026-11-05 · T2

- **Feito:** `02` (47 PKs, 74 FKs, 5 `NOT VALID`), `03` (22 índices, todos com uso confirmado em `pg_stat_user_indexes`), `04` e
  `05_roles.sh`. Volume principal recriado. API no Compose como `api`; `/health` 200. `make check` verde como `api`, com 635
  testes em 71 s, incluindo `tests/integration/core/test_api_role.py`.
- **Divergiu do spec:** a URL do oráculo não entrou no `Settings` da API, para a API nunca conhecer o administrador: fica numa
  classe própria dos testes, e o eval fará o mesmo. A role também perde `TEMP`, por isso o teste da cascata usa o
  administrador. `tool_call` tem PK composta e `position`, porque o id do modelo pode repetir entre mensagens e a ordem
  precisa ser refeita.
- **Medido** (p50, 50 pessoas, como `api`): `list_invoices` 25,2 → 14,6 ms; resumo financeiro 35,1 → 22,9 ms;
  `list_protocols` 53,5 → 37,2 ms; carga da sessão 4,6 → 2,9 ms.
- **Próximo:** patch final do dono e, na próxima sessão, a onda 1.
