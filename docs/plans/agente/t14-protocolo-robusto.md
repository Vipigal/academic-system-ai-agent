---
type: Plan
title: T14 · Protocolo robusto
description: Correção do bug em que o agente propôs trancar o curso inteiro quando o aluno pediu para trancar uma disciplina, com ações determinísticas, mensagem escrita pelo aluno, confirmação forte, evento de confirmação no histórico, relógio real e regra de escopo.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-06T14:00:00Z }
---

# T14 · Protocolo robusto

> **Status:** aprovado para escrita, aguardando o "pode seguir" do dono · **Data:** 2026-11-06
> **Spec-mãe:** [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md), decisões D32 a D42. Depende do baseline de
> [T10](/docs/plans/agente/t10-runner-eval.md): **nada desta tarefa entra antes de o baseline estar salvo.**
> **Spec vivo:** mudanças são editadas aqui e anotadas em "Mudança no spec", no Registro do spec-mãe.

## Para o humano

- **O que muda:** o agente deixa de escrever a mensagem do protocolo e passa a escolher uma ação com o efeito no nome. O aluno
  escreve o pedido no card e, nas ações de alto impacto, digita uma palavra de confirmação que o servidor exige. O modelo fica
  sabendo da confirmação por um evento no histórico. Serviços e cursos ganham nome em português e efeito declarado.
- **Junto:** relógio real em produção, regra de escopo no prompt, limpeza do protocolo de teste.
- **O que não muda:** o LLM continua sem gravar. Abrir protocolo continua sendo a única escrita em dados de origem.
- **Revisar com atenção:** a garantia da §6.8, a tabela de ações da §6.1 e o que fica fora, na §4.

## 1. Contexto e problema

Em 06/11/2026, às 03:44 UTC, no fluxo real do front, o aluno `UniSaoPaulo:181722` pediu "Solicite trancamento de matricula de
Direito Empresarial". O agente propôs `ACA-010` para a matrícula em Ciências Contábeis, com uma mensagem escrita por ele, e o
clique em Confirmar veio cerca de 5 segundos depois. O protocolo `20260025164` foi gravado corretamente, igual à proposta, e pede o
trancamento do **curso inteiro**. O trace é `029b2d9f36fbd3caf45933e6313e1f2e`, na sessão
`80321a80-515d-4c5e-9643-c5eb67a26b9b`.

**A confusão de origem:** em muitas universidades o aluno diz "matrícula" também para disciplina. "Trancar minha matrícula em
Direito Empresarial" significa trancar a disciplina. Na base, matrícula é o vínculo com um curso, e nenhum dos 18 serviços
tranca disciplina. O dono do projeto fez esse pedido sem perceber a diferença, o que prova que a confusão é natural.

**O que o modelo recebeu.** O raciocínio vem criptografado no trace; o que segue é inferência, sustentada pela reprodução da §1.1:

| Onde | Texto | Efeito provável |
|---|---|---|
| Docstring de `propose_protocol` (`tools/protocol.py:66`) | "Use para declaração, boleto, trancamento ou revisão" | A palavra sozinha autoriza propor |
| Schema da tool | `service`, `message` e `enrollment`, sem descrição | Não há onde pôr a disciplina; `message` obriga o modelo a escrever, e ele escreveu a justificativa da troca |
| Skill de protocolos | "Ação de alto impacto [...] exige avisar" | Regra de avisar, não de verificar; a única ambiguidade prevista é ter mais de uma matrícula |
| Prompt `v1`, linha 11 | "Você não grava nada [...] só é aberta depois que o aluno confirmar" | Propor parece inofensivo |
| Ontologia `trancamento` (`academic_enrollment.py:40`) | Sinônimo "trancar", sem qualificar | Não diz o que trancamento não é |
| `list_services` | Só `"name": "Enrollment Lock"` | Sem efeito nem limite do serviço |

O modelo **não confundiu** os conceitos: ele escreveu "Direito Empresarial é uma disciplina, não o curso da matrícula". Ele viu a
diferença e seguiu, sem dizer que o serviço de disciplina não existe.

**O card não barrou.** Ele mostrou "Enrollment Lock", "ACCOUNTING" e a mensagem do modelo. A única frase em português citava
Direito Empresarial, e o dono lembrou de ter confirmado o trancamento da disciplina.

