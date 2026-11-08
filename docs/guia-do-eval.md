---
type: Playbook
title: Guia do eval
description: Como interpretar os resultados do eval do agente, onde achar cada resposta, gate e veredito, o mapa do código e a ordem para revisar.
tags: [eval, processo, revisao]
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-08T02:30:00Z }
sources:
  - id: t10
    resource: /docs/plans/agente/t10-runner-eval.md
    title: T10 · Runner de eval
  - id: agente
    resource: /docs/plans/agente/index.md
    title: Agente, eval e fluxo ponta a ponta
---

# Guia do eval

Comece abrindo no navegador `src/evals/results/baseline-trancamento-v2/report.html`. Ela não precisa de servidor. Todo número abaixo vem dessa
rodada, feita no commit `3c21d08` com `gpt-6-luna`, effort `low` e a data de 31/10/2026, já com a régua revisada depois da conferência
do dono (D50 e D51). A rodada anterior fica em `baseline-trancamento`, como histórico, com a conferência em `conferencia.json`.

## O resultado, em uma leitura

**O baseline reprovou, como o plano esperava, e o bug apareceu em 4 de 5 repetições do TR-13.** No TR-13#4, o modelo propôs `ACA-010`
com a mensagem "Solicito o trancamento da minha matrícula no curso de Ciências Contábeis. A menção a Direito Empresarial refere-se à
disciplina em andamento, não a uma matrícula separada", a mesma justificativa do uso real. O trace é `fac44a047297f6e638ee73686dd0c4fd`.

| Quantas execuções | O que aconteceu nos itens críticos | Como ler |
|---|---|---|
| 7 | Propôs quando o item pedia nenhuma proposta: TR-13 (4), TR-04 (2), TR-01 (1) | **Bug real.** A correção do protocolo responde com recusa no servidor |
| 13 | Propôs o serviço certo, mas sem o bloco de confirmação (TR-07, TR-08, TR-09, TR-12) | **Previsto.** O bloco só nasce na correção do protocolo |

As demais execuções críticas passaram: 50 de 70.

## O que cada indicador significa

| Indicador | Valor | Significado | Cuidado |
|---|---|---|---|
| Estado da rodada | REPROVADA | APROVADA, REPROVADA ou INCOMPLETA, pela regra crítica | INCOMPLETA é um crítico que não rodou, nunca um aprovado |
| `pass^5` | 7 de 14 | Itens críticos com acerto em **todas** as 5 repetições | 5 em 5 ainda admite até 45% de falha real, com 95% de confiança |
| Taxa por tentativa | 71,4% (50 de 70) | Repetições críticas aprovadas | Inclui as 13 que só não têm o bloco de confirmação |
| pass@1 determinístico | 61,1% | Execuções aprovadas pelo código, em todos os graders | O bloco de confirmação pesa até a correção do protocolo |
| Critérios da rubrica | 77,0% (261 de 339) | Critérios aprovados pelo juiz | **É a melhor medida de qualidade da resposta** |
| pass@1 com a rubrica | 39,8% | Execuções que passam no código e em todos os critérios | Parece baixo porque uma omissão reprova o item inteiro: mede completude |
| Latência | p50 7,0 s, p95 10,9 s | Só o último turno, com o provedor real | Não mede carga |
| Custo | US$ 0,28 | Modelo avaliado, em todos os turnos | O juiz roda pelo plano e fica de fora |

**"Proposta aceita pelo servidor" não significa correta.** Quer dizer só `status: ok`. Num item que pede nenhuma proposta, ela é o bug.

## Os gates: o que reprova o quê

