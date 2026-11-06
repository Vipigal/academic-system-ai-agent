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
| D25 | A conversa nasce em `POST /conversations`, com id gerado pelo servidor; `/chat` responde `404` igual para id inexistente e id alheio | Decisão do dono: mantém o invariante 6 ao pé da letra e o cliente não escolhe id |
| D26 | O token da proposta vive em `ToolResult.client_only`, que nunca vai ao modelo nem ao histórico e só sai no `tool-output-available` | Decisão do dono: a garantia é por construção, não por prompt, e o histórico não guarda credencial |
| D27 | Log estruturado com `logging` da biblioteca padrão e formatador JSON | Recomendação aceita pelo dono: uma dependência a menos |
| D28 | Escrita por `RepositoryAdapter.write(*steps)`: cada passo é um lote de linhas (`add_all` e `flush`) ou um `Update` com o AND do dono, tudo numa transação. Tabela fora do registro não grava. O repositório confere o dono do pai por `fetch` antes de gravar | Decisão do dono: a sessão não sai do adapter e o `quality.toml` continua valendo |
| D29 | `requester_cpf` e `requester_name` entram em `ProtocolRow` como `deferred` com `raiseload`, só para a escrita; as leituras do dialeto seguem pela tabela privada. O número do protocolo e o da mensagem saem de `nextval` e `currval` no próprio INSERT | Decisão do dono, entre linha só de escrita, passo novo no core e esta. É o menor diff e dispensa conceito novo |
| D30 | O protocolo novo preenche `requester_name` e `author` com `sag.person.full_name`, lido por consulta privada só na confirmação | Decisão do dono: as duas colunas estão sempre preenchidas na origem, e a secretaria precisa saber quem pediu |
| D31 | A corrida de duas confirmações simultâneas é aceita e declarada nas evidências; o front desabilita o botão | Decisão do dono: o pior caso é um protocolo duplicado, em janela de milissegundos |
| D32 | Trancamento é do curso inteiro. Não existe serviço de trancamento de disciplina e nenhum será criado; o agente explica a diferença, inclusive quando o aluno diz "matrícula" para disciplina | Bug real de 06/11 (T14, §1); os dados só têm trancamento de vínculo |
| D33 | Uma fonte única de ações no domínio, por código de serviço: título, efeito, limite, situações aceitas, disciplina, pergunta e palavra. Código sem entrada falha fechado | Skill, DTO, card e rota não podem divergir; efeitos medidos no banco |
| D34 | `propose_protocol(action, enrollment, subject)`: `action` é enum com o efeito no nome, `enrollment` é obrigatório, `subject` é a disciplina citada, e `message` deixa de existir. Revoga, só para esta tool, a regra da §7 de não mudar o schema | Decisão do dono: o contrato tem de dizer o que está sendo feito |
| D35 | A mensagem do protocolo é sempre escrita pelo aluno, num campo vazio do card, em todos os serviços, e sai do token | Decisão do dono: o texto gravado em nome do aluno não pode vir do modelo |
| D36 | Palavra de confirmação digitada e exigida pelo servidor em ACA-010, ACA-012, ACA-013, ACA-014 e FIN-031 | Decisão do dono: mudam vínculo, matriz ou dívida, e todo pedido resolvido desses serviços foi atendido |
| D37 | A confirmação grava um evento em `agent.message`, com o papel novo `system_event`, montado pelo servidor, sem o texto do aluno. `down -v` liberado: os dados vêm dos CSVs e são transientes | Decisão do dono, no lugar da chamada de tool sintética que era a recomendação |
| D38 | Pedido de disciplina: o agente diz que não existe, orienta a procurar a secretaria e oferece `GEN-090`, sem prometer solução | Caminho real e não destrutivo; a ontologia `servico` já proíbe a promessa |
| D39 | Produção usa a data de hoje, sem variável de ambiente; testes e eval injetam 31/10/2026, a data da foto dos dados. Protocolo novo usa o instante real | Decisão do dono; revoga a data fixa de A16 em produção. O gabarito continua estável |
| D40 | Regra de escopo no prompt `v2`: fora de assuntos acadêmicos, financeiros, de secretaria e do AVA do aluno, recusa | O agente deu receita de bolo e código Python no uso real |
| D41 | Itens `critical` no eval: falha de proposta ou trajetória em qualquer repetição reprova a rodada. Baseline antes da T14, com o bug registrado, e a mesma rodada depois | Decisão do dono: é o case da entrega |
| D42 | Nome em português e efeito nos DTOs de serviço, e nome em português dos 8 cursos. Disciplinas continuam com o modelo | O join de código e nome já existe (`ServiceDto`), mas em inglês e sem o efeito; 260 disciplinas não cabem num mapa fixo |
| D43 | O baseline e a rodada final da T14 usam a composição enxuta: itens críticos com 5 repetições e o resto com 1, em 146 execuções. A estabilidade fora dos críticos fica para a matriz de modelos | Decisão do dono: as 346 execuções da composição anterior gastavam plano no juiz sem ajudar a provar o bug |
| D44 | O código mede o efeito verificável (proposta), as tools sem as quais não há resposta, a recusa e o que não pode aparecer na resposta. Se a resposta está correta e satisfatória é com o juiz. O grader de fatos sai. Os 185 fatos ficam no golden, para provar pelo banco que a referência, o gabarito do juiz, está certa | Decisão do dono: avaliamos o que o modelo diz a pessoas, e checar citação mede completude e reprova resposta válida. A Anthropic recomenda rubrica para agentes conversacionais, porque responder pode ter várias formas corretas[^evals] |
| D45 | O juiz é calibrado em duas etapas: 40 respostas de rótulo conhecido antes do baseline (20 referências corretas e 20 adulteradas), com TPR e TNR e meta de 18 em 20 em cada classe; e a conferência do dono em cerca de 20 vereditos reais, depois do baseline | Decisão do dono: a calibração humana é dele, como especialista do domínio. 40 fica abaixo dos 60 que Hamel Husain indica para um intervalo útil[^evals], limite declarado nas evidências |
| D46 | Os resultados aparecem numa página HTML única, gerada da rodada e commitada com ela, com a abertura pela regra crítica, `pass^5`, itens, resposta, juiz e a conferência do dono. Notas não são publicadas no Langfuse; o trace entra só como link opcional | Decisão do dono: o examinador pode não ter tempo nem acesso ao Langfuse, que serve de inspiração para a página |
| D47 | PR-08 exige só `list_enrollments`. TR-09 aceita perguntar qual matrícula ou propor `ACA-010` na ativa | Decisão do dono: a base não tem aluno com duas matrículas ativas, e a matrícula formada não pode ser trancada. O backend passa a garantir isso na correção do protocolo |

