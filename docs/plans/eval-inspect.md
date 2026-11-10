---
type: Plan
title: Eval no Inspect AI
description: Spec da migração do eval próprio para o Inspect AI, com datasets num esquema só, splits dev e test, juiz configurável, intervalo de confiança e revisão das rubricas.
tags: [plano, eval, inspect, llmops]
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-09T21:30:00Z }
sources:
  - id: guia-eval
    resource: /docs/guia-do-eval.md
    title: Guia do eval
  - id: final-t14
    resource: /src/evals/results/rodada-final-t14/report.md
    title: Rodada final da T14
  - id: interoperabilidade
    resource: /docs/plans/interoperabilidade.md
    title: Interoperabilidade entre sistemas
---

# Eval no Inspect AI

> **Status:** em revisão · **Data:** 2026-11-09
> **Spec vivo:** este arquivo é a fonte única da tarefa. Mudanças são editadas aqui e anotadas em "Mudança no spec" na
> seção Registro; leia o Registro junto do restante.
> **Repos:** só este, no worktree `../cruzeiro-do-sul-eval-inspect`, na branch `feat/eval-inspect`, a partir da `main`. Em
> paralelo, outra sessão refatora o bootstrap com dishka na branch `refactor/simplificacao-idiomatica` (§5.3).

## Para o humano

- **TL;DR:** o eval próprio (cerca de 5 mil linhas de Python) passa a rodar no Inspect AI, o framework de eval do UK AI
  Security Institute.
  - Ficam com o Inspect: a execução, as repetições (epochs), o pass^k, o intervalo de confiança, os logs e o visualizador
    (`inspect view`).
  - Fica nosso só o que é do domínio: o solver que chama o agente, os quatro graders, o juiz com rubrica e o gabarito em SQL.
  - Os quatro YAMLs viram um esquema só, um arquivo por suíte, com `split: dev | test`.
  - O juiz vira parâmetro. O padrão é o Claude via `claude -p`, pelo plano do dono; o examinador troca para a API da OpenAI.
- **Revise com atenção:**
  - o esquema do sample (§6.2);
  - o mapa do que sai e do que fica (§6.1);
  - a regra da revisão das rubricas (§6.6).
- **Para quem consome:** a CLI muda de `python -m evals.run` para `inspect eval`. Os resultados antigos ficam congelados como
  estão.

## 1. Contexto e problema

- O eval tem 5.046 linhas de Python e 2.482 de testes. Cerca de 2.100 delas reproduzem à mão o que um framework de eval já
  faz:
  - runner com paralelismo;
  - manifesto e retomada;
  - regra crítica com pass^k;
  - relatório em Markdown;
  - página HTML.
- O dono não consegue explicar esse volume numa entrevista.
- **Faltam duas coisas que um examinador de Data Science procura:**
  - intervalo de confiança: o relatório escreve "o intervalo de confiança é largo", mas não o calcula;
  - um jeito de navegar conversa por conversa.
- **O vocabulário é próprio:** `golden`, `holdout`, `critical-repeat`, "rodada INCOMPLETA". Na literatura os nomes são
  dataset, test split, epochs e pass^k.
- **Algumas rubricas são puristas.** No DU-01, o critério "avisa que o calendário não traz a data da prova de cada disciplina"
  é falso para o aluno do item. Ele é EAD, e o LMS traz a janela da AV2 por disciplina: 05/12 às 08:00 até 12/12 às 23:59,
  nas três disciplinas (consulta no banco local, 09/11/2026). O critério pune o agente por não dar um aviso que contradiz um
  dado disponível.
- **Um spike de 09/11/2026 provou a viabilidade** (§5.2). Rodaram 10 amostras e o juiz:
  - o agente rodou dentro do Inspect, no mesmo processo;
  - os graders viraram scorers;
  - saíram o `pass_k`, o `ci_wilson`, o `grouped` e o `inspect view`;
  - o juiz rodou pela API da OpenAI e pelo `claude -p`.

## 2. Princípios

