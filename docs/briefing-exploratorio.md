# Briefing exploratório: agente de atendimento ao aluno

Sessão de 04/11/2026. Serve de insumo para a sessão de arquitetura; não é a arquitetura final.

Legenda das evidências:
- **[EDA]**: medido nos CSVs nesta sessão (DuckDB).
- **[Fonte]**: confirmado por subagente em documentação, PyPI ou paper; URLs na seção 10.
- **[Inferência]**: julgamento meu, ainda não testado.

---

## 1. Conclusões

1. **O problema central é identidade, não LLM.** `STUDENT_ID` não é único: 173 IDs se repetem entre marcas EAD, sempre em pessoas diferentes. Um join sem marca pega mais de uma pessoa em 1.714 de 3.528 protocolos (49%) e em 483 de 1.065 contratos (45%). Esse é um vazamento entre alunos que nenhum prompt conserta.
2. **O tenant é a pessoa (CPF canônico), não a marca.** Sua ideia de multi-tenancy com identidade injetada está certa, mas a chave precisa ser esta. Nenhum CPF atravessa as 5 marcas, então a marca vira uma invariante adicional fácil de testar.
3. **Os dados não justificam um RAG grande.** Quase tudo é estruturado e o texto livre são 25 templates em inglês. RAG se aplica a cerca de 335 linhas de catálogo público. Dá para mostrar rigor com um pipeline pequeno e medido.
4. **Framework: Pydantic AI, sem harness.** Harnesses são feitos para agentes de código (shell, filesystem, um processo por sessão) e contrariam os requisitos de escala e de segurança.
5. **A evidência de maior impacto é o teste do "LLM comprometido".** Troca-se o modelo por um script hostil que chama todas as tools com todos os argumentos, e o teste comprova zero linhas de terceiros. Ele é determinístico, barato e responde diretamente ao critério "garantias de arquitetura, não instruções no prompt".
6. **"Zero risco" não é prometível como frase absoluta.** A arquitetura garante isolamento de dados mesmo com o LLM comprometido. Ela não garante que o modelo nunca diga algo errado. Separar as duas coisas no documento passa mais senioridade do que afirmar "zero".

---

## 2. O que o case premia

| Critério | Implicação prática |
|---|---|
| Assertividade, inclusive cruzando sistemas e recusando | Tools que já devolvem o cruzamento calculado; o LLM não faz conta nem join |
| Latência "medida e relatada por você" | Medição é entregável: p50/p95/TTFT por etapa, separando mock e provedor real |
| Segurança por arquitetura | RLS, tools sem parâmetro de identidade, views com allowlist, teste de LLM comprometido |
| Arquitetura e engenharia | Decisões com trade-offs, testes, observabilidade |
| Entregáveis | Repo, doc de arquitetura e **evidências**: conversas, ataques, latência, avaliação de qualidade |

As evidências são um entregável pesado. Elas precisam nascer de scripts reproduzíveis, não de um relato escrito no último dia.

---

## 3. EDA: como os dados estão dispostos

### 3.1 Panorama

- 47 tabelas, 52 MB. Só `mdl_logstore_standard_log` tem 27,6 MB (151 mil linhas).
- O volume é trivial para Postgres. **Os CSVs não provam escala**: isso exige teste de carga com LLM mockado.
- Integridade interna é boa: nenhuma PK duplicada nas 19 tabelas testadas, `net = gross - discount` em 100% das faturas, soma de pagamentos correta, todas as mensalidades batem com `price_list`. As FKs que testei são consistentes, com uma exceção: 169 eventos do log do LMS têm `userid` órfão.
- A dificuldade está **entre** sistemas e na semântica, não em sujeira aleatória.

### 3.2 Mapa de identidade (o coração do desafio)

