---
type: Plan
title: T2 · Banco
description: Tarefa da fase do agente que cria constraints, índices, o schema agent e a role restrita da API, aplicados com volume novo, e separa a URL do oráculo.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:59:00Z }
---

# T2 · Banco: constraints, índices, schema `agent` e role

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Arrumação, depois de T1b. Modelo sugerido:
> Sonnet, com a role revisada com atenção.

## Objetivo

Criar os scripts `02` a `05` de `db/init/` (arquitetura, 5.7) e tirar o superuser da API e do código da API nos testes
(B13, D18 do spec-mãe).

## O que fazer

1. `02_constraints.sql`: PKs do README; FKs, com `NOT VALID` nas 5 violadas (A11, B24).
2. `03_indexes.sql`: índices nas colunas e expressões que as regras de ownership e as consultas de navegação usam, já com o
   desenho de T1b. Derivar das consultas reais: rodar a suíte com `pg_stat_statements` ou log de consultas e conferir com
   `EXPLAIN` as mais frequentes. Predicados de dialeto sobre chaves sujas pedem índice de expressão igual à expressão.
3. `04_agent_schema.sql`: schema `agent` com `conversation`, `message` e `tool_call` (spec-mãe, §6.5) e as sequências de
   número de protocolo e de mensagem, iniciadas acima do maior valor existente.
4. `05_roles.sh`: role `api` com `SELECT` nas tabelas mapeadas e nas tabelas de identidade que a carga da sessão e a
   consulta de pagador leem; `INSERT` só em `protocol`, `protocol_status_history` e `protocol_interaction`; leitura e
   escrita em `agent`; uso das sequências; sem `UPDATE` ou `DELETE` em dados de origem; sem acesso a `analyst`. Script de
   shell para ler a senha de `API_DB_PASSWORD`, que T1 já passa ao serviço `db`.
5. `compose.yaml` e `.env.example`: a URL do serviço `api` passa a usar a role `api`.
6. URL do oráculo: um setting próprio (por exemplo `APP_ORACLE_DATABASE_URL`) que o `SqlOracle` dos testes e o oráculo do
   eval usam com o superuser; o código da API nos testes usa `APP_DATABASE_URL` com a role `api`. O `Makefile` é do dono:
   a tarefa entrega as duas linhas novas de `export` para o patch final.
7. Teste de integração que conecta como `api` e prova: lê uma tabela mapeada, não lê `analyst`, não faz `UPDATE` nem
   `DELETE` em `finance.invoice`, insere em `agent.conversation`.

## Execução

`docker compose down -v && docker compose up -d --wait`, liberado pelo dono (D21). Recriar o volume só depois que os
scripts passarem num banco descartável (outro projeto do Compose em outra porta), para não deixar o banco principal quebrado.

## Pronto quando

- Volume recriado sem erro; os 4 scripts aplicados, conferidos no log do container.
- `make check` verde com a API como `api` e o oráculo como administrador, incluindo o teste da role.
- `docker compose up -d --wait api` sobe com a role, e `/health` responde 200.
- Latência das consultas de ownership medida antes e depois dos índices, registrada no Registro do spec-mãe.

## Oráculo

`psql` como `api`: `SELECT` em `analyst` e `UPDATE` em `finance.invoice` negados. `EXPLAIN` da consulta de faturas usa
índice.
