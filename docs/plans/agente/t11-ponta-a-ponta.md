---
type: Plan
title: T11 · Montagem e ponta a ponta
description: Tarefa da fase do agente que liga as rotas no ApiFactory, sobe tudo no Compose e prova o fluxo login, chat e confirmação de protocolo.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
---

# T11 · Montagem e ponta a ponta

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Onda 3, depende de T8 e T9. Modelo sugerido:
> Sonnet.

## Objetivo

A API real, no Compose, faz o fluxo inteiro.

## O que fazer

1. `bootstrap/app.py`: inclui as rotas de login, chat e confirmação; liga observabilidade; CORS só para a origem do front, com
   o header `Authorization` liberado.
2. `tests/e2e/`: com o modelo fake, login, pergunta com tool, proposta de protocolo, confirmação e listagem do protocolo
   novo, tudo por HTTP. Um teste `live` com o mesmo roteiro e `gpt-6-luna`.

## Pronto quando

`make check` verde; o e2e `live` passa; o fluxo roda contra `docker compose up -d --wait api`.

## Oráculo

`curl` contra o Compose: `dev-login`, `/chat` com stream, `confirm`, e o protocolo novo em `list_protocols`. No log, uma linha
JSON por etapa com o mesmo `trace_id`; no Langfuse, o trace da conversa.