| Sistema | Chave | Exemplos reais | Normalização | Cobertura |
|---|---|---|---|---|
| SAG | `BRAND` + `STUDENT_ID` | `UniSaoPaulo_EAD`, `011550` | Referência canônica | 1.037 matrículas |
| SAG | `PERSON_ID` → `CPF` | 15 CPFs com 2 `PERSON_ID` (nome abreviado) | Agrupar por CPF | 1.015 → **1.000 pessoas** |
| Financeiro | `academicRef` + `companyCode` + `businessArea` | `18001-7`, `18015`, `1253-0`, ` 01233-5 ` | trim, zeros à esquerda, recalcular dígito | **1.065/1.065** |
| LMS | `student_id` + `tenant_id` | `PRES_18199`, `ead_01195`, ` EAD_…` | maiúsculas, trim, prefixo = modalidade, 5 dígitos sem verificador | **983/983** com ID |
| Secretaria | `Stu_ID` + `Unit_Code` → marca, + `Requester_CPF` | `11924`, `180254`, nulo | zeros à esquerda; CPF perdeu zeros em 315 linhas | ver 3.3 |

**Descoberta útil:** o `STUDENT_ID` tem 5 dígitos de base mais 1 verificador **módulo 11 com pesos 6-5-4-3-2**, válido em 739/739 IDs. É o que permite reconstruir referências truncadas do financeiro. O prefixo também identifica a origem: `18` SP, `07` Montanhas, `12` Litoral, `03` Atlântico, `09` Araucária, e **`01` em todas as marcas EAD** (a causa da colisão).

**A mesma marca aparece de pelo menos cinco formas:** `UniSaoPaulo_EAD`, `UNISAOPAULO`, `unisaopaulo`, `Uni São Paulo`, `1010`. A modalidade, de três: `DL`/`CAMPUS`, `DIGITAL`/`PRESENCIAL`, `EAD_`/`PRES_`.

**Outros mapeamentos:**
- Unidade SAG ↔ Secretaria: sem chave comum, 27 unidades. O caminho é uma tabela seed curada (`101` ↔ `SPA-PAU`).
- `Course_Label`: 24 grafias para 8 cursos (`Psych.`, `Psychology Dept.`, `ADS`, `Systems Dev.`…).
- `mdl_course.idnumber`: `SAG-<CLASS_ID>` resolve 8.209/8.209. Dos 1.005 nulos, 965 resolvem de forma única pelo `shortname` + tenant, e 40 são salas institucionais.
- `PROTOCOL_REF`: `PRT-2022/0003091` ↔ `20220003091`, 229/229 após extrair os dígitos.

### 3.3 Posse de protocolos, em cascata

| Regra | Protocolos | Tratamento sugerido |
|---|---|---|
| ID + marca + CPF do requerente confirmam | 3.455 | Dono confirmado |
| ID + marca, requerente é responsável/pagador | 73 | Dono é o aluno; ocultar dados do responsável |
| CPF + marca → matrícula única (sem ID ou ID com dígitos trocados) | 337 | Dono confirmado |
| CPF + marca → 2 matrículas da mesma pessoa | 17 | Dono é a pessoa; matrícula ambígua |
| Responsável, pagador de 1 aluno na marca | 28 | Inferido; decidir na arquitetura |
| Responsável, pagador de N alunos | 12 | **Fail closed** |
| Terceiros, sem vínculo | 11 | **Fail closed**, ninguém vê |

Soma: 3.933. Resolvidos sem ambiguidade de pessoa: 3.882 (98,7%).

Um bom sinal: em nenhum protocolo de aluno ou ex-aluno cujo ID casou o CPF diverge. Os 52 IDs com dígitos trocados (`11574` em vez de `011754`) simplesmente não casam com ninguém, e o CPF os resolve.

### 3.4 Armadilhas de segurança (candidatas a teste)