1. **O framework faz o genérico; o código nosso é só o domínio.** Linha que existe no Inspect sai do nosso código, porque
   cada linha nossa precisa ser explicada.
2. **Vocabulário da literatura:** dataset, sample, split (dev e test), epochs, scorer, pass^k e intervalo de confiança. Nome
   inventado só para conceito do domínio.
3. **Um item, um esquema.** A suíte é um parâmetro do sample, não um tipo Python.
4. **A rubrica descreve o que os dados do aluno sustentam, nos quatro sistemas.** Critério que afirma que um dado não existe
   precisa de uma consulta que prove a ausência.
5. **O juiz é configuração, não código.** O padrão é barato para o dono; a troca é um parâmetro para o examinador.

## 3. Decisões

### 3.1 Batidas (não reabrir)

| # | Decisão | Por quê |
|---|---|---|
| E1 | Inspect AI 0.3.288 como runner, scorer e visualizador, no grupo `dev` do `pyproject` | Único com pass^k nativo, visualizador local sem conta e Python 3.14 no CI. A pesquisa está no vault, em `frameworks-de-eval/` |
| E2 | `agent-client-protocol<1.0` travado junto | O Inspect 0.3.288 aceita a 1.0.0, que removeu `acp.helpers`, e quebra no import (spike) |
| E3 | Um arquivo por suíte: `quality.yaml`, `protocol.yaml`, `security.yaml` e `scope.yaml`, com o mesmo esquema | Decisão do dono: arquivos revisáveis, e cada suíte é uma task com as próprias epochs |
| E4 | `split: dev \| test` substitui `dev \| holdout` | Termo da literatura; o dono não entendeu "holdout" ao ler |
| E5 | Juiz configurável pelo papel `grader` do Inspect. Padrão: `claudecode/claude-sonnet-5-5`, um provedor próprio que chama o `claude -p` | Decisão do dono: o plano dele cobre o custo, é o juiz já calibrado e é de família diferente do agente. O examinador troca com `--model-role grader=openai/<modelo>` |
| E6 | Calibração do juiz mantida, como task do Inspect com a resposta fixa no lugar do agente | Decisão do dono: é o que prova que o juiz presta quando ele muda |
| E7 | Saem: página HTML e amostra de conferência, retomada própria, manifesto, regra crítica própria, relatório Markdown próprio, `evidence`, `divergences`, `bindings`, regras de forma do dataset, checagem do bloco de confirmação no grader de proposta | Decisão do dono (§6.1) |
| E8 | O gabarito em SQL fica, como teste do pytest que confere que a referência cita os valores do banco | É o diferencial do eval; nenhum framework faz isso |
| E9 | A revisão das rubricas é proposta por um subagente, com a prova no banco, e aplicada só com o ok do dono | Decisão do dono: a régua do eval é dele |
| E10 | Latência, TTFT, tokens e custo do agente ficam nos metadados do score, com um resumo de p50 e p95 calculado sobre os logs | O Inspect só conta tokens das chamadas que ele faz, e o reducer vale para todos os scorers da task (spike) |
| E11 | `driver_factory.py` e `student_driver.py` não são tocados. O solver depende só do contrato da §5.3 | Contrato combinado com a sessão do refactor com dishka |
| E12 | Os resultados antigos em `src/evals/results/` ficam congelados como estão. As rodadas novas vão para `logs/` do Inspect | O antes e depois do trancamento é material da entrevista; regerar exige rodada nova, que só o dono pede |

### 3.2 Pendentes (confirmar na revisão)

| # | Proposta | Alternativa | Recomendação |
|---|---|---|---|
| P1 | Epochs por suíte: `protocol` com 5 (gate pass^5), as demais com 3 | Todas com 3 | 5 só no gate, para manter a comparação com o baseline |
| P2 | Pasta dos logs: `src/evals/logs/`, versionada só a rodada que vira evidência | `logs/` na raiz, no `.gitignore` | `src/evals/logs/`, com as rodadas de rascunho no `.gitignore` |

