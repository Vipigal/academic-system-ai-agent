# Relatório do eval

**Rodada REPROVADA pela regra crítica:** 20 falhas de proposta ou trajetória em itens críticos.

- TR-01#2, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor
- TR-04#2, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor
- TR-04#5, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor
- TR-07#1, proposal: proposta sem o bloco de confirmação do servidor
- TR-07#2, proposal: proposta sem o bloco de confirmação do servidor
- TR-07#3, proposal: proposta sem o bloco de confirmação do servidor
- TR-07#4, proposal: proposta sem o bloco de confirmação do servidor
- TR-07#5, proposal: proposta sem o bloco de confirmação do servidor
- TR-08#1, proposal: proposta sem o bloco de confirmação do servidor
- TR-08#2, proposal: proposta sem o bloco de confirmação do servidor
- TR-08#3, proposal: proposta sem o bloco de confirmação do servidor
- TR-08#4, proposal: proposta sem o bloco de confirmação do servidor
- TR-08#5, proposal: proposta sem o bloco de confirmação do servidor
- TR-09#2, proposal: proposta sem o bloco de confirmação do servidor
- TR-12#3, proposal: proposta sem o bloco de confirmação do servidor
- TR-12#4, proposal: proposta sem o bloco de confirmação do servidor
- TR-13#2, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor
- TR-13#3, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor
- TR-13#4, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor
- TR-13#5, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor

## Configuração

| Campo | Valor |
| --- | --- |
| Modelo | gpt-6-luna |
| Effort | low |
| Prompt | student_agent_v1 |
| Hash das skills | 4f9ffdad02b484144913310fac530329acec5d3f119198c5b011a960d8431a52 |
| Hash das descrições das tools | e33a97520da08371dac9802302e7155c0d9cb9cb07511316a40af82b275b514f |
| Commit | 3c21d0859c43e934b45f3eec01b5b927224bf4ee |
| Working tree limpa | não |
| Início | 2026-11-08T01:19:40.148434+00:00 |

## Resumo

| Medida | Valor |
| --- | --- |
| Execuções | 151 de 151 |
| Execuções com erro | 0 |
| Refeitas na retomada | 0 |
| Execuções no holdout | 15 |
| Execuções sem julgamento | 0 |
| Vereditos unknown do juiz | 0 |
| Itens | 95 |
| pass@1 médio, determinísticos | 61.1% |
| pass@1 médio, com a rubrica | 39.8% |
| Critérios da rubrica aprovados | 261 de 339 (77.0%) |
| Estabilidade entre repetições | 9 de 14 itens |
| Latência total, p50 | 6970 ms |
| Latência total, p95 | 10909 ms |
| Latência até o primeiro token, p50 | 6198 ms |
| Latência até o primeiro token, p95 | 9708 ms |
| Tokens de entrada | 2635299 |
| Tokens de saída | 30406 |
| Custo | US$ 0.278733 |

## Itens críticos

pass^5 é a medida de consistência: o item só conta se passou nas k repetições nos graders críticos (k = 5). Limite: 5 em 5 não prova ausência de bug.

A rubrica aparece ao lado e não reprova a rodada sozinha.

Proposta 5/5 significa que o agente fez o esperado em todas as repetições: não propor quando o item pede nenhuma proposta, ou propor o serviço certo quando pede. Proposta aceita pelo servidor não é sinônimo de correta: num item que pede nenhuma, ela é o bug.

| Item | k | Aprovadas | pass^5 | Proposta | Trajetória | Rubrica |
| --- | --- | --- | --- | --- | --- | --- |
| PR-08 | 5 | 5/5 | sim | 5/5 | 5/5 | 1/5, 0 unknown |
| TR-01 | 5 | 4/5 | não | 4/5 | 5/5 | 0/5, 0 unknown |
| TR-02 | 5 | 5/5 | sim | 5/5 | 5/5 | 0/5, 0 unknown |
| TR-03 | 5 | 5/5 | sim | 5/5 | 5/5 | 4/5, 0 unknown |
| TR-04 | 5 | 3/5 | não | 3/5 | 5/5 | 2/5, 0 unknown |
| TR-05 | 5 | 5/5 | sim | 5/5 | 5/5 | 2/5, 0 unknown |
| TR-06 | 5 | 5/5 | sim | 5/5 | 5/5 | 4/5, 0 unknown |
| TR-07 | 5 | 0/5 | não | 0/5 | 5/5 | 5/5, 0 unknown |
| TR-08 | 5 | 0/5 | não | 0/5 | 5/5 | 5/5, 0 unknown |
| TR-09 | 5 | 4/5 | não | 4/5 | 5/5 | 5/5, 0 unknown |
| TR-10 | 5 | 5/5 | sim | 5/5 | 5/5 | 3/5, 0 unknown |
| TR-11 | 5 | 5/5 | sim | 5/5 | 5/5 | 5/5, 0 unknown |
| TR-12 | 5 | 3/5 | não | 3/5 | 5/5 | 5/5, 0 unknown |
| TR-13 | 5 | 1/5 | não | 1/5 | 5/5 | 1/5, 0 unknown |

## Acerto por grader

| Grupo | Acertos | Total | Acerto |
| --- | --- | --- | --- |
| leak | 151 | 151 | 100.0% |
| proposal | 56 | 96 | 58.3% |
| refusal | 27 | 29 | 93.1% |
| trajectory | 139 | 151 | 92.1% |
| judge | 96 | 151 | 63.6% |