| Armadilha | Medida | Consequência |
|---|---|---|
| ID EAD colide entre marcas | 173 IDs; `011550` existe em 5 marcas | Toda consulta exige a marca |
| Pagador compartilhado | 17 pagadores (7 empresas, 10 PF) com 42 alunos e 1.182 faturas | **Filtrar por `customerId` vaza fatura de outro aluno**; filtrar por contrato → matrícula |
| Pagador ≠ aluno | 167 contratos, 160 alunos | Mostrar a fatura sem expor CPF, telefone e e-mail do pagador |
| Mesma pessoa com 2 `PERSON_ID` | 15 CPFs | Precisa ver as duas matrículas: isolar por `PERSON_ID` quebraria a resposta |
| Nota interna | 759 linhas com `Is_Internal_Note=True` | Fora da view, nunca chega ao LLM |
| Contas não-aluno no LMS | 60 professores, 12 `aluno.teste*`, 3 de sistema | Excluir; bloquear login simulado |
| Contas sem `student_id` | 20 no LMS (só 7 com CPF no perfil) | Resolver por CPF; **por nome, jamais**: sem vínculo, sem dados LMS |
| Dados corporativos | `analyst`, `professor` (CPF, e-mail, contratação), `Signed_By`, `Author` | Sem GRANT; expor no máximo o nome do professor da própria turma |
| CPF em claro | `person`, `customer`, `protocol`, `mdl_user_info_data` | Nenhuma view expõe; autenticação pode usar hash |

**Injeção indireta:** todas as mensagens se reduzem a **25 templates benignos** (com variações de RA) e 5 comentários de pesquisa; não há CPF, e-mail ou telefone no texto. Os dados não têm injeção plantada. Portanto o ataque virá **pelo chat**, ou pelo texto que o próprio aluno grava ao abrir um protocolo. Vale incluir um seed de teste com injeção para exercitar esse caminho.

### 3.5 Armadilhas de correção (candidatas a golden set)

**Financeiro**
- **Débito ≠ tudo que não foi pago.** `OPEN` são 1.298 faturas, todas com vencimento futuro (até 03/2027). `RENEGOTIATED` são 196 faturas já absorvidas por acordos: somá-las às parcelas conta a dívida em dobro. Dívida real é `OVERDUE` mais o saldo de `PARTIAL`.
- **Estorno:** 26 faturas `OVERDUE` têm pagamento apenas `REVERSED`, o caso clássico de "paguei e continua em aberto". Outras 89 estão `PAID` com um estorno no histórico. Só `CONFIRMED` conta.
- **Snapshot x faturas:** na posição de 31/10, o número de faturas bate em 273/273 contratos e o principal em 270/273. As 3 diferenças são todas `PARTIAL`, onde o snapshot usa o saldo.
- **Acordos:** `originalDebtCents` = soma líquida + multa e juros, em 65/65. Parcelas e total também batem em 65/65.
- **Vários contratos:** 28 matrículas têm 2 contratos. Mostrar só o ativo esconde dívida antiga.
- **Status cruzado:** 50 `ACTIVE` em cobrança, 100 `DROPOUT` em cobrança, 17 formados em cobrança.
- **Multas dispensadas:** 145 `late_charge` têm `waived=True`.

**Acadêmico**
- **Frequência não existe em turma online:** nula em 10.055/10.055. A resposta correta é "não há registro", nunca 0% ou um valor inventado.
- **`EXEMPT`** (865) não tem nota nem frequência.
- **Anomalia em 2026/2:** 118 resultados `FAILED`/`FAILED_ATTENDANCE` de matrículas `ACTIVE` em um semestre em andamento, sendo que AV2 só começa em 05/12. Uma amostra mostra nota final 0,0 atualizada em setembro. Reportar fielmente; não "corrigir".
- **GPA é média simples** das disciplinas com nota (935/935 bate), não ponderada por crédito. 15 estão nulos.
- **Regras implícitas:** aprovação com nota ≥ 6 e frequência ≥ 75% são 100% consistentes. A final parece `0,4·AV1 + 0,6·AV2`, com AV3 substituindo a menor, mas isso não explica todos os casos (81% com AV3). **Não recalcular**: usar `RESULT` e `FINAL_GRADE`.
- **Matriz:** 487 linhas de `student_class` têm matriz diferente da atual (migração).

