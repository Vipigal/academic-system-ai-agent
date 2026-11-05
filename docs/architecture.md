---
type: Architecture
title: Arquitetura do agente de atendimento ao aluno
description: Decisões, desenho e restrições da API que dá ao agente acesso seguro e normalizado aos quatro sistemas do grupo educacional.
tags: [arquitetura, api, isolamento, normalizacao, agente]
status: stable
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T04:01:00Z }
verified: { by: human:vinicius, at: 2026-11-05T02:53:00Z }
sources:
  - id: readme
    resource: /README.md
    title: Enunciado do case
  - id: eda
    resource: /docs/eda.md
    title: Análise exploratória dos dados
  - id: carga
    resource: /db/init/01_load.sh
    title: Script de carga dos CSVs
  - id: atlas
    resource: https://claude.ai/artifact/QT94fmWSRppKT2JUBGAKds
    title: Atlas de Dados, reconferência de 2026-11-04
---

# Arquitetura do agente de atendimento ao aluno

> **Estado:** verificado. A seção 3 traz o que está decidido. O que falta definir está em
> [Pendências](/docs/pendencias.md).
>
> **Medições:** consultas no banco local e protótipos descartáveis, em 2026-11-04 e 2026-11-05. Latências
> foram medidas em execução sequencial e sem índices; não são resultado de teste de carga.

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
| B3 | Camadas: presentation, application, domain, persistence e banco | Separar negócio de tecnologia |
| B4 | O domínio não depende de ninguém; dependência externa entra por inversão de dependência | Evita o ciclo entre domínio e persistência |
| B5 | O isolamento é por pessoa. Com N matrículas, ela consulta as N na mesma sessão | 37 CPFs têm 2 matrículas |
| B6 | A sessão vem do token e é montada a cada pedido, sem cache por enquanto | Simplicidade; custo medido em A5 |
| B7 | O `WHERE` de ownership é montado a partir da sessão, nunca a partir de parâmetros. Parâmetros apenas navegam nos dados ou consultam tabelas sem dono | É a garantia central de isolamento |
| B8 | Financeiro sempre filtra por contrato, nunca por pagador | 17 pagadores cobrem 44 matrículas de pessoas diferentes |
| B9 | Segurança em código, sem RLS. Em um sistema real as tabelas já existem e talvez nem estejam em Postgres | Não depender de recurso de um banco específico; o repositório central e bem testado é a garantia |
| B10 | Menor privilégio: o agente só tem as ferramentas de que precisa, sem ações destrutivas e sem parâmetro que amplie acesso | Segurança por arquitetura |
| B11 | Não se alteram dados nem colunas recebidas. São permitidos índices e as PKs e FKs do README | Mudam a física e a integridade, não o conteúdo |
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
| B26 | Abrir protocolo cria 3 linhas em 2 passos, com aprovação humana: a proposta aparece na interface, o aluno aprova com um clique e outro endpoint, fora do LLM, grava | O LLM não efetiva escrita sozinho |
| B27 | O agente abre só os 14 serviços sem taxa. Nos 4 com taxa, orienta a procurar a secretaria | Evita protocolo pago sem fatura |
| B28 | Protocolos abertos por terceiros e casos ambíguos: ninguém vê | *Fail closed* |
| B29 | Adapter de repositório acrescenta o `AND` de ownership em toda consulta, a partir de um mapa estático por tabela e dos identificadores da sessão (5.2) | Mesma garantia com menos conceitos, sem depender de lembrar do filtro |
| B30 | O aluno vê os 73 protocolos abertos por responsável com o ID dele, sem os dados do responsável | O protocolo é dele; os dados do responsável não |
| B31 | Models não usam `relationship()`; toda relação é um `JOIN` explícito | O carregamento do relationship gera consulta que o adapter não vê. No teste, o pagador de um aluno devolveu 7 contratos, sendo só 1 dele |
| B32 | O guard de consultas usa lista de permitidos | Com lista de proibidos, `suffix_with("OR true")` devolveu as faturas de todos os alunos |
| B33 | `Via` declara a ligação com o pai, e o adapter a acrescenta com `AND` | `JOIN` com condição errada trouxe pagamentos de terceiros; a garantia não pode depender de quem escreve a consulta |
| B34 | A API fica em `src/api/`; `src/app/` é reservada para o front-end | Separar os dois produtos no repositório |
| B35 | O aluno vê nome e e-mail institucional dos professores da disciplina no semestre, na marca dele; CPF e demais dados de professor ficam fora | Decisão do dono do projeto; o contato com o professor não é dado sensível |

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
| A13 | O conjunto de cada pessoa é pequeno | No máximo 3 contratos, 2 contas no LMS e 18 protocolos por pessoa | Os identificadores cabem na sessão |
| A14 | Protocolo nasce com três linhas | 3.933/3.933 têm histórico `Open` (`changed_by = system`) e mensagem inicial do requerente; `SLA_Due_At` = abertura + `SLA_Hours` em 3.933/3.933 | Regra do domínio para abertura (5.6) |
| A15 | Parte dos serviços tem taxa | 4 de 18 serviços têm taxa; 732 faturas `SERVICE_FEE` apontam para protocolos | B27 |
| A16 | A semântica de negócio tem armadilhas | Dívida real exclui `OPEN` e `RENEGOTIATED`; só pagamento `CONFIRMED` conta; frequência online é nula; data de referência é 31/10/2026[^eda] | Regras no domínio e relógio injetado |
| A17 | O catálogo está em inglês | "Administração" versus `BUSINESS ADMINISTRATION`; `Course_Label` tem 24 grafias para 8 cursos[^eda] | As tools precisam de um resolvedor de entidades |

