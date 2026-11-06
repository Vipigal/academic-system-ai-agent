---
type: Plan
title: T6 · Identidade e login simulado
description: Tarefa da fase do agente que lê o person_id do JWT numa dependência de request, cria o login simulado e o provider da sessão imutável.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
---

# T6 · Identidade e login simulado

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Onda 1, depende de T1. Modelo sugerido: Sonnet.

## Objetivo

A identidade vem só do token (enunciado, premissa de identidade), e a sessão nasce pronta (B37).

## O que fazer

1. `presentation/http/identity.py`: dependência que lê `Authorization: Bearer`, valida assinatura e validade do JWT (HS256,
   segredo de settings) e devolve o `person_id` do `sub`. Sem token ou token inválido: `401`, sem detalhe.
2. `presentation/http/auth.py`: `POST /auth/dev-login` com `{student: "marca:RA"}`, que resolve a pessoa e devolve o JWT.
   Só existe com `APP_DEV_LOGIN=true` (P2). Aluno inexistente: `404`.
3. `bootstrap/identity_providers.py`: provider da `StudentSession` a partir do `person_id`, pelo `StudentSessionLoader`.
4. A resolução de `marca:RA` para pessoa é um caso de uso pequeno na application, sobre um port já existente ou novo.

## Testes

Integração HTTP com um app de teste: login devolve token; rota protegida sem token, com token alterado ou expirado devolve
`401`; o `person_id` vem só do token, mesmo com outro id no corpo; com `dev_login` desligado a rota não existe.

## Pronto quando

`make check` verde.

## Oráculo

`curl` no app de teste: login, chamada protegida com o token, a mesma chamada com o token de outro aluno trazendo outro
`person_id` na sessão.
