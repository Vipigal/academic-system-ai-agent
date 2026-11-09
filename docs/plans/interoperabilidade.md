---
type: Plan
title: Interoperabilidade entre sistemas
description: Spec da tarefa que leva às respostas das tools os vínculos entre entidades de sistemas diferentes, já cruzados, e mede no eval as perguntas que cruzam sistemas.
tags: [plano, interoperabilidade, tools, ontologia, eval]
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-09T18:00:00Z }
sources:
  - id: final-t14
    resource: /src/evals/results/rodada-final-t14/report.md
    title: Rodada final da T14
  - id: arquitetura
    resource: /docs/architecture.md
    title: Arquitetura do agente de atendimento ao aluno
  - id: insumos
    resource: /docs/insumos-da-entrega.md
    title: Insumos da entrega
---

# Interoperabilidade entre sistemas

> **Status:** aprovado para implementação · **Data:** 2026-11-09
> **Spec vivo:** este arquivo é a fonte única da tarefa. Mudanças são editadas aqui e anotadas em
> "Mudança no spec" na seção Registro; leia o Registro junto do restante.
> **Repos:** só este. Nenhum arquivo do dono (`ruff.toml`, `.flake8`, `.importlinter`, `mypy.ini`, `pyrightconfig.json`,
> `quality.toml`, `Makefile`, `tools/quality/`, `tests/lint/`) muda.

## Para o humano

- **TL;DR:** quando uma entidade aponta para outra em outro sistema, a tool passa a trazer o vínculo já resolvido, numa referência
  curta com o nome da tool de detalhe. A fatura da taxa diz de qual protocolo ela é; a matrícula diz a situação do contrato e da conta
  do AVA; o calendário traz a janela da AV online do aluno. O modelo aprende a ler cada vínculo pela ontologia da tool, e não por regra
  de skill. O eval ganha trajetória com alternativas (`any_of`) e 8 perguntas novas de cruzamento.
- **Revise com atenção:** o formato da referência curta (§6.1), o princípio "um fato, um sistema oficial" (§2) e a lista de vínculos
  com o que fica de fora (§4).
- **Para o agente consumidor:** respostas de tool com campos novos, que só aparecem quando o vínculo existe. Nada some.

## 1. Contexto e problema

Nos 9 itens do golden que cruzam sistemas e rodaram na rodada final, a rubrica aprovou 13 de 29 critérios (45%), contra 83,1% da rodada
inteira[^final-t14]. CR-04, CR-08, DU-01 e PR-06 falharam do mesmo jeito em três rodadas seguidas.

A causa não está nos dialetos nem na sessão: quando a tool certa é chamada, o dado cruzado volta certo e da pessoa certa. O problema
está antes e depois dela:

- O agente escolhe a skill pelo assunto da pergunta e não chama a tool do outro sistema. No CR-04 ("nota no AVA diferente do
  histórico") ele respondeu sem chamar nenhuma tool. No CR-08 ("paguei a taxa da segunda chamada?") achou a taxa de R$ 45 e
  respondeu que não sabia de qual pedido ela era.
- Parte dos vínculos só aparece de um lado. O protocolo mostra a fatura da taxa, mas a fatura não mostra o protocolo.
- Vínculos que existem nos dados nunca chegam ao agente: acordo → protocolo de renegociação, mudança de status → protocolo,
  matrícula → contrato.
- A secretaria não informa o período coberto. Com o resultado vazio, o agente disse "não localizei pedidos em 2021", quando os
  registros só começam em 04/03/2022.

A aposta do projeto: entregar o cruzamento pronto dentro da tool custa menos do que escrever uma regra de skill para cada combinação de
sistemas, que sempre ficaria incompleta.

## 2. Princípios

1. **Referência curta, não cópia.** O vínculo traz o identificador, os 2 ou 3 campos que respondem ao cruzamento mais comum e o nome
   da tool de detalhe. Por quê: resposta completa sem inflar a tool, e o agente sabe onde abrir o detalhe.
2. **Só aparece quando existe.** Campo de vínculo vazio sai da resposta. Por quê: 732 de 25.931 faturas têm protocolo; o resto não
   deve pagar tokens por isso.
3. **Um fato, um sistema oficial.** Nunca dois valores paralelos para o mesmo fato. Campo que vem de outro sistema leva o nome dele
   (`contract_situation`, não `status`). Por quê: dois valores para o mesmo fato confundem mais do que ajudam (D3).
4. **O modelo aprende pela ontologia.** Cada vínculo ganha um termo na ontologia que a tool declara. Regra de skill só para o que
   não tem vínculo nos dados. Por quê: a ontologia já chega ao modelo com `load_skill` e fica junto do dado.
5. **O vínculo respeita o dono do outro lado.** A entidade vinculada é lida pelo repositório do sistema dela, com o ownership dele.
   Se o outro lado não for visível na sessão, o vínculo não aparece. Por quê: *fail closed*, como o resto da API.

## 3. Decisões

### 3.1 Batidas (não reabrir)

| # | Decisão | Por quê |
|---|---|---|
| D1 | Formato do vínculo: referência curta com o nome da tool de detalhe | Completa sem inflar; a alternativa da entidade inteira incha, e só o ID obriga a uma segunda chamada |
| D2 | Entram V1, V2, V3, V5, V6, V7 e V9 (§4). V8 fica para depois | Têm chave nos dados e resolvem itens que falham; V8 já sai em `list_protocols` |
| D3 | A nota do AVA não vai para `list_subject_records`. Vale a nota do SAG, e a divergência vira aviso na ontologia e na skill de desempenho | Decisão do dono: dado contraditório confunde. Em 134 de 13.943 provas a nota diverge, e a média final usa a do SAG[^insumos] |
| D4 | `list_online_exams` continua com `ava_grade` e `official_grade` | Nessa tool a nota do AVA é o assunto (CR-04) |
| D5 | A composição fica na application, pelas ports do domínio, com os repositórios de cada sistema | É o padrão de `LmsService` e `ProtocolSource`; cada repositório aplica o próprio ownership |
| D6 | Trajetória com grupos `any_of` no golden | Com os vínculos, o mesmo fato vem de mais de uma tool |
| D7 | 8 perguntas novas de cruzamento: 5 de vínculo e 3 de composição, cerca de 1/3 em holdout | Medem o desenho e também o que ele não cobre |
| D8 | O `Coverage` da secretaria informa os registros desde 04/03/2022 | Mesmo padrão do AVA (`LmsCoverage`) |
| D9 | As skills `finance` e `protocols` mencionam o detalhe disponível como opção, não como regra | Resposta mais completa sem engessar o agente |
| D10 | A pergunta sobre bolsa e reprovação fica fora | É de escopo e está em outra tarefa |
| D11 | Sem pesquisa externa | Decisão do dono |

### 3.2 Pendentes (confirmar na revisão)

| # | Proposta | Alternativa | Recomendação |
|---|---|---|---|
| P1 | Teto de crescimento da resposta: mediana por tool até +30% em caracteres do JSON, nos alunos do golden | Sem teto, só medir e reportar | Teto de +30%; a tool que passar volta para revisão de campos antes de seguir |
| P2 | Nomes dos campos e DTOs da §6.2 | Outros nomes do domínio | Os da §6.2, que seguem o nome da entidade |
| P3 | Janelas da AV online no calendário agrupadas por prova (AV1, AV2) e período, com a contagem de disciplinas | Uma linha por disciplina | Agrupadas: as janelas do período são iguais entre disciplinas, e o detalhe por disciplina já está em `list_online_exams` |

## 4. Escopo

### Dentro

| # | Vínculo | Chave nos dados | Onde aparece | Item que resolve |
|---|---|---|---|---|
| V1 | Fatura de taxa → protocolo | `finance.invoice.protocolref`: 732 faturas, todas `SERVICE_FEE` (ACA-021, DOC-002, DOC-003, DOC-041) | `list_invoices`, item de dívida e próxima fatura de `get_financial_summary` | CR-08 |
| V2 | Acordo → protocolo de renegociação | `finance.agreement.protocolref`: 64 de 65, todos FIN-031 | `list_agreements` | pergunta nova |
| V3 | Mudança de status da matrícula → protocolo | `sag.enrollment_status_history.protocol_ref`: 229, no dialeto `PRT-2022/0003091`, que casa com a secretaria em 229 de 229 | `list_enrollments`, no histórico | pergunta nova |
| V5 | Parcela → acordo | `finance.invoice.agreementid`: 269 | item de dívida e próxima fatura de `get_financial_summary` | CR-06 |
| V6 | Matrícula → contrato (situação e dívida) | `finance.contract.academicref`, pelo `FinanceDialect` | `list_enrollments` | CR-05, CR-07 |
| V7 | Matrícula ↔ conta do AVA | `lms.mdl_user.student_id`, pelo `LmsDialect` | `list_enrollments` (conta) e `get_lms_account` (situação da matrícula) | CR-02, pergunta nova |
| V9 | Calendário → janelas da AV online do aluno | `mdl_course.idnumber = SAG-<class_id>` | `get_academic_calendar` | DU-01 |

Também entram:

- O aviso de D3 na ontologia `nota_do_ava` e na skill `academic_performance`, com a evidência remedida.
- O `Coverage` da secretaria (D8).
- A menção ao detalhe nas skills `finance` e `protocols` (D9).
- `any_of` no golden, a revisão das listas de tools afetadas e as 8 perguntas novas.

### Fora

- **V4, nota do AVA no histórico:** fora por D3. Volta só se o dono mudar a decisão sobre dado contraditório.
- **V8, diploma dentro da matrícula:** entra se a medição mostrar o CR-03 ainda falhando pela falta do pedido; exige trazer protocolos
  para dentro de `list_enrollments`.
- **Skills simétricas para composição (onda 2 do dono):** entram depois da rodada de medição, para os casos sem vínculo nos dados:
  PR-06 e as 3 perguntas de composição. Exigem a medição desta tarefa.
- **Rodada de eval:** só quando o dono pedir. A medição final inclui o holdout de `questions` (`--include-holdout questions`).
- **Bolsa e reprovação:** tarefa de escopo, em outra frente.

## 5. Terreno: como a codebase faz hoje

- **Composição entre áreas já existe na application.** `LmsService` recebe repositórios acadêmicos
  (`src/api/application/lms/service.py:23`). `ProtocolSource` junta protocolo e fatura da taxa
  (`src/api/bootstrap/protocol_providers.py:31`). O bootstrap monta os services em `src/api/bootstrap/student_services.py:24`,
  `:37` e `:45`.
- **V1 só de um lado.** `InvoiceRow.protocol_ref` existe (`src/api/persistence/finance/models.py:33`) e só serve para
  `list_service_fees`, que monta o mapa protocolo → fatura (`src/api/persistence/finance/repositories.py:64`). `Invoice` e
  `InvoiceDto` (`src/api/application/finance/dto/invoice.py:11`) não têm o campo. O lado do protocolo está em `ProtocolFeeDto`
  (`src/api/application/protocol/dto/request.py:55`).
- **V2 e V3 descartados na persistence.** `AgreementRow` (`src/api/persistence/finance/charge_models.py:31`) não declara
  `protocolref`. `EnrollmentHistoryRow` (`src/api/persistence/sag/models.py:37`) não declara `protocol_ref`. `StatusChangeDto`
  (`src/api/application/academic/dto/enrollment.py:19`) não tem protocolo.
- **Dialeto do número de protocolo.** `ProtocolNumber.digits` (`src/api/domain/protocol/proposal.py:41`) já reduz o número aos
  dígitos. O SAG grava `PRT-AAAA/NNNNNNN`; a secretaria grava `AAAANNNNNNN`.
- **V5.** `InvoiceRow.agreement_id` existe (`src/api/persistence/finance/models.py:26`) e o mapper o leva à entidade
  (`src/api/persistence/finance/mappers.py:40`). `DebtItemDto` e `NextInvoiceDto` (`src/api/application/finance/dto/summary.py:13`,
  `:62`) não citam o acordo.
- **V6 e V7.** `EnrollmentDto` (`src/api/application/academic/dto/enrollment.py:39`) não traz contrato nem conta do AVA.
  `ContractSummaryDto` (`src/api/application/finance/dto/summary.py:100`) só traz `course_code`. `LmsAccountDto`
  (`src/api/application/lms/dto/account.py:9`) não traz a situação da matrícula.
- **V9.** `get_academic_calendar` (`src/api/application/academic/service.py:34`) lê só o catálogo; `AcademicService` não recebe o
  repositório do AVA.
- **Referência à tool de detalhe.** Não existe hoje; `Candidate` e `Coverage` (`src/api/application/shared/tool_result.py:65`) são
  os modelos de sinal mais próximos. O `exclude_if` para campo vazio já é usado no `ToolResult` (`tool_result.py:87`).
- **Ontologia.** Cada tool declara termos com `ToolRegistry.declares` (`src/api/application/agent/tools/registry.py:85`). Os termos
  vivem em `src/api/domain/ontology/<área>.py`; `NOTA_DO_AVA` está em `src/api/domain/ontology/lms.py:19`, com a evidência antiga
  (156 de 15.471). `docs/ontology.md` é gerado por `tools/ontology_doc.py` e conferido por `tests/unit/ontology/test_document.py`.
- **Coverage.** Existe no AVA (`src/api/application/lms/scope.py:38`) e no calendário (`src/api/application/academic/scope.py:64`).
  A secretaria não tem.
- **Eval.** `ToolExpectation.expected` é uma tupla de nomes (`src/evals/golden/parts.py:28`). `TrajectoryGrader` exige todos
  (`src/evals/graders/trajectory.py:9`). O check estático confere nomes conhecidos e exige cerca de 1/3 de holdout por área
  (`src/evals/golden/static_checks.py:74` e `:76`).

## 6. Desenho

### 6.1 A referência curta

Um DTO de vínculo por entidade vinculada, sempre com o identificador, poucos campos e `detail_tool`. Exemplo de forma, não de nomes
finais:

```json
{"id": "7077556", "kind": "service_fee", "due_date": "2026-10-11", "status": "overdue",
 "protocol": {"number": "20260022332", "service_name": "Second-Call Exam", "status": "closed",
              "resolution": "granted", "closed_at": "2026-10-09", "detail_tool": "get_protocol"}}
```

- O campo de vínculo é opcional e sai da resposta quando vazio.
- `detail_tool` é o nome da tool registrada que abre o detalhe. Um teste confere que todo `detail_tool` emitido é uma tool que
  existe.
- Pontos debatidos e fechados: entidade inteira embutida foi recusada (incha); só o ID foi recusado (obriga a uma segunda chamada).

### 6.2 Vínculos, campos e onde nascem

| Vínculo | Campo proposto (P2) | Conteúdo | Onde compõe |
|---|---|---|---|
| V1 | `protocol` em `InvoiceDto`, `DebtItemDto` e `NextInvoiceDto` | número, serviço, situação, resultado, data de conclusão | `FinancialService` com a port da secretaria |
| V2 | `protocol` em `AgreementDto` | número, situação, data de abertura | `FinancialService` com a port da secretaria |
| V3 | `protocol` em `StatusChangeDto` | número, serviço, situação | `AcademicService` com a port da secretaria |
| V5 | `agreement` em `DebtItemDto` e `NextInvoiceDto` | ID do acordo, parcela N de M, saldo restante | `FinancialService`, dentro do financeiro |
| V6 | `contracts` em `EnrollmentDto` | ID do contrato, `contract_situation`, dívida total; lista, porque uma matrícula pode ter mais de um contrato | `AcademicService` com a port do financeiro |
| V7 | `lms_account` em `EnrollmentDto`; `enrollment_status` em `LmsAccountDto` | conta existe, suspensa, último acesso; e a situação da matrícula no SAG | `AcademicService` com a port do AVA; `LmsService`, que já tem o repositório acadêmico |
| V9 | `online_exam_windows` em `AcademicCalendarDto` | por prova e período: abertura, fechamento e número de disciplinas (P3) | `AcademicService` com a port do AVA |

- A persistence passa a ler `protocolref` do acordo e `protocol_ref` do histórico. O dialeto do SAG traduz `PRT-AAAA/NNNNNNN` para o
  número canônico; valor fora do padrão levanta erro, como os demais dialetos, e um teste de cobertura sobre o banco prova as 229.
- Cada vínculo ganha um termo de ontologia na área da tool que o mostra, com definição, sistema de origem e "nunca dizer" quando
  couber. Exemplos: "a taxa paga não prova que o pedido foi atendido"; "contrato em cobrança com matrícula ativa não é erro".

### 6.3 Nota do AVA (D3)

- `NOTA_DO_AVA` ganha, na definição ou na relação com o registro oficial: pode haver divergência; vale a nota do SAG, que entra na
  média. A evidência passa a ser a remedida: 134 de 13.943 provas online finalizadas, ligadas à turma pelo `idnumber`, com 112 em
  que o SAG é maior.
- A skill `academic_performance` ganha uma linha: a nota do histórico é a que vale; se o aluno citar outra nota no AVA, `list_online_exams`
  mostra as duas.

### 6.4 Coverage da secretaria (D8)

`list_protocols` com resultado vazio, ou com período anterior a 04/03/2022, devolve `Coverage` com a data inicial e a nota "sem
registros antes desta data", no padrão de `LmsCoverage`. A data é medida no banco (mínimo de `secretary.protocol.opened_at`).

### 6.5 Eval

- **`any_of`:** `tools.expected` aceita, além de nomes, grupos `{any_of: [...]}`. O grader exige cada nome solto e pelo menos uma tool
  de cada grupo. O check estático confere os nomes dentro dos grupos e recusa grupo com menos de 2 tools ou repetido.
- **Listas revisadas:** PR-09 e CR-08 passam a aceitar `get_protocol` ou `list_protocols`. DU-01, CR-02, CR-05, CR-06, CR-07 e CR-08
  são revistos à luz dos vínculos: uma tool que passou a trazer o fato entra num grupo `any_of` com a tool original.
- **Perguntas novas (CR-09 a CR-16):**

| Tipo | Pergunta | Sistemas | Tools esperadas |
|---|---|---|---|
| Vínculo | "Tranquei e o AVA bloqueou?" | SAG + AVA | `any_of: [list_enrollments, get_lms_account]` |
| Vínculo | "Minha taxa de histórico foi paga? O documento saiu?" | Fin + Sec | `any_of: [list_invoices, list_protocols, get_protocol]` |
| Vínculo | "Meu acordo veio do pedido que abri?" | Fin + Sec | `list_agreements` |
| Vínculo | "Por que minha matrícula foi cancelada?" | SAG + Sec | `list_enrollments` |
| Vínculo parcial | "Pedi segunda via do boleto. Já gerou?" | Sec + Fin | `list_protocols`; a rubrica cobra que o agente diga que o pedido não aponta para um boleto |
| Composição | "Pedi revisão de nota. Mudou no histórico?" | Sec + SAG | `list_protocols` e `list_subject_records` |
| Composição | "Pedi desconto. Já entrou na mensalidade?" | Sec + Fin | `list_protocols` e `get_financial_summary` |
| Composição | "Abri chamado do AVA. Já consigo entrar?" | Sec + AVA | `list_protocols` e `get_lms_account` |

- Cada pergunta tem um aluno real, com fatos e evidências provados pelo oráculo em SQL independente das tools. Se não houver aluno
  para um caso, a tarefa para e reporta ao dono, sem inventar um caso parecido.
- Split: a área CR passa de 8 para 16 itens; o check pede de 5 a 6 em holdout, então 2 ou 3 das novas vão para o holdout,
  escolhidas entre as de vínculo e as de composição.
- As de composição devem falhar hoje e servem de linha de base para a onda 2 das skills.

### 6.6 Testes

- **Unitário (regra, com fake):** a composição de cada vínculo no service, inclusive o caso "outro lado não visível → sem vínculo",
  e o grader com `any_of`.
- **Integração (banco, só na fronteira real):** a tradução do dialeto `PRT-` e a leitura das novas colunas, com o teste de cobertura
  sobre os valores distintos. Sem varredura nova além dele.
- **Contrato da tool:** todo `detail_tool` emitido existe no registro; campo de vínculo vazio não aparece no JSON.

## 7. Consequências

- **Melhora:** cruzamentos com chave nos dados passam a ser respondidos com uma tool. CR-04 não muda pela tool (D3) e depende do aviso
  da skill; CR-08, CR-06, DU-01, CR-05 e CR-07 ganham o dado na tool que o agente já chama.
- **Piora ou encarece:** respostas maiores nas tools com vínculo; mais consultas por chamada (a tool de matrícula passa a ler
  financeiro e AVA). Aceito porque o conjunto por pessoa é pequeno (no máximo 3 contratos, 2 contas no AVA e 18 protocolos) e a
  sessão já carrega em milissegundos[^arquitetura]. O teto de P1 limita o tamanho.
- **Riscos e mitigação:**
  - Vínculo para entidade de outra pessoa → o lado de lá é lido pelo repositório dele, com ownership, e some se não for visível; o
    `LeakGrader` segue em toda rodada.
  - O modelo tratar valor de outro sistema como o oficial → princípio 3, nomes com o sistema e "nunca dizer" na ontologia.
  - Dependência circular entre services → a composição usa ports do domínio, nunca outro service.
- **Não pode mudar:**
  - Os contratos de camada do `.importlinter`; LangChain só no agente; domínio sem rede.
  - Nenhum CPF, nota interna ou dado de funcionário em DTO de saída.
  - Campos existentes das tools continuam com o mesmo nome e significado.
  - `list_online_exams` mantém `ava_grade` e `official_grade` (D4).

## 8. Plano de implementação

| # | Tarefa | Depende de | Arquivos | Fronteira de teste | Pronto quando | Oráculo de verificação |
|---|---|---|---|---|---|---|
| T1 | Chaves de vínculo no domínio e na persistence: `protocol_ref` e `agreement_id` em `Invoice`, `protocol_ref` em `Agreement`, protocolo canônico na mudança de status, dialeto `PRT-` | — | `domain/finance/`, `domain/academic/` (entidades), `persistence/finance/` (models, mappers), `persistence/sag/` (models, dialect, enrollment_mapper), `domain/ontology/tables.py` (tabelas novas citadas pelos termos) | unitário do dialeto; integração da cobertura sobre o banco | as entidades carregam as chaves; teste de cobertura prova as 229 referências | consulta no banco: 732, 64 e 229 chaves lidas pelas entidades |
| T2 | Referência curta e ligação dos services no bootstrap: DTO base do vínculo, `detail_tool` conferido no registro, novas ports nos construtores de `AcademicService` e `FinancialService` (`LmsService` já tem o repositório acadêmico) | — | `application/shared/` (DTO do vínculo), `application/academic/service.py` e `application/finance/service.py` (só construtores), `bootstrap/student_services.py` | unitário do DTO e do teste de `detail_tool` | `make check-fast` verde com os construtores novos | API sobe no Compose e o chat responde como antes |
| T3 | Medida de tamanho antes | — | script descartável no scratchpad | — | mediana e p95 de caracteres por tool nos alunos do golden, gravadas na seção Execução deste arquivo | números registrados |
| T4 | Vínculos do financeiro: V1, V2, V5 e os termos de ontologia | T1, T2 | `application/finance/` (service, dto), `domain/ontology/finance_charges.py` e `finance_settlement.py`, `skills/finance/SKILL.md` (D9) | unitário com fake | DTOs com os vínculos; vazio não aparece | `get_financial_summary` e `list_invoices` no painel de debug das tools do chat (login de desenvolvimento), para o aluno do CR-08, mostram o protocolo 20260022332 |
| T5 | Vínculos do acadêmico: V3, V6, V7 (lado da matrícula), V9 e os termos de ontologia | T1, T2 | `application/academic/` (service, dto), `domain/ontology/academic_enrollment.py` e `academic_performance.py`, `skills/academic_performance/SKILL.md` (D3) | unitário com fake | `list_enrollments` com contrato, conta e protocolo do histórico; calendário com janelas | no painel de debug das tools do chat (login de desenvolvimento): aluno do CR-07 mostra a taxa vencida no contrato da matrícula de Pedagogia; aluno do DU-01 mostra a janela da AV2 de 05/12 a 12/12 |
| T6 | Vínculos do AVA e da secretaria: V7 (lado da conta), aviso de D3 em `NOTA_DO_AVA` com a evidência remedida, `Coverage` da secretaria, menção ao detalhe na skill `protocols` | T2 | `application/lms/` (service, dto), `domain/ontology/lms.py`, `application/protocol/` (queries, scope), `domain/ontology/protocols.py`, `skills/protocols/SKILL.md` | unitário com fake | conta com a situação da matrícula; `list_protocols` vazio com `Coverage` | no painel de debug das tools do chat (login de desenvolvimento): aluno do SR-05 com período 2021 recebe o aviso de 04/03/2022 |
| T7 | `any_of` no golden | — | `src/evals/golden/parts.py`, `loader.py`, `static_checks.py`, `src/evals/graders/trajectory.py` e testes | unitário do grader e do check | grader e check aceitam grupos; YAML atual segue válido | `evals.golden check` verde |
| T8 | Golden: listas revisadas e CR-09 a CR-16 | T7 | `src/evals/golden/questions.yaml`, `src/evals/golden/oracle_queries/` | `evals.golden check` | 8 itens novos com fatos e evidências provados; split dentro do check | `evals.golden check` verde, com a lista de alunos escolhidos na seção Execução |
| T9 | Fechamento: `docs/ontology.md` regenerado, medida de tamanho depois, revisão de P1 | T4, T5, T6 | `docs/ontology.md` (gerado por `tools/ontology_doc.py`), seção Execução | teste do documento | `make check` verde; tabela antes e depois por tool | nenhuma tool acima do teto de P1, ou a exceção registrada para o dono |

### Ondas e paralelismo

- **Onda 0:** T1, T2, T3 e T7. Arquivos disjuntos: T1 mexe em domínio e persistence; T2 em `application/shared/`, construtores e
  bootstrap; T3 não toca o repo; T7 só em `src/evals/`.
- **Onda 1:** T4, T5, T6 e T8. Cada uma numa área da application e nos arquivos de ontologia e skill da sua área; T8 só no golden.
  Os construtores dos services já mudaram na T2, então nenhuma delas toca o bootstrap.
- **Onda 2:** T9.
- **Caminho crítico:** T1 → T5 → T9. T5 é a maior tarefa.

## 9. Para o agente executor

- **Comece por:** T1, com o teste de cobertura do dialeto `PRT-` primeiro.
- **Leia antes:** `CLAUDE.md`, `docs/architecture.md` §5.2 a §5.5 e §5.9, `docs/ontology.md`, este arquivo inteiro com o Registro.
- **Não toque:** os arquivos do dono listados no cabeçalho; `list_online_exams` além do que T6 pede; as skills fora das citadas;
  `.env`.
- **Gates:** sem commit (o commit é do dono; numa execução longa, o agente dono commita por tarefa aceita); `make check` verde ao fechar
  cada onda; testes um arquivo por vez no loop; decisão nova é confirmada com o dono, editada aqui e anotada em "Mudança no spec"
  antes de virar código. Rodada de eval só com pedido do dono.
- **Iteração:** perguntas ao dono em lote, numeradas, com a recomendação em cada uma.
- **Insumos:** o que for marcante para a apresentação entra em `docs/insumos-da-entrega.md`, com número e fonte.

## Notas de implementação

## Fontes

[^final-t14]: Rodada final da T14, `executions.jsonl` e `judge_verdicts.jsonl`; a contagem por item está no diagnóstico de 09/11/2026.
[^arquitetura]: Arquitetura, §4, achados A5 e A13.
[^insumos]: Insumos da entrega, seção 4, com a consulta no banco local.

## Execução

## Registro