## 5. Desenho

Os trechos de código são versões condensadas de protótipos que rodaram contra o banco, salvo onde indicado. Eles mostram o
desenho completo, não o código: podem não passar no lint, e o código real cresce por fatia em `src/api/`.

### 5.1 Camadas e organização

```text
Presentation  → rotas HTTP e adaptadores de tool
Application   → services por caso de uso, composição entre sistemas, DTOs de saída
Domain        → entidades, enums, regras, sessão, interfaces (ports)
Persistence   → adapter de repositório, sessão e um pacote por sistema
Banco         → sag · lms · secretary · finance · agent
```

Regra de dependência: Presentation → Application → Domain. Persistence → Domain. O domínio não importa nada de
fora, e a application fala com repositórios por meio de interfaces definidas no domínio. O linter garante as fronteiras
por contratos de importação.

`src/app/` fica reservada para o front-end.

```text
src/api/
├── main.py         composição: o único módulo que conhece todas as camadas
├── presentation/   http/  tools/
├── application/    session_service.py  financial_service.py  dto/
├── domain/         brand.py  session.py  invoice.py  ports.py
└── persistence/
    ├── repository_adapter.py     acrescenta o ownership em toda consulta
    ├── query_guard.py            recusa o que não está na lista de permitidos
    ├── student_session_repository.py
    ├── sag/  lms/  secretary/
    └── finance/
        ├── models.py        models do ORM: quais tabelas e colunas a API conhece
        ├── dialect.py       como este sistema escreve nossas entidades
        ├── mappers.py       model → entidade de domínio
        ├── ownership.py     mapa de ownership das tabelas do sistema
        └── repositories.py  consultas de navegação
```

### 5.2 Isolamento

O padrão é um adapter de repositório que acrescenta `AND` em todas as consultas, como
`AND company_id = session.company_id`. A diferença é que aqui não existe uma coluna comum a todas as tabelas (A3).

**Passo 1: a sessão carrega os identificadores da pessoa.** É montada a cada pedido e descartada ao final.

```python
@dataclass(frozen=True)
class StudentSession:
    person_ids: frozenset[str]
    cpf: str = field(repr=False)
    enrollment_keys: frozenset[tuple[str, str]]  # (BRAND, STUDENT_ID)
    contract_ids: frozenset[str]
    lms_user_ids: frozenset[str]
    protocol_ids: frozenset[str]


class StudentSessionRepository:
    async def load(self, person_id: str) -> StudentSession:
        cpf, enrollments = await self._identity(person_id)
        return StudentSession(
            person_ids=...,
            cpf=cpf,
            enrollment_keys=...,
            contract_ids=await self._contracts_of(enrollments),  # usa FinanceDialect
            lms_user_ids=await self._lms_accounts_of(enrollments),  # usa LmsDialect
            protocol_ids=await self._protocols_of(cpf, enrollments),  # usa SecretaryDialect
        )
```

**Passo 2: um mapa estático diz qual coluna de cada tabela representa o dono.**