**Falhas seguintes na mesma conversa:**
- o modelo citou a própria mensagem inventada como prova contra o aluno (posição 36);
- ele não soube da confirmação e se contradisse (posições 12 a 14);
- ele deu receita de bolo e código Python (posições 20 e 30), porque o prompt não tem regra de escopo.

### 1.1 Reprodução

10 conversas novas com `UniMontanhas:070114`, sem confirmar, com `gpt-6-luna`:

| Pedido | Propostas de `ACA-010` |
|---|---|
| "Solicite trancamento de matricula de Gestão Estratégica II" | 4 de 5 |
| "Quero trancar só a disciplina Gestão Estratégica II, não o curso" | 0 de 5 |

### 1.2 Efeito medido de cada serviço

Por `sag.enrollment_status_history` ligado ao protocolo. Todos os pedidos resolvidos desses serviços foram atendidos: confirmar
significa que vai acontecer.

| Serviço | Efeito | Casos |
|---|---|---|
| ACA-010 | `ACTIVE` para `LOCKED` | 87 de 87 |
| ACA-011 | `LOCKED` para `ACTIVE` | 47 de 47 |
| ACA-012 | `ACTIVE` para `CANCELLED` | 35 de 35 |
| ACA-013 | `ACTIVE` para `TRANSFERRED` | 20 de 20 |
| ACA-014 | Situação mantida, matriz migrada, de `ACTIVE` ou `LOCKED` | 40 de 40 |

Nenhuma mensagem de origem pede trancamento de disciplina. `sag.student_class` tem 172 linhas com `result = WITHDRAWN`, sem
ligação com protocolo; a origem delas não é conhecida.

## 2. Princípios

- **Quem escreve o pedido é o aluno.** O LLM escolhe a ação; o texto com o nome do aluno não vem do modelo.
- **O que a ação faz vem do código, não do modelo.** Skill, DTO e card leem da mesma fonte.
- **Só o servidor garante.** Regra no front sem regra na rota não conta.
- **Não prometer o que um modelo não cumpre.** A garantia absoluta está na barreira determinística (§6.8); o eval mede o resto.

## 3. Decisões

Batidas no spec-mãe, D32 a D42. Resumo do que orienta esta tarefa:

| # | Decisão |
|---|---|
| D32 | Trancamento é do curso inteiro. Não existe serviço de disciplina, e nenhum será criado. O agente precisa explicar isso |
| D33 | Fonte única de ações no domínio, com falha fechada |
| D34 | `propose_protocol(action, enrollment, subject)`, sem `message` |
| D35 | A mensagem é sempre do aluno, num campo vazio do card, em todos os serviços |
| D36 | Palavra digitada, exigida pelo servidor, em ACA-010, ACA-012, ACA-013, ACA-014 e FIN-031 |
| D37 | Evento de confirmação em `agent.message`, com o papel novo `system_event` |
| D38 | Pedido de disciplina: diz que não existe, orienta a secretaria e oferece `GEN-090`, sem promessa |
| D39 | Produção usa a data de hoje, sem variável de ambiente; testes e eval injetam 31/10/2026 |
| D40 | Regra de escopo no prompt `v2` |
| D42 | Nome em português e efeito nos DTOs de serviço; nome em português dos 8 cursos |

## 4. Escopo

### Dentro

As tarefas F1 a F7 da §8, mais a limpeza: `UniSaoPaulo:181722` sai dos atalhos de login (`src/app/src/Login.tsx:5`).

### Fora

| Item | Entra quando |
|---|---|
| Bugs visuais do front | Sessão separada; o dono passa a lista |
| Verificação em 390 px | Junto dos bugs visuais |
| Serviço novo de trancamento de disciplina | Nunca nesta fase: o catálogo vem da origem, e a regra não está na base |
| Comparar o texto do aluno com os nomes das disciplinas | Não entra: as 260 disciplinas estão em inglês ("BUSINESS LAW") e o aluno escreve em português |
| Classificador LLM na confirmação | Não entra: troca uma barreira determinística por outra probabilística |
| Rota nova para dados do card | Não entra: o stream já entrega o resultado da tool sem passar pelo modelo. Reabre se o card precisar de dado que a proposta não tem |
| Reescrever os testes com banco | Ponto de atenção do dono, P8 do spec-mãe. Não é tarefa desta fase |
| Tradução das 260 disciplinas | Fica com o modelo, como hoje |