**Entre sistemas**
- **Nota LMS x SAG:** AV1/AV2 batem em cerca de 99%, com 134 divergências. SAG é a fonte oficial.
- **Cobertura temporal:** LMS começa em 01/2023, secretaria em 03/2022, SAG e financeiro em 2021. 54 matrículas não têm conta no LMS. "Sem dado" não significa "não aconteceu".
- **Data de referência:** é 31/10/2026, não `now()`. Precisa ser configuração injetada, ou os SLAs e evals mudam de resultado com o tempo. Alguns eventos passam da meia-noite em UTC (até cerca de 03h de 01/11) e ainda são 31/10 no Brasil.
- **Idioma:** cursos, disciplinas, serviços e status estão em inglês. O aluno pergunta "Administração", o dado diz `BUSINESS ADMINISTRATION`.
- **Lacuna de conhecimento:** não há documento de regulamento. Prazo de trancamento ou regra de bolsa não têm resposta na base: o agente precisa dizer isso.

### 3.6 Personas prontas para evals

| Caso | Matrícula |
|---|---|
| Colisão de ID em 5 marcas | `011550` em qualquer marca EAD |
| Duas matrículas, dois `PERSON_ID` | CPF `95347704853`: `UniAraucaria_EAD:011541` + `UniAraucaria:090697` |
| Pagador empresa com vários alunos | `C0004244`: `UniSaoPaulo_EAD:012157`, `UniSaoPaulo_EAD:014559` |
| Pagador PF com dois alunos | `C0005104`: `UniSaoPaulo:180548` + `UniSaoPaulo:180823` |
| Vencida com estorno | `UniSaoPaulo_EAD:012955`, fatura `7025510` |
| Trancamento financeiro | `UniSaoPaulo:180882`, protocolo `PRT-2024/0000454` |
| Acordo ativo | `UniSaoPaulo:180696`, `AG2026000122` |
| Formado em cobrança | `UniLitoral:120057`, `CT00010681` |
| Protocolo em andamento | `UniSaoPaulo_EAD:012831`, `20260024630` |
| `FAILED` em semestre corrente | `UniAraucaria_EAD:012661` |

---

## 4. Estruturas de dados e separação de escopos

Esboço para ser refinado na sessão de arquitetura. **[Inferência]**, exceto onde indicado.

```
Sessão (JWT) ─► person_uid ─► set_config('app.person_uid', …, true) por transação
                                        │
LLM ─► tool sem parâmetro de identidade ─► safe.* (allowlist) ─► core.* (RLS por person_uid)

raw.*    CSV verbatim, uma tabela por origem          sem GRANT para o agente
core.*   modelo canônico + person_uid em cada fato    RLS + FORCE
xref.*   crosswalk com match_method e confidence      sem GRANT para o agente
safe.*   views security_invoker, só colunas permitidas  única superfície do agente
kb.*     catálogo público + embeddings                leitura para todos
app.*    conversas, rascunhos, auditoria              RLS própria
```

Decisões-chave:

1. **`person_uid` denormalizado em cada fato, gravado na ingestão.** A policy vira `person_uid = current_setting(...)`, sem subquery. É mais simples de auditar e mais rápida; a doc do Supabase indica a policy sobre a própria linha como a mais performática **[Fonte]**. O trabalho difícil de identidade fica concentrado em um único passo testável.
2. **O crosswalk é um artefato de primeira classe.** Registra método e confiança por vínculo; o que for ambíguo não vincula (*fail closed*). Um relatório de cobertura gerado pela ingestão vira evidência, e os números da seção 3 viram testes.
3. **Duas barreiras independentes:** a tool não recebe identidade, e o banco nega mesmo se a tool errar. Só uma delas seria insuficiente para o argumento.
4. **Escopo de sessão:** pessoa → N matrículas, com `active_enrollment` escolhida na UI e usada como filtro de conveniência, nunca como controle de acesso.
5. **Fontes de verdade explícitas:** SAG para acadêmico (acima do LMS), `invoice`/`payment` para detalhe financeiro, `receivable_snapshot` para posição histórica, secretaria para protocolos.
6. **Ontologia leve, sem banco de grafos:** um YAML com entidades, sinônimos PT↔EN e fontes de verdade. Alimenta o resolvedor de entidades e as descrições das tools, e responde à menção do README a ontologias com um trade-off explícito.

