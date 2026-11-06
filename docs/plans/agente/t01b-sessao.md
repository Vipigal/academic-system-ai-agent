---
type: Plan
title: T1b · Sessão só com identidades
description: Tarefa da fase do agente que reduz a StudentSession às identidades da pessoa e passa a resolver contratos, contas do AVA e protocolos por predicado do dialeto em cada consulta.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:59:00Z }
---

# T1b · Sessão só com identidades

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Arrumação, depois de T1. Modelo sugerido:
> Opus: é o núcleo do isolamento.

## Objetivo

A sessão guarda só quem a pessoa é; o que pertence a ela é resolvido na consulta (D16 do spec-mãe). Mesmo isolamento, menos
consultas por request, nada velho.

## Hoje

`StudentSession` tem 9 campos, e a carga roda 8 consultas por request: CPF, `person_ids`, matrículas, contratos, contratos
pagos pelo próprio aluno, contratos pagos por empresa, contas do AVA e protocolos. As regras de ownership de finance, lms e
secretary usam `IN (ids da sessão)`. Os dialetos já sabem montar o predicado a partir das matrículas:
`FinanceDialect.contract_of`, `LmsDialect.account_of` e `SecretaryDialect.protocol_of`.

## O que fazer

1. `StudentSession` com `person_ids`, `cpf` (`repr=False`) e `enrollment_keys`; `brands` vira propriedade derivada. A carga
   faz no máximo 3 consultas.
2. Cada sistema tem uma tabela-raiz com regra de ownership pelo predicado do dialeto:
   - finance: contrato, por `FinanceDialect.contract_of(matrículas)`;
   - lms: conta do usuário, por `LmsDialect.account_of(matrículas)`;
   - secretary: protocolo, por `SecretaryDialect.protocol_of(cpf, matrículas)`, mantendo a cascata e o *fail closed* (A7,
     B28, B30).
   As demais tabelas do sistema chegam à raiz por `Via` (B33). Tabela que hoje filtra direto por id da sessão passa a `Via`
   da raiz.
3. Tipo de pagador (próprio, empresa, terceiro): resolvido na consulta do resumo financeiro, por uma consulta privada da
   persistence sobre as tabelas de identidade, sem expor CPF do pagador. Só o `RepositoryAdapter` e a carga da sessão abrem
   sessão de banco; se a consulta privada precisar de um caminho novo no adapter, ele aceita só consultas declaradas e
   mantém o ownership da raiz.
4. A regra "toda tabela mapeada declara ownership" e o guard de consultas continuam valendo.

## Testes

Os testes de partição, de volumes e de invariantes são o oráculo e não mudam de asserção:

- 1.000 pessoas carregam sessão; nenhuma linha em duas pessoas.
- Protocolos: 3.882 resolvidos, 51 invisíveis, 11 de terceiros invisíveis.
- Tentativas do AVA: 18.566 de 18.857 visíveis.
- Faturas, pagamentos, disciplinas e contratos com as mesmas contagens.
- Agente comprometido recebe zero linhas alheias.
- FI-05 (pagador) com o mesmo resultado.

Novo: a carga da sessão faz no máximo 3 consultas, contado por um teste.

## Pronto quando

`make check` verde; tempo da carga da sessão e de uma consulta de faturas medido antes e depois, registrado no Registro
do spec-mãe. Se alguma consulta ficar mais lenta, T2 cria o índice de expressão correspondente.

## Oráculo

As mesmas contagens do teste de volumes contra o `SqlOracle`; `EXPLAIN` de uma consulta de faturas mostrando o predicado do
contrato aplicado uma vez.
