---
type: Research
title: Ontologia e evidências no NVIDIA Auto Ontology
description: Como o Auto Ontology modela termos e devolve a procedência das respostas, e quais ideias podem servir de referência para o agente de atendimento.
tags: [pesquisa, ontologia, glossario, evidencias, proveniencia, referencia]
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T02:09:38Z }
sources:
  - id: ao-readme
    resource: https://github.com/NVIDIA/auto-ontology/blob/2a24f5d34ef6b6e168a7f22d308504d3ab36a198/README.md
    title: Auto Ontology, README
  - id: ao-schema
    resource: https://github.com/NVIDIA/auto-ontology/blob/2a24f5d34ef6b6e168a7f22d308504d3ab36a198/auto_ontology/dal/schema.py
    title: Auto Ontology, tabelas de termos e atributos
  - id: ao-extractor
    resource: https://github.com/NVIDIA/auto-ontology/blob/2a24f5d34ef6b6e168a7f22d308504d3ab36a198/auto_ontology/semantic/term_extractor.py
    title: Auto Ontology, extração de termos e sinônimos
  - id: ao-terms
    resource: https://github.com/NVIDIA/auto-ontology/blob/2a24f5d34ef6b6e168a7f22d308504d3ab36a198/auto_ontology/dal/terms.py
    title: Auto Ontology, certificação agregada do termo
  - id: ao-glossary
    resource: https://github.com/NVIDIA/auto-ontology/blob/2a24f5d34ef6b6e168a7f22d308504d3ab36a198/auto_ontology/retrieval/entity_coverage/prompts.py
    title: Auto Ontology, glossário no prompt de extração
  - id: ao-coverage
    resource: https://github.com/NVIDIA/auto-ontology/blob/2a24f5d34ef6b6e168a7f22d308504d3ab36a198/auto_ontology/retrieval/entity_coverage/agents/coverage.py
    title: Auto Ontology, nota de cobertura
  - id: ao-tools
    resource: https://github.com/NVIDIA/auto-ontology/blob/2a24f5d34ef6b6e168a7f22d308504d3ab36a198/mcp/auto_ontology_mcp/tools.py
    title: Auto Ontology, tools publicadas e suas descrições
  - id: ao-conversation
    resource: https://github.com/NVIDIA/auto-ontology/blob/2a24f5d34ef6b6e168a7f22d308504d3ab36a198/docs/conversation-api.md
    title: Auto Ontology, API de conversa
  - id: ao-mcp-chat
    resource: https://github.com/NVIDIA/auto-ontology/blob/2a24f5d34ef6b6e168a7f22d308504d3ab36a198/mcp/auto_ontology_mcp/chat.py
    title: Auto Ontology, formato da resposta no MCP
  - id: ao-links
    resource: https://github.com/NVIDIA/auto-ontology/blob/2a24f5d34ef6b6e168a7f22d308504d3ab36a198/auto_ontology/retrieval/data_access/response_formatting.py
    title: Auto Ontology, links na resposta
  - id: ao-validation
    resource: https://github.com/NVIDIA/auto-ontology/blob/2a24f5d34ef6b6e168a7f22d308504d3ab36a198/skills/nvidia-ontology-query/references/query-validation.md
    title: Auto Ontology, validação de resposta
  - id: case
    resource: /README.md
    title: Enunciado do case
  - id: arch
    resource: /docs/architecture.md
    title: Arquitetura do agente (rascunho)
---

# Ontologia e evidências no NVIDIA Auto Ontology

> **Este documento é uma referência, não uma decisão.** Registra como um projeto resolveu dois problemas e o que
> pode nos servir. Nada aqui foi aprovado, nada obriga a arquitetura e o projeto citado não é fonte de verdade.
> As seções 3 e 4 são hipóteses nossas, com trechos ilustrativos e nomes hipotéticos, que não foram testados.
>
> **Escopo:** somente ontologia e evidências, lidas no commit `2a24f5d` em 2026-11-05. O Auto Ontology não será
> adotado como sistema: ele traduz linguagem natural em SQL sobre um banco inteiro, e o nosso problema central é
> isolar os dados por aluno.[^arch]

## Para o humano

- **Ontologia, no caso deles, é simples:** glossário de termos, ligação de cada termo às colunas, definições de
  cálculo e relações entre tabelas. Não há RDF nem OWL, e o extrator é instruído a não propor relações `IS_A`,
  `PART_OF` ou `ROLE`.[^ao-extractor]
- **A diferença que mais importa:** o termo deles aponta para **colunas**, porque o agente escreve SQL. O nosso
  apontaria para **tools**, porque o agente só chama serviços.
- **Evidência, no caso deles:** a resposta traz o SQL, as linhas e o passo a passo. Serve a um analista, mas não
  pode ser mostrada assim a um aluno.
- **Ideia central para nós:** uma só declaração do termo pode alimentar descrição de tool, skill, eval e citação na
  UI.

## 1. Como eles modelam a ontologia

