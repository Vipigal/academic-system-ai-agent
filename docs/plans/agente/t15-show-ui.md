---
type: Plan
title: T15 · UI sob decisão do modelo (show_ui) e rota de alunos de teste
description: Tarefa da fase do agente que faz o modelo decidir quando um widget aparece, por um parâmetro show_ui nas tools com UI, e entrega a rota dev-only da lista de alunos.
status: aprovado para implementação, aguardando o baseline da T10
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-06T18:00:00Z }
---

# T15 · UI sob decisão do modelo (show_ui) e rota de alunos de teste

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Depende de T12 (widgets e login por unidade) e
> do baseline da T10 commitado. **Spec vivo:** mudanças entram aqui e na seção Registro.

## Para o humano

- **TL;DR.** Hoje o front mostra um widget sempre que uma tool com UI roda, mesmo quando o modelo só a usou como apoio (um
  alerta de dívida numa pergunta sobre outra coisa). A T15 dá a decisão ao modelo: as três tools com UI ganham
  `show_ui: bool = False`, e o front só mostra o widget quando o input da chamada traz `show_ui: true`. Os dados continuam vindo
  do output da tool, nunca dos tokens do modelo. Junto, entra a rota `GET /auth/dev-students`, aprovada na T12 (V7).
- **Revisar com atenção:** a troca da lista de parâmetros permitidos por uma lista de identidade proibida que vive só no teste
  (D3), e o texto que as skills ganham para dizer quando ligar a UI (D5).
- **Para o aluno:** o widget aparece quando a pergunta é sobre aquele resultado, e no máximo um por resposta.

## 1. Contexto e problema

Na T12, os widgets foram ligados ao nome da tool (`src/app/src/widgets/registry.ts`). `get_financial_summary`,
`get_curriculum` e `list_online_exams` também servem de apoio a outras perguntas (no golden, CR-02 e CR-03 usam
`get_financial_summary` sem que a pergunta seja sobre dívida), e o widget aparece fora de contexto.

A pesquisa de 2026-11-06 mostrou que o problema está aberto na indústria: no MCP Apps a UI sempre renderiza quando a tool tem
recurso de UI, e a issue ext-apps #402 pede um sinal de chamada intermediária, sem solução. A OpenAI recomenda separar tool de
dados de tool de exibição, ao custo de mais tools. O dono escolheu um parâmetro na própria tool, que dá a decisão ao modelo sem
tool nova.

## 2. Princípios

- A resposta em texto do agente é o que conta; o widget só acrescenta. O eval de fatos continua lendo o texto.
- Os números do widget vêm do output da API, nunca de argumento do modelo.
- A identidade continua só na sessão; nenhuma tool recebe identidade do modelo.

## 3. Decisões

### 3.1 Batidas (não reabrir)

| # | Decisão | Por quê |
|---|---|---|
| D1 | `show_ui: bool = False` em `get_financial_summary`, `get_curriculum` e `list_online_exams`, e só nelas. | O modelo decide na própria chamada; sem tool nova, a lista de tools não cresce. |
| D2 | Com `show_ui=true`, o resultado traz um campo opcional `ui` com uma frase geral do que foi exibido (ex.: "Painel da situação financeira exibido ao aluno"). Sem `show_ui`, o campo não é serializado. | O modelo sabe que há algo na tela e encaixa no raciocínio, sem detalhes do widget. `explanation` é de erro e `Caveat` é de ontologia, então nenhum dos dois serve. |
| D3 | Sai `ALLOWED_PARAMETERS` e `_check_parameters` de `src/api/application/agent/tools/registry.py`. O invariante "nenhuma tool recebe identidade" passa a ser checado só no teste, com uma lista de nomes proibidos declarada no próprio teste. | Decisão do dono: cada tool declara os parâmetros que precisa; a regra de segurança é verificada por varredura, sem restringir o código. |
| D4 | A docstring de cada uma das três tools ganha uma frase curta: "Pode mostrar UI ao aluno com show_ui." O limite de 200 caracteres continua. | Decisão do dono; o contrato da docstring é dele. |
| D5 | As skills `finance`, `academic_enrollment` e `lms` ganham uma linha: ligue `show_ui` só quando a pergunta do aluno é sobre aquele resultado, no máximo uma vez por resposta; a resposta em texto continua completa. A skill descreve em uma frase o que o painel mostra. | O modelo decide antes de ver os dados; a regra precisa estar onde ele lê sobre a área. |
| D6 | No front, o widget aparece só quando o input da parte da tool tem `show_ui: true`, a tool terminou com `status: ok`, e o resultado não é vazio. Com mais de um pedido na mesma mensagem, só o último aparece. | Mitiga a decisão tomada antes dos dados (resultado vazio não vira widget) e garante um por turno. |
| D7 | Resultado vazio é: nenhuma prova no output (calendário), nenhum contrato (financeiro), nenhuma matrícula nos totais (progresso). Não há widget com texto de "nada encontrado". | Decisão do dono. |
| D8 | `GET /auth/dev-students` → `200` com `[{brand, student_id, full_name, status}]`, uma linha por matrícula, ordenada por `full_name`, montada pelo mesmo `AuthRouter` só com `dev_login` ligado. O front troca a amostra fixa pela chamada. | Contrato aprovado na T12 (V7); estava parado esperando o baseline. |
| D9 | O eval (grader de argumentos e itens do golden com `show_ui`) fica com o dono. | Decisão do dono. |

