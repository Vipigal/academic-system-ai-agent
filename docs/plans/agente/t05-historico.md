---
type: Plan
title: T5 · Histórico
description: Tarefa da fase do agente que cria o port e o repositório das conversas no schema agent, com ownership por pessoa e janela que não separa chamada e resultado de tool.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
---

# T5 · Histórico

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Onda 1, depende de T1 e T2. Modelo sugerido:
> Sonnet.

## Objetivo

Guardar e ler conversas no schema `agent` (spec-mãe, §6.5), com o mesmo isolamento das outras tabelas.

## O que fazer

1. Entidades de domínio da conversa, mensagem e chamada de tool, e o port `ConversationRepository` em
   `domain/ports/conversation.py`: criar conversa, acrescentar uma troca (mensagem do aluno, mensagens do assistente e
   chamadas de tool) e ler a janela das últimas N mensagens.
2. Models, mappers, ownership e o `SqlConversationRepository` em `persistence/agent/`. `conversation` tem dono pelo
   `person_id` da sessão; `message` e `tool_call` chegam a ele por `Via` (B33). Registrar as tabelas em
   `persistence/core/ownership_registry.py`.
3. A janela nunca corta uma mensagem do assistente com chamadas de tool longe dos resultados.
4. `bootstrap/history_providers.py`: provider por request a partir do adapter.

## Testes

Integração: gravar e ler uma conversa com tool calls; janela no limite; conversa de outra pessoa e conversa inexistente têm a
mesma resposta (invariante 6); a carga não depende de dado vindo do cliente.

## Pronto quando

`make check` verde, com a tabela nova coberta pelo teste de ownership completo.

## Oráculo

Linhas em `agent.*` depois do teste de integração, conferidas por `psql`, com `person_id` só em `conversation`.