```python
FINANCE_OWNERSHIP = {
    ContractRow: lambda s: ContractRow.id.in_(s.contract_ids),
    InvoiceRow: lambda s: InvoiceRow.contract_id.in_(s.contract_ids),
    PaymentRow: Via(
        InvoiceRow, PaymentRow.invoice_id == InvoiceRow.id
    ),  # exige JOIN com InvoiceRow
    ProductRow: Public(),  # sem dono: consulta livre
}
SAG_OWNERSHIP = {
    StudentClassRow: lambda s: tuple_(StudentClassRow.brand, StudentClassRow.student_id).in_(
        s.enrollment_keys
    ),
    ClassSectionRow: Public(),
}
SECRETARY_OWNERSHIP = {
    ProtocolRow: lambda s: ProtocolRow.id.in_(s.protocol_ids),
    InteractionRow: lambda s: (
        InteractionRow.protocol_id.in_(s.protocol_ids)
        & (InteractionRow.is_internal_note == "False")
    ),
}
```

O model descreve a tabela com nomes nossos e só com as colunas permitidas:

```python
class InvoiceRow(Base):
    __tablename__ = "invoice"
    __table_args__ = {"schema": "finance"}

    id: Mapped[str] = mapped_column("invoiceid", primary_key=True)
    contract_id: Mapped[str] = mapped_column("contractid")
    due_date: Mapped[str] = mapped_column("duedate")
    net_cents: Mapped[str] = mapped_column("netamountcents")
    status: Mapped[str]
```

**Passo 3: o adapter percorre as tabelas da consulta e acrescenta os `AND`.**

```python
class RepositoryAdapter:
    async def fetch(self, stmt: Select) -> Sequence[Any]:
        async with self._db_session_factory() as db:  # sessão do ORM curta, por chamada
            return (await db.scalars(self._with_ownership(stmt))).all()

    def _with_ownership(self, stmt: Select) -> Select:
        reject_unsafe_constructs(stmt)  # só passa o que está na lista de permitidos
        tables = tables_in(stmt)  # FROM e JOINs do nível principal
        for table in tables:
            rule = OWNERSHIP_BY_TABLE.get(table)
            if rule is None:
                raise OwnershipError(f"tabela sem declaração: {table.fullname}")
            if isinstance(rule, Public):
                continue
            if isinstance(rule, Via):
                if rule.parent.__table__ not in tables:
                    raise OwnershipError(f"{table.name} exige JOIN com {rule.parent.__tablename__}")
                stmt = stmt.where(rule.link)
                continue
            stmt = stmt.where(rule(self._student_session))
        return stmt
```

**O que o desenvolvedor escreve e o SQL resultante:**

```python
# repositories.py: consulta normal, sem pensar em ownership
stmt = select(InvoiceRow).where(InvoiceRow.status == "OVERDUE")
stmt = select(PaymentRow).join(InvoiceRow, PaymentRow.invoice_id == InvoiceRow.id)
```

```sql
SELECT ... FROM finance.invoice
WHERE status = 'OVERDUE' AND contractid IN ('CT00010738');

SELECT ... FROM finance.payment JOIN finance.invoice ON payment.invoiceid = invoice.invoiceid
WHERE payment.invoiceid = invoice.invoiceid AND invoice.contractid IN ('CT00010738');
```

| Situação | Tabelas | Como declara |
|---|---|---|
| Coluna de dono própria (20) | SAG: `enrollment`, `enrollment_status_history`, `term_enrollment`, `student_class`, `person`. Financeiro: `contract`, `discount`, `invoice`, `receivable_snapshot`, `agreement`. LMS: `mdl_user`, `mdl_user_info_data`, `mdl_user_enrolments`, `mdl_quiz_attempts`, `mdl_logstore_standard_log`. Secretaria: `protocol`, `protocol_status_history`, `protocol_interaction`, `issued_document`, `satisfaction_survey` | Cláusula a partir da sessão |
| Dono por `JOIN` (8) | `payment`, `late_charge`, `invoice_tax`, `agreement_invoice` (via fatura); `customer` (via contrato, sem dados pessoais); `mdl_course`, `mdl_course_modules`, `mdl_quiz` (via inscrições) | `Via(pai, ligação)` |
| Catálogo da marca (10) | `sag.brand`, `sag.unit`, `course_offer`, `class_section`, `secretary.unit`, `company`, `price_list`, `mdl_tenant`, `mdl_course_categories`, `professor` (só nome e e-mail, B35) | Cláusula pela marca da sessão |
| Global (8) | `course`, `curriculum`, `subject`, `curriculum_subject`, `term`, `product`, `demand_type`, `mdl_user_info_field` | `Public()` |
| Corporativa (1) | `analyst` | Não mapeada |

**Resultados do protótipo e dos testes:**

- Para as 1.000 pessoas, nenhuma linha apareceu em duas pessoas (A5).
- O guard usa lista de permitidos: colunas de tabela mapeada, parâmetros, operadores comuns e algumas funções. O resto é
  recusado, como `text()`, subquery, alias, CTE, `UNION`, label, sufixo e hint, operador customizado e função do banco.