```text
Tabela ──representa──▶ Termo ◀──propriedade de── Atributo SQL (cálculo revisado)
                         ▲
                         └──propriedade de── Atributo de coluna ──▶ coluna física

Coluna ──FK semântica──▶ Atributo de coluna   (relação usada para descobrir joins)
```

| Elemento | O que guarda | Para que serve |
|---|---|---|
| **Termo** | Nome, descrição, sinônimos e certificação de nome e de descrição[^ao-schema] | Conceito de negócio, como *Customer*[^ao-readme] |
| **Atributo de coluna** | Nome amigável, descrição, tipo e coluna de origem[^ao-schema] | Ligar o conceito ao dado físico |
| **Atributo SQL** | Expressão, descrição e certificação[^ao-schema] | Calcular cada medida sempre do mesmo jeito[^ao-readme] |
| **Relação** | Como as tabelas se ligam, inclusive por tabelas-ponte[^ao-readme] | Dar ao agente os joins |

**Ciclo de vida:** um LLM gera o rascunho a partir dos metadados, pessoas testam e certificam, e o agente responde a
partir do resultado.[^ao-readme]

**Sinônimos e glossário:** são dois mecanismos.

- O termo guarda sinônimos, como abreviações, siglas e nomes alternativos.[^ao-extractor]
- Um glossário curado pela organização entra no prompt e reescreve a expressão antes da busca: `MRR` vira
  `monthly recurring revenue`, sem aumentar o número de entidades extraídas.[^ao-glossary]

**Orientação do agente:**

- As descrições das tools são escritas como prompts. `search_terms` diz para ser usada primeiro, para aprender o que
  uma palavra de negócio significa naquela instalação.[^ao-tools]
- A lista de tools é fechada, e nenhuma navega por tabelas cruas.[^ao-tools]
- `check_answerable` mede quantas entidades da pergunta têm correspondência: cobertos ÷ extraídos.[^ao-coverage] A
  extração usa LLM, e a correspondência, busca vetorial. Isso permite responder que tem receita, mas não gasto com
  anúncios.[^ao-readme]

**Certificação:** é uma marcação humana.[^ao-schema] O estado do termo é derivado das partes: `certified`, `partial` ou
`pending`.[^ao-terms] O README promete validar queries contra definições certificadas,[^ao-readme] mas não encontrei
referência a `certified` em `auto_ontology/retrieval/`, onde o SQL é gerado. Neste commit, ela parece informar pessoas,
não mudar o comportamento do agente.

**Termo ambíguo:** o campo `source` do termo indica a origem da **definição** (por exemplo, `manual` ou `sql` no atributo
SQL),[^ao-schema] não o sistema de onde vem o dado. "Fonte oficial por tema" seria uma ideia nossa, não algo copiado
deles.

## 2. Como eles devolvem evidências

| Mecanismo | O que entrega |
|---|---|
| **Resposta estruturada** | Texto, SQL, linhas e passo a passo em campos separados[^ao-conversation] |
| **Limite explícito** | `row_count` e `truncated`, com no máximo 100 linhas no MCP[^ao-mcp-chat] |
| **Progresso** | Eventos de início e fim de cada etapa, com o SQL validado antes de rodar[^ao-conversation] |
| **Links no texto** | O LLM escreve `[[[nome/id]]]`; o servidor resolve o id contra o que foi recuperado ou contra o catálogo; sem correspondência, sobra só o nome, sem link[^ao-links] |
| **Recibo** | Pergunta, identidade da ontologia e da fonte, SQL, linhas, truncamento, resposta, tentativas e lacunas[^ao-validation] |

Regras do guia de validação deles que valem como referência:[^ao-validation]

- SQL executado com sucesso não prova que a pergunta foi respondida; SQL, linhas e texto são checados separadamente.
- Vazio ou nulo não significa zero automaticamente.
- Resultado truncado não prova lista, ranking ou total completos.
- Valor observado, calculado, previsto e recomendado são estados diferentes de evidência.
- Sem evidência suficiente, a resposta falha de forma explícita, em vez de escolher a linha mais recente disponível.

**Limite para o nosso caso:** a citação deles chega à tabela e à coluna do catálogo,[^ao-links] e o SQL vai junto na
resposta. Nosso enunciado proíbe vazar dados corporativos.[^case]

## 3. Ideia: um termo com vários consumidores

```python
# Ilustrativo: não foi testado nem aprovado
Term(
    key="divida",
    label="Dívida",
    synonyms=("débito", "em aberto", "devendo"),
    definition="Exclui OPEN e RENEGOTIATED; só pagamento CONFIRMED conta.",  # A16 da arquitetura
    source=System.FINANCE,  # fonte oficial do tema
    answered_by=("get_debts",),  # liga o termo às tools
)
```