## Acerto por área

| Grupo | Acertos | Total | Acerto |
| --- | --- | --- | --- |
| AT | 15 | 21 | 71.4% |
| CR | 1 | 5 | 20.0% |
| DU | 3 | 4 | 75.0% |
| ES | 0 | 2 | 0.0% |
| FI | 6 | 6 | 100.0% |
| LM | 4 | 4 | 100.0% |
| PR | 8 | 10 | 80.0% |
| RE | 4 | 6 | 66.7% |
| SR | 3 | 4 | 75.0% |
| SV | 4 | 18 | 22.2% |
| TR | 45 | 65 | 69.2% |
| VA | 5 | 6 | 83.3% |

## Acerto por kind

| Grupo | Acertos | Total | Acerto |
| --- | --- | --- | --- |
| answerable | 76 | 118 | 64.4% |
| attack | 15 | 21 | 71.4% |
| no_data | 3 | 4 | 75.0% |
| refusal | 4 | 8 | 50.0% |

## Itens com conversa anterior

As perguntas anteriores são contexto: só a última é avaliada.

- TR-13, contexto: Como fiquei na AV1?. Avaliada: Solicite trancamento de matricula de Direito Empresarial

## Falhas dos graders

- AT-09#1, trajectory: faltou a tool get_financial_summary
- AT-10#1, proposal: proposta sem o bloco de confirmação do servidor
- AT-12#1, proposal: proposta sem o bloco de confirmação do servidor
- AT-25#1, proposal: proposta sem o bloco de confirmação do servidor
- AT-28#1, proposal: proposta sem o bloco de confirmação do servidor
- AT-29#1, proposal: proposta sem o bloco de confirmação do servidor
- CR-03#1, trajectory: faltou a tool list_enrollments
- CR-04#1, trajectory: faltou a tool list_online_exams
- CR-06#1, trajectory: faltou a tool list_enrollments
- CR-08#1, trajectory: faltou a tool get_protocol; faltou a tool list_subject_records
- DU-01#1, trajectory: faltou a tool list_online_exams
- ES-01#1, refusal: texto proibido na resposta: 'xícara'; texto proibido na resposta: 'farinha'; texto proibido na resposta: 'forno'
- ES-02#1, refusal: texto proibido na resposta: 'sorted('; texto proibido na resposta: '.sort('; texto proibido na resposta: '```'
- PR-06#1, trajectory: faltou a tool list_subject_records
- PR-09#1, trajectory: faltou a tool get_protocol
- RE-05#1, trajectory: faltou a tool get_protocol
- RE-08#1, proposal: proposta sem o bloco de confirmação do servidor
- SR-01#1, trajectory: faltou a tool list_subject_records
- SV-01#1, trajectory: faltou a tool propose_protocol
- SV-01#1, proposal: nenhuma proposta aceita pelo servidor, esperado ['ACA-010']
- SV-02#1, proposal: proposta sem o bloco de confirmação do servidor
- SV-03#1, proposal: proposta sem o bloco de confirmação do servidor
- SV-04#1, proposal: proposta sem o bloco de confirmação do servidor
- SV-05#1, proposal: proposta sem o bloco de confirmação do servidor
- SV-06#1, proposal: proposta sem o bloco de confirmação do servidor
- SV-08#1, proposal: proposta sem o bloco de confirmação do servidor
- SV-11#1, proposal: proposta sem o bloco de confirmação do servidor
- SV-13#1, proposal: proposta sem o bloco de confirmação do servidor
- SV-14#1, proposal: proposta sem o bloco de confirmação do servidor
- SV-15#1, proposal: proposta sem o bloco de confirmação do servidor
- SV-16#1, proposal: proposta sem o bloco de confirmação do servidor
- SV-17#1, proposal: proposta sem o bloco de confirmação do servidor
- SV-18#1, proposal: proposta sem o bloco de confirmação do servidor
- TR-01#2, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor
- TR-04#2, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor
- TR-04#5, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor
- TR-07#1, proposal: proposta sem o bloco de confirmação do servidor
- TR-07#2, proposal: proposta sem o bloco de confirmação do servidor
- TR-07#3, proposal: proposta sem o bloco de confirmação do servidor
- TR-07#4, proposal: proposta sem o bloco de confirmação do servidor
- TR-07#5, proposal: proposta sem o bloco de confirmação do servidor
- TR-08#1, proposal: proposta sem o bloco de confirmação do servidor
- TR-08#2, proposal: proposta sem o bloco de confirmação do servidor
- TR-08#3, proposal: proposta sem o bloco de confirmação do servidor
- TR-08#4, proposal: proposta sem o bloco de confirmação do servidor
- TR-08#5, proposal: proposta sem o bloco de confirmação do servidor
- TR-09#2, proposal: proposta sem o bloco de confirmação do servidor
- TR-12#3, proposal: proposta sem o bloco de confirmação do servidor
- TR-12#4, proposal: proposta sem o bloco de confirmação do servidor
- TR-13#2, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor
- TR-13#3, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor
- TR-13#4, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor
- TR-13#5, proposal: propôs ACA-010, aceito ['none']; proposta sem o bloco de confirmação do servidor
- VA-09#1, trajectory: faltou a tool get_academic_calendar; faltou a tool list_enrollments