## 5. Terreno

Fatos conferidos em 2026-11-06:

- **Tool:** `ProtocolTools.propose_protocol` em `tools/protocol.py:63`. `ToolRegistry` limita a docstring a 200 caracteres (`registry.py:13`) e aceita só `ALLOWED_PARAMETERS` (`registry.py:15`), que precisa ganhar `action` e `subject`.
- **Schema:** `ToolSchema._infer` (`tool_schema.py`) gera os argumentos sem descrição; é onde a descrição por argumento entra.
- **Proposta:** `ProtocolProposer` (`application/protocol/proposer.py`); `ProposalRules` e `SignedProposal` em `domain/protocol/proposal.py`.
- **Token:** `ProposalJwtSigner` (`infrastructure/proposal_signer.py`) assina `message`, que sai.
- **Confirmação:** `ProtocolConfirmation` (`application/protocol/confirmation.py`) e `ProtocolConfirmationRouter` (`presentation/http/protocol_confirmation.py`).
- **Gravação:** `ProtocolOpeningMapper` (`persistence/secretary/opening_mapper.py`) grava `message` em `protocol_interaction`.
- **Histórico:** `MessageRole` (`domain/conversation/message.py`), `PastMessages` (`application/chat/past_messages.py`), `AgentMessages` (`application/agent/agent_messages.py`). `agent.message.role` tem `CHECK` em `db/init/04_agent_schema.sql`, e o `append` calcula a posição.
- **Relógio:** `reference_date` em `.env.example:15`, `bootstrap/settings.py:12` e `bootstrap/singletons.py:20`; `ReferenceClock` em `infrastructure/clock.py`; o port só tem `today()`. A abertura usa meia-noite (`domain/protocol/opening.py`, `time.min`). O prompt recebe a data em `agent_runtime.py:41`. Há referência à data em 16 arquivos de teste.
- **Dados:** foto de 31/10/2026. As consultas do oráculo fixam essa data em `src/evals/oracle_queries/`.
- **Front:** `src/app/src/ProtocolCard.tsx` e `api.ts`.
- **Testes que citam o contrato atual:** `tests/unit/agent/tool_descriptions/ProtocolTools.json`, `tests/agent_map.py`, `tests/e2e/student_flow.py`, `tests/unit/infrastructure/test_proposal_signer.py`, `tests/unit/protocol/test_opening.py`, `tests/integration/protocol/` e `tests/integration/agent/test_tool_invariants.py`.
- **Inconsistência a corrigir:** `test_pr08_lock_request_is_a_proposal_for_confirmation` recebe proposta para `LOCKED_PERSON`, enquanto o PR-08 do golden diz para não propor novo trancamento.

## 6. Desenho

### 6.1 Fonte única de ações

Um catálogo no domínio liga cada código a uma `ServiceAction`, com: ação, título em português, efeito, limite (`not_for`), situações de
matrícula aceitas, se aceita disciplina, pergunta de confirmação e palavra de confirmação.

- **Falha fechada:** código sem entrada não pode ser proposto nem confirmado.
- **Teste de cobertura:** o catálogo cobre os 18 códigos de `secretary.demand_type`.
- **Quem lê:** DTO, skill (tabela gerada, como as ontologias), card e rota.

| Código | Ação (valor visto pelo modelo) | Situação aceita | Disciplina | Palavra |
|---|---|---|---|---|
| ACA-010 | `trancar_curso_inteiro` | `ACTIVE` | Recusa | TRANCAR |
| ACA-011 | `reativar_matricula` | `LOCKED` | Recusa | — |
| ACA-012 | `cancelar_curso_inteiro` | `ACTIVE` | Recusa | CANCELAR |
| ACA-013 | `transferir_de_curso` | `ACTIVE` | Recusa | TRANSFERIR |
| ACA-014 | `migrar_matriz_curricular` | `ACTIVE`, `LOCKED` | Recusa | MIGRAR |
| ACA-020 | `revisar_nota` | Qualquer | Aceita | — |
| DOC-001 | `declaracao_de_matricula` | Qualquer | Recusa | — |
| DOC-040 | `emitir_diploma` | Qualquer | Recusa | — |
| FIN-030 | `segunda_via_de_boleto` | Qualquer | Recusa | — |
| FIN-031 | `renegociar_divida` | Qualquer | Recusa | RENEGOCIAR |
| FIN-032 | `pedir_desconto_ou_bolsa` | Qualquer | Recusa | — |
| GEN-090 | `informacoes_gerais` | Qualquer | Aceita | — |
| OUV-099 | `reclamacao_na_ouvidoria` | Qualquer | Aceita | — |
| TEC-060 | `problema_de_acesso_ao_ava` | Qualquer | Aceita | — |