## 4. Escopo

### Dentro

- Dataset num esquema só, com os 163 itens migrados para quatro arquivos.
- Solver, scorers, juiz, provedor `claudecode`, tasks por suíte e task de calibração.
- Teste do gabarito em SQL.
- Proposta de revisão das rubricas (tabela para o dono).
- Remoção do código substituído e dos testes dele.
- Atualização do `guia-do-eval.md` e do README (seção do eval).

### Fora

- **Rodar a rodada completa nova:** é do dono, quando ele pedir. A migração prova com uma amostra pequena (§8, oráculo).
- **Aplicar a revisão das rubricas:** entra depois do ok do dono, como tarefa seguinte.
- **Trajetória com alternativas (`any_of`):** é do spec de interoperabilidade. O esquema novo já aceita o campo, mas o grader
  só o usa quando aquela tarefa entrar.
- **Red team gerado pelo promptfoo:** entra se a entrevista pedir ferramenta de ataque; exige Node 22 ou mais novo.

## 5. Terreno: como a codebase faz hoje

### 5.1 O que fica e de onde vem

- **Captura dos eventos:** `src/evals/capture.py` (`ExecutionRecorder`, `TurnClock`, `SpentUsage`), com o TTFT e os tokens.
- **Conversa com turnos anteriores:** `src/evals/conversation.py`.
- **Graders:** `src/evals/graders/` (trajetória, recusa, vazamento, proposta), puros sobre o `Execution` e o `ItemContext`.
- **Contexto de vazamento:** `src/evals/context_loader.py` e `src/evals/item_context.py`, com os identificadores dos outros
  alunos lidos pelo oráculo.
- **Oráculo SQL:** `src/evals/golden/oracle.py` e `src/evals/golden/oracle_queries/`.
- **Prompt do juiz:** `.claude/agents/eval-judge.md`, lido por `src/evals/judge/agent_file.py`.
- **Pedido ao juiz:** montado hoje em `src/evals/run_log.py` (`_request_of`), com a pergunta, a resposta, a referência, a
  rubrica, o histórico e os dados das tools.
- **Preço:** `src/evals/pricing.py` e `pricing.toml`.

### 5.2 O que o spike provou (09/11/2026)

O código do spike está no scratchpad da sessão, fora do repo; ele é referência, não base.

- O solver chamou `StudentDriver.run(...)` e o `GraderSuite` sem mudança. 10 amostras em 32 s.
- `Epochs(3, ["mean", pass_k(3)])` gerou as duas reduções.
- O `ci_wilson` deu [0,342; 1,0] para 2 de 2 amostras, e o `grouped(accuracy(), "kind")` funcionou.
- O juiz rodou pelo `get_model("openai/...", api_key=...)` e pelo provedor `@modelapi(name="claudecode")`: 6,8 s por
  chamada, com o mesmo veredito do juiz calibrado no DU-01.
- **Limites achados:**
  - a transcrição do agente não aparece no visualizador, porque o agente chama a OpenAI por fora;
  - o reducer de pass^k também se aplicou à latência;
  - o `agent-client-protocol` 1.0.0 quebra o import do Inspect.

### 5.3 Contrato com o refactor do bootstrap (sessão paralela)

Combinado em 09/11/2026. Estas interfaces ficam iguais no bootstrap com dishka:

1. `DriverFactory.settings_for(model, effort, env_file=None) -> Settings`
2. `DriverFactory.create(settings) -> StudentDriver`
3. `StudentDriver.run(student, question, history, listener) -> None`, com o `RunListener` atual (`receive`, `bind_trace`,
   `begin_final_turn`, `add_usage`)
4. `StudentDriver.close()`, `StudentDriver.versions` e `StudentDriver.trace_url_prefix()`

O `RunListener` sai de `src/evals/runner.py` e vai para `src/evals/listener.py`. No rebase, quem chegar depois troca o
import em `student_driver.py`. O construtor do `StudentDriver`, o `DriverFactory.singletons_for`, o `Singletons` e o
`ChatAgentScope` mudam do lado de lá; o código novo do eval não usa nenhum deles.

