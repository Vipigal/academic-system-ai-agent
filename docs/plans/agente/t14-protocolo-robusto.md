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

- **O texto gravado nunca vem do modelo.** O LLM escolhe a ação; o texto é o fixo da ação ou, nos pedidos de texto livre, o que o aluno escreveu.
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
| D35 | Revisada pela D52: texto fixo do catálogo nos serviços simples, só com o botão; campo vazio do aluno só nos serviços que pedem texto livre |
| D36 | Palavra digitada, exigida pelo servidor, em ACA-010, ACA-012, ACA-013, ACA-014 e FIN-031 |
| D37 | Evento de confirmação em `agent.message`, com o papel novo `system_event` |
| D38 | Pedido de disciplina: diz que não existe, orienta a secretaria e oferece `GEN-090`, sem promessa |
| D39 | Produção usa a data de hoje, sem variável de ambiente; testes e eval injetam 31/10/2026 |
| D40 | Regra de escopo no prompt `v2` |
| D42 | Nome em português e efeito nos DTOs de serviço; nome em português dos 8 cursos |
| D53 | A busca de serviço por nome casa também o nome em português da D42 |
| D54 | A skill `overview` trata a rematrícula do próximo período como pendência perto do fim do período |
| D55 | Segundo item âncora do bug, com outro aluno de Administração e "Gestão Estratégica II", entra no golden junto com a T14 |

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
- **Dados:** foto de 31/10/2026. As consultas do oráculo fixam essa data em `src/evals/golden/oracle_queries/`.
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
| Mensagem vazia em serviço que pede texto livre, ou acima de 4.000 caracteres | `422` |
| Palavra ausente ou errada em ação que a exige | `422` |
| Serviço não aberto, com taxa, ou matrícula em situação incompatível | `422` |

- A palavra é comparada sem diferenciar maiúsculas e ignorando espaços nas pontas.
- O token perde `message` e deixa de ter o texto em `SignedProposal`. Nos serviços com `requires_student_message`, a mensagem digitada é o que vai para `protocol_interaction`; nos demais, o servidor grava o texto fixo da ação, e `message` é ignorada.
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
- Nos serviços com `requires_student_message`, como pedido de informações, revisão de nota e reclamação: campo de texto vazio e obrigatório, sem texto sugerido pelo agente (D52).
- Nos demais, como segunda via de boleto e declaração: o card mostra o texto fixo da ação, só com o botão.
- Campo da palavra, quando exigida. O botão só libera com os campos preenchidos, e o erro do servidor aparece no card.
- O botão fica desabilitado enquanto o agente responde, para reduzir colisão de posição.

É o mínimo funcional. Estilo e demais bugs visuais ficam na sessão própria.

### 6.6 Textos

**Skill `protocols`**, com este texto:

> **Trancamento é sempre do curso inteiro.** O aluno pode dizer "matrícula" também para uma disciplina: "trancar minha matrícula em Direito Empresarial" fala da disciplina, não do curso. Não é possível abrir pedido para trancar uma disciplina. Nesse caso, não chame `propose_protocol`: explique isso e pergunte se ele quer trancar o curso inteiro. A mesma regra vale para cancelamento.

A skill também passa a trazer:
- a tabela de ações gerada da §6.1;
- o caminho do D38;
- o fato de o card trazer o texto da ação e, nos serviços de texto livre, o aluno escrever a mensagem, e o agente não;
- o evento de confirmação como fato: depois dele, o pedido está aberto.

**Skill `overview`** (D54): perto do fim do período, a rematrícula do período seguinte que ainda não consta entra como pendência. O implementador confere no banco de onde vem a rematrícula e qual antecedência os dados sustentam.

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

> Nenhum protocolo abre sem o aluno confirmar num card cujo texto vem do catálogo de ações, nunca do modelo. Nos pedidos de texto livre, o texto gravado é o que o aluno escreveu; nas ações de alto impacto, ele também digita a palavra de confirmação. O agente é avaliado por itens críticos no eval, com tolerância zero, mas um modelo é probabilístico: é a barreira determinística que impede o protocolo errado.

## 7. Consequências