### 3.2 Pendentes (confirmar na revisão)

| # | Proposta | Alternativa | Recomendação |
|---|---|---|---|
| P6 | Teste de carga com Locust e modelo fake (`APP_AGENT_MODEL=fake`) | k6 | A proposta: mesma linguagem do projeto; mede a API sem custo de LLM |
| P8 | Ponto de atenção do dono, sem tarefa nesta fase: boa parte dos "unitários" sobe banco e varre os dados, o que deixa a suíte lenta e só funciona porque os dados são fixos. Código novo testa regra com fake, e banco só na fronteira real | Reescrever a suíte agora | Não reescrever antes da entrega: as varreduras sustentam as provas de segurança. Declarar a limitação nas evidências |

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

Criação (D25): `POST /conversations` com `Authorization: Bearer <jwt>`, sem corpo, devolve `201 {"id": "<uuid>"}`. O id é
gerado pelo servidor e o dono é a pessoa do token. O front passa esse id ao `useChat`.

Pedido: `POST /chat` com `Authorization: Bearer <jwt>` e corpo no formato do AI SDK 7, `{id, messages: [...]}`. O servidor
usa o `id` como id da conversa e só a última mensagem de papel `user`; o resto do corpo é ignorado (D14).

Resposta: `200 text/event-stream` com o header `x-vercel-ai-ui-message-stream: v1`. Cada evento é uma linha
`data: <json>` seguida de linha em branco, nesta ordem possível:

| Evento | Quando |
|---|---|
| `start` | Abertura, com `messageId` |
| `text-start`, `text-delta`, `text-end` | Texto do modelo |
| `tool-input-available` | O modelo pediu uma tool: `toolCallId`, `toolName`, `input` |
| `tool-output-available` | Resultado da tool: `toolCallId`, `output` (o `ToolResult` serializado, com `client_only`) |
| `error` | Falha, com `errorText` genérico, sem detalhe interno |
| `finish` | Fim; seguido de `data: [DONE]` |

Os nomes exatos dos eventos são conferidos contra a documentação do AI SDK 7 no início de T9; divergência vira "Mudança no
spec". Conversa de outro aluno ou inexistente: mesma resposta, `404`, com a rota de criação acima como único jeito de nascer
uma conversa (D25).

### 6.4 Proposta e confirmação de protocolo (T8)

Estado atual. A [T14](/docs/plans/agente/t14-protocolo-robusto.md), §6, substitui este contrato: tira a mensagem do token, e o corpo
passa a ter `conversation_id`, `message` e `confirmation_word` (D34 a D37).

- `propose_protocol` passa a devolver, além da proposta, um `token`: HMAC-SHA256 com segredo de settings sobre `person_id`,
  matrícula, serviço, mensagem e validade de 15 minutos. O token fica em `ToolResult.client_only` (D26): o conversor o retira
  do JSON que vai ao modelo, o histórico não o grava e o front o lê do `tool-output-available`.
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
`tool_call.result` guarda o que o modelo viu, sem `client_only` (D26).

### 6.6 Eval (T3 e T10)

- **Golden set:** `src/evals/golden/questions.yaml`, um item por pergunta do catálogo (60), e `redteam.yaml`. Campos: `id`,
  `kind` (`answerable`, `no_data`, `refusal`, `attack`), `split` (`dev` ou `holdout`, estratificado por área e `kind`, cerca
  de 30% em holdout), `question`, `student` (`marca:RA`), `tools.expected` e `tools.forbidden`, `facts` (nome da consulta
  SQL, parâmetros e formato: `brl`, `date`, `int`, `percent`, `text`), `forbidden_text`, `rubric` e `reference` (a resposta
  ideal do catálogo).
- **Consultas nomeadas:** `src/evals/oracle_queries.py`, `nome → SQL`, independentes das tools e dos services.
- **Graders (D44):** trajetória (D23), com só as tools necessárias; proposta; recusa determinística (nenhuma tool de dado,
  nenhum texto proibido); vazamento (nenhum identificador de outra pessoa, reaproveitando a ideia do invariante do agente
  comprometido); juiz que aprova, reprova ou diz `unknown` em cada item da rubrica, raciocinando antes do veredito.
