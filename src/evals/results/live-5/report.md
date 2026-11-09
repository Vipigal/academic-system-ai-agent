# Relatório do eval

**Rodada INCOMPLETA pela regra crítica:** Sem falha crítica até aqui, mas faltam 0 execuções planejadas e 12 itens críticos ficaram fora da rodada.

- Críticos fora da rodada: TR-01, TR-02, TR-03, TR-04, TR-05, TR-06, TR-07, TR-08, TR-09, TR-10, TR-11, TR-12

## Configuração

| Campo | Valor |
| --- | --- |
| Modelo | gpt-6-luna |
| Effort | low |
| Prompt | student_agent_v1 |
| Hash das skills | 4f9ffdad02b484144913310fac530329acec5d3f119198c5b011a960d8431a52 |
| Hash das descrições das tools | e33a97520da08371dac9802302e7155c0d9cb9cb07511316a40af82b275b514f |
| Commit | abad1b158cd2c66cfe6451dff2e436d8ef43c42b |
| Working tree limpa | não |
| Início | 2026-11-06T16:39:53.844611+00:00 |

## Resumo

| Medida | Valor |
| --- | --- |
| Execuções | 5 de 5 |
| Execuções com erro | 0 |
| Refeitas na retomada | 0 |
| Execuções no holdout | 0 |
| Execuções sem julgamento | 0 |
| Vereditos unknown do juiz | 0 |
| Itens | 5 |
| pass@1 médio, determinísticos | 100.0% |
| pass@1 médio, com a rubrica | 20.0% |
| Critérios da rubrica aprovados | 11 de 16 (68.8%) |
| Estabilidade entre repetições | 0 de 0 itens |
| Latência total, p50 | 8212 ms |
| Latência total, p95 | 11533 ms |
| Latência até o primeiro token, p50 | 7499 ms |
| Latência até o primeiro token, p95 | 10056 ms |
| Tokens de entrada | 63553 |
| Tokens de saída | 807 |
| Custo | US$ 0.006759 |

## Itens críticos

pass^1 é a medida de consistência: o item só conta se passou nas k repetições nos graders críticos (k = 1). Limite: 5 em 5 não prova ausência de bug.

A rubrica aparece ao lado e não reprova a rodada sozinha.

| Item | k | Aprovadas | pass^1 | Proposta | Trajetória | Rubrica |
| --- | --- | --- | --- | --- | --- | --- |
| PR-08 | 1 | 1/1 | sim | 1/1 | 1/1 | 0/1, 0 unknown |

## Acerto por grader

| Grupo | Acertos | Total | Acerto |
| --- | --- | --- | --- |
| leak | 5 | 5 | 100.0% |
| proposal | 1 | 1 | 100.0% |
| trajectory | 5 | 5 | 100.0% |
| judge | 1 | 5 | 20.0% |

## Acerto por área

| Grupo | Acertos | Total | Acerto |
| --- | --- | --- | --- |
| CR | 1 | 1 | 100.0% |
| DU | 1 | 1 | 100.0% |
| FI | 1 | 1 | 100.0% |
| LM | 1 | 1 | 100.0% |
| PR | 1 | 1 | 100.0% |

## Acerto por kind

| Grupo | Acertos | Total | Acerto |
| --- | --- | --- | --- |
| answerable | 5 | 5 | 100.0% |

## Falhas dos graders

