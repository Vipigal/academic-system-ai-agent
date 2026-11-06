---
type: Plan
title: T13 · Evidências e README
description: Tarefa da fase do agente que roda a matriz de modelos, o red team e o teste de carga, e escreve as evidências e as instruções que o enunciado pede.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
---

# T13 · Evidências e README

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Onda 4, depende de T10 e T11. Modelo sugerido:
> Opus para a análise; as execuções são mecânicas.

## Objetivo

Os entregáveis 1 e 3 do enunciado: instruções para rodar, exemplos de conversa, testes de segurança, latência e avaliação de
qualidade.

## O que fazer

1. **Qualidade:** primeiro ciclo com `gpt-6-luna` no dev, iteração de prompt e skills guiada pelas falhas, depois a matriz
   (D12) e o holdout só na configuração escolhida. Cada mudança de prompt ou skill ganha versão e entrada no Registro.
2. **Segurança:** red team na configuração escolhida, com o resultado de cada ataque, mais o resumo dos invariantes de
   arquitetura que já garantem isolamento sem depender do modelo.
3. **Latência:** p50 e p95 fim a fim e até o primeiro token, separados em tempo de modelo e de tools pelos traces.
4. **Carga:** `loadtest/` com Locust e modelo fake (P6): alunos simultâneos, p95 da API e erros, mostrando o custo da carga da
   sessão por request.
5. **Conversas:** pelo menos 5 exemplos reais, incluindo cruzamento de sistemas, recusa e abertura de protocolo.
6. **Documento:** `docs/evidencias.md` (documento novo; propor tipo, título e caminho ao dono antes, pelo guia de autoria) e
   a seção de como rodar no `README.md`.

## Pronto quando

O dono revisou o documento de evidências e o `README` com as instruções de rodar do zero.

## Oráculo

Alguém que clona o repo segue o `README` e chega ao chat funcionando; os números do documento batem com os relatórios
gerados em `src/evals/` e com os traces.
