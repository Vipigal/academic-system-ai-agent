---
type: Plan
title: Simplificação idiomática
description: Spec da refatoração que troca soluções feitas à mão por recursos do SQLAlchemy, do LangChain e do dishka, mantendo a arquitetura e o comportamento, para o código ficar menor e mais fácil de explicar.
tags: [plano, refatoracao, ownership, sqlalchemy, dialeto, tools, injecao-de-dependencia]
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-09T20:00:00Z }
sources:
  - id: arquitetura
    resource: /docs/architecture.md
    title: Arquitetura do agente de atendimento ao aluno
  - id: sqlalchemy-criteria
    resource: https://docs.sqlalchemy.org/en/20/orm/queryguide/api.html#adding-global-where-on-criteria
    title: SQLAlchemy, Adding global WHERE / ON criteria (with_loader_criteria e do_orm_execute)
  - id: fastapi-overrides
    resource: https://github.com/fastapi/fastapi/pull/5452
    title: Posição do mantenedor do FastAPI sobre dependency_overrides fora de teste
  - id: dishka
    resource: https://github.com/reagento/dishka
    title: dishka, container de DI com escopos APP e REQUEST e integração com FastAPI
---

# Simplificação idiomática

> **Status:** em revisão · **Data:** 2026-11-09
> **Spec vivo:** este arquivo é a fonte única da tarefa. Mudanças são editadas aqui e anotadas em
> "Mudança no spec" na seção Registro; leia o Registro junto do restante.
> **Repos:** só este. `ruff.toml`, `.flake8`, `.importlinter`, `mypy.ini`, `pyrightconfig.json`, `quality.toml`, `Makefile`,
> `tools/quality/` e `tests/lint/` são do dono e não mudam aqui. Se uma regra deles atrapalhar, o caso é relatado com
> exemplo e espera decisão. `pyproject.toml` e `uv.lock` mudam só para entrar o `dishka` (T4).

## Para o humano

- **TL;DR:** quatro soluções feitas à mão saem e dão lugar a recursos padrão das bibliotecas, com a mesma
  arquitetura e o mesmo comportamento:
  1. O ownership deixa de ser um adapter que percorre o `FROM` e passa a ser o critério global do ORM
     (`do_orm_execute` com `with_loader_criteria`). Saem `Via`, `Public`, `Update`, `DeclaredQuery`, o `QueryGuard`
     e o `WritePlan`.
  2. O dialeto encolhe para a chave de dono. A tradução de valores (status, marca, centavos, datas) vira tipo de
     coluna (`Enum` e `TypeDecorator`).
  3. As tools passam a ter a assinatura como fonte da verdade do schema.
  4. O bootstrap passa a ser um container `dishka`, com escopos APP e REQUEST, usado igual pela API, pelo eval e pelos
     testes.
- **Revise com atenção:**
  - o desenho do ownership e a sessão "sistema" (§6.1);
  - o container e a origem da `StudentSession` no HTTP (§6.4);
  - os oráculos de "comportamento igual" (§8, T0), que são a prova de que nada mudou para o aluno.
- **Para o aluno e para o agente:** nada muda. As respostas das tools, o schema que o modelo recebe e as linhas que cada
  aluno vê ficam idênticos. A única diferença aceita é a ordem das cláusulas no SQL gerado.

## 1. Contexto e problema

O projeto foi escrito trazendo conceitos do NestJS, e várias peças reimplementam o que as bibliotecas já oferecem. Isso
custa código e, principalmente, custa explicação diante de um examinador sênior de Python.

**Ownership.** O isolamento tem cerca de 370 linhas em `src/api/persistence/core/`:

- o adapter percorre as tabelas do `FROM` e acrescenta um `AND` por regra (`repository_adapter.py:60`);
- `Via` exige que a tabela-pai esteja no `JOIN` (`ownership.py:21`);
- `DeclaredQuery` e um registro controlam as consultas que leem tabelas Core privadas (`ownership_registry.py`);
- o `QueryGuard` mantém uma lista de construções de SQL permitidas e lê atributos privados do `Select`
  (`query_guard.py:31`);
- o `WritePlan` acrescenta o dono no `UPDATE`.

Além disso, os repositórios fazem `JOIN` só para satisfazer o ownership (`finance/repositories.py:30-42`).

**Dialeto.** O dialeto mistura duas funções. A primeira é a chave de dono, que é conhecimento de domínio e fica. A
segunda é a tradução de valor: são 33 dicionários `*_BY_SOURCE` e 25 chamadas a `DialectLookup.find`, espalhadas em
`dialect.py`, `labels.py` e `vocabulary.py`. Os models declaram tudo como `Mapped[str]`, e os mappers convertem
centavos, datas e enums à mão.

**Tools.** A descrição de cada parâmetro vive fora da assinatura:

- `ToolSchema` monta o schema com `create_model` (`tool_schema.py`);
- `GUIDES` e `DESCRIPTIONS` são tabelas por nome de parâmetro (`tool_arguments.py`);
- um cache global de schemas fica em `tool_schema.py:65`.

**Bootstrap.** São 539 linhas de classes `*Providers` no estilo Nest, mais as fábricas `Router.build` na presentation. As
tools são montadas em três lugares diferentes:

- o turno do chat (`chat_agent_scope.py:28`);
- o eval (`src/evals/student_driver.py`);
- os testes de integração (`tests/integration/support/tools.py`).

O FastAPI não resolve `Depends` fora de um request, e usar `dependency_overrides` para montar a aplicação não é
oficial[^overrides].

Este spec fecha os quatro pontos sem mudar a arquitetura de `docs/architecture.md`: camadas, ports, domínio só com a
biblioteca padrão, `StudentSession` imutável por request, um mapa de ownership por sistema e sem RLS (B9).

## 2. Princípios

- **Comportamento idêntico é o critério de pronto.** Tudo que o aluno e o agente veem fica igual, e isso é provado por
  comparação antes e depois (T0), não por leitura de código.
- **Recurso da biblioteca antes de mecanismo próprio.** A explicação para o examinador deve caber em "é a receita
  oficial de X".
- **A arquitetura não se renegocia.** Camadas, composition root no bootstrap e ownership declarado por tabela continuam.
- **Fail closed.** Uma consulta sem aluno na sessão de banco é recusada. A exceção existe só onde está escrita
  explicitamente.
- **O desenvolvedor revisa o próprio código.** Mecanismo que só impede o desenvolvedor de escrever SQL errado sai: o
  agente e o usuário nunca escrevem SQL.

## 3. Decisões

### 3.1 Batidas (não reabrir)

