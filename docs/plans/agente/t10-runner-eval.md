---
type: Plan
title: T10 · Runner de eval
description: Tarefa da fase do agente que executa o golden set e o red team contra um modelo, aplica os graders e o juiz, e gera o relatório com qualidade, latência e custo.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
---

# T10 · Runner de eval

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Onda 2, depende de T3, T4 e T7. Modelo sugerido:
> Opus.

## Objetivo

Comparar modelos e versões de prompt e skills com números (spec-mãe, §6.6).

## O que fazer

1. `src/evals/runner.py`: para cada item, carrega a sessão do aluno, monta o agente como o bootstrap monta e executa a
   pergunta. Concorrência limitada e repetições configuráveis. Sem HTTP.
2. `src/evals/graders/`: trajetória (D23), fatos com normalização pt-BR, recusa e vazamento.
3. `src/evals/judge/` (D19 do spec-mãe): port do juiz com duas implementações. A principal grava os pedidos em JSONL, sem o
   nome do modelo avaliado, e chama `claude -p` com o agente `.claude/agents/eval-judge.md`, sem ferramentas, em lotes, com
   saída JSON validada por esquema. A reserva manda o mesmo pedido a `gpt-6.1-terra`. O juiz recebe pergunta, resposta,
   referência e rubrica, raciocina antes do veredito e devolve aprovação por item.
4. Registro de cada execução: modelo, effort, versão do prompt, hash das skills e das descrições das tools, trajetória,
   latência total e até o primeiro token, tokens e custo pela tabela de preços em configuração.
5. `src/evals/report.py`: JSONL e Markdown com acerto por grader, área e `kind`; pass@1 médio; estabilidade entre repetições;
   p50 e p95 de latência; custo. O holdout só roda com uma opção explícita.
6. CLI: `python -m evals.run --model <modelo> --effort <effort> --split dev --repeat 3`, e uma opção para o red team.
7. Traces no Langfuse com a tag `eval` e as versões.

## Testes

Unitário: cada grader com respostas boas e ruins escritas à mão, incluindo números em formatos diferentes e um vazamento;
o runner com modelo fake gera um relatório completo.

## Pronto quando

`make check` verde; uma rodada `live` com `gpt-6-luna` em 5 perguntas do dev gera relatório e traces; os 15 primeiros
vereditos do juiz são conferidos à mão e a concordância vai para o Registro.

## Oráculo

O relatório da rodada `live` e os traces com a tag `eval` no Langfuse.