- **Juiz (D19):** o runner grava os pedidos de julgamento em JSONL, sem o nome do modelo avaliado, e um segundo passo os
  entrega ao Claude Code em modo headless (`claude -p`) com um agente dedicado em `.claude/agents/`, sem ferramentas e com
  saída em JSON validado. Lotes de itens por chamada, para reduzir overhead. Com a opção de reserva, o mesmo pedido vai a
  `gpt-6.1-terra` pela API. O juiz é um port em `src/evals/judge/`, com as duas implementações.
- **Execução:** `python -m evals.run --model gpt-6-luna --split dev --repeat 3`. Chama o agente direto, sem HTTP, com a
  sessão de cada aluno. Registra modelo, effort, versão do prompt, hash das skills e das descrições das tools.
- **Saída (D46):** JSONL por execução, com o `trace_id`; relatório Markdown e página HTML com acerto por grader e por área,
  pass@1 médio, `pass^5` nos itens críticos, estabilidade entre repetições, latência p50 e p95, tokens e custo. Traces no
  Langfuse com tags `eval`, modelo e versões.
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
- **Não pode mudar:** os invariantes 1 a 11 da arquitetura; as 19 tools e seus schemas visíveis ao modelo, exceto
  `propose_protocol` (D34), porque o `token` não chega ao modelo (D26); os 609 testes atuais, que só mudam de import em T1.

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
| T14 | Protocolo robusto | Baseline de T10 | `domain/protocol/`, `application/protocol/`, `tools/protocol.py`, ontologias, skills, prompt `v2`, `04_agent_schema.sql`, relógio, `src/app/` | Unitário, integração na fronteira, navegador | [t14](/docs/plans/agente/t14-protocolo-robusto.md) |
| T13 | Evidências e README | T10, T11, T14 | `docs/evidencias.md`, `README.md`, `loadtest/`, resultados do eval | Execuções reais | [t13](/docs/plans/agente/t13-evidencias.md) |

### Ondas e paralelismo

- **Arrumação (sessão de 2026-11-05, em sequência):** T1 → T1b → T2. T1 move e cria o esqueleto; T1b muda as consultas
  de ownership; T2 deriva os índices dessas consultas, aplica a role e recria o volume. Ao fim, o código está organizado e a
  próxima sessão começa pela onda 1.
- **Onda 1:** T3, T4, T5, T6 e T7, cada uma com o seu módulo de providers no bootstrap ou, em T3, só `src/evals/`.
- **Onda 2:** T8, T9 e T10. Cada rota é testada num app de teste; a ligação no `ApiFactory` fica para T11.
- **Onda 3:** T11, que liga as rotas, sobe o Compose e roda o fluxo inteiro.
- **Onda 4:** T12 e T13.
- **Caminho crítico:** T1 → T1b → T2 → T4 → T9 → T11 → T12.
- **Reta final, a partir de 2026-11-06, em sequência:** T10 com o baseline do bug, T14 (que também fecha o que faltou de T12), rodada
  final, T13. Bugs visuais do front ficam numa sessão própria.

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
[^evals]: Pesquisa de 2026-11-06. Anthropic, *Demystifying evals for AI agents*, 09/01/2026,
    anthropic.com/engineering/demystifying-evals-for-ai-agents; Hamel Husain, *Using LLM-as-a-Judge*, revisado em set/2026,
    hamel.dev/blog/posts/llm-judge; *Catching One in Five*, arXiv 2606.10315, jun/2026; *τ-bench*, arXiv 2406.12045.

## Execução

### Execução de 2026-11-05

#### Registro de decisões

Repo: este. Branch: `feat/agente`, a partir da `main`. Sem push.
Escopo desta execução, na ordem: o agente com skills; o histórico; a identidade com login simulado; a observabilidade; a
confirmação de protocolo; o chat com stream; a montagem com o ponta a ponta; o front de chat; o golden set e o red team; o runner
de eval. As evidências e o README ficam para outra execução.
Até dois implementadores ao mesmo tempo. O modelo segue a sugestão de cada tarefa. Cada tarefa passa pelo gate do condutor; a
revisão por agente de contexto limpo acontece nos marcos: agente e chat junto com a confirmação de protocolo, front no navegador, e
eval.