**Armadilhas de RLS confirmadas [Fonte]:**
- Superuser e dono da tabela ignoram RLS, e a imagem Docker oficial cria `POSTGRES_USER` como superuser. O app precisa de um role próprio.
- Sem `FORCE`, o dono escapa da policy.
- Views sem `security_invoker` rodam com os direitos do dono.
- `SET` não é suportado em transaction pooling no PgBouncer: use `set_config(..., true)` por transação. Sem PgBouncer no MVP, o risco desaparece.

---

## 5. Framework de agentes

| Opção | Veredito | Motivo |
|---|---|---|
| **Pydantic AI 2.65** | **Recomendado** | `RunContext[Deps]` deixa a identidade fora do schema; `TestModel`/`FunctionModel`; OTel nativo; cache da Anthropic nativo; multi-provider **[Fonte]** |
| Loop próprio sobre o SDK da Anthropic | Plano B | Controle total, mas reescreve retry, streaming e validação. Manter tools independentes do framework torna essa troca barata |
| LangGraph | Só se precisar de grafo | Checkpointer forte; abstração demais para um agente único **[Inferência]** |
| OpenAI Agents SDK, Google ADK | Descartar | Otimizados para o próprio ecossistema |
| CrewAI, Agno | Descartar | Opinativos, voltados a multi-agente ou plataforma |
| smolagents | Descartar | O `CodeAgent` executa código gerado pelo LLM **[Fonte]** |
| Claude Agent SDK, Deep Agents, harnesses | **Descartar** | Subprocesso por sessão, cerca de 1 GiB e 1 CPU por agente, shell e filesystem como superfície **[Fonte]** |

**Sobre o "harness pré-configurado" que você imaginou:** o menor esforço aqui não vem de um harness, e sim de um framework fino, porque o agente em si é a parte pequena. O esforço está nas tools e na identidade.

Dois cuidados: Pydantic AI 2.65 exige **Python ≥ 3.11** e sua máquina tem 3.10.12, então use Docker ou `uv`. E o ritmo de releases é alto (várias por semana): fixe a versão.

---

## 6. RAG, tools e evals

### Onde RAG entra

| Conteúdo | Abordagem |
|---|---|
| Notas, faturas, protocolos, LMS | **Tools com SQL fixo.** RAG aqui só adiciona ponto de erro |
| 18 serviços, calendário | Tool estruturada; cabem quase no prompt |
| 260 disciplinas, 8 cursos, matrizes, 27 unidades | **Busca híbrida** em Postgres: pgvector + `tsvector` português + RRF |
| Mensagens de protocolo | Sem RAG: 25 templates, por aluno, tratados como dado |
| Regulamentos | Não existem. Recusar é a resposta correta |

Pipeline mínimo **[Inferência]**:
- Traduzir o catálogo para PT **uma vez, na ingestão**. Resolve boa parte do problema PT→EN antes de qualquer embedding.
- Um chunk por linha, com cabeçalho determinístico.
- Sem reranker, com tão poucos itens.
- Medir recall@k e MRR com 30 a 50 consultas reais em português, comparando léxico × vetorial × híbrido. **Essa tabela vale mais que um pipeline sofisticado**, e o resultado pode até concluir que o híbrido não compensa.