Os 4 serviços com taxa (ACA-021, DOC-002, DOC-003, DOC-041) têm entrada no catálogo, para título e efeito, mas não têm ação: não há
como propor.

Os efeitos escritos usam só o que está medido (§1.2) ou na ontologia. Nada sobre cobranças: as regras não estão na base. O FIN-031
usa "leva a um acordo", como a ontologia `servico`.

### 6.2 Tool

`propose_protocol(action, enrollment, subject=None)`:

- `action`: enum das 14 ações, com a descrição de quando usar;
- `enrollment`: obrigatório, escolhido a partir de `list_enrollments`;
- `subject`: a disciplina citada pelo aluno, mesmo de passagem. É `null` apenas se ele não citou nenhuma.

**Recusas novas em `ProposalRules`:**
- `subject_not_supported`: `subject` preenchido em ação que recusa disciplina, com uma explicação que orienta o modelo a dizer que o
  serviço de disciplina não existe e a perguntar se ele quer o curso inteiro;
- `enrollment_status`: situação da matrícula fora das aceitas.

**Resultado:**
- `data` mantém `service.code`, que o grader do eval lê, e ganha título, efeito, limite, nome do curso em português e `requires_student_message`;
- `client_only` leva o token e o bloco `confirmation`, com as chaves `question`, `effect`, `limit` e `word`, fora do modelo e do histórico, como em D26. O grader do eval lê essas chaves.

Nas ações que aceitam disciplina, `subject` fica na proposta e aparece no card, mas não é gravado como mensagem do aluno.

### 6.3 Confirmação

`POST /protocols/proposals/confirm` com `{token, conversation_id, message, confirmation_word}`.

| Situação | Resposta |
|---|---|
| Tudo certo | `201 {protocol_number, status, sla_due_at}` |
| Token inválido, expirado, de outro aluno; conversa alheia ou inexistente | `404` uniforme |
| Duplicado | `409` |
| Mensagem vazia ou acima de 4.000 caracteres | `422` |
| Palavra ausente ou errada em ação que a exige | `422` |
| Serviço não aberto, com taxa, ou matrícula em situação incompatível | `422` |

- A palavra é comparada sem diferenciar maiúsculas e ignorando espaços nas pontas.
- O token perde `message` e deixa de ter o texto em `SignedProposal`. A mensagem digitada é o que vai para `protocol_interaction`.
- A mensagem digitada não entra em log, como hoje.

### 6.4 Evento no histórico

Depois de gravar, a rota anexa à conversa uma mensagem com o papel novo `system_event`, cujo texto o servidor monta com o número, o título, o curso e o prazo.

- **O texto do aluno nunca entra no evento**, para não dar a ele um caminho até o papel de sistema.
- O `/chat` continua aceitando só `user` (D14), então o evento não pode ser forjado pelo chat.
- `AgentMessages` converte o evento em mensagem de sistema na posição certa. **Verificar em teste `live`** que o provedor aceita mensagem de sistema no meio do histórico; se não aceitar, é uma dúvida para o dono, sem troca silenciosa de desenho.
- O protocolo é a fonte da verdade. Se o evento colidir de posição, há uma nova tentativa; se falhar de novo, a resposta segue `201`, com log de erro.
- O schema muda em `04_agent_schema.sql`, com `down -v` (D37).

### 6.5 Card

Dados só do resultado da tool e de `client_only`, nunca do texto do modelo.

- Título em português e curso em português.
- Com palavra exigida: a pergunta de confirmação ("Tem certeza de que deseja trancar o curso Ciências Contábeis?"), o efeito, o limite ("Não tranca uma disciplina") e o aviso de que as regras e os efeitos sobre cobranças não estão nos dados.
- Campo de texto vazio e obrigatório em todos os serviços. Sem texto sugerido.
- Campo da palavra, quando exigida. O botão só libera com os campos preenchidos, e o erro do servidor aparece no card.
- O botão fica desabilitado enquanto o agente responde, para reduzir colisão de posição.