## 6. Desenho

### 6.1 O que sai, o que fica e o que muda

| Hoje | Destino |
|---|---|
| `run.py`, `selection.py`, `runner.py`, `run_session.py` | Saem: `inspect eval` e as tasks |
| `run_manifest.py`, `run_files.py`, `run_log.py`, `records.py`, `run_data.py` | Saem: o log do Inspect. A montagem do pedido ao juiz vai para o scorer do juiz |
| `critical_rule.py`, `critical_consistency.py` | Saem: o reducer `pass_k` |
| `report/`, `page/` | Saem: `inspect view` e um resumo curto (§6.5) |
| `judge/claude_code.py`, `judge/session.py`, `judge/__main__.py` | Viram o provedor `claudecode` e o scorer do juiz. Lote e retomada saem |
| `calibration/` | Vira uma task. Os rótulos ficam em `calibration.yaml` |
| `golden/__main__.py`, `static_checks.py`, `query_checks.py`, `report.py`, `oracle_names.py` | Saem a CLI e as regras de forma. A conferência da referência contra o SQL vira teste |
| `golden/items.py`, `parts.py`, `vocabulary.py`, `loader.py`, `expected_proposal.py` | Viram um esquema só (§6.2) |
| `capture.py`, `conversation.py`, `graders/`, `context_loader.py`, `item_context.py`, `golden/oracle*`, `golden/formats.py`, `pricing.py` | Ficam. `ToolSteps` deixa de chamar a checagem do bloco de confirmação |
| `driver_factory.py`, `student_driver.py`, `settings_sources.py`, `trace_links.py` | Ficam intocados (E11) |

### 6.2 Esquema do sample

Um item por entrada do YAML da suíte, validado por pydantic (`extra="forbid"`). Os campos:

- **Identidade e seleção:** `id`, `suite` (`quality`, `protocol`, `security` ou `scope`), `split` (`dev` ou `test`),
  `category` (o antigo `kind`), `area` (o prefixo do id), `student` e `pass_k` (inteiro, só nos itens de gate).
- **Entrada:** `question` e `history`.
- **Expectativas determinísticas:**
  - `expect.tools` e `expect.forbidden_tools`;
  - `expect.forbidden_text`;
  - `expect.proposal` (código do serviço, lista, ou `none`);
  - `expect.forbidden_facts` (consultas do oráculo cujos valores não podem aparecer).
- **Gabarito:** `facts` (consulta, parâmetros e formato), `reference` e `rubric`.

O que sai:
- `evidence`, `divergences` e `bindings`. Os valores dos ataques passam a ser escritos no YAML;
- os quatro tipos Python;
- o `critical: true`, que vira `pass_k`.

O mapeamento dos 163 itens antigos é mecânico e feito por script descartável. O script não fica no repo.

### 6.3 Execução

- **Uma task por suíte.**
  - Parâmetros de task: `split` (padrão `dev`) e `ids`.
  - Epochs: as da P1.
  - Os itens de gate da suíte `protocol` usam o reducer `pass_k`; as outras, `mean` e `at_least`, este para ter um valor
    binário no intervalo de confiança.
- **Solver:**
  - carrega o contexto do item no oráculo;
  - roda o `StudentDriver`;
  - grava a execução no `store`;
  - **converte os eventos do agente em mensagens do Inspect** (assistente com tool calls, mensagem de tool, resposta final),
    para o visualizador mostrar a conversa;
  - preenche `state.output`.
- **Scorers:**
  - `graders`: CORRECT se todos os graders aplicáveis passam. A explicação lista os problemas, e os metadados levam o veredito
    de cada grader;
  - `rubric`: o juiz, via `get_model(role="grader")`, com um critério por linha na explicação.