| # | Decisão | Por quê |
|---|---|---|
| D1 | O ownership passa a ser um listener `do_orm_execute` que aplica `with_loader_criteria` por tabela a todo `SELECT`, `UPDATE` e `DELETE` do ORM | É a receita oficial do SQLAlchemy para critério global[^criteria]. O spike de 2026-11-09 confirmou três coisas: o critério entra nas subqueries do critério vizinho, entra no `ON` de um `JOIN` com condição errada e entra no `UPDATE` |
| D2 | O `Via` vira uma subquery no próprio critério do filho: `InvoiceRow.contract_id.in_(select(ContractRow.id))`. O critério do pai entra sozinho nessa subquery | Some a exigência de `JOIN` com o pai. `select(PaymentRow)` sozinho já sai filtrado em cadeia (spike) |
| D3 | O `QueryGuard` sai | O agente e o usuário não escrevem SQL. O guard só impedia o desenvolvedor de escrever SQL errado, e isso é papel do review |
| D4 | `DeclaredQuery` e o registro de consultas privadas saem. As consultas de pagador e de nome do requerente viram métodos comuns de repositório | Mesmo motivo de D3. A linha raiz delas (`ContractRow`, `PersonRow`) recebe o critério do ORM; a tabela Core correlacionada é lida só no contexto de uma linha que já pertence ao aluno |
| D5 | A sessão "sistema" (a carga da `StudentSession`, antes de existir aluno) marca as consultas com `.execution_options(skip_ownership=True)`, e o listener pula só essas. Uma sessão de banco sem aluno em `session.info` e sem a flag é recusada | É a forma oficial do critério global, a mesma da opção `include_private` da receita. Testado no SQLAlchemy 2.1.8 |
| D6 | O dialeto fica só com a chave de dono (`contract_of`, `account_of`, `protocols_of`, `tenants_of`, `source_brands`) | É a parte que é conhecimento de domínio e precisa casar com os índices de expressão de `db/init/03_indexes.sql` |
| D7 | A tradução de valores vira tipo de coluna. Os casos são: `sqlalchemy.Enum(E, native_enum=False, create_constraint=False)` quando o valor da origem é o nome do membro; `TypeDecorator` próprio quando não é (como `"Open"` para `ProtocolStatus.OPEN`); centavos em texto; datas ISO em texto; timestamp UTC em texto para Brasília; booleano em texto; e a marca da origem (`UniSaoPaulo_EAD`) | O model passa a devolver tipos do domínio, e os mappers ficam quase triviais. Valor desconhecido continua dando erro. Nenhum DDL muda (B11) |
| D8 | As tools têm a assinatura como fonte da verdade: `Annotated[T, Field(description=..., pattern=..., examples=[...])]` nos parâmetros, e o `StructuredTool.from_function` infere o schema | É a vantagem de declarar tools em Python. Saem `ToolSchema`, `ParameterGuide`, `GUIDES`, `DESCRIPTIONS` e o cache `SCHEMAS` |
| D9 | O `ToolRegistry` fica, com a declaração de ontologias (`@ToolRegistry.declares`) e as checagens de contrato (docstring, async, retorno `ToolResult`, nome único) | As ontologias são do projeto e funcionam bem |
| D10 | O `ToolTeaching` vira o `handle_validation_error` da tool, com o mesmo texto de ensino | É o gancho que a biblioteca já oferece. O texto é sensível para o eval e não muda |
| D11 | O bootstrap passa a ser um container `dishka`. O escopo APP guarda settings, banco, relógio, assinador, rate limiter, runtime do agente e identidade. O escopo REQUEST guarda `StudentSession`, adapter, repositórios, services, tools, `ChatService` e confirmação | É o mesmo conceito do escopo `REQUEST` do Nest e de B37. O mesmo grafo serve a API, o eval e os testes. Testado com 4 alunos concorrentes fora do HTTP, e cada um recebeu a própria sessão e o próprio adapter |
| D12 | A `StudentSession` tem duas origens. Na API, um provider REQUEST a lê do JWT do `Request`. No eval e nos testes, ela entra por `from_context` | O resto do grafo é o mesmo nas duas |
| D13 | As rotas viram módulos com `router = APIRouter(route_class=DishkaRoute)` e parâmetros `FromDishka[...]`. As fábricas `Router.build` saem | A presentation importa só `dishka.integrations.fastapi`, nunca o bootstrap. O `.importlinter` atual não proíbe `dishka` em nenhuma camada |
| D14 | Ordem: ownership primeiro e sozinho. O critério de pronto dele é o `EXPLAIN ANALYZE` das subqueries `IN` aninhadas comparado ao `JOIN` atual | É a mudança de maior risco: toca o isolamento e o plano de consulta |
| D15 | As classes só com métodos estáticos continuam | Escolha de estilo do dono: o namespace na chamada (`FinanceDialect.contract_of`) é legível |

### 3.2 Pendentes (confirmar na revisão)

| # | Proposta | Alternativa | Recomendação |
|---|---|---|---|
| P1 | O limiar de "sem regressão" do T1 é: tempo de execução p95 de cada consulta da amostra até 1,2× o atual, e nenhum `Seq Scan` novo em tabela que tem índice de dono | Exigir plano idêntico | Limiar. O plano muda de forma (semi-join em vez de join) e pode ser igual ou melhor em custo |
| P2 | Os repositórios perdem os `JOIN` que existiam só para o ownership (`finance/repositories.py:30-42` e equivalentes no LMS e na secretaria) | Manter os `JOIN` | Remover. Cada `JOIN` desses vira um filtro duplicado, e removê-los é parte do corte |
| P3 | O `RepositoryAdapter` continua, com o mesmo nome e caminho, e encolhe para: abrir a sessão de banco com `info={"student": session}`, `fetch` e `write`. O construtor passa a receber `Database` em vez de `async_sessionmaker` | Repositórios recebendo a sessão de banco direto | Manter o adapter. O `quality.toml` já cita o caminho dele (`session_access_allowed`), e assim o bootstrap não precisa de tipos do SQLAlchemy (contrato `database-drivers`) |
| P4 | Se o `handle_validation_error` do LangChain não devolver o `ToolExecution` como artifact (que `agent_stream.py:90` lê), a validação continua dentro do `call`, usando o `args_schema` inferido, e o texto vem da mesma função de ensino | Mudar o `agent_stream` para aceitar tool sem artifact | Decidir no primeiro passo do T3, com o teste em mãos. As duas opções preservam D8 e D10 |
| P5 | O 401 da `StudentSession` no HTTP sai do provider do dishka (D12) | Manter a `StudentSession` como `Depends` do FastAPI e entregá-la ao dishka por um middleware que abre o escopo com contexto | Provider. Fazer um spike de 15 minutos no primeiro passo do T4: o `HTTPException` levantado no provider precisa chegar como 401, e o Pyright precisa tipar o `FromDishka`. Se falhar, usar a alternativa |

## 4. Escopo

### Dentro

- O ownership por critério global do ORM (D1 a D5).
- O dialeto reduzido e os tipos de coluna (D6, D7).
- As tools com a assinatura como fonte da verdade (D8 a D10).
- O bootstrap em `dishka`, e o eval e os testes usando o mesmo container (D11 a D13).
- Detalhes menores:
  - `Money.from_cents` sai, porque é idêntico ao construtor (14 usos);
  - `BrasiliaTime` passa a usar `zoneinfo.ZoneInfo("America/Sao_Paulo")` e é absorvido pelo tipo de timestamp do T2;
  - `Settings.from_environment` sai se o `Settings()` direto passar no Pyright; se não passar, fica, com o motivo
    anotado nas Notas de implementação.
- Correções em `docs/architecture.md` só onde o texto ficou errado: §5.1, §5.2 e §5.3 e as decisões B29, B31, B32, B33
  e B36. O documento não é reescrito.

### Fora

- **Classes estáticas virando módulos (D15).** Entra se o dono quiser. Exige olhar o `WPS202` do `.flake8`, que é dele.
- **Liberar `relationship()`.** O critério global também filtra o carregamento de relacionamento, então a regra B31
  perde o motivo original. O banimento está no `ruff.toml`, que é do dono, e liberar não é necessário agora.
- **RLS no Postgres.** Continua fora por B9.
- **Rodada de eval.** Não roda neste trabalho. A equivalência do schema das tools é provada por snapshot (T0); uma
  rodada só acontece com pedido do dono.