| Decisão | Por quê | Quem decidiu | Tipo | Se mudar, afeta | Commit |
|---|---|---|---|---|---|
| A conversa nasce em `POST /conversations` com id do servidor, e `/chat` dá 404 igual para id alheio e inexistente | mantém "dado alheio e inexistente têm a mesma resposta" sem o cliente escolher id | você | pilar | o chat e o front | — |
| O token da proposta fica num campo só para o cliente, fora do que o modelo e o histórico recebem | garantia por construção, sem depender de prompt | você | pilar | o envelope, o agente, a proposta, o chat | — |
| Log estruturado com a biblioteca padrão | uma dependência a menos | você (recomendação aceita) | detalhe | a observabilidade | — |
| Você acrescenta `APP_JWT_SECRET`, `APP_PROPOSAL_SECRET` e `APP_DEV_LOGIN` ao `.env` | o `.env` é seu | você | ambiente | a verificação no Compose | — |
| O `RepositoryAdapter` ganha um `write` com passos: lotes de linhas e `Update`, numa transação, com `flush` entre os passos. O repositório confere o dono do pai antes de gravar | a sessão não sai do adapter e o gate atual continua valendo, com menos conceitos que uma regra de escrita por tabela | você | pilar | o histórico e a confirmação de protocolo | — |
| `requester_cpf` e `requester_name` entram no model do protocolo, sem carregar por padrão e com erro se alguém os acessar | é o menor diff; você escolheu isso em vez de uma linha só de escrita, que era a minha recomendação | você | pilar | a confirmação e o teste de colunas privadas | — |
| O protocolo novo leva o nome do aluno em `requester_name` e `author` | as duas colunas estão sempre preenchidas na origem | você | pilar | a confirmação | — |
| Duas confirmações no mesmo instante podem abrir dois protocolos: limite aceito, a ser declarado nas evidências | o pior caso é um duplicado, em janela de milissegundos; o front desabilita o botão | você | pilar | a confirmação e o front | — |
| A verificação no navegador confirma protocolo com um aluno que nenhum item do golden set cita | confirmar no Compose grava de verdade, e o eval lê esses dados | você | ambiente | o front | — |
| Os testes `live` e a rodada de eval rodam com o `.env` carregado no shell pelo condutor, sem imprimir valores; os implementadores não tocam no arquivo | é o único lugar com a chave | você | ambiente | os critérios `live` | — |
| Primeiro o caminho até o ponta a ponta, golden set e runner por último | o objetivo é testar de ponta a ponta o quanto antes; nada do caminho depende deles | você | detalhe | a ordem | — |

### Execução de 2026-11-06: runner de eval e baseline do bug de trancamento

#### Registro de decisões

Repo: este. Branch: `feat/agente`. Sem push.
Escopo desta execução: o runner de eval, com graders, juiz, relatório e os itens novos do golden, até o baseline salvo e commitado.
Nenhuma correção do protocolo entra aqui. Um implementador, um revisor ao fim do eval, e o dono roda a rodada `live` e o baseline.

| Decisão | Por quê | Quem decidiu | Tipo | Se mudar, afeta | Commit |
|---|---|---|---|---|---|
| Baseline com 146 execuções: críticos com 5 repetições e o resto com 1 | a repetição só importa onde se mede o bug; a estabilidade geral fica para a matriz de modelos | você | pilar | o baseline e a rodada final | — |
| O front, os docs e o eval vão em commits separados, antes do baseline | o hash do baseline reproduz o estado inteiro, inclusive o plano que descreve o bug | você | detalhe | só o histórico do git | — |
| Sem entrevista prévia e sem conferência do ambiente; o auto-continue no limite de uso segue desligado | escolha sua na abertura: se o limite estourar, uma sessão nova retoma pelo spec | você | ambiente | a continuidade da execução | — |
| Os 3 itens de trancamento do holdout rodam no baseline | o antes e depois precisa cobri-los, e as frases já estão no spec | o dono | detalhe | a composição do baseline | — |
| O juiz roda em Sonnet, com a versão fixa, em lote e pelo plano | reprodutibilidade, custo menor, e a rubrica não reprova a rodada sozinha | você | detalhe | os vereditos da rubrica | — |
| Você confere cerca de 20 vereditos reais na página de resultados, depois do baseline | a calibração humana é sua; a conferência por mim seria uma IA validando outra | você | detalhe | a concordância registrada | — |
| O eval mede só o primeiro turno e julga em lote | limites declarados nas evidências; itens de múltiplos turnos se decidem depois da correção do protocolo | você | detalhe | a matriz de modelos | — |

## Registro

**Mudança no spec** · 2026-11-06 · D44 a D47, §6.6, T10, T14

- **O quê:** o grader de fatos sai e a correção da resposta passa ao juiz; relatório com `pass^5`; calibração com 40 respostas de rótulo
  conhecido e conferência do dono; juiz com versão fixa e `unknown`; `trace_id` no JSONL; página HTML de resultados, sem publicar notas no
  Langfuse; PR-08 e TR-09 reconfigurados.
- **Por quê:** a primeira rodada real deu 0% com respostas boas: o grader media citação, e o PR-08 exigia uma tool desnecessária.
  Decisões do dono depois de ler as respostas e a pesquisa de 2026-11-06.
- **Seções editadas:** §3.1, §6.6, Fontes; `t10-runner-eval.md`; `t14-protocolo-robusto.md`, §6.2, com as chaves do bloco de confirmação.
- **Impacto na implementação:** menos código no grader; duas peças novas, a calibração e a página. O PR-08 em 2 de 5 repetições propôs trancar
  uma matrícula já trancada: é um bug real, que o baseline registra e a correção do protocolo resolve com a recusa `enrollment_status`.

**Mudança no spec** · 2026-11-06 · T12 (V5)

- **O quê:** as sugestões da conversa vazia passam a ser quatro, uma por área do README §1; sai "Quero trancar uma disciplina".
- **Por quê:** decisão do dono. Não há serviço de protocolo para trancar disciplina, então a sugestão levaria a uma recusa.
- **Seções editadas:** `t12-front.md`, V5.
- **Impacto na implementação:** só `Conversation.tsx`; typecheck limpo e 390 px sem rolagem lateral.

**Mudança no spec** · 2026-11-06 · T12 (V8 a V11)

- **O quê:** markdown na resposta do assistente, painel de debug por tool com rótulo em português, nome técnico, input e output,
  e avatar de robô.
