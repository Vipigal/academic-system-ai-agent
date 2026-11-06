---
type: Plan
title: T7 · Observabilidade
description: Tarefa da fase do agente que liga o Langfuse Cloud com handler por request e decorators nos casos de uso, e cria o log estruturado em JSON.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
---

# T7 · Observabilidade

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Onda 1, depende de T1. Modelo sugerido: Sonnet,
> usando a skill `langfuse` para conferir a API do SDK 5.

## Objetivo

Traces com latência, tokens e custo por request no Langfuse Cloud, e log estruturado (D10, P7).

## O que fazer

1. `infrastructure/tracing.py`: inicializa o cliente do Langfuse a partir de settings. Sem chaves, o tracing fica desligado
   sem erro. Cria um `CallbackHandler` **por request** e as tags e metadados: `user_id` como HMAC do `person_id`, id da
   conversa, modelo, versão do prompt e hash das skills.
2. Os casos de uso da application que viram span (`ChatService` e confirmação de protocolo, nas tarefas que os criam) usam
   `@observe` do SDK; esta tarefa documenta o padrão e o aplica no `HealthService` como exemplo, o único caso de uso que nenhuma outra
   tarefa da onda toca.
3. `infrastructure/logging.py`: formatador JSON com `logging` da biblioteca padrão; campos fixos `level`, `logger`,
   `message`, `request_id` e `trace_id`. Nunca CPF, nunca `person_id` em claro.
4. `bootstrap/observability.py`: liga tracing e log na subida.

## Testes

Unitário: sem chaves, nada é enviado; o `user_id` não é o `person_id`; o log sai em JSON válido sem campos proibidos.

## Pronto quando

`make check` verde; um trace de exemplo aparece no projeto do Langfuse com as tags esperadas.

## Oráculo

Consulta pelo MCP ou pela skill do Langfuse: o trace existe, com `user_id` anonimizado e as tags.