## 5. Terreno: como a codebase faz hoje

- **Ownership:**
  - `RepositoryAdapter.fetch` roda o guard, aplica as regras e abre uma sessão de banco curta por chamada
    (`persistence/core/repository_adapter.py:34`);
  - `write` prepara cada passo pelo `WritePlan` (`:50`);
  - os mapas por sistema estão em `persistence/*/ownership.py`;
  - `OwnershipRegistry.assert_complete` roda na subida (`bootstrap/app.py:24`).
- **Escrita:** `agent/repository.py:27,43` (conversa, mensagens e o `UPDATE` de `updated_at`) e
  `secretary/protocol_writer.py:17` (abrir protocolo). Hoje o `INSERT` confere só que a tabela tem regra declarada, não
  o dono da linha. O desenho novo mantém esse comportamento.
- **Tabelas Core privadas:** `persistence/identity/tables.py` (CPF, pagador, requerente). Elas são lidas em
  `identity/payer_queries.py`, `identity/requester_queries.py`, `identity/queries.py` e `secretary/dialect.py`
  (subquery da cascata de protocolos). O critério do ORM não as filtra: elas só aparecem correlacionadas a uma linha
  raiz que já é filtrada, ou na carga da sessão.
- **Sessão de banco:** só `database.py`, `repository_adapter.py` e `student_session_repository.py` podem importar
  `sqlalchemy.ext.asyncio` (`quality.toml`, `session_access_allowed`).
- **Tradução de valores:** `finance/labels.py`, `finance/dialect.py`, `sag/vocabulary.py`, `secretary/vocabulary.py`,
  `lms/vocabulary.py` e `core/dialect_lookup.py`. Os enums em que o valor da origem é o nome do membro estão nos
  `SHIFT_BY_SOURCE = {shift.name: shift ...}` e similares (`sag/vocabulary.py:9-13`) e em `InvoiceStatus`.
- **Tools:**
  - `ToolRegistry` em `application/agent/tools/registry.py`;
  - a conversão para LangChain em `langchain_tools.py`, que usa `content_and_artifact` com `ToolExecution`, lido em
    `agent_stream.py:90`;
  - o ensino em `tool_teaching.py`, que hoje lê `GUIDES`.
- **Bootstrap e uso fora do HTTP:**
  - `Singletons` (`bootstrap/singletons.py`), mais `StudentProviders`, `StudentServices`, `ToolProviders`,
    `ProtocolProviders`, `HistoryProviders`, `ChatProviders`, `IdentityProviders`, `ProtocolConfirmationProviders`,
    `ProtocolConfirmationAssembly`, `ChatAgentScope` e `RateLimitProviders`;
  - fora do HTTP: `src/evals/driver_factory.py`, `src/evals/student_driver.py`, `tests/integration/support/tools.py`,
    `tests/integration/conftest.py:56`, `tests/integration/agent/invariant_sample.py` e
    `tests/unit/agent/test_agent_providers.py`.
- **Rotas com `build`:** `presentation/http/{auth,health,identity,chat,protocol_confirmation}.py`.
- **Testes que dependem do ownership atual e serão reescritos:** `tests/unit/core/test_query_guard.py`,
  `tests/unit/core/test_ownership_registry.py`, `tests/integration/core/test_repository_adapter.py` e
  `tests/integration/core/test_adapter_write.py`.
- **Testes que provam o isolamento e não podem mudar de resultado:** `tests/integration/agent/test_tool_invariants.py`
  (varredura) e `tests/integration/identity/test_session_partition.py`.

## 6. Desenho

### 6.1 Ownership (T1)

O mapa por sistema continua sendo a declaração. O tipo da regra passa a ser uma função da sessão que devolve uma
expressão, ou `PUBLIC`:

```python
FINANCE_OWNERSHIP: OwnershipMap = {
    ContractRow: lambda s: FinanceDialect.contract_of(s.enrollments),
    InvoiceRow: lambda s: InvoiceRow.contract_id.in_(select(ContractRow.id)),
    PaymentRow: lambda s: PaymentRow.invoice_id.in_(select(InvoiceRow.id)),
    ProductRow: PUBLIC,
}
```

O listener é registrado uma vez, na classe `Session` do SQLAlchemy:

- pula o que não é `SELECT`, `UPDATE` nem `DELETE`;
- pula a consulta marcada com `skip_ownership`;
- lê o aluno de `session.info`, e recusa (fail closed) a sessão de banco sem aluno;
- aplica `with_loader_criteria(model, regra(aluno), include_aliases=True)` para cada model com regra.

`assert_complete` continua, como checagem de que toda tabela do `Base.metadata` tem uma entrada no mapa, e roda na
subida.

Pontos debatidos e fechados:

- O `Via` com `AND` (B33) existia porque um `JOIN` com condição errada trazia linhas de terceiros. No desenho novo cada
  tabela é filtrada sozinha pela própria regra, então o `JOIN` errado continua sem vazar (spike).
- Uma regra com `OR` vindo de parâmetro fica entre parênteses, como hoje: o `with_loader_criteria` acrescenta o
  critério com `AND`.
- Uma pessoa sem identificadores gera `IN ()`, que não devolve nenhuma linha, como hoje.
- No `INSERT`, nada muda (§5).

O teste de unidade novo usa `Session` sem banco e compila o SQL, como o spike, para provar seis casos: tabela filha
sem `JOIN`, `JOIN` com condição errada, `UPDATE`, flag `skip_ownership`, sessão de banco sem aluno e tabela `PUBLIC`.
Os testes de integração existentes de isolamento são o oráculo de comportamento.

### 6.2 Dialeto (T2)

- **`persistence/core/column_types.py`** guarda os tipos genéricos: o enum por mapa explícito, centavos em texto, data
  ISO em texto, timestamp UTC em texto convertido para `ZoneInfo("America/Sao_Paulo")` e booleano em texto. O
  `UnknownDialectValueError` continua sendo o erro de valor desconhecido.
- **Os tipos por sistema** (como a marca da origem do SAG) ficam no pacote do sistema.
- **Os models** passam a declarar o tipo do domínio. Por exemplo:
  `status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus, native_enum=False, create_constraint=False))`.
- **Os filtros nos repositórios** passam a usar o valor do domínio: `InvoiceRow.kind == InvoiceKind.SERVICE_FEE` em vez
  de `SERVICE_FEE_KIND`.
- **As regras de ownership** que comparam colunas que ganharam tipo passam a receber valores do domínio. O tipo converte
  o valor no bind, e o SQL gerado fica igual.
- **O que sai ou encolhe:** `core/dialect_lookup.py` e `finance/labels.py` saem, e os `vocabulary.py` saem ou encolhem
  ao que não é coluna. Os `dialect.py` ficam só com D6 e com mapas que servem à escrita, como
  `UNIT_CODE_BY_ACADEMIC_UNIT`.

Ponto fechado: a coluna usada dentro de função SQL nos índices de expressão (`academicref`, `student_id`, `stu_id`,
`requester_cpf`) continua `str`, para o SQL gerado bater com `03_indexes.sql`.

### 6.3 Tools (T3)

- **A assinatura** carrega o tipo, a descrição, o padrão e o exemplo de cada parâmetro com `Annotated[..., Field(...)]`.
  O texto que hoje está em `GUIDES` e `DESCRIPTIONS` migra para lá sem mudar uma palavra.