### 3.2 Pendentes

Nenhuma.

## 4. Escopo

### Dentro

- Contrato das três tools, campo `ui` no resultado, registro sem a lista, teste de identidade por lista proibida.
- Docstrings e skills (D4, D5).
- Front: gatilho por `show_ui`, um widget por mensagem, sem widget vazio.
- Rota `GET /auth/dev-students` e a troca da amostra no front.

### Fora

- Eval: grader que confere argumentos, `show_ui` esperado ou proibido no golden. Entra quando o dono mexer no eval.
- Widget para outras tools. Entra com uma linha no registro do front e `show_ui` na tool nova.
- UI composta pelo modelo (OpenUI, caminho C da T12). Fica para estudo depois do case.

## 5. Terreno: como a codebase faz hoje

- Tools: `src/api/application/agent/tools/finance.py:28` (`get_financial_summary`, sem parâmetros), `academic.py:70`
  (`get_curriculum`), `lms.py:22` (`list_online_exams`). Parâmetros keyword-only depois de `*` são o idioma para flags
  (`pending_only` em `get_curriculum`).
- Registro: `ALLOWED_PARAMETERS` em `src/api/application/agent/tools/registry.py:15`, conferido por `_check_parameters`
  (linha 80).
- Teste de identidade: `tests/integration/agent/test_tool_invariants.py:123`, `test_no_tool_receives_identity`, que hoje
  importa `ALLOWED_PARAMETERS`. `TOOL_COUNT = 19` (linha 25) não muda.
- Identidade na sessão: `StudentSession` em `src/api/domain/identity/session.py:14` (`person_ids`, `cpf`,
  `enrollment_keys`).
- Envelope: `ToolResult` em `src/api/application/shared/tool_result.py`; campos opcionais usam
  `exclude_if=lambda value: value is None` (`explanation`, `coverage`).
- Skills: `src/api/application/agent/skills/<área>/SKILL.md`; system prompt em `src/api/application/agent/system_prompt.py`.
- Front: `src/app/src/MessageView.tsx` (`widgetsOf` escolhe os widgets pelo nome da tool), `src/app/src/widgets/registry.ts`,
  `src/app/src/api.ts` (`listDevStudents` lê `src/app/src/devStudentsSample.ts`).
- Rota de login: `src/api/presentation/http/auth.py` (`AuthRouter`), montada em
  `src/api/bootstrap/identity_providers.py:31` só com `settings.dev_login`. Leitura por `PersonDirectory`
  (`src/api/domain/ports/identity.py:10`), implementado em `StudentSessionRepository`
  (`src/api/persistence/identity/student_session_repository.py`), queries em `src/api/persistence/identity/queries.py`.

## 6. Desenho

### 6.1 Contrato

- `get_financial_summary(*, show_ui: bool = False)`, `get_curriculum(..., *, pending_only: bool = False, show_ui: bool = False)`,
  `list_online_exams(..., *, show_ui: bool = False)`. O dado devolvido é o mesmo com ou sem `show_ui`.
- `ToolResult.ui: str | None`, serializado só quando preenchido. A frase vem de uma constante por tool.

### 6.2 Teste de identidade

A lista proibida fica no teste: `person_id`, `person_ids`, `cpf`, `student_id`, `enrollment_keys`, `requester_name`. O teste
varre os parâmetros de todas as tools registradas e falha se algum estiver na lista. `enrollment` continua permitido: é a
referência que o modelo escolhe e que a application confere contra a sessão.

### 6.3 Front