- **Melhora:** o protocolo errado exige dois atos conscientes do aluno; o modelo perde uma superfície de injeção (AT-10 pedia para gravar um texto na mensagem); ele passa a ler o efeito de cada serviço sem cruzar tools.
- **Piora:** os pedidos de texto livre exigem que o aluno escreva no card. Os simples continuam com um clique, com o texto fixo da ação (D52).
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
| F1 | Catálogo de ações e nomes | Baseline de T10 | `domain/protocol/`, DTOs de serviço e curso, `application/shared/name_search.py` | Unitário | Os 18 códigos cobertos, cada um com texto fixo e `requires_student_message` (D52); código desconhecido falha fechada; a busca acha "revisão de nota" em ACA-020 (D53) | `list_services` mostra título e efeito; `list_protocols(service='revisão de nota')` acha o protocolo do PR-03 |
| F2 | Contrato da tool e proposta | F1 | `tools/protocol.py`, `registry.py`, `tool_schema.py`, `proposer.py`, `domain/protocol/proposal.py`, `proposal_signer.py` | Unitário, com fakes | Recusas novas testadas; token sem mensagem; `test_pr08` corrigido; `client_only` traz `confirmation` | Chamada real devolve `subject_not_supported` |
| F5 | Textos | F1 | `domain/ontology/`, `skills/`, `prompts/student_agent_v2.md`, `system_prompt.py` | Unitário | Prompt `v2` em uso; skill com a regra e a tabela gerada; entrada só explicativa, sem opção; `overview` com a rematrícula (D54) | Teste `live` da frase literal não gera proposta válida |
| F4 | Confirmação e evento | F2 | `confirmation.py`, `protocol_confirmation.py`, `domain/protocol/opening.py`, `opening_mapper.py`, `domain/conversation/`, `past_messages.py`, `agent_messages.py`, `04_agent_schema.sql` | Unitário nas regras; integração só na rota e na gravação | Tabela da §6.3 coberta; o texto digitado é o gravado; evento visível no turno seguinte; aluno não forja evento | Teste `live`: depois da confirmação, o modelo sabe que o pedido está aberto |
| F6 | Card e limpeza do login | F4 | `src/app/src/` | Navegador | Card da §6.5; atalho removido | Chromium do WSL com `UniMontanhas:070114`: stream, erro da API, card sem mensagem do agente, botão só libera com os campos, protocolo aberto com o texto digitado |
| F3 | Relógio | F4 | `infrastructure/clock.py`, `domain/ports/clock.py`, `bootstrap/settings.py`, `singletons.py`, `.env.example`, `opening.py`, testes, runner | Unitário | Produção com a data real; nenhum teste depende de `.env` para a data; `docs/architecture.md` A16 corrigido | Prompt mostra a data de hoje no Compose; eval roda com 31/10 |
| F7 | Rodada final e comparação | F3, F5, F6 | Resultados em `src/evals/`, `docs/plans/agente/`, `golden/protocol_actions.yaml` | Execução real | Segundo item âncora no golden (D55); `down -v` antes; `make check` verde; itens críticos sem falha; comparação com `baseline-trancamento-v2` escrita | Relatório da rodada e tabela de antes e depois, para a T13 |

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


## Execução

### Execução de 2026-11-07: protocolo robusto, com o show_ui junto, e a rodada final

#### Registro de decisões

Repo: este. Branch: `feat/agente`, a partir do commit do front com widgets. Sem push.
Escopo desta execução, na ordem das ondas:
1. o catálogo de ações e os nomes em português, junto com o `show_ui` nas três tools com UI;
2. o contrato da tool de proposta, junto com os textos (skills, ontologias, prompt `v2`);
3. a confirmação com o evento no histórico, junto com a rota de alunos de teste;
4. o widget só quando o modelo pede, no front, junto com o relógio real;
5. o card de confirmação e a limpeza do login;
6. a rodada final do eval, com `down -v`, `make check` verde e a comparação com o baseline v2.

O contrato da tool depende do catálogo e do `show_ui` na API, que tira a lista de parâmetros permitidos. O card depende da
confirmação e do widget por `show_ui`. A rodada final depende de tudo.
Até dois implementadores ao mesmo tempo, em arquivos disjuntos. Checkpoints da T14 no `## Registro` do spec-mãe; os da T15 no
`## Registro` da T15.