- **A paginação** (`BoundedPage`) continua como modelo Pydantic.
- **O `ToolRegistry`** valida o contrato (D9) e entrega `RegisteredTool`, com a mesma interface pública:
  `ToolRegistry(...).tools` e `StudentTools.registry()`. A conversão usa `StructuredTool.from_function` sobre o método
  ligado à instância.
- **O ensino:** o `ToolTeaching` lê "aceita" e "exemplo" do `json_schema` inferido (`description`, `enum`, `examples`) e
  vira o `handle_validation_error`, sujeito a P4.
- **Parâmetro desconhecido:** a recusa (`extra="forbid"`) continua.
- **Oráculo:** o snapshot do JSON schema de cada tool (T0) fica idêntico, e o texto de ensino dos casos de
  `tests/unit/agent` fica idêntico.

### 6.4 Bootstrap em dishka (T4)

```python
class AppProvider(Provider):
    scope = Scope.APP
    settings = from_context(provides=Settings)
    database = provide(Database.from_settings)
    clock = provide(SystemClock, provides=Clock)
    ...


class StudentProvider(Provider):
    scope = Scope.REQUEST
    adapter = provide(RepositoryAdapter)
    finance_repository = provide(SqlFinanceRepository, provides=FinanceRepository)
    financial = provide(FinancialService)
    ...
    tools = provide(StudentTools)


class HttpSession(Provider):
    @provide(scope=Scope.REQUEST)
    async def session(self, request: Request, identity: IdentityService) -> StudentSession: ...


class GivenSession(Provider):
    session = from_context(provides=StudentSession, scope=Scope.REQUEST)
```

- **Na API:** `make_async_container(AppProvider(), StudentProvider(), HttpSession(), context={Settings: settings})`,
  com `setup_dishka(container, app)`. O lifespan fecha o container, que também fecha o banco, o Redis e o tracing.
- **No eval e nos testes:** o mesmo container com `GivenSession()`, e
  `async with container(context={StudentSession: s}) as scope: await scope.get(StudentTools)`.
- **O turno do agente:** `ChatAgentScope` deixa de montar as tools. Ele as recebe do escopo REQUEST e continua dono do
  tracing por turno.
- **Rate limit e confirmação de protocolo** viram providers REQUEST. As rotas declaram `FromDishka[ChatRateLimit]`,
  `FromDishka[ChatService]` e `FromDishka[ProtocolConfirmation]`.
- **A rota de login de desenvolvimento** continua condicionada a `settings.dev_login`. O app factory inclui o router só
  quando a flag está ligada.
- **Isolamento:** um teste de unidade novo abre dois escopos REQUEST concorrentes com alunos diferentes, sem banco, e
  prova que `StudentSession`, adapter e services são objetos distintos, enquanto `Database` é o mesmo.

## 7. Consequências

- **Melhora:**
  - menos código: estimativa de cerca de 370 para cerca de 80 linhas no ownership, e de 539 para cerca de 190 no
    bootstrap, mais os dicionários de tradução, `ToolSchema` e `GUIDES`;
  - o repositório escreve só a consulta de navegação;
  - as rotas ficam com a cara padrão do FastAPI;
  - cada peça se explica em uma frase, com nome da indústria.
- **Piora ou encarece:**
  - entra uma dependência (`dishka`);
  - o SQL do ownership passa de `JOIN` com `AND` para `IN` com subquery aninhada, e o plano precisa ser medido (P1);
  - o bootstrap passa a depender de autowiring por tipo: quem lê precisa saber que `provide(X)` olha o construtor de X.
- **Riscos e mitigação:**
  - critério que não entra em algum caso de consulta: mitigado pelo teste de unidade de §6.1, pela varredura de
    invariantes e pelo snapshot de T0;
  - tool com schema diferente mudando o comportamento do modelo: mitigado pelo snapshot de schema;
  - o 401 no provider do dishka: mitigado pelo spike de P5.
- **Não pode mudar:**
  - nenhuma linha de outra pessoa em nenhuma tool (`test_tool_invariants.py`);
  - a partição de sessões (`test_session_partition.py`);
  - o JSON de cada tool para os alunos da amostra de T0;
  - o JSON schema de cada tool;
  - o texto de ensino;
  - as rotas, os status HTTP e os cabeçalhos;
  - o DDL do banco.

## 8. Plano de implementação

| # | Tarefa | Depende de | Arquivos | Fronteira de teste | Pronto quando | Oráculo de verificação |
|---|---|---|---|---|---|---|
| T0 | Fotografia de referência | — | Só o scratchpad, nada no repo | Script descartável | Existem três arquivos gravados a partir do código atual: o JSON de todas as tools para uma amostra fixa de alunos (com 2 matrículas, pagador terceiro, protocolo de responsável e aluno sem LMS); o JSON schema de cada tool; e o `EXPLAIN (ANALYZE, BUFFERS)` das consultas de fatura, pagamento, acordo, tentativas do LMS e interações de protocolo | Os três arquivos existem e são reproduzíveis: duas execuções seguidas dão o mesmo resultado |
| T1 | Ownership por critério global do ORM | T0 | `persistence/core/*`, `persistence/*/ownership.py`, repositórios, `persistence/identity/*`, `bootstrap/app.py` (só a chamada de `assert_complete`), testes de `tests/unit/core` e `tests/integration/core` | Unidade (compilação do SQL, §6.1) e integração | `make check` verde; saem `Via`, `Public` como classe, `Update`, `DeclaredQuery`, `QueryGuard`, `WritePlan` e `ownership_registry.py`; `fetch_declared` não existe mais | O JSON das tools é idêntico ao de T0, a varredura de invariantes está verde e o `EXPLAIN` dentro do limiar de P1, com a tabela antes e depois anotada no Registro |
| T2 | Dialeto reduzido e tipos de coluna | T1 | `persistence/core/column_types.py` (novo), `persistence/*/models.py`, `*_models.py`, mappers, `dialect.py`, `vocabulary.py`, `finance/labels.py`, `core/dialect_lookup.py`, `core/brasilia.py`, repositórios e testes de mapper e dialeto | Unidade (tipos de coluna) e integração | `make check` verde; nenhum `DialectLookup` nem `*_BY_SOURCE` de tradução de coluna sobra; os models declaram tipos do domínio | O JSON das tools é idêntico ao de T0, e o SQL do ownership de uma sessão de amostra é idêntico ao de T1 |
| T3 | Tools com assinatura como fonte da verdade | T0. Espera o T1 só por D14 | `application/agent/tools/*`, `tool_schema.py`, `tool_arguments.py`, `tool_teaching.py`, `langchain_tools.py`, `agent_stream.py` (só se P4 pedir) e `tests/unit/agent` | Unidade | `make check` verde; saem `ToolSchema`, `ParameterGuide`, `GUIDES`, `DESCRIPTIONS` e `SCHEMAS`; a interface `StudentTools.registry().tools` é a mesma | O JSON schema de cada tool é idêntico ao de T0, e o texto de ensino dos casos de teste é idêntico |
| T4 | Bootstrap em dishka | T1 | `bootstrap/*`, `presentation/http/*`, `persistence/core/repository_adapter.py` (só o construtor, P3), `src/evals/driver_factory.py`, `src/evals/student_driver.py`, `tests/integration/support/tools.py`, `tests/integration/conftest.py`, `tests/integration/agent/invariant_sample.py`, `tests/unit/agent/test_agent_providers.py`, `tests/unit/core/test_rate_limit_providers.py`, `pyproject.toml` e `uv.lock` | Unidade (isolamento dos escopos) e integração/e2e | `make check` verde; saem `Singletons`, todos os `*Providers`, `StudentServices`, `ProtocolConfirmationAssembly` e os `build` das rotas | A API sobe com `docker compose up -d --wait api`; com o dev-login de dois alunos, cada um vê só os próprios dados em `/chat` com o modelo `fake` e na confirmação de protocolo; o log mostra um `person_id` por request; `tests/e2e` verde; o eval monta as tools pelo container (uma execução de fumaça com o modelo `fake`, sem rodada de eval) |
| T5 | Detalhes menores | T2, T4 | `domain/shared/money.py` e os usos de `from_cents`; `bootstrap/settings.py` | Unidade | `make check` verde | O JSON das tools é idêntico ao de T0 |
| T6 | Correções em `docs/architecture.md` | T1, T2, T3, T4 | `docs/architecture.md` | Leitura | Os trechos de código e as decisões B29, B31, B32, B33 e B36 batem com o código; o resto do documento não muda | Cada trecho citado em §5.1 a §5.3 existe no código com o mesmo formato |