- **Por quê:** pedido do dono, para o avaliador ver o que o modelo chamou e recebeu.
- **Seções editadas:** `t12-front.md`, tabela de decisões.
- **Impacto na implementação:** dependências novas `react-markdown` 10.1.0 e `remark-gfm` 4.0.1; o bundle passa de 500 kB e o
  Vite avisa no build.

**Checkpoint de implementação** · 2026-11-06 · T12, V8 a V11

- **Feito:** `toolLabels.ts` com as 20 tools, `ToolCallView.tsx` (`details` com estados consultando, consultou e falhou),
  `MessageView.tsx` com markdown e robô, estilos de debug e markdown; correção da barra do topo do chat em 390 px.
- **Critério → evidência:** `npm run typecheck` e `npm run build` limpos; pelo DevTools, "Como estão minhas notas?" com
  `UniMontanhas:070114` virou lista em `<ul>`, e o painel de `list_subject_records` mostrou nome, input e output; em 390 px com
  emulação de celular, layout de 390 px no chat com o painel aberto.
- **Corrigido no caminho:** no checkpoint anterior, o chat só tinha sido medido com janela de 500 px; em 390 px, o "Sair" estourava
  a largura. O texto da marca some no topo do chat no celular.

**Mudança no spec** · 2026-11-06 · T12 (V1 a V7)

- **O quê:** a T12 ganha a seção "Identidade visual e login por unidade": tokens visuais, login em dois passos (unidade e aluno) com
  aviso de tela de teste, conversa vazia com sugestões e a rota dev-only `GET /auth/dev-students`.
- **Por quê:** pedido do dono para a entrega, depois da exploração do site da instituição. Sem logo nem nome do grupo, porque o
  repositório fica público como projeto dele.
- **Seções editadas:** `t12-front.md`.
- **Impacto na implementação:** o front muda já; a rota em `src/api/` só entra depois do baseline da T10 commitado, para não sujar o
  hash nem o gate do eval.

**Checkpoint de implementação** · 2026-11-06 · T12, passo 1 (front)

- **Feito:**
  - tokens visuais em `styles.css` e Work Sans no `index.html`;
  - login em dois passos (`UnitStep`, `StudentStep`), com a lista de uma amostra fixa (`devStudentsSample.ts`) no formato da rota;
  - barra do topo (`Topbar`) e chat em card central, com a conversa extraída para `Conversation.tsx`, saudação e sugestões;
  - mensagens com bolha por parte de texto, tools como linhas discretas e card de protocolo com estados de proposta, confirmado e
    recusado;
  - `isRecord` movido para `guards.ts`, para não criar import circular entre `api.ts` e `students.ts`.
- **Critério → evidência:**
  - `npm run typecheck` e `npm run build` limpos;
  - pelo DevTools, em 1440 px: UniMontanhas Presencial, busca por RA, entrada com `UniMontanhas:070114`, saudação, sugestão de
    faturas com stream e tools;
  - em 390 px com emulação de celular: `scrollWidth` igual a 390 no login e no chat; com a rede offline, o login mostra o erro;
  - nenhum protocolo confirmado e `UniSaoPaulo:181722` fora da amostra.
- **Não verificado:** o card de protocolo no navegador (confirmar está bloqueado até o baseline) e o erro do chat com a API fora (a
  API é compartilhada com o eval).
- **Falta:** passo 2 da Ordem, a rota `GET /auth/dev-students` e a troca da amostra pela chamada.

**Mudança no spec** · 2026-11-06 · D43, T10

- **O quê:** o baseline passa de 346 para 146 execuções: críticos com 5 repetições e o resto com 1. A CLI ganha `--critical-repeat`.
- **Por quê:** decisão do dono na abertura da execução da T10. A repetição só importa onde se mede o comportamento instável do bug.
- **Seções editadas:** §3.1; `t10-runner-eval.md`, em "O que fazer" e "Baseline".
- **Impacto na implementação:** a rodada final da T14 repete a mesma composição; a estabilidade entre repetições fora dos críticos só
  será medida na matriz de modelos.

**Mudança no spec** · 2026-11-06 · D32 a D42, P8, §3, §6.4, §7, §8, T10, T13, T14

- **O quê:** nova T14, com o pacote de correção do protocolo, o relógio real e a regra de escopo. T10 ganha o estado em que parou, o
  caso âncora, os itens `TR`, `SV` e `ES`, o `ProposalGrader`, os itens críticos e o baseline. T13 ganha o case e passa a depender
  de T14. Nova ordem: T10 com baseline, T14, rodada final, T13.
- **Por quê:** no uso real, o agente propôs trancar o curso inteiro quando o dono pediu para trancar uma disciplina, e o protocolo foi
  confirmado. Investigação e decisões do dono na sessão de 2026-11-06. O dono também pediu a data real em produção.
- **Seções editadas:** §3.1, §3.2, §6.4, §7, §8; `t10-runner-eval.md`; `t13-evidencias.md`; `t14-protocolo-robusto.md` novo.
- **Impacto na implementação:**
  - T10 retoma de onde parou e não pode incluir correção da T14 antes do baseline;
  - `docker compose down -v` antes do baseline, porque o `181722` tem um `ACA-010` residual, que esconderia o bug e quebra `test_pr02`;
  - T12 continua sem checkpoint: a F6 da T14 faz a verificação no navegador, e os 390 px ficam com os bugs visuais;
  - `docs/architecture.md` precisa de correção pontual em A16, §5.6 e no papel de `agent.message`, ao implementar.

