---
type: Plan
title: T8 · Confirmação de protocolo
description: Tarefa da fase do agente que assina a proposta de protocolo, abre o protocolo no domínio e grava as 3 linhas por uma rota fora do LLM.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
---

# T8 · Confirmação de protocolo

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Onda 2, depende de T1, T2 e T6. Modelo sugerido:
> Opus: é a única escrita do sistema.

## Objetivo

O aluno aprova com um clique e a API grava, sem o LLM (B26, B40; spec-mãe, §6.4).

## O que fazer

1. `infrastructure/proposal_signer.py`: assina e confere o token da proposta (HMAC-SHA256, segredo e validade de settings),
   atrás de um port.
2. `ProtocolProposer` passa a devolver o `token` junto da proposta. É a única mudança no schema visível ao modelo; o snapshot
   das descrições continua igual.
3. Domínio: abertura do protocolo com as regras e efeitos em memória (arquitetura, 5.6): situação aberta, prazo pelo SLA do
   serviço, histórico inicial e mensagem do requerente. Número de protocolo e de mensagem vêm das sequências do schema `agent`.
4. `persistence/secretary/protocol_writer.py`: grava as 3 linhas numa transação, com `flush` entre o protocolo e as filhas.
5. `application/protocol_confirmation.py`: confere o token, confere o dono contra a sessão, reaplica as regras da proposta e
   chama o domínio e o writer.
6. `presentation/http/protocol_confirmation.py`: `POST /protocols/proposals/confirm`, com as respostas da §6.4 do spec-mãe.
   `bootstrap/protocol_providers.py` monta só o necessário.

## Testes

Integração com app de teste, desfazendo a escrita ao final: confirmação grava 3 linhas e o protocolo aparece em
`list_protocols` do aluno; token de outro aluno, alterado ou expirado devolve `404` igual; segunda confirmação devolve `409`;
serviço com taxa devolve `422`; nenhuma tabela além das 3 recebe escrita.

## Pronto quando

`make check` verde; o teste da role de T2 continua passando com a escrita como `api`.

## Oráculo

No banco, as 3 linhas novas com o número da sequência e o SLA correto; no log, a confirmação com `trace_id` e sem dado pessoal.