| Decisão | Por quê | Quem decidiu | Tipo | Se mudar, afeta | Commit |
|---|---|---|---|---|---|
| A T15 entra nesta execução, e a sessão paralela deixa de cuidar dela | a rodada final precisa medir o contrato definitivo das tools, para não ter de ser refeita | você | pilar | o contrato da tool, o card e a rodada final | — |
| Sem pré-voo; preflight feito, com o Chromium aberto pelo `chrome-wsl` e o Remote Control inativo | as decisões estavam fechadas e cada tarefa tem oráculo | você | ambiente | a continuidade da execução | — |
| Verificadores podem entrar pela tela de login de teste como qualquer aluno; protocolo só se confirma com `UniMontanhas:070114` | o login do front é simulado, sem senha | você | ambiente | a verificação no navegador | — |
| `down -v` na confirmação com evento (o schema de `agent.message` muda) e antes da rodada final | o spec manda; o banco é o do Compose | você | ambiente | os dados locais de conversa e protocolos de teste | — |
| Os filtros de `get_curriculum` (semestre, disciplina, só pendentes) viram um objeto aninhado, para o `show_ui` caber no limite de 5 argumentos | o linter barrou 6 argumentos; você preferiu o objeto a uma exceção na régua ou a um decorador, que eram as minhas recomendações | você | pilar | o schema de `get_curriculum` que o modelo vê e a rodada final | 4aa9d7c |
| A regra "só preenche `ui` com status ok" fica numa classe da camada das tools (`ToolUi.shown`), e o envelope `ToolResult` ganha só o campo; a função solta virou classe na revisão, pela regra da casa | a classe passaria do limite de métodos, e a regra de exibição é das tools | o dono | detalhe | o `show_ui` na API | 4aa9d7c |
| O campo `ui` só aparece com status ok, nunca em vazio ou não encontrado | o front não mostra widget vazio, e o modelo não deve ouvir "painel exibido" sem painel | o dono (do implementador) | detalhe | o `show_ui` na API | 4aa9d7c |
| Revisão por área pronta, e não dois revisores por tarefa: um revisor de código ao fechar a API do protocolo e um de comportamento ao fechar o front. Toda tarefa passa pelo gate do dono, com evidência | o orçamento de tokens é curto, como você pediu na execução de 05/11 | você (regra anterior) | detalhe | a profundidade da revisão por tarefa | — |
| Nome em português de CON é "Ciências Contábeis", como no exemplo do card | o catálogo de perguntas diz "Contabilidade"; o spec usa "Ciências Contábeis" | o dono (do implementador) | detalhe | o card e os nomes de curso | 5a3900d |
| A rematrícula do semestre seguinte vira pendência nos últimos 30 dias do semestre | nos dados, a rematrícula mais cedo aparece 20 dias antes do fim do semestre anterior; com 31/10 a regra não dispara no eval | o dono (do implementador) | detalhe | a skill `overview` | 13ce26f |
| A tabela de ações da skill diz que o aluno digita uma palavra, sem dizer qual | a palavra fica fora do modelo, como o token | o dono (do implementador) | detalhe | a skill `protocols` | 13ce26f |
| O bloco `confirmation` vai como objeto dentro de `client_only`, com as 4 chaves sempre presentes | é o formato que o grader do eval já lê | o dono (do implementador) | detalhe | o card e o eval | 7347373 |
| As descrições dos argumentos de `propose_protocol` ficam num mapa por tool, e não no guia por nome de argumento | `subject` existe em outras tools com outro sentido | o dono (do implementador) | detalhe | o schema das tools | 7347373 |
| Testes `live` e a prova da frase literal rodam pela API do Compose, que já tem a chave | o auto mode barrou carregar o `.env` no shell, e você não quer o `.env` no shell | você | ambiente | os testes `live` | — |
| A rodada final lê a chave pelo próprio processo: `evals.run` ganha `--env-file`, e o `pydantic-settings` lê o arquivo sem passar pelo shell | você pediu um script no lugar do `.env` no shell; o `Makefile` é seu e fica intacto | você (o desenho é do dono) | detalhe | a rodada final e o guia do eval | ce93d20 |
| O 422 da confirmação traz o motivo em `detail` (`empty_message`, `confirmation_word`, `enrollment_status` e outros) | o card precisa mostrar o erro do servidor, e o 422 só sai depois de token, dono e conversa conferidos | o dono (do implementador) | detalhe | a rota e o card | 0dfdc5f |
| O limite de 4.000 caracteres vale para qualquer serviço; o vazio só é recusado onde o aluno escreve | é a leitura da linha da tabela de respostas | o dono (do implementador) | detalhe | a confirmação | 0dfdc5f |
| Revisão de código da API: nada bloqueante de correção, segurança ou requisito; entram na correção do card a classe `ToolUi`, o 201 com log para qualquer falha do evento, a confirmação fechada pelo catálogo (`proposable`) e a remoção da escolha ambígua de matrícula, que ficou sem uso | os opcionais são baratos e fecham a falha fechada do catálogo também na confirmação | o dono | detalhe | a confirmação e as tools com UI | 6b7898e |
| O card dos serviços simples mostra o texto fixo da ação, e a proposta passa a trazer `request_text` em `data` | é o critério do card no spec; o texto é do catálogo, nunca do modelo | o dono | detalhe | a proposta e o card | e4cc3b9 |
| O segundo item âncora (TR-14) usa `UniMontanhas:070467`, de Administração, que cursa Gestão Estratégica II em 2026/2, num turno só, com a frase literal | mesma marca e modalidade do aluno em que a frase deu 4 de 5; a D55 pede a disciplina no primeiro turno | o dono (do implementador) | detalhe | a rodada final, que passa a 156 execuções | ce93d20 |
| Confirmar serviço com taxa dá 404, e não 422, porque os 4 códigos com taxa não têm ação no catálogo | a confirmação fecha pelo catálogo; uma proposta desses serviços nunca é assinada | o dono (do implementador) | detalhe | a tabela de respostas da confirmação | 6b7898e |
| A rodada final saiu reprovada por uma falha de trajetória no PR-08 (matrícula já trancada): ajustar a skill para consultar `list_enrollments` antes de perguntar "curso ou disciplina" e oferecer a reativação, e rodar de novo? | aguardando: uma rodada nova gasta crédito e juiz, e você decide quando rodar o eval | aguardando você | pilar | a skill `protocols` e uma nova rodada | — |