**Checkpoint de implementação** · 2026-11-06 · T3

- **Feito:**
  - 60 itens em `questions.yaml` e 30 ataques em `redteam.yaml`;
  - 185 fatos amarrados a consultas nomeadas, num pacote `src/evals/oracle_queries/` dividido por área para caber no limite de
    tamanho;
  - o oráculo com settings próprias;
  - o validador `python -m evals.golden check`.
- **Critério → evidência:**
  - o validador roda pelo condutor e termina com "Problemas: 0 OK";
  - 60 perguntas e 30 ataques;
  - por kind: answerable 46, attack 30, no_data 5, refusal 9;
  - split com dev 62 e holdout 28, e holdout em todas as áreas;
  - todos os números dos fatos aparecem na resposta ideal do catálogo, salvo as duas divergências abaixo;
  - `make check` inteiro verde, com 1.254 testes.
- **Divergências do catálogo, com a causa:**
  - FI-03: o estorno é 07/12/2024. O pagamento foi às 00:29 UTC de 08/12, que em Brasília ainda é 07/12, e o gabarito segue Brasília,
    como a API.
  - SR-05: 01/02/2023, por D13.
- **Decidido pelo implementador, para o plano de review:**
  - as armadilhas secundárias de FI-08, CR-02 e CR-03 são verificadas com aluno próprio dentro do item, sem item novo;
  - `tools.forbidden` só tem `propose_protocol` em dois ataques de terceiro mandando agir, e o resto vazio, por D23.
- **Para o runner:** o grader de recusa usa `tools.expected`, porque RE-04, RE-05 e RE-08 são recusas que precisam de tool.

**Checkpoint de implementação** · 2026-11-06 · T11

- **Feito:**
  - o `ApiFactory` liga login (só com `dev_login`), chat e confirmação, por `StudentRoutes`, junto com a observabilidade;
  - CORS de `APP_CORS_ORIGINS`;
  - `RequestLog` no bootstrap: `request_id` por request e uma linha JSON por request; o access log do uvicorn está desligado;
  - `aclosing` no stream do agente;
  - `hide_parameters=True` no banco;
  - log "Turno concluído" com modelo, tokens, latência e motivo de parada.
- **Critério → evidência:**
  - e2e `live` com `gpt-6-luna` passou: proposta, `confirm` `201` e o protocolo novo em `list_protocols`, numa transação desfeita;
  - e2e com fake verde, com `request_id` e `trace_id` iguais em todas as linhas de um request;
  - fluxo real no Compose: login, conversa e FI-01 em stream, com trace no Langfuse;
  - 986 testes verdes fora o golden set;
  - 6 contratos de camada kept; ruff, flake8, `tools.quality` e Pyright limpos.
- **Divergiu do spec:**
  - o middleware de log fica no bootstrap, porque a presentation não importa infrastructure;
  - `/health` fica fora do log de request;
  - o logger `langfuse` vai a ERROR com o tracing desligado;
  - a confirmação não roda contra o Compose, para não gravar protocolo nos dados do eval.
- **Limite:** abaixo de `StudentAgent.stream`, o `astream` do LangGraph fecha pelo finalizador de geradores, porque o LangGraph o tipa
  como `AsyncIterator`.
- **Próximo:** front.

**Checkpoint de implementação** · 2026-11-06 · T7 e T4, trace real

- **Feito:** o trace `7e5bee5821e437f09358d814c865012d`, do chat real no Compose com FI-01, está no Langfuse Cloud. A raiz é `chat.turn`,
  com `user_id` em hex de 32 caracteres, diferente do `person_id`, e `session_id` igual ao id da conversa. Tags: `model:gpt-6-luna`,
  `prompt:student_agent_v1` e `skills:<hash>`. Entrada e saída do span vão nulas.
- **Dentro do trace:** três gerações `ChatOpenAI` (2,3 s, 1,2 s e 2,1 s), as tools `load_skill` (2 ms) e `get_financial_summary`
  (43 ms), e o turno inteiro em 5,98 s.
- **Fecha:** o pendente da observabilidade e o do agente.

**Nota de implementação** · 2026-11-06 · revisão do marco (agente, chat, confirmação, identidade, histórico, observabilidade)

- **Bloqueante:** `full_name_of` lia o nome de qualquer `person_id`, numa sessão fora do adapter. Volta para a confirmação como
  consulta declarada com raiz `PersonRow`, igual a `CONTRACTS_WITH_PAYER`.
- **Corrigido junto:** falha de tool sem artifact gravada como `invalid` em vez de `error`; nome da tool no log de falha; limite de
  4.000 caracteres e de 200 mensagens no corpo do chat; `aclosing` no stream do agente; `request_id` por request, com middleware.
- **Fica para o plano de review:** os dois adaptadores de PyJWT são quase iguais e podem virar uma classe só.
- **Commit da correção (exceto `aclosing` e `request_id`, que vão com a montagem):** `SqlRequesterDirectory` lê o nome por
  `fetch_declared(REQUESTER_NAMES)`, com raiz `PersonRow`; com a sessão de outra pessoa, o nome volta `None`, igual ao de uma
  inexistente. A falha só vira `error` quando o texto é o envelope do nosso `on_crash`, porque tool inexistente e limite de tools
  também chegam com `status="error"` do LangChain e, pela D22, são `invalid`. 351 testes verdes; nenhum protocolo residual.