### Ondas e paralelismo

- **Onda 0:** T0. É a referência de comportamento de todas as outras.
- **Onda 1:** T1, sozinha, por D14.
- **Onda 2:** T2, T3 e T4, em paralelo.
  - Os arquivos são disjuntos: T2 fica nos pacotes de sistema da persistence; T3 em `application/agent`; T4 em
    `bootstrap`, `presentation`, `src/evals`, no apoio dos testes e no construtor do adapter.
  - T3 mantém a interface `StudentTools.registry().tools` que T4 consome.
  - T2 não toca `repository_adapter.py`.
- **Onda 3:** T5 e T6, com arquivos disjuntos.
- **Caminho crítico:** T0 → T1 → T4 → T5 e T6.

## 9. Para o agente executor

- **Comece por:** T0, e depois T1.
- **Leia antes:**
  - `docs/architecture.md`, §3 e §5.2;
  - `CLAUDE.md`;
  - os mapas `persistence/*/ownership.py`;
  - `tests/integration/agent/test_tool_invariants.py`.
- **Leia sempre:** este arquivo inteiro, com o Registro.
- **Não toque:**
  - os arquivos do dono listados no cabeçalho;
  - os prompts e as skills do agente (`application/agent/prompts`, `application/agent/skills`);
  - o texto das docstrings e das descrições de tool, que só muda de lugar;
  - o DDL em `db/init/`.
- **Gates:**
  - sem commit; o commit é do dono;
  - review por pontos numerados;
  - decisão nova é confirmada com o dono, editada aqui e anotada em "Mudança no spec" antes de virar código;
  - `make check-fast` no loop e `make check` ao fechar cada tarefa;
  - o oráculo de T0 ao fechar cada tarefa;
  - rodada de eval só com pedido do dono.
- **Iteração:** perguntas ao dono em lote, numeradas, com a sua recomendação em cada uma.

## Notas de implementação

