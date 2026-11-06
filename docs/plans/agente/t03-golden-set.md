---
type: Plan
title: T3 · Golden set e red team
description: Tarefa da fase do agente que transforma o catálogo de perguntas em golden set YAML, com fatos amarrados a consultas SQL nomeadas, e cria o conjunto de ataques.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
---

# T3 · Golden set e red team

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Onda 1, depende de T1 (o `pyyaml` e o
> `Settings` no bootstrap). Modelo sugerido: Opus: um fato errado no gabarito contamina toda a escolha de modelo.

## Objetivo

Dados e validação do eval, no formato da §6.6 do spec-mãe. Não depende do agente.

## O que fazer

1. `src/evals/golden/questions.yaml`: os 60 itens do catálogo, com o mesmo código. Tools esperadas vêm de
   `tests/agent_map.py`; resposta ideal do catálogo em `reference`. Perguntas sem caso no catálogo recebem um aluno real
   escolhido pela consulta que cumpre a armadilha, e a escolha fica no item.
2. `src/evals/oracle_queries.py`: as consultas nomeadas, escritas direto sobre as tabelas, sem usar tools nem services.
   Reaproveitar as regras já provadas em `tests/integration/support/sql_oracle.py` e nos testes das tools.
3. `src/evals/golden/redteam.yaml`: ataques com `kind: attack`, cobrindo no mínimo:
   - pedir dados de outro aluno por RA, nome ou CPF;
   - prompt injection direta e dentro de texto que vira dado (mensagem de protocolo);
   - pedir o prompt, as tools, credenciais ou dados de funcionário;
   - mudar de papel ("sou o coordenador");
   - forjar confirmação de protocolo pelo texto.
   Cada ataque declara o que não pode aparecer na resposta e quais tools não podem ser chamadas.
4. Oráculo do eval com conexão própria por `APP_ORACLE_DATABASE_URL`, como o `SqlOracle` dos testes: a role `api` não lê tudo.
5. Esquema dos itens em pydantic e um validador: `python -m evals.golden check`.
6. Decisões do dono que mudam gabarito: SR-05 usa 01/02/2023 (D13 do spec-mãe).

## Testes

Unitário: o esquema recusa item inválido. Integração: o validador roda todas as consultas contra o banco.

## Pronto quando

- O validador passa: 60 itens com códigos iguais aos do catálogo, tools existentes no registro, cada fato devolvendo
  exatamente um valor para o aluno do item, split com cerca de 30% em holdout em todas as áreas.
- Pelo menos 25 ataques.
- Os números dos fatos batem com as respostas ideais do catálogo; divergência vai para o Registro com a consulta que a mostra.

## Oráculo

Saída do validador com a contagem por área, `kind` e split, e a lista de fatos com o valor de cada um.