É o mínimo funcional. Estilo e demais bugs visuais ficam na sessão própria.

### 6.6 Textos

**Skill `protocols`**, com este texto:

> **Trancamento é sempre do curso inteiro.** O aluno pode dizer "matrícula" também para uma disciplina: "trancar minha matrícula em Direito Empresarial" fala da disciplina, não do curso. Não é possível abrir pedido para trancar uma disciplina. Nesse caso, não chame `propose_protocol`: explique isso e pergunte se ele quer trancar o curso inteiro. A mesma regra vale para cancelamento.

A skill também passa a trazer:
- a tabela de ações gerada da §6.1;
- o caminho do D38;
- o fato de o aluno escrever a mensagem no card, e o agente não;
- o evento de confirmação como fato: depois dele, o pedido está aberto.

**Ontologias:**
- `trancamento`: troca o sinônimo "trancar" por "trancar o curso", "trancar a matrícula do curso" e "parar o curso", e a definição diz que vale para o curso inteiro;
- `matricula`: registra que o aluno também chama de matrícula a inscrição numa disciplina;
- uma entrada `matricula_em_disciplina` **só para explicar a confusão**: nunca aparece como serviço ou opção, e tem `never_say` para não oferecê-la. Relação `NOT_SAME_AS` com `trancamento`;
- `data_de_referencia`: reescrita para a data de hoje (F3).

**Docstring e `declares` da tool, com a F2, porque ficam em `tools/protocol.py`:** a docstring (até 200 caracteres) deixa de citar "trancamento" como uso livre e manda conferir o objeto do pedido. A tool passa a declarar `trancamento`, `matricula_em_disciplina` e `regras_de_trancamento`. A entrada `matricula_em_disciplina` nasce na F1, para a F2 poder declará-la, e recebe o texto final na F5.

**Prompt `student_agent_v2`:**
- propor ação de alto impacto exige certeza sobre o objeto do pedido;
- regra de escopo: atende só assuntos acadêmicos, financeiros, de secretaria e do AVA do próprio aluno; para o resto, recusa em uma frase e oferece o que pode fazer. A recusa não se aplica a dúvida sobre o próprio curso;
- "hoje" passa a ser a data real.

### 6.7 Relógio

- `SystemClock` em `infrastructure/clock.py`, com o fuso de Brasília. O port ganha `now()`.
- `reference_date` sai de `Settings` e do `.env.example`.
- `Singletons` recebe o relógio por parâmetro, com `SystemClock` como padrão de produção.
- `FixedClock` para testes e eval, com 31/10/2026, porque os dados e o gabarito são a foto desse dia. As consultas do oráculo não mudam.
- O protocolo novo usa o instante real, no lugar de meia-noite.
- **Efeito aceito:** com a data de hoje, faturas em aberto passam a contar como atrasadas (177 entre 31/10 e 06/11, e cresce a cada dia), porque a foto não anda. Fica declarado nas evidências.

### 6.8 A garantia

Esta é a redação para a entrega, e os testes a sustentam:

> Nenhum protocolo abre sem o aluno escrever o próprio pedido e, nas ações de alto impacto, digitar a palavra de confirmação, num card cujo texto vem do catálogo de ações, nunca do modelo. O agente é avaliado por itens críticos no eval, com tolerância zero, mas um modelo é probabilístico: é a barreira determinística que impede o protocolo errado.

## 7. Consequências

- **Melhora:** o protocolo errado exige dois atos conscientes do aluno; o modelo perde uma superfície de injeção (AT-10 pedia para gravar um texto na mensagem); ele passa a ler o efeito de cada serviço sem cruzar tools.
- **Piora:** pedir uma declaração simples agora exige escrever o pedido no card. O dono escolheu isso (D35).
- **Riscos:**
  - **Mensagem de sistema no meio do histórico:** verificar em teste `live` (§6.4).
  - **Golden:** itens existentes podem citar `message`. Só muda o item que o novo contrato torna impossível, com registro, para manter o baseline comparável.
  - **Ajustar skill ao eval:** T10 tem frases novas no holdout.
  - **Contagem de turnos:** o `system_event` conta na janela de 20 mensagens. Sem ação.
