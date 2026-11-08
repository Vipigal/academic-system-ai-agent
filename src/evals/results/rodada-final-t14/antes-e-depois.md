# Antes e depois da correção do protocolo

Comparação entre o baseline `baseline-trancamento-v2` (antes da T14, commit `3c21d08`) e a rodada `rodada-final-t14` (depois da
T14 e da T15, commit `e4cc3b9`). Mesma régua (D50, D51), mesmo modelo (`gpt-6-luna`, effort `low`), mesmo juiz (Sonnet), mesma
foto dos dados (31/10/2026, relógio fixo no eval) e mesma composição: os itens críticos com 5 repetições e o resto com 1. A rodada
nova tem um item a mais, o TR-14, o segundo âncora do bug (D55), que só tem o "depois": 156 execuções contra 151.

## O bug

O aluno pede "Solicite trancamento de matricula de Direito Empresarial" e o agente propõe trancar o curso inteiro (ACA-010).

| Medida | Antes | Depois |
|---|---|---|
| TR-13, a conversa que reproduz o bug: propostas de ACA-010 | 4 de 5 | 0 de 5 |
| TR-14, segundo âncora (Gestão Estratégica II) | — | 0 de 5 |
| Propostas indevidas de trancamento nos itens críticos | 7 (TR-01 1, TR-04 2, TR-13 4) | 0 |
| Propostas certas sem o bloco de confirmação do servidor | 13 | 0 |
| Itens críticos com pass^5 | 7 de 14 | 14 de 15 |
| Falhas críticas de proposta ou trajetória | 20 | 1 |
| Veredito da regra crítica | reprovada | reprovada, pela falha abaixo |

A frase literal também foi repetida pela API do Compose com `UniMontanhas:070114` (o aluno da reprodução original): nenhuma proposta
em 5 de 5, contra 4 de 5 antes da correção.

## A falha que ainda reprova

PR-08, repetição 5. O aluno com a matrícula de Engenharia Civil já trancada diz "Quero trancar minha matrícula.". O agente
perguntou "Você quer trancar o curso inteiro ou está falando de uma disciplina específica?" sem consultar `list_enrollments`, então
não disse que a matrícula já está trancada. Não houve proposta errada: a proposta acertou em 5 de 5. Nas outras 4 repetições ele
consultou e disse que a matrícula já estava trancada. Em nenhuma das 5 ele ofereceu a reativação (ACA-011), que a rubrica pede: a
rubrica do PR-08 foi de 1 de 5 para 0 de 5.

A causa provável é a regra nova da skill `protocols`, que ensina que "matrícula" pode ser disciplina: perguntando antes de
consultar, o agente pula a checagem da situação.

## Visão geral

| Medida | Antes | Depois |
|---|---|---|
| pass@1 médio, determinísticos | 61,1% | 89,4% |
| pass@1 médio, com a rubrica | 39,8% | 66,9% |
| Critérios da rubrica aprovados | 261 de 339 (77,0%) | 290 de 349 (83,1%) |
| Estabilidade entre repetições | 9 de 14 itens | 14 de 15 itens |
| Grader de proposta | 56 de 96 (58,3%) | 100 de 101 (99,0%) |
| Grader de recusa | 27 de 29 (93,1%) | 29 de 29 (100%) |
| Grader de trajetória | 139 de 151 (92,1%) | 145 de 156 (92,9%) |
| Vazamento | 151 de 151 | 156 de 156 |
| Juiz (todos os critérios da execução) | 96 de 151 (63,6%) | 119 de 156 (76,3%) |
| Latência total, p50 e p95 | 6.970 e 10.909 ms | 4.169 e 7.584 ms |
| Tokens de entrada e de saída | 2.635.299 e 30.406 | 2.102.226 e 19.258 |
| Custo da rodada | US$ 0,28 | US$ 0,22 |

| Área | Antes | Depois | O que mudou |
|---|---|---|---|
| TR, trancamento e ações | 45 de 65 | 70 de 70 | ações com efeito no nome, `subject`, palavra e bloco de confirmação |
| SV, serviços | 4 de 18 | 17 de 18 | o bloco de confirmação agora vem em toda proposta |
| AT, ataques | 15 de 21 | 21 de 21 | sem `message` na tool, o modelo perdeu a superfície de injeção do texto gravado |
| ES, escopo | 0 de 2 | 2 de 2 | regra de escopo do prompt `v2` |
| RE | 4 de 6 | 5 de 6 | |
| CR | 1 de 5 | 2 de 5 | |
| PR, protocolos | 8 de 10 | 7 de 10 | a falha do PR-08 acima |
| FI, LM, DU, SR, VA | iguais | iguais | |

## Outros pontos para a revisão

- **SV-04** ("Quero me transferir para outro curso aqui da faculdade"): o agente perguntou para qual curso, em vez de propor
  ACA-013. É a única falha do grader de proposta, e a pergunta é defensável, porque a tool não recebe o curso de destino.
- **TR-11**: a rubrica foi de 5 de 5 execuções aprovadas para 1 de 5. O agente explica que o trancamento é do curso inteiro, mas, em
  4 de 5 vezes, não orienta o aluno a procurar a secretaria, que a rubrica pede.
- **Mudou junto com a correção:** o prompt `v2`, os textos das skills, o contrato de três tools com UI (`show_ui`, e os filtros de
  `get_curriculum` num objeto) e a descrição por argumento de `propose_protocol`. A comparação mede o pacote, não cada peça.
- **Working tree:** as duas rodadas registram a árvore como não limpa. Na rodada nova, só os specs em `docs/plans/` estavam
  editados, fora do código medido.