- **Métricas:** `accuracy`, `stderr`, `ci_wilson` e `grouped(accuracy(), "category")`.
- **Comando de demonstração:**
  - `inspect eval src/evals/tasks.py@security --model none`;
  - `inspect view`;
  - o juiz padrão não precisa de flag; para trocar, `--model-role grader=openai/gpt-6-luna`.
- **Concorrência do provedor `claudecode`:** limitada por `max_connections`. Com o teto do plano estourado, o julgamento é
  refeito com `inspect score` sobre o log, sem rodar o agente de novo.

### 6.4 Provedor `claudecode`

- Um `ModelAPI` registrado com `@modelapi(name="claudecode")`.
- Reaproveita o isolamento do juiz atual (`ISOLATION`, `IsolatedProcess`).
- Monta o agente do `claude -p` com o system prompt recebido.
- Confere que o modelo usado é o pedido, como o juiz atual faz.
- Erro do processo vira erro do Inspect, que o registra na amostra.

### 6.5 Resumo para o README e a apresentação

Um módulo pequeno lê os logs com `inspect_ai.analysis` e imprime, por suíte:
- acerto com o intervalo de confiança;
- pass^k;
- latência p50 e p95, e TTFT p50 e p95;
- tokens e custo.

Ele substitui a seção "Resumo" do `report.md` antigo.

### 6.6 Revisão das rubricas

Um subagente lê os itens com rubrica e classifica cada critério:
- **(a)** responde ao que foi perguntado;
- **(b)** detalhe ou aviso que o aluno não pediu;
- **(c)** depende de tool de outro sistema;
- **(d)** afirma a ausência de um dado.

Para cada (d), roda no oráculo uma consulta que prova a ausência nos quatro sistemas, para o aluno do item. Se o dado existir,
propõe a reescrita.

Entrega uma tabela, item por item: critério, tipo, evidência e proposta (manter, remover ou reescrever, com o texto novo).
Nada é aplicado sem o dono.

### 6.7 Testes

- **Unitários, com fakes:**
  - o carregamento e a validação do esquema;
  - o mapeamento de eventos para mensagens;
  - os scorers sobre um `Execution` montado à mão;
  - o provedor `claudecode` com o processo falso;
  - o resumo sobre um log de exemplo.
- **Integração:** o teste do gabarito em SQL, que exige o banco, como hoje.
- **Sem rodada real na suíte de testes.** A rodada real é o oráculo da tarefa.

## 7. Consequências

- **Melhora:**
  - o código nosso cai para algo entre 700 e 1.000 linhas de Python (estimativa);
  - o vocabulário vira o da literatura;
  - entram o intervalo de confiança e o visualizador por amostra;
  - o examinador reproduz com a chave dele.
- **Piora:**
  - entram cerca de 38 dependências no grupo `dev`;
  - a CLI e o formato dos resultados mudam;
  - os resultados antigos ficam num formato que o código novo não lê.
- **Riscos:**
  - **Conflito com o refactor do bootstrap.** Mitigação: o contrato da §5.3 e nenhum arquivo em comum.
  - **Teto do plano no juiz padrão.** Mitigação: `max_connections` e `inspect score`.
  - **`acp` quebrando de novo.** Mitigação: E2.
- **Não pode mudar:**
  - os quatro graders julgam o que julgam hoje;
  - o oráculo continua independente das tools;
  - a identidade do item vem do `student` do dataset, nunca do texto;
  - nenhuma rubrica muda sem o ok do dono.

## 8. Plano de implementação