- Foram bloqueados: `payment` sem `JOIN` e tabela não declarada.
- `JOIN` com condição errada não traz linhas de terceiros, porque o adapter acrescenta a ligação de `Via` com `AND`.
- `OR` vindo de parâmetro fica entre parênteses: `(status = 'OVERDUE' OR status = 'PAID') AND contractid IN (...)`.
- Pessoa sem identificadores gera uma cláusula vazia, que não devolve nenhuma linha.
- Subquery não custou latência no teste: os planos de consulta foram iguais. Ela saiu porque não é necessária.

**Custos aceitos:**

- Repositórios só usam o que está na lista de permitidos. Se surgir necessidade real, o guard passa a aceitar o caso.
- Com a sessão montada de uma vez, a queda de um sistema afeta todos os pedidos. Hoje há um só banco, então o risco é
  pequeno. O carregamento por sistema é o caminho de evolução.

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
class SagDialect:
    @classmethod
    def enrollment_ref(cls, brand: str, student_id: str) -> EnrollmentRef:
        modality = Modality.ONLINE if brand.endswith("_EAD") else Modality.IN_PERSON
        return EnrollmentRef(
            lookup(cls._BRANDS, brand.removesuffix("_EAD"), "BRAND"), modality, student_id[:5]
        )
```

O número canônico usa os 5 dígitos de base, sem verificador; a combinação é única nas 1.037 matrículas. Valor
desconhecido levanta erro em vez de ser adivinhado. A exceção é o `academicRef`, normalizado no SQL para carregar só
os contratos da pessoa: valor fora do padrão não casa com nenhuma matrícula e o contrato fica sem dono. Um teste de
cobertura roda sobre o banco real, prova que todo valor distinto tem tradução e serve como evidência para a entrega.

Cada entidade tem um mapper simples, que usa o dialeto para converter o model:

```python
# persistence/finance/mappers.py
class InvoiceMapper:
    @staticmethod
    def to_entity(row: InvoiceRow) -> Invoice:
        return Invoice(
            id=row.id,
            due_date=date.fromisoformat(row.due_date),
            net=Money.from_cents(int(row.net_cents)),
            status=FinanceDialect.invoice_status(row.status),
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

O CPF só aparece nas definições privadas da carga da sessão. A sessão o guarda com `repr=False`, para não aparecer em log.

### 5.5 Composição entre sistemas

`JOIN` entre sistemas é permitido quando simplifica (B23). Toda consulta passa pelo adapter, que aplica o ownership de cada
tabela envolvida. Quando o `JOIN` exigir chaves sujas, ou quando o custo de normalizar em SQL não compensar, a application
compõe os resultados pelas chaves canônicas.

### 5.6 Escrita: abrir protocolo

Dois passos, com aprovação humana:

```text
Aluno pede → tool propose_protocol → rascunho em agent.protocol_draft → interface mostra a proposta
Aluno clica em aprovar → POST /protocol-drafts/{id}/confirm, fora do LLM
  → confere que o rascunho é da sessão → domínio abre o protocolo → grava 3 linhas em uma transação
```

O LLM consegue propor, mas não efetivar. A aprovação exige uma página mínima de chat.

Trecho ilustrativo; ainda não foi testado.

```python
# domain/protocol.py: regras e efeitos em memória
class StudentProtocol:
    @classmethod
    def open(cls, *, session, enrollment, demand, message, number, now) -> "StudentProtocol":
        if not session.owns(enrollment):
            raise EnrollmentNotOwned()
        if not demand.active or demand.has_fee:
            raise DemandUnavailable(demand.code)
        return cls(
            number=number,
            enrollment=enrollment,
            demand=demand,
            status=ProtocolStatus.OPEN,
            opened_at=now,
            sla_due_at=now + demand.sla,
            history=[StatusChange(seq=1, to=ProtocolStatus.OPEN, at=now)],
            interactions=[Interaction(author=AuthorType.REQUESTER, message=message, at=now)],
        )


# persistence/secretary/repositories.py: traduz e grava em uma transação
class ProtocolWriter:
    async def save(self, protocol: StudentProtocol) -> None:
        async with self._db_session_factory() as db, db.begin():
            db.add(ProtocolMapper.to_row(protocol))
            await db.flush()  # sem relationship(), a ordem precisa ser explícita
            db.add_all(ProtocolMapper.history_rows(protocol))
            db.add_all(ProtocolMapper.interaction_rows(protocol))
```

O `flush` é obrigatório: sem ele, o ORM gravou as linhas filhas antes do protocolo no teste, o que violaria as FKs
criadas em `02_constraints.sql`. A ordem com `flush` foi confirmada em transação desfeita.

A unidade e o nome do curso vêm da matrícula e são traduzidos pelo dialeto da secretaria; unidades de SAG e secretaria
casam em 27/27 por marca, modalidade, cidade e UF.[^atlas] Números de protocolo e de mensagem vêm de sequências no
schema `agent`, sem alterar as tabelas recebidas.

### 5.7 Banco

| Script | Conteúdo | Estado |
|---|---|---|
| `01_load.sh` | Carga dos CSVs nos schemas sem prefixo, sem `\r` | Aplicado |
| `02_constraints.sql` | PKs do README; FKs, com `NOT VALID` nas 5 de A11 | Pendente |
| `03_indexes.sql` | Índices nas colunas de ownership e de navegação, derivados das consultas reais | Pendente |
| `04_agent_schema.sql` | Conversas, logs, auditoria, rascunhos, sequências | Pendente |
| `05_roles.sql` | Role da API: `SELECT` nas tabelas mapeadas, `INSERT` só em `protocol`, `protocol_status_history` e `protocol_interaction`, leitura e escrita em `agent`; sem `UPDATE` ou `DELETE` em dados de origem; sem acesso a `analyst` | Pendente |

### 5.8 Assincronia e recursos

- Uma sessão do ORM é aberta por chamada de repositório e nunca fica presa durante uma chamada ao LLM.
- Paralelismo com `asyncio.gather` usa uma sessão do ORM por tarefa, porque ela não aceita uso concorrente.
- Custo do ORM medido: 5,07 ms contra 4,35 ms em conexão direta, com 49 faturas e conversão para entidade.
- A aplicação é stateless. A sessão morre com o pedido.
- Relógio injetado, com a data de referência de 31/10/2026 em configuração.

Limites de concorrência, deadlines, retry e proteção do provedor de LLM entram junto com o agente.

### 5.9 Agente, tools e skills

- **Tools:** adaptadores finos na presentation. Não recebem identidade. A sessão chega pelo contexto de execução,
  fora do schema visível ao modelo.
- **Parâmetros amigáveis:** "Administração" ou "semestre passado" viram entidades canônicas. Caso ambíguo devolve
  candidatos em vez de erro.
- **Respostas das tools:** já trazem totais calculados, rótulos em português e sinais de qualidade, como
  "frequência não registrada" ou "sem dados antes de 2023".
- **Skills:** instruções versionadas, carregadas sob demanda. Ajudam na qualidade, mas não são barreira de segurança.
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
  não contém segredos e o modelo não tem acesso além das tools. Medido por red team.

| # | Risco | Mitigação |
|---|---|---|
| R1 | Repositório é barreira única (B9) | Invariantes da seção 6 e role restrita |
| R2 | Código contorna o adapter com SQL manual | Invariante 8, lint que restringe quem abre sessão de banco e revisão |
| R3 | Escala não comprovada | Índices e teste de carga com LLM simulado |
| R4 | Escrita altera os dados usados pelo eval | Eval em banco recarregado ou com transação desfeita ao final |
| R5 | Texto do aluno em protocolo pode conter injeção | Texto tratado como dado; escrita depende de aprovação humana |
| R6 | Sem regulamento na base[^eda] | O agente diz que não tem a informação |
| R7 | Sistemas com períodos e valores diferentes[^eda] | Fonte oficial por tema e ausência de dado explicada |

## 8. Pendências

A lista de pendências fica em [Pendências](/docs/pendencias.md).

## 9. Fora de escopo por enquanto

| Item | Volta quando |
|---|---|
| Crosswalk persistido e schemas intermediários de dados normalizados | O custo de resolver identidade exigir; hoje contradiz B11 |
| RLS | B9 for revista |
| Cache ou Redis | Teste de carga mostrar que montar a sessão a cada pedido pesa |
| RAG e pgvector | Ainda em aberto; avaliar com as perguntas de catálogo |
| Atender responsável ou pagador | O enunciado fala em aluno autenticado |
| Escritas além de abrir protocolo | O case exigir ou o primeiro fluxo estiver estável |

[^readme]: Enunciado do case, seções 1 e 3.
[^eda]: Análise exploratória dos dados, seções 5 a 8.
[^carga]: Script de carga: todas as colunas são `text`, para preservar os valores originais.
[^atlas]: Atlas de Dados: correspondência de unidades entre SAG e secretaria.