- `widgetsOf` passa a exigir `show_ui === true` no input da parte, além do estado `output-available` e `status: ok`.
- Cada widget devolve `null` para o resultado vazio de D7 (o calendário, o financeiro e o progresso já fazem isso hoje).
- Só o último widget pedido na mensagem é renderizado.
- A amostra fixa sai: `listDevStudents` chama `GET /auth/dev-students` e reaproveita `parseStudents`.

### 6.4 Rota

Query nova em `IdentityQueries` (`sag.enrollment` com `sag.person`), método novo no port `PersonDirectory`, método no
`IdentityService` que devolve o DTO, rota no `AuthRouter`. Sem token, como o `dev-login`.

## 7. Plano em ondas

**Onda 1 (API).** Toca `tools/finance.py`, `tools/academic.py`, `tools/lms.py`, `tools/registry.py`, `shared/tool_result.py`,
as três `SKILL.md`, `tests/integration/agent/test_tool_invariants.py` e os testes unitários das três tools.
- Pronto quando: com `show_ui=true` o resultado traz `ui` e o mesmo `data`; sem ele, `ui` não aparece; o teste de identidade
  passa e falha se uma tool ganhar `cpf`; `make check` verde.

**Onda 2, em paralelo à 3 (front).** Toca `src/app/src/MessageView.tsx` e, se preciso, os widgets.
- Pronto quando: tsc e build limpos; o oráculo abaixo passa.

**Onda 3, em paralelo à 2 (rota).** Toca `presentation/http/auth.py`, `application/identity/service.py` e o DTO,
`domain/ports/identity.py`, `persistence/identity/queries.py` e `student_session_repository.py`, `src/app/src/api.ts`, e apaga
`src/app/src/devStudentsSample.ts`.
- Pronto quando: teste da rota com `dev_login` ligado (200, ordenação, campos) e desligado (404); a tela de unidade mostra as
  contagens reais (UniSaoPaulo_EAD com 164 matrículas); `make check` verde.

## 8. Oráculo

Pelo Chrome DevTools MCP, numa aba própria, em 1440 px e 390 px:
- `UniAraucaria_EAD:013161`, "Como está minha situação financeira?": widget financeiro depois do texto.
- `UniAtlantico:030171`, "Quanto falta para eu me formar?": anel.
- `UniLitoral_EAD:012149`, "Quais provas online eu tenho?": calendário.
- `UniAraucaria:090271`, "Não consigo entrar no AVA. É por causa da dívida?" (CR-02): nenhum widget, e o painel de debug mostra
  `show_ui` ausente ou `false` em `get_financial_summary`.
- Em todos, o texto do agente traz os fatos sem depender do widget.

Não confirmar protocolo com `UniSaoPaulo:181722` (TR-01 do eval).

## 9. Consequências

- **Melhora:** o widget aparece quando a pergunta é sobre ele; o modelo sabe que há algo na tela; nenhuma tool nova.
- **Piora ou encarece:** o schema de três tools muda, então o eval roda de novo depois da T15; o modelo pode ligar `show_ui`
  demais ou de menos, o que só o eval do dono vai medir.
- **Não pode mudar:** os fatos continuam no texto; o widget lê só o output da tool; nenhuma tool recebe identidade.

## Para o agente executor

- **Por onde começar:** confirme que o baseline da T10 foi commitado (pergunte ao dono ou ao agente do eval) antes de tocar
  `src/api/`.
- **Leia antes:** `CLAUDE.md`, este arquivo, a seção "Identidade visual e login por unidade" de `t12-front.md` e
  `src/app/src/MessageView.tsx`.
- **Não toque:** `src/evals/`, `tests/unit/evals/`, o golden e os arquivos de regra do dono listados no `CLAUDE.md`.
- **Gates:** `make check` inteiro verde ao fim das ondas 1 e 3; tsc e build do front na onda 2; o oráculo da seção 8.
- **Pendente de registro:** linkar a T15 no plano do `index.md` e criar a entrada "Mudança no spec" no `## Registro` dele;
  registrar na T12 a decisão de caminho (B agora, OpenUI depois do case) e os widgets. Os dois arquivos estavam travados pelo
  agente do eval quando este spec foi escrito.

## Registro

**Mudança no spec** · 2026-11-06 · T15 criada

- **O quê:** spec novo, com D1 a D9.
- **Por quê:** decisões do dono depois da pesquisa sobre quando mostrar UI de tool.
- **Seções editadas:** arquivo novo.
- **Impacto na implementação:** nada implementado; aplicar em sessão nova, depois do baseline da T10.

---

Pesquisa de base: vault do dono, `generative-ui/` (2026-11-06).
