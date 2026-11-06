---
type: Plan
title: T12 · Front de chat
description: Tarefa da fase do agente que cria a página de chat em React com AI SDK useChat, escolha de aluno simulada e o card de confirmação de protocolo.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
---

# T12 · Front de chat

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Onda 4, depende de T11. Modelo sugerido: Sonnet.

## Objetivo

A página mínima de chat que o enunciado e B26 pedem, sem gastar tempo com UI (D8).

## O que fazer

1. `src/app/`: React com Vite e TypeScript, `ai` e `@ai-sdk/react` em versões exatas. Componentes prontos do assistant-ui
   são opcionais; se derem atrito, `useChat` com poucos componentes próprios.
2. Escolha do aluno: campo `marca:RA` e alguns alunos do golden set como atalho; chama `dev-login` e guarda o token na memória
   da página.
3. Chat com `useChat` e `DefaultChatTransport` apontando para `/chat`, com o Bearer no header.
4. Parte `tool-propose_protocol` renderizada como card: serviço, matrícula, mensagem e o botão "Confirmar", que chama a rota
   de confirmação com o token da proposta. Mostra o número do protocolo ou o erro.
5. Estados: carregando, erro da API, conversa vazia.
6. Instruções de rodar no `README` de `src/app/`, com `npm` e a URL da API.

## Pronto quando

O fluxo roda no navegador contra a API do Compose.

## Oráculo

Pelo Chrome DevTools MCP: escolher `UniAraucaria_EAD:013161`, perguntar FI-01 e ver o stream; pedir um protocolo, ver o card,
confirmar e ver o número; derrubar a API e ver o estado de erro; largura de celular sem rolagem lateral.
