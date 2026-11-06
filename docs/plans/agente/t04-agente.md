---
type: Plan
title: T4 · Agente e skills
description: Tarefa da fase do agente que converte as tools para o LangChain, cria as 7 skills e a tool load_skill, e monta o agente com prompt, middlewares e modelo.
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:45:00Z }
---

# T4 · Agente e skills

> Spec-mãe: [Agente, eval e fluxo ponta a ponta](/docs/plans/agente/index.md). Onda 1, depende de T1. Modelo sugerido: Opus.

## Objetivo

Um `StudentAgent` que recebe as tools de um aluno e responde, testável sem rede (spec-mãe, §6.7).

## O que fazer

1. **Conversor** (`application/agent/langchain_tools.py`): de `RegisteredTool` para `StructuredTool`.
   - O `args_schema` é calculado uma vez por método, a partir da assinatura, e guardado num cache de módulo indexado pela
     função, nunca pelo método ligado.
   - Por request, cada tool é uma closure que chama o handler do aluno e devolve o `ToolResult` em JSON.
   - Nome e descrição vêm de `ToolDefinition`.
2. **Skills:** `application/agent/skills/<area>/SKILL.md` para as 7 áreas de `Area`, com `name` e `description` no
   frontmatter e o corpo com instruções da área. `SkillLibrary` lê os arquivos uma vez. `load_skill(area)` é uma tool em
   `application/agent/tools/skill_tools.py`, com docstring e `area` tipado pelo enum, e devolve o corpo mais
   `OntologyRenderer.for_skill(area)`. Ela passa pelas mesmas regras do `ToolRegistry`; o parâmetro `area` já está na lista
   permitida.
3. **Prompt** versionado em arquivo, com um id de versão usado pelo eval.
4. **Agente** (`application/agent/student_agent.py`): `create_agent` com o modelo injetado, as tools do aluno, `load_skill`,
   o prompt e os middlewares de limite de chamadas ao modelo e às tools e retry do modelo. Expõe execução completa e em stream, com eventos próprios da application (texto, chamada de tool, resultado de
   tool, fim), para que nem presentation nem eval conheçam tipos do LangChain.
5. **Modelo:** `bootstrap/agent_providers.py` cria o `ChatOpenAI` com `use_responses_api=True`, modelo e effort de settings,
   ou o modelo `fake`, um modelo de roteiro do LangChain para testes e carga.
6. **Concorrência:** limite de chamadas simultâneas ao provedor e timeout por execução, de settings.
7. **Erro ensino (D22 do spec-mãe):**
   - `ToolStatus` ganha `invalid` e `error`, e `ToolResult` ganha `explanation`.
   - O conversor trata o erro de validação do schema e devolve `invalid` com uma frase por parâmetro errado: o que veio, o
     que é aceito e um exemplo válido. Os valores aceitos saem do próprio tipo (membros do enum, faixa de `limit`, formato de
     `period`), para o texto não desatualizar.
   - Exceções esperadas das tools (período mal formado, matrícula que não é do aluno no formato `marca:RA`) são tipadas e
     carregam o parágrafo; o conversor as devolve como `invalid`.
   - Qualquer outra exceção vira `error` genérico, registrada no log com `trace_id`. A execução do agente continua.
   - Os testes de schema visível ao modelo não mudam: só o envelope de saída ganha os campos.

## Testes

- Unitário com modelo fake: o modelo pede uma tool, a closure chama o handler certo, o resultado volta como JSON, a resposta
  final sai.
- Erro ensino, para cada uma das 20 tools: chamada com cada parâmetro errado (tipo, enum, faixa, formato) devolve `invalid`
  com parágrafo em português que cita o parâmetro e um valor aceito; o modelo fake corrige na chamada seguinte e a resposta
  final sai.
- Exceção inesperada num handler vira `error` genérico, sem detalhe interno, e o turno termina com resposta.
- `load_skill` devolve corpo e ontologias, sem `evidence` nem `data`.
- **Dependência cativa (invariante 11):** dois alunos seguidos no mesmo processo recebem tools ligadas aos próprios services;
  o cache só guarda schemas.
- `live`: FI-01 com `gpt-6-luna` chama `get_financial_summary` e responde R$ 277,05.

## Pronto quando

`make check` verde; o teste `live` passa com `--live`; o tempo de montar o agente por request é medido e registrado.

## Oráculo

O teste `live` e o seu trace: uma chamada ao modelo com tool call, a tool executada, a resposta final em português.