- `Settings.from_environment` fica. O Pyright recusa `Settings()` direto ("Argument missing for parameter
  "database_url""), porque o pydantic-settings preenche o campo pelo ambiente e o tipo não sabe disso.

## Fontes

[^criteria]: SQLAlchemy, "Adding global WHERE / ON criteria",
    https://docs.sqlalchemy.org/en/20/orm/queryguide/api.html#adding-global-where-on-criteria. O comportamento foi
    conferido com spike no SQLAlchemy 2.1.8, em 2026-11-09: o critério entra em subquery, `JOIN` e `UPDATE`, e a flag em
    `execution_options` funciona tanto no statement quanto no `execute`.
[^overrides]: tiangolo, PR fastapi/fastapi#5452, comentário de 2025-06-17: "The current intention of dependency
    overrides is mainly for tests." Conferido na API do GitHub em 2026-11-09.

A pesquisa comparou as opções nativas do FastAPI, `fastapi-injectable`, `fast-depends`, `dishka`, `dependency-injector`
e `svcs`, em 2026-11-09. O `dishka` 1.10.1 foi testado num venv isolado com 4 escopos REQUEST concorrentes fora do
HTTP. O `dependency-injector` foi descartado: não tem escopo de request nos docs e a rota importa o container. O `svcs`
foi descartado por ser um service locator.

## Execução

### Execução de 2026-11-09

#### Registro de decisões

Repo: este, na branch `refactor/simplificacao-idiomatica`, que nasceu da `main` em `e983e40`.

Escopo desta execução, na ordem:

1. a fotografia de referência, no scratchpad;
2. o ownership pelo critério global do ORM;
3. em paralelo, o dialeto com tipos de coluna, as tools pela assinatura e o bootstrap em dishka;
4. os detalhes menores e as correções no `architecture.md`.

O ownership depende da fotografia. O dialeto e o bootstrap dependem do ownership. As tools dependem só da fotografia,
mas esperam o ownership pela ordem combinada. Os detalhes menores dependem do dialeto e do bootstrap. As correções no
`architecture.md` dependem de todas.

| Decisão | Por quê | Quem decidiu | Tipo | Se mudar, afeta | Commit |
|---|---|---|---|---|---|
| Um commit local por tarefa aceita, sem push e sem PR (o spec dizia "sem commit") | Três implementadores dividem a mesma árvore na segunda onda, e o commit isola cada entrega para review e rollback | você | pilar | nada além da forma de entrega | — |
| Os testes existentes mantêm as asserções. Mudam só o setup e os imports | O que você pediu: os testes são a rede de segurança da refatoração | você | pilar | todas as tarefas | — |
| Saem só os testes cujo assunto o spec remove: QueryGuard, "tabela filha exige JOIN com o pai", consulta privada não declarada e recusa de `Update`. Cada um fica listado nos checkpoints com o motivo, e o teste de seis casos com SQL compilado entra no lugar | O comportamento que eles afirmam deixa de existir por decisão do spec | você | pilar | o ownership | — |
| Valem as recomendações do spec: limiar de 1,2× no p95 e nenhum `Seq Scan` novo; remover os `JOIN` que só serviam ao ownership; manter o `RepositoryAdapter` recebendo `Database`; o ensino vira `handle_validation_error`, ou continua dentro do `call` se o artifact se perder; o 401 sai do provider do dishka, ou de um middleware se o spike falhar | Recomendações do próprio spec, aceitas na abertura | você | pilar | o ownership, as tools e o bootstrap | — |
| Pré-voo e preflight pulados. Vale a checagem do ambiente da abertura: API, banco, Redis e front saudáveis | As decisões estavam batidas no spec e o ambiente estava de pé | você | detalhe | nada | — |
| O listener do ownership recusa com `OwnershipError` a consulta que lê um model sem entrada no mapa, e não só confia na checagem de subida. O `write` continua recusando lote de tabela sem regra | É fail closed, como o spec pede. Mantém com a mesma asserção os testes "tabela sem declaração é recusada" e "lote de tabela não registrada não escreve nada" | o dono | detalhe | o ownership | — |
| A proteção contra SQL livre (`suffix_with`, `text`, funções fora da lista) sai junto com o `QueryGuard`, sem substituto | Decisão batida no spec: o agente e o usuário não escrevem SQL | spec | detalhe | o ownership | — |
| A regra das interações de protocolo vira `protocol_id IN (select dos protocolos)` mais o filtro de nota interna, numa expressão só | Hoje o filtro de nota interna mora dentro do `Via`. Sem ele, a nota interna voltaria a aparecer | o dono | detalhe | o ownership e o dialeto | — |
| O adapter ganhou um terceiro método, `fetch_rows`, que devolve linhas em tupla. As consultas do pagador e do nome do requerente devolvem `(ContractRow, texto)`, e o `fetch` só devolve a primeira coluna | Mantém a asserção do teste do pagador sem mexer no model. É o antigo `fetch_declared` sem a declaração | o implementador, aceito pelo dono | detalhe, mas entra no plano de review | o ownership | f51cfcf |
| O listener do ownership é registrado em `database.py`, sobre `AsyncSession.sync_session_class`, que é a própria classe `Session` | O `ruff.toml` bane importar `sqlalchemy.orm.Session`, e só três arquivos podem importar `sqlalchemy.ext.asyncio` | o implementador, aceito pelo dono | detalhe | o ownership | f51cfcf |
| O listener também recusa `SELECT`, `UPDATE` e `DELETE` que não são do ORM (tabela Core sozinha). Já uma tabela Core ou um alias Core no `FROM`, ao lado de um model, passa sem filtro. A sonda tirou CPFs alheios assim, e o `QueryGuard` antigo recusava. Nenhum código de produção monta essa consulta | O spec decidiu que o `QueryGuard` sai sem substituto: o agente e o usuário não escrevem SQL, e o review cobre o desenvolvedor | spec, confirmado pelo dono | detalhe, mas entra no plano de review | o ownership | f51cfcf |
| O health check do banco roda com `skip_ownership` | Ele abre sessão sem aluno, e o fail closed derrubaria o health | o implementador, aceito pelo dono | detalhe | o ownership | f51cfcf |
| Na segunda onda, cada tarefa roda num worktree próprio, criado a partir do commit do ownership: `../cruzeiro-do-sul-wt/{dialeto,tools,bootstrap}`. Cada commit entra depois na branch da execução por cherry-pick. A suíte com banco roda sob `flock`, uma de cada vez | A fotografia de referência passa por arquivos de mais de uma tarefa, e duas suítes `-n 4` ao mesmo tempo esgotaram as 100 conexões do Postgres | o dono | detalhe | a segunda onda | — |
| A partir da segunda onda, a execução economiza tokens. Os três implementadores foram retomados de onde pararam, sem começar do zero. Os dois revisores por tarefa saíram: o dono confere a fotografia e roda o `make check` de cada entrega, e um revisor de código só, em Sonnet, olha a onda inteira no fim. Os detalhes menores o dono faz direto, e as correções do `architecture.md` vão para um agente Sonnet | Você pediu para fechar com os cerca de 70% de limite que restavam. A fotografia e o `make check` já são a prova de comportamento igual | você | detalhe | a segunda e a terceira ondas | — |
| Nas tools, o texto de ensino ("aceita" e "exemplo") sai das tabelas `GUIDES` e entra na assinatura como um marcador próprio dentro do `Annotated`, ao lado do `Field`. Ele não vai para o JSON schema, e o ensino o lê da assinatura | O spec pede duas coisas que se excluem: o ensino ler "aceita" e "exemplo" do JSON schema, e o JSON schema ficar idêntico. Hoje esses textos nunca vão ao modelo, só à mensagem de erro. Pôr `examples` no `Field` mudaria o que o modelo recebe | o dono | detalhe, mas entra no plano de review | as tools | — |
| A validação dos argumentos continua dentro do `call` da tool, com o modelo inferido da assinatura e o mesmo texto de ensino | O `handle_validation_error` do langchain-core 1.7.6 devolve só a string, sem o `ToolExecution`, e a mensagem sai com `status="error"` e duração 0. É a alternativa já escrita no spec para esse caso | o dono | detalhe | as tools | — |
| O schema que conta como "idêntico" é o JSON que vai ao modelo (`convert_to_openai_tool`). Diferença só no `args_schema` cru, como `title`, é aceita se o JSON do modelo não muda, e fica explicada no checkpoint | É o que o modelo vê. O `bind_tools` do LangChain usa essa conversão | o dono | detalhe | as tools | — |
| No dialeto, entram também como tipo de coluna o epoch em texto do LMS e o booleano em texto com o literal de cada sistema ("Y" no SAG, "True" na secretaria e no financeiro). Inteiro e decimal em texto viram tipo só se isso simplificar o mapper. As tabelas Core sem model (requerente, CPF, pagador) continuam comparando texto cru, e suas constantes vão para o dialeto do sistema que as usa | São variantes dos casos que o spec já lista. As tabelas Core não têm model para receber tipo | o dono | detalhe | o dialeto | — |
| O fuso de Brasília passa a `ZoneInfo("America/Sao_Paulo")` só se a saída das tools ficar idêntica à fotografia. Antes de 2019 havia horário de verão, e o offset fixo de −3 e a zona dão horas diferentes para datas antigas. Se der diferença, o offset fixo fica, com o motivo no checkpoint. O `BRASILIA` do domínio, em `domain/protocol/opening.py`, não muda | O critério de pronto é comportamento idêntico | o dono | detalhe | o dialeto e os detalhes menores | — |

## Registro

### 2026-11-09 — Checkpoint de implementação: fotografia de referência

Nada mudou no repo. A fotografia mora no scratchpad da sessão
(`/tmp/claude-1000/-home-vinicius-interviews-cruzeiro-do-sul/5db92a5a-3e22-498c-9b5f-b254d9cf8fca/scratchpad/oraculo/`). O
`README.md` desse diretório lista os pontos de entrada do código que o script usa e o que adaptar quando um deles mudar
de forma.

| Critério | Evidência |
|---|---|
| Saída de todas as tools para uma amostra fixa de alunos | `base/tools_output.json`, com sete alunos: dois com duas matrículas (3000178 e 3000471), dois com pagador terceiro e protocolo de responsável (3000096 e 3000003), um sem LMS e sem protocolo (3000020) e dois comuns (3000021 e 3000336). Inclui as caminhadas paginadas com páginas de 3 e de 100 |
| JSON schema de cada tool | `base/tool_schemas.json`, 19 tools, com o JSON que vai ao modelo (`convert_to_openai_tool`) e os schemas de argumento |
| `EXPLAIN (ANALYZE, BUFFERS)` de fatura, pagamento, acordo, tentativas do LMS e interações de protocolo | `base/explain/`, com o aluno 3000178, mais as duas consultas da cascata de protocolos. Há o plano na forma estável, o completo para leitura e 30 execuções por consulta em `timings.json` |
| Reproduzível | `snapshot.py base` e `snapshot.py base2` seguidos; `compare.sh base base2` sem diferença, com saída 0 (conferido pelo dono) |

Notas:

- O script roda com `PYTHONHASHSEED=0`. O SQL atual emite o `IN (...)` na ordem de um `frozenset` de chaves de
  matrícula, e essa ordem varia entre processos.
- O assinador de proposta usa um segredo fixo só no script. Assim o token de `propose_protocol` sai estável.
- Depois do ownership e do dialeto, o `.sql` e o plano mudam por desenho. O oráculo deles é o `p95.py`, com o limiar de
  1,2× e nenhum `Seq Scan` novo. As consultas rodam abaixo de 1 ms, então a razão oscila: entre duas fotografias do
  mesmo código ela ficou entre 0,19 e 0,86. Estouro do limiar é confirmado repetindo a fotografia antes de reprovar.

### 2026-11-09 — Checkpoint de implementação: ownership pelo critério global do ORM

Commit `f51cfcf`, com 32 arquivos: saem 375 linhas e entram 164. O ownership em `persistence/core` caiu de cerca de 300
para 157 linhas.

| Critério | Evidência |
|---|---|
| `make check` verde | Rodado pelo dono, sozinho no banco: "All checks passed!" e 1612 passed, 8 skipped |
| Saem `Via`, `Public` como classe, `Update`, `DeclaredQuery`, `QueryGuard`, `WritePlan`, `ownership_registry.py` e `fetch_declared` | Grep sem resto em `src`, `tests` e `tools`, conferido pelo revisor de código |
| JSON das tools idêntico ao da fotografia | `cmp` em `tools_output.json` e `tool_schemas.json`, sem diferença (conferido pelo dono) |
| `EXPLAIN` dentro do limiar | Tabela abaixo. Nenhuma consulta acima de 1,2× e nenhum `Seq Scan` novo |
| Varredura de invariantes e partição de sessões verdes | 32 passed com o implementador. 166 passed com o revisor de comportamento, junto com e2e, core, identity e protocol |
| Isolamento no ambiente real | Login de dois alunos na API: cada conversa foi gravada com o dono do token, e a conversa de um aluno dá 404 para o outro. Sonda adversarial com cinco alunos e onze formas de consulta (sem `JOIN`, `JOIN` errado, alias, subquery, union, count, exists, update): nenhuma linha alheia pelo ORM. Logs da API sem erro |

| Consulta | p95 antes (ms) | p95 depois (ms) | Razão |
|---|---|---|---|
| Faturas | 0,235 | 0,118 | 0,50 |
| Pagamentos | 0,361 | 0,300 | 0,83 |
| Acordos | 0,134 | 0,056 | 0,42 |
| Tentativas do LMS | 0,190 | 0,029 | 0,15 |
| Interações de protocolo | 0,306 | 0,249 | 0,81 |
| Protocolo, na cascata | 0,433 | 0,203 | 0,47 |
| Lista de protocolos, na cascata | 0,440 | 0,217 | 0,49 |

Testes removidos, porque o spec remove o assunto deles:

- `tests/unit/core/test_query_guard.py`, o arquivo inteiro: o `QueryGuard` sai.
- Em `test_repository_adapter.py`:
  - os três testes de "tabela filha exige `JOIN` com o pai", porque a filha agora sai filtrada sozinha;
  - o teste do guard contra `suffix_with`;
  - os dois testes de consulta privada não declarada e de consulta sem raiz.
- Em `test_adapter_write.py`, os dois testes de recusa de `Update` em tabela filha e em tabela pública. O `UPDATE` agora
  recebe o critério.

Os testes que ficaram mantêm as asserções. Dois foram renomeados porque o nome citava a consulta declarada: viraram
`test_payer_query_keeps_the_ownership_of_the_root` e `test_payer_query_of_an_empty_session_sees_nothing`. Num deles, a
chamada dentro do `assert` trocou `fetch_declared` por `fetch_rows`, com o mesmo valor esperado.

O teste novo `tests/unit/core/test_ownership_criteria.py` compila o SQL sem banco e cobre oito casos:

- filha sem `JOIN`;
- `JOIN` com condição errada;
- `UPDATE`;
- `skip_ownership`;
- sessão sem aluno;
- tabela `PUBLIC`;
- tabela Core recusada;
- listener instalado.

Com o listener desligado, cinco desses casos falham.

### 2026-11-09 — Checkpoint de implementação: segunda onda e detalhes menores

Commits: `c943edd` (tools), `9bd6872` (dialeto), `2e2af94` (bootstrap em dishka) e `6c83b9d` (`from_cents`). Cada tarefa
rodou num worktree próprio e entrou na branch por cherry-pick, sem conflito.

| Critério | Evidência |
|---|---|
| `make check` verde com tudo junto | Rodado pelo dono, sozinho no banco: "All checks passed!", 7 contratos mantidos, mypy e Pyright sem erro e 1631 passed, 8 skipped |
| JSON das tools e schema idênticos à fotografia | Fotografia do código juntado (`oraculo/onda2`): `cmp` sem diferença nos dois arquivos (conferido pelo dono) |
| SQL do ownership igual ao do ownership aceito | Os sete `.sql` de `onda2` são iguais aos do ownership. p95 sem consulta acima de 1,2× e sem `Seq Scan` novo |
| Tools: saem `ToolSchema`, `ParameterGuide`, `GUIDES`, `DESCRIPTIONS` e `SCHEMAS` | Arquivo `tool_schema.py` removido. O ensino virou o marcador `Teaching` dentro do `Annotated`. O texto de ensino de 233 chamadas, erradas e certas, ficou idêntico antes e depois |
| Dialeto: nenhum `DialectLookup` nem `*_BY_SOURCE` de coluna; os models declaram tipos do domínio | Grep vazio em `persistence`. Tipos em `core/column_types.py`, `core/source_enum.py` e `column_types.py` por sistema. Nenhum DDL mudou |
| Bootstrap: saem `Singletons`, os `*Providers` de montagem à mão, `StudentServices`, `ProtocolConfirmationAssembly` e os `build` das rotas | Removidos. O container serve a API, o eval e os testes. Teste novo com dois escopos REQUEST concorrentes: sessão, adapter e services distintos, `Database` o mesmo |
| A API sobe e isola dois alunos | `docker compose up -d --build --wait api` saudável. Dev-login de dois alunos, conversa de um dá 404 para o outro, sem token dá 401 com `WWW-Authenticate: Bearer`, logs sem erro (verificado pelo dono). O `/chat` não foi chamado porque o modelo do `.env` é o real; o fluxo com o modelo `fake` está no `tests/e2e`, verde |
| O eval monta as tools pelo container | Fumaça com o modelo `fake`: 14 eventos até `AgentFinished`, tool `get_financial_summary`, sem rodada de eval |
| `from_cents` sai | Os usos passaram ao construtor, que é idêntico. `Settings.from_environment` fica (Notas de implementação) |

Testes removidos ou com a fonte do esperado trocada, porque o spec remove o objeto:

- `test_the_schema_is_cached_by_function_never_by_bound_method`: o cache `SCHEMAS` sai. A intenção volta no teste novo
  `test_the_model_is_inferred_once_per_function_never_per_student`.
- O esperado de dois testes de schema passou a vir da assinatura e de um dado fixo, no lugar de `ToolSchema` e
  `DESCRIPTIONS`.
- No bootstrap, as asserções que liam `Singletons` passaram a ler o mesmo objeto do container, como
  `await c.get(AgentRuntime) is await c.get(AgentRuntime)`.
- Os usos de `Money.from_cents(n)` nos testes viraram `Money(n)`.

Diferenças conhecidas, que vão para o plano de review:

- O comportamento HTTP mudou num caso de borda. Sem token e com corpo inválido, a rota responde 422; antes respondia
  401. O dishka resolve a sessão depois de o FastAPI validar o corpo.
- O OpenAPI deixou de declarar o esquema Bearer.
- O tipo de enum é um `TypeDecorator` próprio (`SourceEnum`) em todos os casos, e não o `sqlalchemy.Enum` de D7. O
  `Enum` levantaria `LookupError` em vez de `UnknownDialectValueError` e mudaria o bind no SQL.
- O dono acrescentou o tipo `BlankableIsoDate` no `validto` do contrato, porque o vazio virava "sem data" e passaria a
  dar erro.
- O fuso de Brasília passou a ser a zona `America/Sao_Paulo`. Todos os timestamps do banco são de 2021 em diante, e a
  saída ficou idêntica.
- As tools têm um `functools.cache` por função no modelo de argumentos. Sem ele, montar o schema a cada turno bloqueia o
  event loop e quebra o teste de turnos simultâneos.

### 2026-11-09 — Checkpoint de implementação: correções no architecture.md e review da segunda onda

Commit do `docs/architecture.md` (T6). Mudaram só §5.1, §5.2, §5.3 e as decisões B29, B31, B32, B33 e B36.

| Critério | Evidência |
|---|---|
| Os trechos de §5.1 a §5.3 batem com o código | Revisor Sonnet conferiu cada bloco contra `src/api`. Duas correções: o `event.listen` passou a citar `persistence/core/database.py`, onde ele mora; e "Custos aceitos" deixou de atribuir a recusa de `text()` ao listener, porque quem a barra é o `ruff.toml` |
| `make check` verde | "All checks passed!", mypy e Pyright sem erro e 1631 passed, 8 skipped |

O review da segunda onda rodou com três revisores Sonnet, um por commit (tools, dialeto, bootstrap e `from_cents`), só leitura. Nenhum achado de severidade alta. Nada foi mudado; os pontos abaixo esperam decisão do dono.

1. **Bootstrap, média-baixa.** `bootstrap/lifespan.py`: o `container.close()` fica depois do `yield`, sem `try/finally`, e o aquecimento roda antes. Se um `get` do aquecimento falhar, o Redis e o pool já abertos não fecham. A correção é um `try/finally` em volta do aquecimento e do `yield`.
2. **Bootstrap, baixa.** As duas diferenças conhecidas (422 em vez de 401 sem token e com corpo inválido; OpenAPI sem Bearer) têm correção de cerca de 10 linhas. Seria uma subclasse de `HTTPBearer` que levanta `Unauthorized`, como `dependencies=[Security(...)]` nos routers autenticados. O FastAPI resolve dependência antes do erro de corpo.
3. **Bootstrap, baixa.** Containers criados nos testes sem `close()` (`agent_of.py`, `test_agent_providers.py`, `test_container_scopes.py`).
4. **Bootstrap, risco latente.** O escopo REQUEST fecha antes de o `StreamingResponse` do `/chat` terminar. Hoje nenhum provider REQUEST tem finalizer, então não falha.
5. **Tools, baixa.** `LIST_SEPARATOR` e `PATH_SEPARATOR` estão duplicados em `tool_arguments.py` e `tool_teaching.py`.
6. **Tools, baixa.** A troca implícita de `PageRequest` por `PageArgument` em `ToolArguments._inferred`. As tools poderiam declarar `PageArgument` na assinatura, o que seria mais fiel a D8.
7. **Tools, baixa.** `tests/unit/agent/test_tool_schema.py` ainda tem o nome do módulo removido.
8. **Dialeto, baixa.** `TextFlag` lê qualquer texto diferente do literal verdadeiro como `False`, sem erro. O código antigo fazia o mesmo.
9. **Dialeto, baixa.** O erro de valor desconhecido sai de dentro do result processor, só com o valor, sem o nome do campo que o `DialectLookup` dava.
10. **Dialeto, baixa.** Instâncias de tipo repetidas: `SourceEnum.by_name(EnrollmentStatus)` 3×, `by_name(Shift)` 3× e `TextFlag("True", "False")` 2×. Poderiam virar constantes.
11. **Dialeto, baixa.** A zona `America/Sao_Paulo` depende do zoneinfo do sistema. A imagem atual tem, e foi conferido no container. Declarar `tzdata` no `pyproject.toml` tiraria a dependência da imagem.

Conferido sem defeito:

- nada por aluno em escopo APP;
- o cache do modelo de argumentos é por função, sem estado de aluno;
- docstrings das tools intactas;
- todos os `TypeDecorator` com `cache_ok` e `None` tratado;
- colunas dos índices de expressão continuam `str`;
- a escrita grava os mesmos valores;
- DDL intocado;
- sem sobra de `Singletons`, `*Providers` antigos, `Router.build`, `DialectLookup`, `*_BY_SOURCE`, `BrasiliaTime`, `ToolSchema`, `GUIDES` ou `from_cents`.

### 2026-11-09 — Checkpoint de implementação: fixes do review e limpeza do dialeto

O dono liberou todos os pontos do review e pediu atenção especial ao dialeto. Cada frente rodou num worktree próprio a partir de `e70cc16`: tools e bootstrap com Sonnet, dialeto com Opus. Entraram na branch por cherry-pick, num worktree de integração. O repo principal tinha sido trocado para a `main` durante a execução.

| Commit | O que entrou |
|---|---|
| `5db3588` | Pontos 5 a 7: os separadores ficaram num lugar só; as tools paginadas declaram `page: PageArgument` na assinatura, e a troca implícita saiu de `_inferred`; `test_tool_schema.py` virou `test_langchain_tools.py` |
| `03e4adf` | Pontos 1 a 3: o lifespan fecha o container num `AsyncExitStack`, porque o WPS229 barra o `try` com corpo grande, e isso cobre também a falha no aquecimento; `RequiredBearer` como `Security` nos routers de chat e de confirmação devolve o 401 antes do 422 e o Bearer no OpenAPI; os containers dos testes fecham |
| `18ec3eb` | Pontos 8 a 11: `TextFlag` estrito, depois de medir no banco que só aparecem os dois literais por coluna; o erro nomeia o vocabulário, como em "valor fora do vocabulário InvoiceStatus: 'WAIVED'"; tipos repetidos viraram constantes; `tzdata` entrou no `pyproject.toml` |
| `28e6462` | Limpeza do dialeto (detalhada abaixo) |

O que mudou na limpeza do dialeto:

- `member_of` duplicava `from_source` e saiu;
- os mapas reversos passaram a usar `SourceEnum.inverse_of`;
- o formato da marca do SAG ficou só em `SagDialect.source_brand`, que a secretaria também usa;
- as constantes duplicadas da secretaria se juntaram;
- os tipos configurados ficaram todos no `column_types.py` do sistema, e foi criado `finance/column_types.py`;
- `CourseLabel.by_course` e `LmsDialect.user_key` saíram dos mappers;
- `enrollment_key` foi para dentro do seu único chamador.

| Critério | Evidência |
|---|---|
| Comportamento idêntico | Fotografia do código juntado (`oraculo-integ` no scratchpad desta sessão): `tools_output.json` e `tool_schemas.json` iguais à base, e os 7 `.sql` iguais aos de `onda2` |
| `make check` verde | "All checks passed!", 7 contratos mantidos, mypy e Pyright sem erro e 1638 passed, 8 skipped |

O ponto 4 (o escopo REQUEST fecha antes do fim do streaming) fica registrado, sem correção: hoje nenhum provider REQUEST tem finalizer.

Propostas de desenho do dialeto, não aplicadas:

1. "Student", "Alumni" e "Guardian" aparecem no dialeto e no `REQUESTER` de `column_types`.
2. O formato `brand:student_id` é montado na persistence e lido na application. Poderia virar um objeto de valor do domínio.
3. O `tenant_id` do LMS poderia ser coluna tipada `Brand`, o que mexe no ownership.
4. O `NOT_A_DIGIT` se repete em três lugares.