| # | Tarefa | Depende de | Arquivos | Fronteira de teste | Pronto quando | Oráculo de verificação |
|---|---|---|---|---|---|---|
| T0 | Fundação: dependências (E1, E2), o esquema do sample (§6.2), o `listener.py` e o loader | — | `pyproject.toml`, `uv.lock`, `src/evals/dataset/`, `src/evals/listener.py` | Unitário | `uv lock --check` passa; o esquema valida um item de cada suíte; `make check-fast` verde | `inspect --version` no venv do worktree |
| T1 | Migrar os 163 itens para os quatro YAMLs novos | T0 | `src/evals/dataset/*.yaml` | Unitário (todos carregam e validam) | 163 itens, os mesmos ids, os ataques com os valores escritos | Contagem por suíte e split igual à soma antiga |
| T2 | Solver, scorer `graders`, tasks por suíte, métricas e mapeamento de eventos para mensagens | T0 | `src/evals/tasks.py`, `src/evals/solver.py`, `src/evals/scorers.py` | Unitário com fake do driver | Os scorers reproduzem os vereditos dos graders | `inspect eval ...@protocol -T ids=TR-01,TR-13 --epochs 2`: a conversa aparece no `inspect view` |
| T3 | Provedor `claudecode`, scorer `rubric`, task de calibração | T0 | `src/evals/judge/` | Unitário com processo falso | O juiz responde pelos dois provedores | Uma amostra julgada por `claudecode` e uma por `openai`; calibração em 4 rótulos |
| T4 | Resumo sobre os logs (§6.5) | T0 | `src/evals/summary.py` | Unitário com log de exemplo | Imprime acerto com o intervalo, pass^k, p50 e p95 e custo | Rodar sobre os logs do oráculo da T2 |
| T5 | Teste do gabarito em SQL | T1 | `tests/integration/evals/` | Integração | Toda referência cita os valores do oráculo | `pytest` do arquivo verde com o banco de pé |
| T6 | Remover o código substituído e os testes dele; atualizar o guia e o README | T2, T3, T4, T5 | `src/evals/` (os módulos da §6.1), `tests/*/evals/`, `docs/guia-do-eval.md`, `README.md` | Gate completo | `make check` verde; nenhum import morto | `rg` não acha os módulos removidos |
| R1 | Proposta de revisão das rubricas (§6.6) | — | Nenhum arquivo do repo: a tabela vai para o dono | Nenhuma | Tabela com todos os critérios classificados e as provas do tipo (d) | Conferência por amostra pelo agente dono |

### Ondas e paralelismo

- **Onda 0:** T0 e R1. R1 só lê e roda em paralelo com tudo.
- **Onda 1:** T1, T2, T3 e T4, com arquivos disjuntos.
- **Onda 2:** T5.
- **Onda 3:** T6.
- **Caminho crítico:** T0 → T1 → T5 → T6.

## 9. Para o agente executor

- **Comece por:** T0.
- **Leia antes:** a §5 e a §6 deste arquivo, `docs/guia-do-eval.md`, `src/evals/capture.py`, `src/evals/graders/suite.py` e
  `src/evals/judge/claude_code.py`.
- **Não toque:**
  - `src/evals/driver_factory.py`, `src/evals/student_driver.py` e os testes deles;
  - `src/api/`;
  - os arquivos do dono listados no `CLAUDE.md`;
  - `src/evals/results/`.
- **Ambiente:** o worktree tem venv próprio (`make setup`). O banco é o do Compose da pasta principal. A chave da OpenAI vem
  do `.env` da pasta principal, lido pelo processo e nunca carregado no shell.
- **Gates:** `make check-fast` por tarefa e `make check` ao fechar a onda. Comentário só no formato `# examiner:`. Decisão
  nova vai para o Registro antes de virar código.
- **Rodada real:** só a amostra do oráculo de cada tarefa. A rodada completa é do dono.

## Fontes

[^vault]: Vault do Obsidian, `frameworks-de-eval/`: pesquisa de 09/11/2026 sobre Inspect AI, DeepEval, promptfoo, Langfuse e
LangSmith.

## Registro

### 2026-11-09 — Mudança no spec: sem Inspect, eval enxuto e painel próprio

O dono decidiu não migrar para o Inspect AI. O que ficou depois do corte já é o domínio (graders, captura, driver, juiz e calibração), e
o visualizador do Inspect, um dos ganhos previstos, não serviu como apresentação. Este spec passa a valer como referência dos cortes e do
vocabulário, sem as tarefas T0 a T6. O que entrou, nesta mesma sessão, sem spec novo:

- **Vocabulário (E3, E4, P1 adaptados):** `golden/` virou `dataset/`, com um arquivo por suíte (`quality`, `security`, `protocol`,
  `scope`). `holdout` virou `test`, `--repeat` virou `--epochs`, `critical: true` virou `pass_k: 5` no item, e a regra crítica virou
  `gate.py`, com o pass^k junto. Os itens com `pass_k` sempre rodam quando a suíte entra, mesmo no split `test`. Os resultados antigos
  continuam legíveis: o loader traduz `holdout`, `critical`, `repetition`, `critical_keys` e `golden_critical_items`.
- **Oráculo:** saíram `facts`, `evidence`, `divergences`, `bindings` e `forbidden_facts`, com as cerca de 900 linhas de SQL e a CLI
  `evals.golden check`. Os valores dos ataques e os proibidos foram lidos do banco uma vez e escritos no YAML (`forbidden_values`). Ficou só
  a consulta dos identificadores alheios, conferida igual à antiga para três alunos.
- **Cortes da E7 sem Inspect:** a página por rodada, a amostra de conferência, o relatório em Markdown e a consistência separada saíram.
  O manifesto e a retomada ficaram. Saíram também as métricas que só o relatório antigo usava (pass@1 médio, estabilidade, acerto por grupo) e o rastreio de execuções refeitas. A checagem do bloco de confirmação no grader de proposta ficou, porque mudaria o que o grader julga.
- **Intervalo de confiança:** Wilson de 95% no acerto dos graders e do juiz (`report/metrics.py`).
- **Painel:** `python -m evals.dashboard` gera `src/evals/results/index.html` com todas as rodadas. A rodada e o julgamento o regeram ao
  terminar.
- **Tamanho:** o Python do eval caiu de 5.046 para 3.026 linhas, e os testes, de 2.482 para 1.880.

### 2026-11-09 — Checkpoint de implementação: eval enxuto e painel

Working tree no worktree `../cruzeiro-do-sul-eval-inspect`, sem commit. `make lint` e `make types` verdes; a suíte inteira passou
(1.374 testes, cobertura de 98%) com o ambiente do `.env.example` carregado só no processo do pytest, porque o worktree não tem `.env`.
Sem rodada de eval nova.

### 2026-11-09 — Mudança no spec: estados do gate e consistência no painel

- A rodada sem nenhum item de gate planejado passa a ser `SEM GATE` (saída 0), e não `INCOMPLETA`. Rodada que planeja só parte dos itens
  de gate é `PARCIAL` (saída 2). `INCOMPLETA` fica só para execução planejada que não rodou.
- O painel ganha a consistência geral: pass^k sobre todo item com mais de uma epoch, em todos os graders. A suíte de escopo, que não tem
  gate, mostra pass^3 em 40 de 41 itens.
- O painel explica graders, juiz, gate e a barra do intervalo no topo, e mostra quais execuções de gate falharam. Trocar de rodada não
  redesenha mais o histórico, o que fazia a página pular para o fim.

### 2026-11-09 — Mudança no spec: resultado da rodada, suítes no painel e skill `protocols`

- **Resultado da rodada** (`report/approval.py`): APROVADA quando nenhuma execução de gate falha, nenhuma execução planejada ficou de
  fora e graders e juiz ficam a partir de 85%. PENDENTE enquanto o juiz não julgou. É do painel; a saída do comando continua a do gate,
  porque o juiz roda depois.
- **Suítes por rodada:** o painel mostra quantos itens de cada suíte a rodada rodou, para não comparar a rodada de escopo com a de entrega.
- **Skill `protocols`:** antes de perguntar o que trancar ou cancelar, o agente consulta `list_enrollments`; matrícula já trancada leva a
  oferecer a reativação. Pedido explícito de uma disciplina vai direto para a orientação de procurar a secretaria. É a correção pendente
  do PR-08#5 e do TR-11 da T14. Sem rodada nova até o dono pedir.