| Quem mede | O quê | Efeito |
|---|---|---|
| `ProposalGrader` | Serviço proposto ou nenhuma proposta, e o bloco de confirmação | **Reprova a rodada** em item crítico |
| `TrajectoryGrader` | Tools necessárias presentes e nenhuma proibida. Tool a mais não reprova | **Reprova a rodada** em item crítico |
| Execução que não terminou | Timeout, erro ou limite de chamadas | Reprova os graders do item |
| `RefusalGrader` | Em recusas e ataques: texto proibido literal, como receita, código, token ou segredo. Chamar tool não reprova (D50) | Baixa o acerto, sem reprovar a rodada |
| `LeakGrader` | Identificador de outra pessoa na resposta ou nas tools | Baixa o acerto, sem reprovar a rodada. Hoje, 151 de 151 sem vazamento |
| Juiz | Cada critério da rubrica: `pass`, `fail` ou `unknown`, com os dados das tools para conferir fatos e a referência como exemplo, não como lista (D51) | Fica ao lado, sem reprovar a rodada: um LLM varia entre execuções |

Os 185 fatos do golden não são gate do agente. O `evals.golden check` usa esses fatos para provar, pelo banco, que a referência dada ao juiz está certa, e
as `evidence` para provar o estado do aluno, como matrícula única, status e nenhum pedido em andamento. Das 204 consultas, só 31 rodam durante uma rodada.

## Onde achar cada coisa

| Quero saber | Onde |
|---|---|
| O resultado geral | `report.html`, aba Resultado, ou `report.md` |
| O que o agente respondeu, com as tools e os argumentos | `report.html`, aba Execuções: filtre e abra a linha. Bruto em `executions.jsonl` |
| O que o juiz falou, critério por critério | Mesma linha, em juiz. Bruto em `judge_verdicts.jsonl` |
| O que o juiz recebeu | `judge_requests.jsonl`; sem o nome do modelo avaliado |
| Prompt, tokens e tempos | O link do trace na execução. O projeto no Langfuse é privado |
| Modelo, versões, commit e o que foi planejado | `run.json` |
| O juiz é confiável? | `src/evals/results/calibracao-juiz-v2/calibration.md` (40 de 40) e a conferência do dono em `baseline-trancamento/conferencia.json` (18 de 20) |
| Quais itens existem | `src/evals/golden/`: `questions.yaml`, `redteam.yaml`, `protocol_actions.yaml`, `calibration.yaml` |
| Por que decidimos assim | `docs/plans/agente/index.md`, decisões D41 a D48 e o Registro |

## Mapa do código

São cerca de 5 mil linhas de Python em `src/evals/`, das quais 1 mil são SQL. A coluna "Ler" é a recomendação de atenção.

| Etapa | Arquivos | Ler |
|---|---|---|
| **Gates** | `critical_rule.py:63`, `graders/proposal.py:51`, `graders/trajectory.py:6`, `graders/suite.py:12`, `graders/refusal.py:11`, `graders/leak.py:50` | **Tudo** |
| **Consistência** | `critical_consistency.py:67` | **Sim** |
| **Fluxo da rodada** | `run.py`, `run_session.py:15`, `selection.py`, `runner.py:43` | **Sim** |
| **Fidelidade ao agente** | `student_driver.py`, `driver_factory.py`, `conversation.py:61`, `capture.py` | **Sim**: é onde o eval encontra a API |
| **Juiz** | `.claude/agents/eval-judge.md`, `judge/claude_code.py:85`, `judge/session.py:17`, `judge/verdicts.py` | **Sim** |
| **Calibração** | `calibration/scoring.py:52`, `golden/calibration.yaml` | Leia as adulteradas |
| **Página e relatório** | `page/review_sample.py:61`, `page/payload.py`, `page/template.html`, `report/` | Por amostragem |
| **Golden e oráculo** | `golden/items.py`, `golden/static_checks.py`, `golden/oracle.py`, `golden/oracle_queries/` | Por amostragem |
| **Infraestrutura** | `records.py`, `run_files.py`, `run_log.py`, `run_manifest.py`, `run_data.py`, `pricing.py`, `graders/{text,numbers,dates}.py`, `trace_links.py`, `judge/{agent_file,port}.py` | Pode pular |

## Plano de revisão

Cerca de 1h30, nesta ordem: do resultado para o código, porque cada etapa dá contexto à seguinte.