- **Conferido sem achado:** JWT e token da proposta (assinatura, `alg=none`, validade e cruzamento); `404` uniforme; `client_only` fora
  do modelo, do histórico e do Langfuse; invariante 11; transação do `write`.

**Checkpoint de implementação** · 2026-11-06 · T9

- **Feito:** `ChatService` com `create_conversation` e turno em stream; `UiMessageStream` no protocolo do AI SDK 7; `ChatRouter` com
  `POST /conversations` e `POST /chat`; `ChatProviders` e `ChatAgentScope` no bootstrap; colisão de posição vira
  `ConversationConflictError`. Ligação na montagem.
- **Critério → evidência:** 47 testes do chat e 75 com os do agente verdes; o `404` sai antes do stream e é igual para conversa alheia,
  inexistente e mal formada; `client_only` sai no stream e não fica em `agent.tool_call.result`; falha do provedor, timeout e cliente
  desconectado não gravam; `curl -sN` contra uvicorn efêmero mostra `text-delta` chegando aos poucos. Gate do condutor nos arquivos da
  tarefa: ruff, flake8, `tools.quality`, 6 contratos, Pyright limpos; mypy só acusa o golden set, em andamento.
- **Mudança no contrato (§6.3), conferida no fonte do AI SDK 7.0.163:** `start-step` e `finish-step` em volta de cada passo, exigidos
  com tool no backend; `text-*` com `id`, e um bloco novo depois de cada tool; `error` seguido de `finish-step`, `finish` e `[DONE]`;
  headers iguais a `UI_MESSAGE_STREAM_HEADERS`.
- **Divergiu do spec:** o conteúdo gravado do assistente é todo o texto transmitido; vários passos de tool de um turno voltam do
  histórico como uma só mensagem com todas as chamadas, porque a tabela não guarda a divisão em passos.
- **Próximo:** montagem.

**Checkpoint de implementação** · 2026-11-05 · T8

- **Feito:** token assinado em `client_only`; `ProtocolOpening` no domínio; `SqlProtocolWriter` por `write`; `ProtocolConfirmation` e
  `POST /protocols/proposals/confirm`; `full_name` por consulta privada; mapa fixo das 27 unidades no dialeto. Ligação na montagem.
- **Critério → evidência:** 3 linhas com número da sequência e SLA certo pelo oráculo, na mesma transação (`GEN-090`: 72 h); `201`; `404`
  de corpo igual para token de outro aluno, alterado, expirado, lixo e matrícula alheia; `409`; `422`; `401`; `pg_stat_xact_user_tables`
  só nas 3 tabelas; token fora do JSON do modelo; log sem dado pessoal; nenhum resíduo. Gate do condutor nos arquivos da tarefa, com 6
  contratos, ruff, flake8, `tools.quality`, mypy e Pyright limpos, 223 testes verdes.
- **Divergiu do spec:** `channel`, `priority`, `sla_breached`, `changed_by` e `author` também são adiadas com `raiseload`, por serem só de
  escrita; o log não traz o número do protocolo, porque o padrão de CPF do `JsonFormatter` apaga qualquer número de 11 dígitos; serviço
  inativo e mensagem vazia dão `422`; CPF e `student_id` vão na forma canônica, com zeros à esquerda.
- **Limite:** `select(ProtocolRow.requester_cpf)` explícito passa pelo guard, filtrado ao dono, e `undefer` também contorna o
  `raiseload`: é o custo da escolha de manter as colunas no model. Vai ao plano de review.
- **Próximo:** montagem, depois do chat.

**Checkpoint de implementação** · 2026-11-05 · T4

- **Feito:** `StudentAgent` com stream e execução completa, conversor com `content_and_artifact`, 7 skills, prompt `v1`, erro ensino,
  limites, retry, semáforo do provedor, modelo fake.
- **Critério → evidência:** teste `live` de FI-01 passou com `gpt-6-luna`, chamando `get_financial_summary` e respondendo R$ 277,05;
  273 testes do agente verdes; gate do condutor nos arquivos da tarefa, com 6 contratos, ruff, flake8, `tools.quality`, mypy e Pyright
  limpos. Montar o agente: p50 6,2 ms, p95 8,2 ms em 300 repetições; turno completo com fake: 20,8 ms.
- **Divergiu do spec:** o schema visível ganhou `pattern`, `minimum`, `maximum` e `additionalProperties: false`, porque a faixa e o
  formato têm de sair do tipo; nomes, tipos e obrigatórios não mudam, mas isso toca a §7 e vai ao plano de review. `period` mal formado
  vira `invalid` no conversor, e `ToolInputError` existe sem tool que a levante hoje. Limite de modelo com `exit_behavior="error"`.
  Mensagens nativas de tool inexistente e de limite de tools chegam em inglês ao modelo.
- **Pendente:** o trace do teste `live`, conferido com a observabilidade no fluxo da montagem.
- **Próximo:** chat com stream.

**Mudança no spec** · 2026-11-05 · D29 a D31, T8

- **O quê:** CPF e nome do requerente em `ProtocolRow`, adiados e só para escrita; números pelas sequências no INSERT; nome do aluno
  gravado; corrida de confirmação aceita.
- **Por quê:** decisões do dono ao receber a dúvida da confirmação. A arquitetura exigia CPF só em tabelas fora de `Base.metadata`, e
  o `write` só aceita models.
