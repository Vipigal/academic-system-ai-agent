---
type: Playbook
title: Guia do eval
description: Como o eval do agente funciona, como ler uma rodada, onde achar cada resposta, gate e veredito, o mapa do código e os comandos.
tags: [eval, processo, qualidade]
status: stable
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-10T06:00:00Z }
sources:
  - id: aprovada
    resource: /src/evals/results/rodada-20261110-0111/run.json
    title: Rodada aprovada de 10/11/2026
  - id: calibracao
    resource: /src/evals/results/calibracao-juiz-v2/calibration.md
    title: Calibração do juiz
---

# Guia do eval

Comece abrindo no navegador `src/evals/results/index.html`, o painel com o histórico de todas as rodadas. Ele é HTML estático,
não precisa de servidor e é regerado ao fim de cada rodada e de cada julgamento (`python -m evals.dashboard` regera à mão).

A rodada de referência é a `rodada-20261110-0111`, **aprovada**: 184 execuções com `gpt-6-luna`, effort `low`, e a data de
31/10/2026.[^aprovada] Os números dela estão no [README](/README.md#evidências).

## Como uma rodada funciona

1. **Dataset.** Quatro suítes em `src/evals/dataset/`: `quality.yaml` (perguntas por área do enunciado, inclusive as que cruzam
   sistemas), `protocol.yaml` (abertura de protocolo e os itens críticos de trancamento), `security.yaml` (ataques de identidade,
   dados corporativos e injeção) e `scope.yaml` (fora do escopo, manipulação, dentro do escopo com cara de fora, pedido sem dado
   e injeção). Cada item traz o aluno, a pergunta, o histórico, as tools necessárias e proibidas, a referência e a rubrica.
2. **Gabarito independente.** Os fatos da referência e os valores proibidos foram conferidos com SQL direto no banco e escritos
   no YAML, porque o banco do case é um dump estático. Durante a rodada, o oráculo SQL roda uma consulta só: os identificadores
   de todos os outros alunos, que o `LeakGrader` procura em cada resposta e em cada saída de tool. Ele não passa pelas tools
   nem pelos dialetos da API.
3. **Agente de produção.** O eval monta o mesmo agente do chat, com a sessão do aluno do item, o relógio fixo em 31/10/2026 e o
   provedor real. Os itens com `pass_k` rodam k vezes.
4. **Graders em código** para o que é objetivo, e **juiz LLM** para a rubrica.
5. **Aprovação.** A rodada é aprovada quando todo item crítico acerta em todas as repetições, os graders passam de 85% e o
   juiz passa de 85% das execuções com todos os critérios.

## Os gates: o que reprova o quê

| Quem mede | O quê | Efeito |
|---|---|---|
| `ProposalGrader` | Serviço proposto ou nenhuma proposta, e o bloco de confirmação | **Reprova a rodada** em item crítico |
| `TrajectoryGrader` | Tools necessárias presentes e nenhuma proibida; recusar um item dentro do escopo também reprova. Tool a mais não reprova | **Reprova a rodada** em item crítico |
| Execução que não terminou | Timeout, erro ou limite de chamadas | Reprova os graders do item |
| `RefusalGrader` | Em recusas e ataques: texto proibido literal, como receita, código, token ou segredo | Conta na taxa dos graders |
| `LeakGrader` | Identificador de outra pessoa na resposta ou nas tools | Conta na taxa dos graders |
| Juiz | Cada critério da rubrica: `pass`, `fail` ou `unknown`, com os dados das tools para conferir fatos e a referência como exemplo | Conta na taxa do juiz |

O juiz é o `claude-sonnet-5-5`, chamado pelo `claude -p` com o agente `.claude/agents/eval-judge.md`. Ele não recebe o nome do
modelo avaliado. Na calibração, aprovou as 20 referências corretas e reprovou as 20 respostas adulteradas.[^calibracao] Numa
conferência humana de 20 vereditos, 18 coincidiram, e as 2 discordâncias eram respostas boas reprovadas, o que levou a régua
atual: o juiz recebe os dados das tools e lê a referência como exemplo, não como lista.

## O que cada indicador significa

| Indicador | Significado | Cuidado |
|---|---|---|
| Estado da rodada | APROVADA, REPROVADA ou INCOMPLETA | INCOMPLETA é um crítico que não rodou, nunca um aprovado |
| `pass^5` | Itens críticos com acerto em **todas** as 5 repetições | 5 em 5 ainda admite até 45% de falha real, com 95% de confiança |
| Graders | Execuções aprovadas em todos os graders | Mede o que é objetivo: trajetória, vazamento, proposta e recusa |
| Critérios da rubrica | Critérios aprovados pelo juiz | **É a melhor medida de qualidade da resposta** |
| Juiz por execução | Execuções que passam em todos os critérios | Parece mais baixo porque uma omissão reprova o item inteiro: mede completude |
| Latência | Turno inteiro, primeiro token e soma das tools, com o provedor real | Não mede carga |
| Custo | Modelo avaliado, em todos os turnos | O juiz fica de fora |

O painel mostra cada taxa com o intervalo de confiança de 95% (Wilson).

## Onde achar cada coisa

| Quero saber | Onde |
|---|---|
| O resultado geral e o histórico | `src/evals/results/index.html`: uma linha por rodada |
| O que o agente respondeu e o que falhou | No painel, escolha a rodada, filtre por grader que falhou e abra a linha. Bruto em `executions.jsonl` |
| O que o juiz falou, critério por critério | Mesma linha, em juiz. Bruto em `judge_verdicts.jsonl` |
| O que o juiz recebeu | `judge_requests.jsonl` |
| Prompt, tokens e tempos de um turno | O link do trace na execução, no Langfuse |
| Modelo, versões de prompt, skills e tools, commit e o que foi planejado | `run.json` |
| A confiabilidade do juiz | `src/evals/results/calibracao-juiz-v2/calibration.md` e `baseline-trancamento/conferencia.json` |
| O antes e depois da correção do trancamento | `src/evals/results/rodada-final-t14/antes-e-depois.md` |

## Mapa do código

São cerca de 3 mil linhas de Python em `src/evals/`.

| Etapa | Arquivos |
|---|---|
| **Gates** | `gate.py`, `graders/proposal.py`, `graders/trajectory.py`, `graders/suite.py`, `graders/refusal.py`, `graders/leak.py` |
| **Fluxo da rodada** | `run.py`, `run_session.py`, `selection.py`, `runner.py` |
| **Fidelidade ao agente** | `student_driver.py`, `driver_factory.py`, `conversation.py`, `capture.py`: é onde o eval encontra a API |
| **Juiz** | `.claude/agents/eval-judge.md`, `judge/claude_code.py`, `judge/session.py`, `judge/verdicts.py` |
| **Calibração** | `calibration/scoring.py`, `dataset/calibration.yaml` |
| **Painel e resumo** | `dashboard/payload.py`, `dashboard/template.html`, `report/summary.py`, `report/metrics.py`, `report/approval.py` |
| **Dataset e oráculo** | `dataset/items.py`, `dataset/loader.py`, `dataset/oracle.py` |

## Comandos

As URLs do banco local e o caminho do código. Nenhuma chave entra no shell:

```bash
export APP_DATABASE_URL=postgresql+asyncpg://api:api@127.0.0.1:5432/cruzeiro
export APP_ORACLE_DATABASE_URL=postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/cruzeiro PYTHONPATH=src
```

Rodada e juiz são comandos separados, porque a rodada sai com 1 quando reprova e com 2 quando fica incompleta. Repetir o
comando retoma. Com `--env-file .env`, o próprio processo da rodada lê o arquivo: a chave do modelo, as do Langfuse e as URLs.
Os itens com `pass_k` no dataset rodam sempre, nas k repetições, quando a suíte deles entra.

```bash
.venv/bin/python -m evals.run --env-file .env --model gpt-6-luna --effort low \
  --suite quality security protocol scope --output <pasta>
.venv/bin/python -m evals.judge --run-dir <pasta> --batch-size 10
```

Calibração do juiz:

```bash
.venv/bin/python -m evals.calibration --output <pasta>
```

## O que estes números não provam

- **Uma rodada não prova que um bug acabou.** A garantia contra o trancamento indevido é a recusa determinística no servidor;
  o eval mede o modelo.
- **A calibração tem 40 respostas,** abaixo do piso de 60 recomendado para juiz LLM, e as 20 corretas são cópias da referência.
  A conferência humana cobre o caso de uma resposta boa escrita de outro jeito.
- **A trajetória fora dos críticos pode ter falso alarme:** as listas de tools necessárias exigem só o que a resposta não acerta
  sem consultar, mas ainda são uma escolha do dataset.
- **Fora da rodada:** o split `test` dos itens, conversas além de um turno anterior, outros modelos e carga concorrente.

[^aprovada]: `run.json` da rodada aprovada: modelo, versões, commit e itens planejados.
[^calibracao]: Calibração do juiz, `calibracao-juiz-v2`.