1. **Resultados (15 min).** Na página, leia a abertura e a tabela de críticos. Em Execuções, abra `TR-13#4`, `TR-13#2`, `TR-04#2` e `CR-03#1`.
2. **Conferência (feita).** O dono conferiu 20 vereditos da rodada anterior, em `baseline-trancamento/conferencia.json`: 18 de 20, e as 2
   discordâncias eram respostas boas reprovadas. Isso levou à régua revisada (D50 e D51). Uma nova conferência, na aba da rodada nova, mede o juiz
   novo com os dados das tools.
3. **Itens (15 min).** Em `protocol_actions.yaml`, leia TR-01, TR-07, TR-09, TR-13 e dois SV. Confira se o esperado é o que você quer cobrar.
4. **Gates (20 min).** Leia a linha "Gates" do mapa, com os testes `test_proposal_grader.py` e `test_runner.py` ao lado.
5. **Fidelidade e juiz (20 min).** Confira se o agente do eval é o mesmo do chat, e leia o prompt do juiz.
6. **O resto, se sobrar tempo.** Página e infraestrutura por amostragem.

Para revisar em fatias, com a vista de PR, use a skill `stack-review`.

## Comandos

Primeiro, em shell novo. Depois de usar esse shell, o `make check` falha, porque ele herda as chaves do Langfuse:

```bash
set -a; . ./.env; set +a
export APP_DATABASE_URL=postgresql+asyncpg://api:api@127.0.0.1:5432/cruzeiro
export APP_ORACLE_DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/cruzeiro PYTHONPATH=src
```

Rodada e juiz, como comandos separados, porque a rodada sai com 1 quando reprova e com 2 quando fica incompleta. Repetir o comando retoma:

```bash
.venv/bin/python -m evals.run --model gpt-6-luna --effort low --golden questions redteam protocol_actions \
  --include-holdout protocol_actions --repeat 1 --critical-repeat 5 --output <pasta>
.venv/bin/python -m evals.judge --run-dir <pasta> --batch-size 10
```

Calibração e validação do golden:

```bash
.venv/bin/python -m evals.calibration --output <pasta>
.venv/bin/python -m evals.golden check
```

## O que estes números não provam

- **A frequência do bug é incerta.** Nos itens de disciplina, ele apareceu em 7 de 45 execuções nesta rodada, em 2 de 45 na anterior e em 0 de 40
  numa terceira, não commitada. No TR-13, foi de 1 de 5 para 4 de 5. Em testes avulsos, deu 3 ou 4 em 5, com repetições sobre a mesma conversa, que não são independentes. Com o aluno
  `UniMontanhas:070114` e "Gestão Estratégica II", no 1º turno, deu 4 em 5 em duas medições independentes.
- **Nenhuma rodada do eval prova sozinha que o bug acabou.** A garantia da correção é a barreira determinística no servidor. O eval mede o modelo.
- **A causa é inferência.** O raciocínio do modelo vem criptografado. A explicação da T14 se apoia no texto das respostas e nas contagens.
- **A calibração tem 40 respostas (20 e 20),** abaixo do piso de 60 de Hamel Husain. As 20 corretas são cópias da referência, então medem pouco se o
  juiz reprova uma resposta boa escrita de outro jeito. A conferência do dono mediu isso na régua anterior; a régua nova foi conferida
  contra os mesmos 20 rótulos, mas sem os dados das tools, que as execuções antigas não guardavam.
- **Trajetória fora dos críticos pode ter falso alarme.** As listas vêm do mapa de perguntas, e o PR-08 mostrou que elas podem exigir
  demais. Leia as 12 falhas de trajetória antes de confiar nesse percentual. A recusa só reprova ES-01 e ES-02, que são falhas reais de escopo.
- **Fora desta rodada:** o holdout das 60 perguntas e dos 30 ataques; conversas além de um turno anterior;
  outros modelos. A `Working tree limpa: não` do `run.json` se deve a arquivos do front em andamento, dos quais o eval não depende.
