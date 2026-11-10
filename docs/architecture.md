---
type: Architecture
title: Arquitetura do agente de atendimento ao aluno
description: Decisões, desenho e restrições da API que dá ao agente acesso seguro e normalizado aos quatro sistemas do grupo educacional.
tags: [arquitetura, api, isolamento, normalizacao, agente]
status: stable
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T23:30:00Z }
verified: { by: human:vinicius, at: 2026-11-05T02:53:00Z }
sources:
  - id: readme
    resource: /docs/diretrizes.md
    title: Enunciado do case
  - id: eda
    resource: /docs/eda.md
    title: Análise exploratória dos dados
  - id: carga
    resource: /db/init/01_load.sh
    title: Script de carga dos CSVs
---

# Arquitetura do agente de atendimento ao aluno

> **Estado:** verificado. A seção 3 traz as decisões; a seção 5, o desenho como está no código.
>
> **Medições:** consultas no banco local e protótipos, em 2026-11-04 e 2026-11-05, salvo onde indicado. Latências
> foram medidas em execução sequencial; não são resultado de teste de carga. A latência do agente, medida no eval, está no
> [README](/README.md#latência-e-custo).

## Para o humano

- **O problema:** dar ao agente uma visão única e segura de quatro sistemas que descrevem as mesmas
  entidades de formas diferentes. O agente é a parte fácil. O diferencial está na API.
- **Diferencial 1, isolamento:** um adapter de repositório acrescenta `AND <dono>` em toda consulta, com valores
  vindos da sessão. Parâmetros só navegam dentro do que o aluno já pode ver, ou em tabelas sem dono.
- **Diferencial 2, modelo canônico:** o domínio tem a linguagem nossa. Cada sistema traduz o próprio dialeto.
- **Postura de segurança:** menor privilégio. O agente não tem ferramenta para ações destrutivas nem parâmetro
  que amplie o acesso. Ele ainda pode interpretar mal um dado; esse risco é tratado à parte (seção 7).
- **Por onde começar:** seção 3 (decisões) e seção 5.2 (isolamento).

## 1. O problema

O agente responde sobre vida acadêmica, financeiro, protocolos e LMS, além de abrir solicitações. Isso deve
funcionar para milhares de alunos simultâneos, sem vazamento entre alunos e sem vazamento de dados corporativos,
com respostas fiéis aos dados.[^readme] A identidade vem da sessão e nunca do texto da conversa.[^readme]

Três problemas cabem à API:

1. **Identificar:** descobrir quais registros de cada sistema pertencem à pessoa autenticada.
2. **Isolar:** garantir que nenhuma consulta devolva dados de outra pessoa, mesmo com um agente comprometido.
3. **Normalizar:** devolver sempre a mesma grafia e o mesmo formato, seja qual for o sistema de origem.

## 2. Vocabulário

| Termo | Significado |
|---|---|
| **Pessoa** | Um ser humano, identificado pelo CPF canônico. Pode ter vários `PERSON_ID` e várias matrículas. |
| **Matrícula** | Vínculo da pessoa com um curso, identificado por marca, modalidade e número do aluno. |
| **Marca** | Uma das 5 instituições, sem modalidade. |
| **Modalidade** | Presencial ou EAD. |
| **`StudentSession`** | Objeto imutável, montado a cada pedido, com a pessoa autenticada e os identificadores dela em cada sistema. |
| **Ownership** | Cláusula que restringe uma tabela ao que pertence à pessoa da sessão. |
| **Dialeto** | Forma como um sistema escreve uma entidade ou chave. |

Evitar **tenant** sem qualificação: no LMS, `mdl_tenant` significa marca. Evitar **session** sem qualificação:
o termo colide com a sessão de banco do SQLAlchemy.

## 3. Decisões tomadas

| # | Decisão | Motivo |
|---|---|---|
| B1 | Python e FastAPI, com qualidade de produção | Mostrar a construção de uma API escalável e resiliente |
| B2 | Assíncrono de ponta a ponta, log estruturado, validação de entrada e saída, injeção de dependência, orientação a objetos | Requisitos de produção |
| B3 | Camadas: bootstrap, presentation, application, domain, persistence, infrastructure e banco | Separar negócio de tecnologia |
| B4 | O domínio não depende de ninguém; dependência externa entra por inversão de dependência | Evita o ciclo entre domínio e persistência |
| B5 | O isolamento é por pessoa. Com N matrículas, ela consulta as N na mesma sessão | 37 CPFs têm 2 matrículas |
| B6 | A sessão vem do token e é montada a cada pedido, sem cache por enquanto | Simplicidade; custo medido em A5 |
| B7 | O `WHERE` de ownership é montado a partir da sessão, nunca a partir de parâmetros. Parâmetros apenas navegam nos dados ou consultam tabelas sem dono | É a garantia central de isolamento |
| B8 | Financeiro sempre filtra por contrato, nunca por pagador | 17 pagadores cobrem 44 matrículas de pessoas diferentes |
| B9 | Segurança em código, sem RLS. Em um sistema real as tabelas já existem e talvez nem estejam em Postgres | Não depender de recurso de um banco específico; o repositório central e bem testado é a garantia |
| B10 | Menor privilégio: o agente só tem as ferramentas de que precisa, sem ações destrutivas e sem parâmetro que amplie acesso | Segurança por arquitetura |
| B11 | Não se alteram dados nem colunas recebidas. São permitidos índices e as PKs e FKs do enunciado | Mudam a física e a integridade, não o conteúdo |
| B12 | Schemas `sag`, `lms`, `secretary`, `finance`, sem prefixo `raw_` | Aplicado na carga |
| B13 | Role restrita para a API, nunca superuser | Menor privilégio também no banco |
| B14 | Schema novo `agent` para conversas, logs e auditoria | Separar dados do agente dos dados de origem |
| B15 | Escrita de negócio vai nas tabelas recebidas. As regras ficam no domínio: muda em memória e depois persiste. Por enquanto a escrita se limita a abrir protocolo | O domínio é dono das regras; escopo pequeno |
| B16 | Modelo canônico nosso; enums no domínio e um tradutor por sistema na persistência, sem `BrandUtil` central | Tradução depende do sistema de origem |
| B17 | Tudo que sai para o agente é um DTO estruturado, com uma única grafia | O agente não lida com variações |
| B18 | As tools chamam os services com parâmetros amigáveis, traduzidos para o modelo interno | A camada de application é a superfície do agente |
| B19 | Agente baseado em tools e skills; o eval avalia o conjunto e iteramos nos dois | Melhoria guiada por medição |
| B20 | Arquitetura simples, que cresce conforme a necessidade | Critério 80/20 |
| B21 | SQLAlchemy ORM assíncrono, com um model por tabela e um mapper por entidade de domínio | É a forma mais legível e simples; evita `.c`, usa nomes nossos e mantém a composição segura de consultas |
| B22 | Entidades de domínio só com os campos necessários | Campo não carregado não vaza |
| B23 | `JOIN` entre sistemas é permitido quando simplifica, sempre respeitando o ownership de cada tabela | Conhecemos o sistema e preferimos simplicidade; aceito o acoplamento ao mesmo banco nessas consultas |
| B24 | As 5 FKs com violação são criadas com `NOT VALID` | A regra vale para linhas novas e os dados recebidos ficam intactos |
| B25 | O agente roda no mesmo processo da API | Menos latência e nenhuma propagação de identidade |
| B26 | Abrir protocolo cria 3 linhas em 2 passos, com aprovação humana: a proposta aparece na interface, o aluno aprova no card, com a mensagem e a palavra de confirmação, e outro endpoint, fora do LLM, grava | O LLM não efetiva escrita sozinho |
| B27 | O agente só abre serviço sem taxa e compatível com a situação da matrícula. Nos 4 com taxa, orienta a procurar a secretaria | Evita protocolo pago sem fatura |
| B28 | Protocolos abertos por terceiros e casos ambíguos: ninguém vê | *Fail closed* |
| B29 | Um listener `do_orm_execute` acrescenta o `AND` de ownership em toda consulta com `with_loader_criteria`, a partir de um mapa estático por model e dos identificadores da sessão (5.2) | Mesma garantia com menos conceitos, sem depender de lembrar do filtro |
| B30 | O aluno vê os 73 protocolos abertos por responsável com o ID dele, sem os dados do responsável | O protocolo é dele; os dados do responsável não |
| B31 | Models não usam `relationship()`; toda relação é um `JOIN` explícito | Era o carregamento do relationship que gerava consulta fora do adapter: o pagador de um aluno devolveu 7 contratos, sendo só 1 dele. O critério global agora o filtra também; o banimento fica por legibilidade e está no `ruff.toml` |
| B32 | Não há guard de consultas: o critério global entra por fora do que o repositório escreve, e só passa consulta ORM sobre model declarado | Com lista de proibidos, `suffix_with("OR true")` devolveu as faturas de todos os alunos; o critério é acrescentado com `AND`, então não há construto a proibir |
| B33 | Cada tabela se filtra sozinha: a filha declara `Filho.fk.in_(select(Pai.id))` e o próprio critério restringe o pai | `JOIN` com condição errada trouxe pagamentos de terceiros; com a regra por tabela, o `JOIN` errado continua sem vazar |
| B34 | A API fica em `src/api/`; `src/app/` é reservada para o front-end | Separar os dois produtos no repositório |
| B35 | O aluno vê nome e e-mail institucional dos professores da disciplina no semestre, na marca dele; CPF e demais dados de professor ficam fora | Decisão do dono do projeto; o contato com o professor não é dado sensível |
| B36 | `bootstrap/` é o composition root: o único módulo que conhece todas as camadas. Monta os singletons na subida (escopo `APP`) e o grafo por aluno a cada request (escopo `REQUEST`) com um container dishka; as rotas usam `DishkaRoute` e `FromDishka` | A montagem precisa conhecer a persistence e as camadas de cima; fora dele, nenhuma camada conhece a vizinha. É o papel do "Main" da Clean Architecture e do `bootstrap.py` do Cosmic Python |
| B37 | A `StudentSession` é imutável e nasce numa dependência de escopo de request: JWT, depois `person_id`, depois a carga dos identificadores. Não existe sessão vazia preenchida depois | Uma sessão vazia lida antes de ser preenchida abriria a consulta; criada pronta, a falha é fechada. Equivale ao escopo `REQUEST` do NestJS |
| B38 | `infrastructure/` guarda os adaptadores técnicos que não são banco (relógio, cliente do Langfuse, log) e é irmã de application e persistence. A instanciação fica no bootstrap | Se a montagem morasse em infrastructure, a camada subiria para o topo e a persistence poderia importar a application |
| B39 | O agente e as tools ficam na application, em `application/agent/`; LangChain só ali e no bootstrap. A presentation só tem rotas HTTP | O agente é o caso de uso "atender o aluno"; o domain segue só com a biblioteca padrão, e um contrato do linter impede o framework de vazar para os services |
| B40 | A proposta de protocolo é um token assinado e preso ao aluno; a rota de confirmação valida de novo as regras antes de gravar. Sem tabela de rascunho | Mesma garantia de B26 sem estado no servidor |
| B41 | Histórico em `agent.conversation`, `agent.message` e `agent.tool_call`; observabilidade no Langfuse Cloud | O histórico funciona com várias réplicas e tem dono testável; o Langfuse evita subir serviços de observação |

## 4. O que os dados impõem

| # | Achado | Evidência | Consequência |
|---|---|---|---|
| A1 | O aluno pode ter mais de uma matrícula | 1.037 matrículas, 1.015 `PERSON_ID`, 1.000 CPFs; 37 CPFs têm 2 matrículas, 17 deles em modalidades diferentes | A sessão guarda a pessoa |
| A2 | Nenhum CPF atravessa marcas | Distribuição de marcas por CPF | Invariante extra, testável |
| A3 | Não existe uma coluna como `company_id` em todas as tabelas | Das 47 tabelas, 28 têm dono: 20 têm uma coluna que casa com um identificador da sessão, 8 só chegam ao dono por `JOIN` | Cada tabela declara o próprio ownership |
| A4 | O ID sozinho identifica a pessoa errada | 483 de 1.065 contratos casam com mais de uma matrícula sem marca e modalidade | Toda resolução usa marca + modalidade + número |
| A5 | A chave suja é resolvível, e barata | Protótipo com as 1.000 pessoas, sem nenhuma linha em duas pessoas: contratos 1.065/1.065, faturas 25.931/25.931, pagamentos 24.380/24.380, disciplinas 20.277/20.277, protocolos 3.882/3.933, tentativas 18.566/18.857. Sessão completa: p50 17 ms, p95 32 ms | Dispensa crosswalk persistido e cache, por enquanto |
| A6 | Filtrar por pagador vaza dados | 17 pagadores, 44 matrículas de pessoas diferentes | B8 |
| A7 | Posse de protocolo é uma cascata, não uma chave | 351 protocolos sem ID, 315 CPFs sem zeros à esquerda, 113 de responsáveis, 11 de terceiros. Os 51 protocolos invisíveis no protótipo são os 11 de terceiros e 40 de responsáveis sem ID do aluno | Resolução própria na sessão, com *fail closed* |
| A8 | A linha certa pode trazer dado proibido | Nota interna, CPF e contato do pagador e do requerente, analistas e CPF de professores[^eda] | Filtro de linha não basta (5.4) |
| A9 | Marca tem 5 grafias e duas granularidades | `UniSaoPaulo_EAD` (10 valores, com modalidade), `unisaopaulo`, `UNISAOPAULO`, `1010`, `Uni São Paulo` (5 valores) | Tradutor por sistema; o caminho inverso exige a modalidade |
| A10 | Os formatos variam além das chaves | CPF com pontuação em `sag.person`, taxa como `R$ 0,00`, datas em epoch e ISO, valores em centavos, tudo em `text`[^carga] | O tradutor também converte tipos |
| A11 | PKs e FKs batem quase integralmente | 47/47 PKs sem duplicata nem nulo; 69/74 FKs sem violação. As 5 restantes: `log.courseid` (27.322 valores `0` e 202 órfãos), `log.userid` (169), `category.parent` (5 valores `0`), `protocol.demand_analyst` (23) e `issued_document.signed_by` (6) | B24 |
| A12 | Consulta sem índice lê a tabela inteira | Log: 17–24 ms. Fatura: cerca de 2–6 ms sem índice, cerca de 0,02–0,06 ms com índice | Índices nas colunas de ownership |
| A13 | O conjunto de cada pessoa é pequeno | No máximo 3 contratos, 2 contas no LMS e 18 protocolos por pessoa | Cada consulta devolve poucas linhas; resolver o dono na consulta é barato com índice |
| A14 | Protocolo nasce com três linhas | 3.933/3.933 têm histórico `Open` (`changed_by = system`) e mensagem inicial do requerente; `SLA_Due_At` = abertura + `SLA_Hours` em 3.933/3.933 | Regra do domínio para abertura (5.6) |
| A15 | Parte dos serviços tem taxa | 4 de 18 serviços têm taxa; 732 faturas `SERVICE_FEE` apontam para protocolos | B27 |
| A16 | A semântica de negócio tem armadilhas | Dívida real exclui `OPEN` e `RENEGOTIATED`; só pagamento `CONFIRMED` conta; frequência online é nula; os dados são a foto de 31/10/2026[^eda] | Regras no domínio e relógio injetado: data real em produção, 31/10/2026 nos testes e no eval |
| A17 | O catálogo está em inglês | "Administração" versus `BUSINESS ADMINISTRATION`; `Course_Label` tem 24 grafias para 8 cursos[^eda] | As tools precisam de um resolvedor de entidades |

## 5. Desenho

Os trechos de código são versões condensadas do código em `src/api/`, sem imports e sem os detalhes que não mudam o
desenho.

### 5.1 Camadas e organização

```text
Bootstrap       → composition root: settings, singletons e o grafo por aluno a cada request (B36)
Presentation    → rotas HTTP, identidade pelo JWT e stream da resposta
Application     → services por caso de uso, composição entre sistemas, DTOs, o agente e as tools (B39)
Domain          → entidades, enums, regras, sessão, ontologia, interfaces (ports)
Persistence     → adapter de repositório, carga da sessão e um pacote por sistema
Infrastructure  → adaptadores técnicos que não são banco: relógio, cliente do Langfuse, log, rate limit em Redis (B38)
Banco           → sag · lms · secretary · finance · agent
```

Regra de dependência: Bootstrap → Presentation → Application → Domain. Persistence → Domain. Infrastructure → Domain.
Application, persistence e infrastructure não se importam: a application fala com elas por interfaces definidas no
domínio, e o bootstrap entrega a implementação. Em execução a application chama a persistence; no import, as duas só
conhecem o port. O linter garante as fronteiras por contratos de importação, incluindo LangChain só em
`application/agent/` e no bootstrap.

`src/app/` fica reservada para o front-end.

```text
src/api/
├── bootstrap/      ApiFactory, settings, containers dishka e providers por escopo
├── presentation/   http/: health, chat, confirmação de protocolo, identidade
├── application/    services por área, dto/, chat/, agent/ (agente, tools, skills)
├── domain/         um pacote por área (shared/, identity/, finance/...)  ontology/  ports/
├── infrastructure/ relógio, Langfuse, log, rate limit
└── persistence/
    ├── core/           Database, RepositoryAdapter, ownership_criteria.py, column_types.py, source_enum.py
    ├── identity/       student_session_repository.py, queries.py
    ├── sag/  lms/  secretary/
    └── finance/
        ├── models.py        models do ORM: quais tabelas e colunas a API conhece, com o tipo de coluna que traduz o valor
        ├── dialect.py       chave de dono e mapas de escrita deste sistema
        ├── mappers.py       model → entidade de domínio
        ├── ownership.py     mapa de ownership dos models do sistema
        └── repositories.py  consultas de navegação
```

### 5.2 Isolamento

O padrão é um critério global que acrescenta `AND` em todas as consultas, como
`AND company_id = session.company_id`. A diferença é que aqui não existe uma coluna comum a todas as tabelas (A3).

**Passo 1: a sessão carrega só quem a pessoa é.** É montada a cada pedido e descartada ao final. Uma
dependência de escopo de request lê o `person_id` do JWT e chama a carga; os services que precisam da sessão a recebem
pronta, e a sessão nunca existe vazia (B37). O que pertence à pessoa (contratos, contas do AVA, protocolos) não fica na
sessão: é resolvido em cada consulta pelo mapa de ownership. A carga faz 2 consultas.

```python
@dataclass(frozen=True, slots=True)
class StudentSession:
    person_ids: frozenset[str]
    cpf: str = field(repr=False)
    enrollment_keys: frozenset[EnrollmentKey]  # grafia do SAG + EnrollmentRef canônico

    @property
    def enrollments(self) -> frozenset[EnrollmentRef]: ...

    @property
    def brands(self) -> frozenset[Brand]: ...


BEFORE_THE_STUDENT = {SKIP_OWNERSHIP: True}


class StudentSessionRepository:
    async def load(self, person_id: str) -> StudentSession:
        async with self._database.db_session_factory() as db:
            cpf = await self._cpf_of(db, person_id)
            if not cpf:
                return self._empty_session()
            identities = IdentityQueries.identities_of(cpf)
            result = await db.execute(identities, execution_options=BEFORE_THE_STUDENT)
            return self._session_of(cpf, result.all())
```

**Passo 2: um mapa estático diz como cada model chega ao dono.** Cada sistema tem um model-raiz cuja regra é o
predicado do dialeto sobre as matrículas da sessão; os demais filtram pela chave do pai (`in_(select(Pai.id))`), e o
critério global restringe o próprio pai. `PUBLIC` marca a tabela sem dono. A carga da sessão roda com `skip_ownership`,
porque é ela que cria o aluno.

```python
FINANCE_OWNERSHIP: OwnershipMap = {
    ContractRow: lambda session: FinanceDialect.contract_of(session.enrollments),
    InvoiceRow: lambda _: InvoiceRow.contract_id.in_(select(ContractRow.id)),
    PaymentRow: lambda _: PaymentRow.invoice_id.in_(select(InvoiceRow.id)),
    ProductRow: PUBLIC,
}
LMS_OWNERSHIP: OwnershipMap = {
    LmsUserRow: lambda session: LmsDialect.account_of(session.enrollments),
    LmsQuizAttemptRow: lambda _: LmsQuizAttemptRow.user_id.in_(select(LmsUserRow.id)),
}
SECRETARY_OWNERSHIP: OwnershipMap = {
    ProtocolRow: lambda session: ProtocolRow.id.in_(
        SecretaryDialect.protocols_of(session.cpf, session.enrollment_keys)
    ),
    ProtocolInteractionRow: lambda _: and_(
        ProtocolInteractionRow.protocol_id.in_(select(ProtocolRow.id)),
        ProtocolInteractionRow.is_internal_note == PUBLIC_MESSAGE,
    ),
}
```

O tipo de pagador do contrato sai de uma consulta privada, `PayerQueries.contracts_with_payer`, executada por
`RepositoryAdapter.fetch_rows`: a raiz `ContractRow` recebe o ownership, e o CPF do pagador é comparado no banco e nunca
é lido.

O model descreve a tabela com nomes nossos e só com as colunas permitidas:

```python
class InvoiceRow(Base):
    __tablename__ = "invoice"
    __table_args__ = FINANCE_SCHEMA

    id: Mapped[str] = mapped_column("invoiceid", primary_key=True)
    contract_id: Mapped[str] = mapped_column("contractid")
    due_date: Mapped[date] = mapped_column("duedate", IsoDate())
    net: Mapped[Money] = mapped_column("netamountcents", TextCents())
    status: Mapped[InvoiceStatus] = mapped_column(SourceEnum.by_name(InvoiceStatus))
```

**Passo 3: o listener acrescenta o critério de cada model em toda consulta.**

```python
class OwnershipCriteria:
    @classmethod
    def apply(cls, state: ORMExecuteState) -> None:
        if not cls._is_guarded(state):
            return
        student = cls._student_of(state)
        cls._assert_declared(state)
        state.statement = state.statement.options(*cls._criteria_of(student))

    @staticmethod
    def _criteria_of(student: StudentSession) -> list[ORMOption]:
        return [
            with_loader_criteria(row, rule(student), include_aliases=True)
            for row, rule in OWNERSHIP_BY_ROW.items()
            if rule is not None
        ]


# persistence/core/database.py
event.listen(AsyncSession.sync_session_class, "do_orm_execute", OwnershipCriteria.apply)


class RepositoryAdapter:
    async def fetch[RowT](self, stmt: Select[RowT]) -> Sequence[RowT]:
        async with self._db_session() as db:
            result = await db.scalars(stmt)
            return result.all()

    def _db_session(self) -> AsyncSession:
        return self._database.db_session_factory(info={STUDENT: self._student_session})
```

**O que o desenvolvedor escreve e o SQL resultante:**

```python
# repositories.py: consulta normal, sem pensar em ownership
stmt = select(InvoiceRow).where(InvoiceRow.status == InvoiceStatus.OVERDUE)
```

```sql
SELECT ... FROM finance.invoice
WHERE invoice.status = 'OVERDUE'
  AND invoice.contractid IN (
    SELECT contract.contractid FROM finance.contract
    WHERE (contract.companycode, contract.businessarea,
           lpad(split_part(trim(contract.academicref), '-', 1), 5, '0')) IN (('1050', 'DIGITAL', '01154')));
```

| Situação | Tabelas | Como declara |
|---|---|---|
| Dono direto (8) | SAG: `enrollment`, `enrollment_status_history`, `term_enrollment`, `student_class`, `person`. Raízes dos outros sistemas: `contract`, `mdl_user`, `protocol` | Cláusula a partir da sessão; nas raízes, o predicado do dialeto |
| Dono pela tabela pai (20) | Financeiro: `discount`, `invoice`, `receivable_snapshot`, `agreement`, `payment`, `late_charge`, `invoice_tax`, `agreement_invoice`, `customer`. LMS: `mdl_user_info_data`, `mdl_user_enrolments`, `mdl_quiz_attempts`, `mdl_logstore_standard_log`, `mdl_course`, `mdl_course_modules`, `mdl_quiz`. Secretaria: `protocol_status_history`, `protocol_interaction`, `issued_document`, `satisfaction_survey` | `Filho.fk.in_(select(Pai.id))` até a raiz |
| Catálogo da marca (10) | `sag.brand`, `sag.unit`, `course_offer`, `class_section`, `secretary.unit`, `company`, `price_list`, `mdl_tenant`, `mdl_course_categories`, `professor` (só nome e e-mail, B35) | Cláusula pela marca da sessão |
| Global (8) | `course`, `curriculum`, `subject`, `curriculum_subject`, `term`, `product`, `demand_type`, `mdl_user_info_field` | `PUBLIC` |
| Corporativa (1) | `analyst` | Não mapeada |

**Resultados do protótipo e dos testes:**

- Para as 1.000 pessoas, nenhuma linha apareceu em duas pessoas (A5).
- O listener só deixa passar consulta ORM sobre model declarado no mapa; consulta sem model e tabela não declarada levantam
  `OwnershipError`.
- `payment` sem `JOIN` não traz linhas de terceiros, porque a regra dele sobe até o contrato da sessão.
- `JOIN` com condição errada não traz linhas de terceiros, porque cada tabela é filtrada pela própria regra.
- `OR` vindo de parâmetro fica entre parênteses: `(status = 'OVERDUE' OR status = 'PAID') AND contractid IN (...)`.
- Pessoa sem identificadores gera uma cláusula vazia, que não devolve nenhuma linha.
- Subquery não custou latência no teste: os planos de consulta foram iguais. Ela saiu porque não é necessária.

**Custos aceitos:**

- Repositórios usam consultas ORM sobre models declarados. O listener recusa consulta Core fora do ORM; `text()` é barrado pelo linter (`ruff.toml`), não pelo listener.
- A sessão depende só do SAG. Se ele cair, nenhum pedido autenticado passa; a queda de outro sistema afeta só as consultas
  daquele sistema.
- Cada consulta repete o predicado do dialeto sobre chaves sujas. Os índices de expressão de `03_indexes.sql` pagam esse custo.

Dado de outra pessoa e dado inexistente têm a mesma resposta, para que o agente não descubra a existência de um registro.

### 5.3 Normalização

```python
# domain/brand.py: linguagem nossa, sem conhecer nenhum sistema
class Brand(Enum):
    SAO_PAULO = "sao_paulo"
    MONTANHAS = "montanhas"
    LITORAL = "litoral"
    ATLANTICO = "atlantico"
    ARAUCARIA = "araucaria"


class Modality(Enum):
    IN_PERSON = "in_person"
    ONLINE = "online"


@dataclass(frozen=True, slots=True)
class EnrollmentRef:
    brand: Brand
    modality: Modality
    student_number: str
```

```python
# persistence/finance/dialect.py: `1010` só existe aqui
class FinanceDialect:
    @classmethod
    def contract_of(cls, enrollments: Collection[EnrollmentRef]) -> ColumnElement[bool]:
        keys = [cls._contract_key(enrollment) for enrollment in enrollments]
        columns = tuple_(ContractRow.company_code, ContractRow.business_area, cls._student_number())
        return columns.in_(keys)

    @staticmethod
    def _contract_key(enrollment: EnrollmentRef) -> tuple[str, str, str]:
        company = COMPANY_BY_BRAND[enrollment.brand]  # Brand.SAO_PAULO → "1010"
        area = AREA_BY_MODALITY[enrollment.modality]  # Modality.ONLINE → "DIGITAL"
        return company, area, enrollment.student_number

    @staticmethod
    def _student_number() -> ColumnElement[str]:  # `1253-0` → `01253`, `013463` → `01346`
        reference = func.trim(ContractRow.academic_ref)
        number = func.split_part(reference, "-", 1)
        return func.lpad(number, STUDENT_NUMBER_LENGTH, "0")


# persistence/sag/dialect.py: `UniSaoPaulo_EAD` só existe aqui
SOURCE_BRAND = SourceEnum({source: brand for brand, source in SOURCE_BY_BRAND.items()})


class SagDialect:
    @staticmethod
    def enrollment_ref(brand: str, student_id: str) -> EnrollmentRef:
        modality = Modality.ONLINE if brand.endswith(ONLINE_SUFFIX) else Modality.IN_PERSON
        canonical_brand = SOURCE_BRAND.member_of(brand.removesuffix(ONLINE_SUFFIX))
        return EnrollmentRef(canonical_brand, modality, student_id[:STUDENT_NUMBER_LENGTH])
```

O número canônico usa os 5 dígitos de base, sem verificador; a combinação é única nas 1.037 matrículas. Valor
desconhecido levanta erro em vez de ser adivinhado. A exceção é o `academicRef`, normalizado no SQL para carregar só
os contratos da pessoa: valor fora do padrão não casa com nenhuma matrícula e o contrato fica sem dono. Um teste de
cobertura roda sobre o banco real, prova que todo valor distinto tem tradução e serve como evidência para a entrega.

A tradução do valor da coluna é um tipo de coluna (`persistence/core/column_types.py` e `source_enum.py`, mais um
`column_types.py` por sistema): o model já entrega o valor canônico. Já o `dialect.py` fica só com a chave de dono e os
mapas de escrita.

```python
# persistence/core/column_types.py
class TextCents(SourceText[Money]):
    cache_ok = True

    @override
    def to_source(self, value: Money) -> str:
        return str(value.cents)

    @override
    def from_source(self, text: str) -> Money:
        return Money(int(text))
```

Cada entidade tem um mapper simples, que só copia os campos do model:

```python
# persistence/finance/mappers.py
class InvoiceMapper:
    @staticmethod
    def _invoice(row: InvoiceRow, payments: tuple[Payment, ...], late_charge: Money) -> Invoice:
        return Invoice(
            id=row.id,
            contract_id=row.contract_id,
            due_date=row.due_date,
            net=row.net,
            status=row.status,
            payments=payments,
            late_charge=late_charge,
        )
```

O model não sai da camada de persistência. A application só recebe entidades de domínio.

### 5.4 Campos sensíveis

Três filtros em sequência, cada um mais restrito:

| Etapa | O que faz | Exemplo |
|---|---|---|
| Model do ORM | A API só conhece colunas declaradas | `CustomerRow` não declara `taxId`, `email` e `phone`; `select` nunca os traz |
| Entidade de domínio | Só o que a regra de negócio usa, com métodos | `Invoice.is_debt()` |
| DTO de saída | Allowlist do que o agente vê | Status em linguagem canônica, valor em reais |

Para leitura, o CPF, os dados do requerente e o vínculo entre contrato e pagador só aparecem em tabelas Core locais, fora de
`Base.metadata`, usadas na carga da sessão. O tipo de pagador é calculado ali. A sessão guarda o CPF com `repr=False`,
para não aparecer em log. A exceção é a escrita do protocolo: `requester_cpf` e `requester_name` estão em `ProtocolRow` como
`deferred` com `raiseload`, então não carregam numa consulta, e tocar neles levanta erro.

### 5.5 Composição entre sistemas

`JOIN` entre sistemas é permitido quando simplifica (B23). Toda consulta passa pelo adapter, que aplica o ownership de cada
tabela envolvida. Quando o `JOIN` exigir chaves sujas, ou quando o custo de normalizar em SQL não compensar, a application
compõe os resultados pelas chaves canônicas.

### 5.6 Escrita: abrir protocolo

Dois passos, com aprovação humana:

```text
Aluno pede → tool propose_protocol(action, enrollment, subject) → regras do domínio → token assinado, preso à pessoa
  → o front mostra o card da proposta
Aluno escreve a mensagem, digita a palavra de confirmação → POST /protocols/proposals/confirm, fora do LLM
  → confere assinatura e dono → o domínio valida de novo e abre o protocolo → grava 3 linhas em uma transação
```

O LLM consegue propor, mas não efetivar. O pior resultado de uma injeção dentro do turno é uma proposta, que o aluno precisa
confirmar.

- **Disponibilidade:** `ServiceAvailability` diz, para cada serviço, se ele pode ser aberto pelo agente e por quê não: serviço
  inativo, com taxa, tratado só pela secretaria ou incompatível com a situação da matrícula (trancamento só com matrícula
  ativa, reativação só trancada, diploma só concluída). `list_services` devolve essa resposta, e `propose_protocol` recusa no
  servidor o que não está disponível.
- **Recusas antes de assinar:** trancamento de disciplina (trancamento é sempre do curso inteiro), matrícula em situação
  incompatível e pedido igual já aberto. A recusa volta como resultado `refused`, com o motivo, para o modelo explicar.
- **Token:** assina pessoa, serviço e matrícula e expira em 15 minutos (`APP_PROPOSAL_TTL_MINUTES`). Não existe tabela de
  rascunho (B40).
- **Confirmação:** a rota confere a assinatura e que a pessoa do token pertence à sessão, relê os protocolos do aluno e
  chama de novo a regra do domínio, com a mensagem e a palavra digitadas pelo aluno:

```python
# application/protocol/confirmation.py
class ProtocolConfirmation:
    async def confirm(
        self, token: str, conversation_id: str, answer: StudentAnswer
    ) -> ConfirmedProtocolDto:
        proposal = self._ports.signer.verify(token)
        if proposal is None or proposal.person_id not in self._session.person_ids:
            raise ProposalNotFoundError
        conversation = await self._events.conversation_of(conversation_id)
        parties = await self._parties.of(proposal)
        opening = await self._opening_of(parties, answer)
        number = await self._ports.writer.save(opening)
        await self._events.attach(conversation, ConfirmationEvent.message(number, opening, parties))
        return ConfirmedProtocolDto.of(number, opening)


# domain/protocol/opening.py
class ProtocolOpening:
    @classmethod
    def open(cls, service, enrollment, existing, request) -> Self:
        reason = request.refusal(service, enrollment)
        if reason is not None:
            raise ServiceNotOpenableError(reason)
        if ProposalRules.duplicate_of(existing, service, enrollment) is not None:
            raise DuplicateProtocolError
        ...
```

`SqlProtocolWriter` grava protocolo, histórico `Open` e mensagem inicial numa transação, com `flush` entre os lotes: sem ele,
o ORM gravou as linhas filhas antes do protocolo, o que violaria as FKs de `02_constraints.sql`. A unidade e o nome do curso
vêm da matrícula e são traduzidos pelo dialeto da secretaria; unidades de SAG e secretaria casam em 27/27 por marca,
modalidade, cidade e UF (consulta no banco local). Números de protocolo e de mensagem vêm de sequências no schema `agent`,
sem alterar as tabelas recebidas. A confirmação vira um evento `system_event` no histórico da conversa, para o modelo saber
no turno seguinte que o pedido foi aberto.

### 5.7 Banco

| Script | Conteúdo | Estado |
|---|---|---|
| `01_load.sh` | Carga dos CSVs nos schemas sem prefixo, sem `\r` | Aplicado |
| `02_constraints.sql` | 47 PKs do enunciado; 74 FKs, com `NOT VALID` nas 5 de A11 | Aplicado |
| `03_indexes.sql` | 22 índices nas colunas e expressões de ownership e navegação, derivados das varreduras medidas na suíte de testes | Aplicado |
| `04_agent_schema.sql` | `conversation`, `message`, `tool_call` e as sequências de protocolo e mensagem | Aplicado |
| `05_roles.sh` | Role `api`: `SELECT` só nas 34 tabelas mapeadas; `INSERT` só em `protocol`, `protocol_status_history` e `protocol_interaction`; leitura e escrita em `agent`, sem `DELETE`; sem `UPDATE` ou `DELETE` em dados de origem; sem `analyst`; sem tabela temporária. A API e o código dela nos testes conectam com essa role; só o oráculo SQL usa o administrador | Aplicado |

Índices medidos com a role, p50 em 50 pessoas: `list_invoices` de 25,2 para 14,6 ms; resumo financeiro de 35,1 para 22,9 ms; `list_protocols` de 53,5 para 37,2 ms; carga da sessão de 4,6 para 2,9 ms.

### 5.8 Assincronia e recursos

- Uma sessão do ORM é aberta por chamada de repositório e nunca fica presa durante uma chamada ao LLM.
- Paralelismo com `asyncio.gather` usa uma sessão do ORM por tarefa, porque ela não aceita uso concorrente.
- Custo do ORM medido: 5,07 ms contra 4,35 ms em conexão direta, com 49 faturas e conversão para entidade.
- A aplicação é stateless. A sessão morre com o pedido.
- Relógio injetado: `SystemClock` com a data real em produção, `FixedClock` com 31/10/2026 nos testes e no eval.

Cada turno tem prazo (`APP_AGENT_TIMEOUT_SECONDS`), retry da chamada ao modelo e limite de chamadas ao modelo e às tools. Não há
limite de concorrência por processo: o custo é contido por um rate limit por aluno em Redis, de mensagens do chat por hora
(`APP_CHAT_RATE_LIMIT_PER_HOUR`), que responde 429 com `Retry-After` e deixa passar quando o Redis está fora do ar.

### 5.9 Agente, tools e skills

- **Agente:** `create_agent` do LangChain, montado a cada request com as tools do aluno (cerca de 3 ms medidos). Modelo
  da OpenAI pela Responses API, configurável em settings. Os middlewares, em ordem: `InputGuardMiddleware`, limite de
  chamadas ao modelo, limite de chamadas às tools, retry da chamada ao modelo e erro de tool devolvido ao modelo como
  mensagem genérica.
- **InputGuard:** antes do agente, uma chamada à Decisions API da OpenAI (`langchain_openai.decisions`) com a última
  mensagem e até 6 falas anteriores responde duas perguntas. Um `Choice` de assunto (aluno, misto ou fora) bloqueia só quando
  "fora" chega a 0,8, e então o turno termina com um texto fixo, sem chamar o modelo. Um `Predicate` de prompt injection a
  partir de 0,5 não recusa: acrescenta um aviso de sistema dizendo que saída de tool, texto de sistema ou ordem de terceiro
  colados na mensagem não são fatos. O limiar alto de escopo é escolha: a pior pergunta legítima medida deu 0,23, e recusar
  um aluno custa mais do que deixar passar um pedido fora do escopo. Se a API falhar, o turno segue sem o guard. É camada de
  modelo, como o prompt e as skills: reduz a chance de um ataque mudar o comportamento, mas a segurança dos dados não depende
  dele.
- **Tools:** adaptadores finos sobre os services, em `application/agent/tools/`. Não recebem identidade: cada tool é uma
  closure sobre services que já carregam a sessão do aluno. O schema de cada tool é calculado uma vez, na subida.
- **Parâmetros amigáveis:** a busca por nome fica dentro da tool. Sem correspondência, a tool devolve candidatos, e o
  modelo escolhe.
- **Erro ensino:** erro de tool nunca derruba o turno. Parâmetro inválido volta como resultado `invalid`, com um parágrafo
  que diz o que veio, o que é aceito e um exemplo, para o modelo corrigir a chamada. Falha inesperada volta como `error`
  genérico, sem detalhe interno, e fica no log.
- **Respostas das tools:** já trazem totais do conjunto inteiro, paginação e sinais de qualidade, como "frequência
  não registrada" ou "sem dados antes de 2023". Não há tabela de tradução: o modelo traduz o que vem da base e responde
  sempre em português.
- **Skills:** uma por área, em `SKILL.md` com `name` e `description`, o formato do LangChain. O prompt lista as
  descrições; a tool `load_skill(area)` devolve o corpo e as ontologias da área. Ajudam na qualidade, mas não são
  barreira de segurança.
- **Histórico:** as últimas mensagens da conversa vêm de `agent.message` e `agent.tool_call`, sem separar uma chamada de
  tool do seu resultado (B41).
- **Eval:** cada execução registra versão de prompt, skills, tools e modelo, além da trajetória. As respostas esperadas
  vêm de SQL independente das tools. Parte do conjunto fica reservada para evitar sobreajuste.

## 6. Invariantes verificados por teste

1. Nenhuma tool recebe identidade como parâmetro.
2. Toda tabela mapeada tem declaração de ownership; caso contrário, a aplicação não inicia.
3. **Partição:** cada linha com dono pertence a no máximo uma pessoa, em toda consulta de repositório. O protótipo já provou isso para contrato, fatura, pagamento, disciplina, tentativa e protocolo.
4. Parâmetros não ampliam resultados: um "agente comprometido" chama todas as tools com todos os argumentos e recebe zero linhas alheias.
5. Nenhum CPF, nota interna ou dado de funcionário aparece em DTO de saída, exceto nome e e-mail de professor (B35).
6. Dado de outro aluno e dado inexistente têm a mesma resposta.
7. Valor desconhecido em identificador levanta erro.
8. Apenas a persistência importa o SQLAlchemy.
9. Nenhum model usa `relationship()`.
10. LangChain só aparece em `application/agent/` e no bootstrap.
11. Nenhum objeto que vive o processo inteiro guarda algo de um aluno: dois alunos seguidos não compartilham tools,
    agente nem histórico.

## 7. O que a arquitetura garante e o que não garante

**Garantido por arquitetura, independentemente do que o modelo faça:**

- Um aluno não acessa dados de outro por nenhum parâmetro de tool.
- Dados corporativos não mapeados são inalcançáveis.
- O agente não realiza ações destrutivas: não há ferramenta para isso, e a role do banco também as nega.
- O agente não efetiva escrita sozinho: abrir protocolo exige aprovação humana fora do LLM.

**Não garantido, tratado por medição:**

- O modelo pode interpretar mal um dado, chamar a ferramenta errada ou responder de forma imprecisa. Isso é qualidade,
  medida por eval e melhorada por iteração.
- Jailbreak pode mudar o comportamento e o tom do modelo e até revelar o prompt. O dano é limitado porque o prompt
  não contém segredos e o modelo não tem acesso além das tools. O InputGuard reduz essa chance, e o red team do eval mede.

| # | Risco | Mitigação |
|---|---|---|
| R1 | Repositório é barreira única (B9) | Invariantes da seção 6 e role restrita |
| R2 | Código contorna o adapter com SQL manual | Invariante 8, lint que restringe quem abre sessão de banco e revisão |
| R3 | Escala não medida sob carga | API stateless, índices, rate limit por aluno e limites por turno; latência medida por turno no eval |
| R4 | Escrita altera os dados usados pelo eval | O eval só propõe e nunca confirma; os testes de escrita usam um Postgres efêmero |
| R5 | Texto do aluno em protocolo pode conter injeção | Texto tratado como dado; escrita depende de aprovação humana |
| R6 | Sem regulamento na base[^eda] | O agente diz que não tem a informação |
| R7 | Sistemas com períodos e valores diferentes[^eda] | Fonte oficial por tema e ausência de dado explicada |

## 8. Fora de escopo

| Item | Volta quando |
|---|---|
| Crosswalk persistido e schemas intermediários de dados normalizados | O custo de resolver identidade exigir; hoje contradiz B11 |
| RLS | B9 for revista |
| Cache da sessão em Redis | Teste de carga mostrar que montar a sessão a cada pedido pesa |
| RAG e busca vetorial | A base ganhar texto de conhecimento para indexar |
| Atender responsável ou pagador | O enunciado fala em aluno autenticado |
| Escritas além de abrir protocolo | O case exigir ou o primeiro fluxo estiver estável |

[^readme]: Enunciado do case, seções 1 e 3.
[^eda]: Análise exploratória dos dados, seções 5 a 8.
[^carga]: Script de carga: todas as colunas são `text`, para preservar os valores originais.