| Consumidor | O que usaria do termo | Possível verificação |
|---|---|---|
| **Pessoas do projeto** | `label` e `definition`, como vocabulário comum | Revisão humana registrada em `verified` do OKF |
| **Escolha de tool** | `answered_by` | No eval, a trajetória chamou a tool esperada |
| **Sinônimos** | `synonyms`, para "Administração" e `Course_Label` (A17)[^arch] | Pergunta com sinônimo chega ao mesmo termo |
| **Descrição da tool** | `definition` e `synonyms`, gerando o texto em vez de duplicá-lo | Snapshot das descrições |
| **Skills** | Definições carregadas sob demanda | O eval mede o conjunto (B19)[^arch] |
| **Eval** | Casos por termo, sinônimo e armadilha da definição | SQL independente como gabarito[^arch] |
| **Recusa** | Termo desconhecido vai para `uncovered` | Conjunto de perguntas fora de escopo |

**Pontos em que a nossa versão seria diferente da deles:**

- **Curadoria manual:** temos poucos termos e já conhecemos os dados, então um LLM gerando o rascunho agrega pouco.
- **Sem colunas:** o termo não precisa conhecer tabelas, o que mantém essa informação fora do contexto do modelo.
- **Sinônimos antes de vetores:** vale testar a resolução simples antes de decidir sobre RAG, que segue em aberto.[^arch]

## 4. Ideia: evidência para citar na UI

Cada resultado de tool traria uma evidência montada pelo **servidor**, nunca declarada pelo modelo. O modelo só
referencia o id, e o servidor resolve o id, como nos links deles.

```python
# Ilustrativo: não foi testado nem aprovado
class Evidence(BaseModel):
    id: str  # gerado pelo servidor, ex.: "ev_1"
    source: System  # exibido como "Financeiro", nunca "finance.invoice"
    label: str  # "Faturas vencidas"
    term: str | None  # definição usada, para a UI poder explicá-la
    as_of: date  # data de referência, vinda do relógio injetado
    row_count: int
    truncated: bool
    coverage_note: str | None  # "sem dados do LMS antes de 2023"
```

```text
Você tem R$ 1.240,00 em débito [1].

[1] Financeiro · Faturas vencidas (2) · posição em 31/10/2026
    O que conta como dívida: exclui faturas em aberto e renegociadas.
```

Possíveis usos, além da UI:

- **Eval:** citação com id inexistente ou número sem evidência correspondente vira falha mensurável, em vez de só cair
  para texto sem link, como acontece com eles.[^ao-links]
- **Auditoria:** o recibo pode ficar no schema `agent`, previsto para conversas, logs e auditoria (B14).[^arch]
- **Coerência entre termo e dado:** um teste pode comparar a fonte declarada no termo com a fonte da evidência.

## 5. Cuidados se isso for aplicado

- **Nada interno na tela do aluno:** sem SQL, nome de tabela, coluna ou analista.[^case]
- **Ontologia não é controle de acesso:** ela orienta o modelo; o isolamento continua no repositório (B7).[^arch]
- **Citação não prova correção:** ela mostra de onde veio o dado, não que o modelo o interpretou bem. A correção segue
  medida por eval.
- **Sinônimo errado pode levar à tool errada:** cada sinônimo precisa de caso no eval.
- **O prompt pode vazar:** o glossário não pode conter segredo ou regra interna sensível.[^arch]

## 6. Perguntas em aberto

1. O glossário fica em código Python, para ser ligado às tools por teste, ou em arquivos OKF, para leitura humana?
2. A citação chega ao tipo de registro ("Faturas vencidas") ou ao registro específico ("Fatura 123")?
3. O que conta como "certificado" para nós: revisão humana, teste contra SQL independente ou os dois?
4. A UI mostra a definição do termo sempre ou só quando o aluno pede?

[^ao-readme]: Auto Ontology, README: seções "How it works" e "Quickstart".
[^ao-schema]: Auto Ontology, `dal/schema.py`: tabelas `term`, `column_attribute`, `sql_attribute` e `column__semantic_fk`.
[^ao-extractor]: Auto Ontology, `semantic/term_extractor.py`: prompt `_SYSTEM`, regra 4, e `_SynonymExtractionModel`.
[^ao-terms]: Auto Ontology, `dal/terms.py`: certificação agregada do termo.
[^ao-glossary]: Auto Ontology, `retrieval/entity_coverage/prompts.py`: "Glossary rule".
[^ao-coverage]: Auto Ontology, `retrieval/entity_coverage/agents/coverage.py`: `_compute_coverage`.
[^ao-tools]: Auto Ontology, `mcp/auto_ontology_mcp/tools.py`: `CURATED` e `route_maps`.
[^ao-conversation]: Auto Ontology, `docs/conversation-api.md`: "Response stream".
[^ao-mcp-chat]: Auto Ontology, `mcp/auto_ontology_mcp/chat.py`: `DataAnswer`.
[^ao-links]: Auto Ontology, `retrieval/data_access/response_formatting.py`: `_highlight_entity` e `_prepare_link`.
[^ao-validation]: Auto Ontology, `skills/nvidia-ontology-query/references/query-validation.md`.
[^case]: Enunciado do case, seção 1, requisito "Seguro".
[^arch]: Arquitetura do agente: B7, B14, B19, A16, A17, seção 5.9, seção 7 e seção 9.