- **Não pode mudar:**
  - o LLM não grava;
  - o histórico nunca vem do cliente (D14);
  - `client_only` não vai ao modelo, ao histórico nem aos relatórios do eval (D26);
  - `data.service.code` continua na proposta, porque o baseline depende dele;
  - o eval nunca confirma protocolo.

## 8. Plano de implementação

| # | Tarefa | Depende de | Arquivos principais | Fronteira de teste | Pronto quando | Oráculo |
|---|---|---|---|---|---|---|
| F1 | Catálogo de ações e nomes | Baseline de T10 | `domain/protocol/`, DTOs de serviço e curso | Unitário | Os 18 códigos cobertos; código desconhecido falha fechada | `list_services` mostra título e efeito |
| F2 | Contrato da tool e proposta | F1 | `tools/protocol.py`, `registry.py`, `tool_schema.py`, `proposer.py`, `domain/protocol/proposal.py`, `proposal_signer.py` | Unitário, com fakes | Recusas novas testadas; token sem mensagem; `test_pr08` corrigido; `client_only` traz `confirmation` | Chamada real devolve `subject_not_supported` |
| F5 | Textos | F1 | `domain/ontology/`, `skills/`, `prompts/student_agent_v2.md`, `system_prompt.py` | Unitário | Prompt `v2` em uso; skill com a regra e a tabela gerada; entrada só explicativa, sem opção | Teste `live` da frase literal não gera proposta válida |
| F4 | Confirmação e evento | F2 | `confirmation.py`, `protocol_confirmation.py`, `domain/protocol/opening.py`, `opening_mapper.py`, `domain/conversation/`, `past_messages.py`, `agent_messages.py`, `04_agent_schema.sql` | Unitário nas regras; integração só na rota e na gravação | Tabela da §6.3 coberta; o texto digitado é o gravado; evento visível no turno seguinte; aluno não forja evento | Teste `live`: depois da confirmação, o modelo sabe que o pedido está aberto |
| F6 | Card e limpeza do login | F4 | `src/app/src/` | Navegador | Card da §6.5; atalho removido | Chromium do WSL com `UniMontanhas:070114`: stream, erro da API, card sem mensagem do agente, botão só libera com os campos, protocolo aberto com o texto digitado |
| F3 | Relógio | F4 | `infrastructure/clock.py`, `domain/ports/clock.py`, `bootstrap/settings.py`, `singletons.py`, `.env.example`, `opening.py`, testes, runner | Unitário | Produção com a data real; nenhum teste depende de `.env` para a data; `docs/architecture.md` A16 corrigido | Prompt mostra a data de hoje no Compose; eval roda com 31/10 |
| F7 | Rodada final e comparação | F3, F5, F6 | Resultados em `src/evals/`, `docs/plans/agente/` | Execução real | `down -v` antes; `make check` verde; itens críticos sem falha; comparação com o baseline escrita | Relatório da rodada e tabela de antes e depois, para a T13 |

### Ondas e paralelismo

- **Onda 0:** F1.
- **Onda 1:** F2 e F5, em arquivos disjuntos.
- **Onda 2:** F4.
- **Onda 3:** F6 e F3, em arquivos disjuntos. F3 toca `opening.py` depois de F4, por isso espera.
- **Onda 4:** F7.
- **Caminho crítico:** baseline de T10, F1, F2, F4, F3, F7.

**Testes (ponto de atenção P8):** regra de domínio e de aplicação fica em teste unitário com fake, sem banco. Banco só onde a fronteira é a gravação ou a rota real. Não criar varredura nova do banco inteiro.

## 9. Para o agente executor

- **Comece por:** confirmar que o baseline de T10 está salvo e commitado. Sem ele, pare e avise.
- **Leia antes:** este arquivo, T10, o spec-mãe com o Registro e `CLAUDE.md`.
- **Não toque:** arquivos do dono listados no `CLAUDE.md`; o que for visual além da §6.5.
- **Confirmação no navegador:** só com `UniMontanhas:070114`, nunca com aluno do golden, e rodar `down -v` antes da F7.
- **Gates:** `make check-fast` no loop, `make check` ao fechar. Numa execução longa, o condutor commita por tarefa aceita.
- **Dúvida:** decisão nova vai ao dono, numerada e com recomendação, e entra no Registro do spec-mãe antes de virar código.

## Notas de implementação

