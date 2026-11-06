---
type: Plan
title: T9 · Chat com stream
description: Tarefa da fase do agente que cria o ChatService, com histórico e agente, e a rota /chat que emite o protocolo de stream do AI SDK.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
---

# T9 · Chat com stream

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Onda 2, depende de T4, T5, T6 e T7. Modelo
> sugerido: Opus.

## Objetivo

Uma conversa por HTTP, com resposta em stream, histórico gravado e identidade do token (spec-mãe, §6.3).

## O que fazer

1. **Antes de codar:** conferir na documentação do AI SDK 7 os nomes e campos dos eventos do stream. Divergência da §6.3 vira
   "Mudança no spec".
2. `application/chat/`: `ChatService` carrega a janela do histórico, executa o agente em stream, repassa os eventos e grava
   a troca ao final, com modelo, tokens e latência. Usa só a última mensagem do aluno (D14). É um span do Langfuse.
3. `presentation/http/ui_stream.py`: converte os eventos da application para o protocolo do AI SDK, com os headers e o
   `[DONE]` final. Erro vira o evento `error` com texto genérico.
4. `presentation/http/chat.py`: `ChatRouter.build(...)` com `POST /chat`, recebendo o provider do `ChatService`.
5. `bootstrap/chat_providers.py`: monta o `ChatService` por request a partir das tarefas de T4, T5, T6 e T7.

## Testes

Integração HTTP com app de teste e modelo fake: a ordem dos eventos para uma resposta com tool; a troca gravada no
histórico; a segunda mensagem da conversa vê a primeira; mensagens de assistente enviadas pelo cliente são ignoradas;
conversa de outro aluno devolve `404`; sem token, `401`.

## Pronto quando

`make check` verde.

## Oráculo

`curl -N` no app de teste mostra os eventos chegando aos poucos, e o histórico em `agent.*` bate com o que foi transmitido.