#### Plano de review

Resumo: as 9 tarefas de código ficaram prontas e commitadas: o catálogo de ações, o contrato da tool, os textos, a confirmação
com palavra e evento, o relógio real, o card, e a T15 inteira (o `show_ui` na API e no front, e a rota de alunos de teste). A rodada
final rodou: o bug sumiu (o TR-13 caiu de 4 propostas indevidas em 5 para 0, e o TR-14 ficou em 0 de 5), mas ela saiu reprovada por
uma falha de trajetória fora do bug, no PR-08.

**Precisa da sua decisão**

1. Corrigir a skill e rodar a rodada de novo?
   No PR-08#5, o aluno com a matrícula já trancada disse "Quero trancar minha matrícula". O agente perguntou "curso inteiro ou
   disciplina?" sem consultar as matrículas. Em nenhuma das 5 repetições ele ofereceu a reativação. No TR-11, ele não mandou procurar
   a secretaria em 4 de 5. As duas falhas pedem uma ou duas linhas na skill `protocols`, e uma rodada nova custa cerca de US$ 0,22 mais
   o juiz.
   Recomendo: ajustar a skill (consultar `list_enrollments` antes de perguntar o objeto; matrícula trancada leva a oferecer a
   reativação) e rodar de novo. Estado atual: nada aplicado, e a rodada salva é a reprovada.
   Se mudar: só a skill `protocols` e a pasta da rodada.
2. O widget do calendário só apareceu quando o aluno pediu "mostre num calendário"; em "Quais provas online eu tenho?" o modelo usou
   `show_ui: false` duas vezes. O eval do `show_ui` é seu (D9 da T15).
3. Confirmar serviço com taxa agora dá 404, e não o 422 da tabela de respostas: esses códigos não têm ação no catálogo, e a proposta
   deles nunca é assinada. Se preferir o 422, a taxa é conferida antes da ação.

**Onde olhar**

Confirmação e evento
- `src/api/application/protocol/confirmation.py` e `confirmation_event.py`: a ordem das checagens e o 201 com log quando o evento falha.
- `src/api/domain/protocol/opening.py`: `StudentAnswer.recorded_text`, onde se decide o texto gravado (do aluno ou fixo).
- Verificado: tabela de respostas em unitário e na rota; protocolos `20260024923` (trancamento, com "trancar") e `20260025024` (com
  "migrar") abertos, e o agente citou o número no turno seguinte.

Contrato da tool
- `src/api/application/protocol/proposer.py` e `src/api/domain/protocol/proposal.py`: recusas `subject_not_supported` e
  `enrollment_status`.
- `src/api/application/agent/tool_arguments.py`: a descrição de `subject`, que manda preencher sempre que o aluno cita uma disciplina.

Textos
- `src/api/application/agent/skills/protocols/SKILL.md`: a regra do curso inteiro. É onde a decisão 1 mexe.

Front
- `src/app/src/ProtocolCard.tsx` e `proposal.ts`: o card só lê `data` e `client_only`. Screenshots `card-01` a `card-10` e `widget-*`
  no scratchpad da sessão.

**Pode pular**
Fakes dos testes, a troca dos testes para o contrato novo, os snapshots de descrição das tools, o `.env.example`, a rota de alunos de
teste e a leitura do `--env-file`.

**Para você:** a mensagem do banimento de `datetime.now` no `ruff.toml` ainda diz que a data vem da configuração; se o seu `.env`
tiver `APP_REFERENCE_DATE`, a linha pode sair; `docs/pendencias.md` ainda tem "Corrigir A16", que foi feito.

Para consulta: registro de decisões acima e checkpoints no `## Registro` do spec-mãe e da T15; commits `5a3900d` (catálogo), `4aa9d7c`
(show_ui na API), `13ce26f` (textos), `d36af62` (rota de alunos de teste), `e125bec` (widget), `7347373` (contrato da tool), `0dfdc5f`
(confirmação e evento), `6a7463c` (relógio), `6b7898e` (correções da revisão), `e4cc3b9` (card), `ce93d20` (preparação da rodada),
`d3707a0` (rodada final e comparação).