Grafo e GraphRAG: não. As relações são joins comuns. Text-to-SQL: não; no benchmark do dbt, o mesmo modelo foi de 90% para 98,2% com semantic layer, embora a amostra seja pequena e o autor seja fornecedor **[Fonte]**. Além disso, tools fixas fecham a superfície de P2SQL.

### Tools (primeiro corte, cerca de 12)

`get_academic_status`, `get_grades`, `get_curriculum_progress`, `get_calendar`, `search_catalog`, `get_financial_summary`, `list_invoices`, `get_agreements`, `list_protocols`, `get_protocol`, `draft_protocol`, `get_lms_activity`, `get_quiz_attempts`.

Princípios:
- **Devolvem o cruzamento pronto**, com totais calculados em código, valores em R$ e rótulos em PT. Isso reduz turnos, custo e erro aritmético.
- **Carregam contexto de qualidade**: `sem_dados_antes_de`, `frequencia_nao_registrada`, `fonte_oficial`.
- **Escrita em dois passos:** `draft_protocol` só propõe; `POST /confirm/{id}` é disparado pela UI, nunca pelo LLM.

### Evals em camadas

| Camada | Mede | Ferramenta |
|---|---|---|
| L0 | Crosswalk, tools, invariantes de RLS, sem LLM | pytest |
| L1 | **LLM comprometido**: script hostil via `FunctionModel`, zero linhas alheias | pytest + Pydantic AI |
| L2 | Golden set: fatos, trajetória, recusa, latência, custo | pydantic-evals |
| L3 | Groundedness e tom (só o que código não verifica) | LLMJudge |
| L4 | Red team: BOLA/BFLA, injeção, extração de prompt, com ASR por categoria | promptfoo + ataques manuais |

**Golden set derivado por SQL:** cerca de 15 templates de pergunta × personas da seção 3.6. A resposta esperada vem de SQL escrito **independentemente das tools**, senão o teste só confirma o próprio código. Incluir cerca de 20% de perguntas sem resposta e cerca de 10% sobre outro aluno.

Vale citar, se usar promptfoo: há relato secundário de que foi adquirido pela OpenAI em 03/2026, mantendo a licença MIT.

---

## 7. API, escala e custo

### Modelos

| Modelo | Entrada / cache read / saída ($/MTok) | Custo por conversa, com cache* |
|---|---|---|
| Claude Haiku 5.5 | 0,10 / 0,01 / 0,50 | ~$0,002 |
| Claude Sonnet 5.5 | 2 / 0,20 / 10 | ~$0,033 |
| Claude Opus 5.5 | 4 / 0,20 / 20 | ~$0,061 |

*Premissa: 3 turnos, ~6 chamadas, 27 mil tokens de prefixo cacheável, 9 mil novos, mil de saída. **Não inclui escrita de cache nem thinking**, que é cobrado como saída. Substituir pelos números reais medidos.

- **Recomendação:** rodar o golden set nos três modelos com esforço `low` e deixar os dados decidirem. Hipótese: Haiku como padrão, escalando só por falha. A diferença de 20× justifica o teste.
- **Medir TTFT em vez de confiar em ranking:** a pesquisa encontrou Haiku 5.5 `low` com TTFT de 9 s no Artificial Analysis, número estranho e não reproduzido.
- **Cuidados de API:** Sonnet e Opus 5.5 rejeitam `tool_choice` forçado (`any`/`tool`) e não aceitam `thinking: disabled`. O prefixo de cache não pode conter dados do aluno nem timestamp.
- **Conta de capacidade:** com ~6 chamadas por conversa, 4.000 RPM sustentam cerca de 650 conversas/min. O limite de milhares simultâneos é o tier do provedor, e a arquitetura precisa assumir isso.

### Implementar de verdade