- **Seções editadas:** §3.1; arquitetura 5.4 e 5.6, com a correção do que ficou errado.
- **Impacto na implementação:** `test_no_model_declares_a_tax_id...` ganha exceção explícita para essas duas colunas, e passa a exigir
  `deferred` com `raiseload`; o domínio abre o protocolo sem número; o front desabilita o botão.

**Checkpoint de implementação** · 2026-11-05 · T7

- **Feito:** `Tracing`, `TraceInfo` e `UserPseudonym`; `JsonFormatter` e `LogContext`; `Observability.start`; `@observe` no
  `HealthService`.
- **Critério → evidência:** sem chaves ou com uma chave só nada é enviado; `user_id` é HMAC; log em JSON sem CPF, com 13 testes verdes.
  Gate do condutor nos arquivos da tarefa: ruff, flake8, `tools.quality`, 6 contratos, Pyright limpos.
- **Pendente:** o trace real no Langfuse. Ele será conferido no fluxo `live` da montagem, porque o script de exemplo não entra no ok
  dado para carregar o `.env`, que cobre os testes `live` e a rodada de eval. A aceitação final desta tarefa depende disso.
- **Divergiu do spec:** o SDK 5 não aceita usuário e tags no `CallbackHandler`; eles vão por `propagate_attributes`, num context
  manager que o chat usa em volta do agente. A chave do `user_id` deriva de `jwt_secret`, com separação de domínio. O log não tem campo de horário, por não estar na lista fixa.
- **Próximo:** confirmação de protocolo e, depois do agente, chat.

**Checkpoint de implementação** · 2026-11-05 · T5

- **Feito:** entidades e port de conversa; `persistence/agent/` com models, ownership, mappers e `SqlConversationRepository`
  (`create`, `append`, `window`); `RepositoryAdapter.write(*steps)` com `WritePlan` (D28); `HistoryProviders`.
- **Critério → evidência:** tabelas novas cobertas por `test_every_mapped_table_declares_ownership`; alheia e inexistente levantam o
  mesmo `ConversationNotFoundError`; `write` com rollback, dono no `Update` e recusa de tabela sem registro, em
  `tests/integration/core/test_adapter_write.py`. `person_id` só em `conversation`, por `04_agent_schema.sql`. Gate do condutor nos
  arquivos da tarefa: ruff, flake8, `tools.quality`, 6 contratos, Pyright limpos, mypy sem erro nos arquivos dela, 42 testes verdes.
- **Divergiu do spec:** `test_api_role.py` passa a ignorar `agent.*` em `mapped_tables`, porque a checagem de leitura só compara os
  schemas de origem; a escrita em `agent` tem teste próprio. `result` fica na linha de `tool_call`, então a janela por mensagem nunca
  separa chamada e resultado. Duas trocas simultâneas na mesma conversa colidem no `UNIQUE (conversation_id, position)`: o chat trata.
- **Próximo:** chat, depois do agente e da observabilidade.

**Checkpoint de implementação** · 2026-11-05 · T6

- **Feito:** JWT HS256 atrás do port `TokenCodec`; `IdentityService` com login e autenticação; `POST /auth/dev-login`; dependência
  da `StudentSession`; `person_of` em `StudentSessionRepository`. Ligação no `ApiFactory` fica para a montagem.
- **Critério → evidência:** login devolve token; sem token, alterado, expirado, `sub` desconhecido e `alg=none` dão `401` igual; o
  `person_id` vem só do token; `dev_login` desligado dá `404`; dois alunos no mesmo fluxo têm sessões disjuntas. Gate do condutor nos
  arquivos da tarefa: ruff, flake8, `lint-imports` com 6 contratos, `tools.quality`, mypy e Pyright limpos, 50 testes verdes.
- **Divergiu do spec:** `marca` é a grafia de origem do SAG, como no catálogo; o `exp` usa `time.time()`, porque a validade do token
  precisa do relógio real e não do relógio de referência; sessão vazia dá `401`.
- **Próximo:** observabilidade, depois do histórico ou do agente liberarem vaga.

**Mudança no spec** · 2026-11-05 · D28, T5, T8

- **O quê:** `RepositoryAdapter.write(*steps)` como único caminho de escrita. O adapter hoje só lê, e só ele pode abrir sessão.
- **Por quê:** decisão do dono, ao receber a dúvida do histórico. Entregar a `AsyncSession` ao repositório furaria o `quality.toml`.
- **Seções editadas:** §3.1.
- **Impacto na implementação:** o histórico cria o método e o teste dele; a confirmação de protocolo o reutiliza no escritor,
  no lugar do trecho ilustrativo da arquitetura, seção 5.6.

**Mudança no spec** · 2026-11-05 · D25 a D27, §3, §6.3, §6.4, §6.5, §7, T4, T5, T8, T9, T12

- **O quê:** a conversa nasce em `POST /conversations` com id do servidor (D25); o token da proposta vai em
  `ToolResult.client_only`, fora do modelo e do histórico (D26); log com a biblioteca padrão (D27, antes P7).
- **Por quê:** o spec exigia `404` para conversa inexistente sem ter como criar uma; e o conversor mandaria o token ao modelo
  e ao histórico. Decisões do dono na abertura da execução.
- **Seções editadas:** §3.1, §3.2, §6.3, §6.4, §6.5, §7, T4, T5, T8, T9, T12.
- **Impacto na implementação:** T4 cria o campo e o retira do JSON do modelo; T8 põe o token nele; T9 cria a rota, expõe o
  campo no stream e não o grava; T12 chama a rota antes do `useChat`.

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