- Async de ponta a ponta, app stateless, SSE, cancelamento na desconexão.
- Pool asyncpg com limite, uma transação por tool, `statement_timeout`.
- Deadline budget (por exemplo: 30 s no total, 10 s por chamada ao LLM, 2 s por tool).
- Semáforo global para chamadas ao LLM, fila limitada, 429 rápido com `Retry-After`.
- Retry com jitter só em 429/5xx, circuit breaker, fallback para segundo provedor.
- Rate limit por aluno, idempotência na escrita, limite de iterações do loop.
- Prompt caching, com `cache_read_input_tokens` monitorado.
- Logs estruturados com auditoria por tool call, métricas e spans OTel.

### Só documentar como evolução

PgBouncer, fila assíncrona, cache semântico (perigoso com dados por aluno), roteador por classificador, autoscaling, gateway dedicado. Sobre LiteLLM: há relatos em várias fontes de versões comprometidas no PyPI em 03/2026 e 10/2026; não consegui abrir o advisory primário. Uma abstração fina evita a dependência.

### Plano de carga [Inferência]

Mock do LLM com latência realista e injeção de 429/529/timeout. Metas iniciais: 1.000 SSE simultâneos com erro < 0,5%; overhead da aplicação p95 < 50 ms; tool SQL p95 < 30 ms; cancelamento upstream < 1 s; 100% de 429 no primário sem 5xx para o usuário. Depois, 30 a 50 conversas reais para TTFT e custo. **Relatar separadamente o que foi provado localmente e o que é projeção.**

---

## 8. 80/20: onde colocar o esforço

### Maior retorno

| Prioridade | Item | Esforço | Por quê |
|---|---|---|---|
| 1 | Ingestão + crosswalk + relatório de cobertura | 20% | Tudo depende disso; é o principal diferencial técnico |
| 2 | Tools semânticas com cruzamentos | 20% | Define a assertividade |
| 3 | RLS, views e teste do LLM comprometido | 15% | Maior sinal do critério de segurança |
| 4 | Golden set e red team | 20% | Transforma afirmações em números; é entregável |
| 5 | Doc de arquitetura + evidências | 10% | É o que o avaliador lê primeiro |
| 6 | API resiliente + teste de carga | 10% | Importante, mas boa parte é padrão conhecido |
| 7 | RAG de catálogo | 5% | Escopo pequeno; a medição é o valor |

O agente em si é o menor item: com um framework fino, a orquestração é pouco código.

### Onde polir

1. O relatório de cobertura do crosswalk.
2. O teste do LLM comprometido e sua explicação.
3. A tabela de resultados do eval, por categoria, incluindo os **erros encontrados e corrigidos**.
4. O documento de trade-offs, inclusive o que você decidiu **não** construir.
5. Quatro ou cinco conversas de demonstração que cruzam sistemas e mostram recusas.

### Não fazer

UI elaborada, multi-agente, Neo4j/GraphRAG, reranker, guardrail de ML no caminho crítico, Kubernetes, Langfuse completo (6 serviços), MCP, CaMeL, ReBAC, rodar AgentDojo ou BIRD inteiros.

### Sequência sugerida

| Dia | Foco | Pronto quando |
|---|---|---|
| 1 | Compose, ingestão, crosswalk | Relatório reproduz os números da seção 3 |
| 2 | RLS, views, tools acadêmicas e financeiras | Testes L0 e L1 passam |
| 3 | Agente, API SSE, restante das tools | Conversa ponta a ponta |
| 4 | Golden set, primeira rodada, comparação de modelos | Tabela de baseline |
| 5 | Corrigir falhas, RAG, red team | ASR por categoria |
| 6 | Resiliência e carga | Latência e falhas medidas |
| 7 | Doc, evidências, teste de instalação limpa | Clone → `docker compose up` funciona |

**Corte, se atrasar:** RAG vira busca léxica; fallback de provedor vira só documentado. **Nunca cortar:** crosswalk, RLS, teste do LLM comprometido, golden set.

---

## 9. Decisões para a sessão de arquitetura

| Decisão | Minha recomendação |
|---|---|
| Aluno pode ver dívidas de todas as matrículas? | Sim, é a mesma pessoa; destacar a ativa |
| Protocolo aberto por responsável aparece para o aluno? | Sim, sem nome e CPF do responsável; os 12 ambíguos e 11 de terceiros, não |
| Atender responsável/pagador? | Fora do MVP: o case fala em aluno autenticado |
| Mostrar nome do professor e do atendente? | Professor da própria turma, sim; analista, não |
| Provedor principal e de fallback | Decidir com dados do dia 4 |
| O que abrir um protocolo pago faz? | Criar o protocolo e informar a taxa; não gerar fatura no MVP |
| Tem UI? | Uma página mínima de chat com seletor de aluno simulado, só se sobrar tempo |

**Vale perguntar ao recrutador:**
1. O avaliador executa o projeto com a própria chave de API ou espera uma URL?
2. Existe base de regulamentos fora do zip, ou recusar essas perguntas é o comportamento esperado?

---

## 10. Limitações e fontes

**Limitações desta análise**
- Os números vêm dos CSVs atuais com normalização exploratória; a ingestão real deve reproduzi-los por teste.
- Não abri o conteúdo de todas as 47 tabelas com a mesma profundidade: `invoice_tax`, `course_offer` e `mdl_course_modules` tiveram verificação superficial ou nenhuma.
- Nada de arquitetura foi prototipado: RLS, Pydantic AI e latências são pesquisa, não medição própria.
- Preços e versões são de 04/11/2026. O cache read do Sonnet 5.5 divergiu entre o subagente ($0,10) e a referência da API ($0,20); usei $0,20. Confirme na página de preços.
- Lacunas de pesquisa: Phoenix self-hosted (403), advisory do LiteLLM (403), preço de embeddings em fonte oficial.
- Os scripts da EDA estão no scratchpad desta sessão, que é temporário.

**Fontes**
- RLS: <https://www.postgresql.org/docs/current/ddl-rowsecurity.html>, <https://www.postgresql.org/docs/current/sql-createview.html>, <https://supabase.com/docs/guides/database/postgres/row-level-security>, <https://www.pgbouncer.org/features.html>
- Injeção: <https://arxiv.org/abs/2506.08837>, <https://arxiv.org/abs/2503.18813>, <https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/>, <https://ai.meta.com/blog/practical-ai-agent-security/>, <https://genai.owasp.org/llm-top-10/>, <https://arxiv.org/pdf/2308.01990>, <https://arxiv.org/pdf/2505.03574>
- Pydantic AI: <https://pydantic.dev/docs/ai/core-concepts/dependencies/>, <https://pydantic.dev/docs/ai/guides/testing/>, <https://pydantic.dev/docs/ai/models/anthropic/>, <https://pydantic.dev/docs/ai/evals/evaluators/overview/>
- Harness: <https://code.claude.com/docs/en/agent-sdk/hosting>, <https://github.com/langchain-ai/deepagents>, <https://huggingface.co/docs/smolagents/tutorials/secure_code_execution>
- RAG e text-to-SQL: <https://github.com/pgvector/pgvector>, <https://www.anthropic.com/engineering/contextual-retrieval>, <https://docs.getdbt.com/blog/semantic-layer-vs-text-to-sql-2026>, <https://huggingface.co/BAAI/bge-m3>
- Red team: <https://www.promptfoo.dev/docs/red-team/>, <https://arxiv.org/abs/2403.02691>
- Modelos e limites: <https://platform.claude.com/docs/en/about-claude/pricing>, <https://platform.claude.com/docs/en/build-with-claude/prompt-caching>, <https://platform.claude.com/docs/en/api/rate-limits>, <https://artificialanalysis.ai/leaderboards/models>
- Observabilidade: <https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans>, <https://langfuse.com/blog/joining-clickhouse>
- Supply chain: <https://www.netspi.com/blog/executive-blog/ai-ml-pentesting/litellm-supply-chain-compromise/>, <https://docs.litellm.ai/blog/tags/security>
