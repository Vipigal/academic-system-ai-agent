---
type: Plan
title: Ontologia e topologia de tools
description: Spec da tarefa que cria a classe Ontology, as 19 tools do agente, o envelope de resposta com paginação e a correção do cálculo de dívida.
tags: [plano, ontologia, tools, agente]
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T16:17:34Z }
sources:
  - id: catalogo
    resource: /docs/question-catalog.md
    title: Catálogo de perguntas do aluno
  - id: arquitetura
    resource: /docs/architecture.md
    title: Arquitetura do agente de atendimento ao aluno
  - id: auto-ontology
    resource: https://github.com/NVIDIA/auto-ontology/tree/c4495670
    title: NVIDIA Auto Ontology, v1.2.0, lido em 2026-11-05
  - id: banco
    resource: /db/init/01_load.sh
    title: Consultas de 2026-11-05 no banco local, carregado por este script
---

# Ontologia e topologia de tools

> **Status:** em revisão · **Data:** 2026-11-05
> **Spec vivo:** este arquivo é a fonte única da tarefa. Mudanças são editadas aqui e anotadas em
> "Mudança no spec" na seção Registro; leia o Registro junto do restante.
> **Repos:** só este.

## Para o humano

- **O que muda:** a API ganha 54 conceitos declarados na classe `Ontology`, 19 tools prontas para o agente chamar,
  um envelope de resposta com paginação e o cálculo correto de dívida.
- **Por quê:** o catálogo mostra que o risco está no significado dos dados. Ontologia e tools resolvem isso juntas: as
  tools entregam dados e avisos, e as ontologias alimentam skills e evals.
- **O que não entra:** loop do agente, texto e carregamento das skills, execução de evals e gravação de protocolo.
  Esta tarefa entrega as peças que essas frentes vão consumir.
- **Revisar com atenção:** a lista de ontologias e relações da seção 6.1 e o plano da seção 8.

## 1. Contexto e problema

O catálogo tem 60 perguntas, e as armadilhas se repetem em três formas:[^catalogo]

- **Significado:** dívida não é a soma das faturas abertas; frequência nula não é 0%; estorno não é falta de pagamento.
- **Relações que não valem:** dívida não prova bloqueio de diploma nem suspensão no AVA; protocolo resolvido não prova
  taxa paga; trancar não quita o que já se deve.
- **Ausência:** não há regulamento, horário de aula nem gabarito na base.

Hoje a API só tem faturas: `Invoice`, `FinancialService` e uma sessão com pessoa e contratos. Não existe pasta de tools,
ontologia ou envelope de resposta. O cálculo de dívida também diverge da regra do catálogo (seção 5).

## 2. Princípios

- **Registrar tudo, entregar pouco:** a ontologia guarda tudo o que sabemos, e cada consumidor recebe só o que precisa.
- **Contexto vem sob demanda:** o que importa em uma resposta chega pela skill da área ou pelo resultado da tool.
- **O modelo redige, a API calcula:** totais, saldos e estimativas chegam prontos.
- **Sem fonte, sem afirmação:** dado ausente vira "não tenho a informação", sem precisar listar cada ausência.
- **Desenho simples:** cada conceito novo precisa de um motivo concreto vindo do catálogo.

## 3. Decisões

### 3.1 Batidas (não reabrir)

| # | Decisão | Por quê |
|---|---|---|
| D1 | A classe se chama `Ontology`; há uma instância por conceito, com relações tipadas entre instâncias | Decisão do dono: registrar tudo o que sabemos sobre cada ideia |
| D2 | As ontologias ficam em Python em `src/api/domain/ontology/`, com `docs/ontology.md` gerado e um teste de sincronia | Tipos e testes pegam referência errada, e a pessoa revisa um documento legível |
| D3 | Ontologias escritas em português. Não há tabela de tradução: o modelo traduz o que vem da base e sempre responde em português | Decisão do dono: evita revisar 286 rótulos |
| D4 | O prompt não carrega ontologias: `POLICY` é garantido por arquitetura e `ABSENT` é coberto pela regra de só afirmar o que tem fonte | Evita que as instruções se percam; o Auto Ontology também não põe glossário nas instruções[^auto-ontology] |
| D5 | Descrição de tool é curta: diz o que faz e quando chamar. Dados, estados e avisos vêm no resultado | Decisão do dono, com precedente no Auto Ontology[^auto-ontology] |
| D6 | As ontologias entram nas skills, com relações. `evidence` e `data` nunca chegam ao modelo | Decisão do dono; `evidence` tem agregados de outros alunos (RE-06) e `data` tem nomes de tabelas |
| D7 | Lista plana de 19 tools, incluindo `get_pending_items` | Decisão do dono; cobre as 60 perguntas com no máximo 3 tools por pergunta |
| D8 | Parâmetros só navegam dentro do que o aluno pode ver; nenhuma tool recebe identidade | B7 e B10 da arquitetura[^arquitetura] |
| D9 | A busca por nome fica dentro da tool; sem correspondência, ela devolve candidatos e o modelo escolhe | Sem tradução, busca por palavras não liga "Programação II" a `ALGORITHMS AND PROGRAMMING II` |
| D10 | Toda conta é feita na API, inclusive a estimativa de AV2, que sai com aviso | Modelo errar conta é risco evitável |
| D11 | Paginação em vez de truncamento: `total`, `next_offset` e `totals` do conjunto inteiro | Decisão do dono: o modelo precisa saber quantos são e conseguir chegar a todos |
| D12 | Recusa não é tool: o que não tem tool não pode ser executado | 7 das 60 perguntas não chamam nenhuma tool |
| D13 | Sem RAG e sem vetores; a dúvida sobre regulamentos não será levada ao recrutador | Decisão do dono; a base não tem texto de conhecimento (seção 5) |
| D14 | `get_ontology` não entra agora; é um experimento posterior, medido no eval | Cada busca custa uma ida e volta ao modelo |
| D15 | Dívida usa faturas `OVERDUE` e `PARTIAL` já vencidas, pelo saldo | Bate com a posição de 31/10 em 273/273 contratos[^banco] |

| D16 | Paginar em memória na application: o repositório traz o conjunto filtrado do aluno, o service calcula `totals` e recorta a página | O maior conjunto é de 115 disciplinas, 73 faturas e 76 pagamentos, e não cresce com o número de alunos. `sum` em SQL falha porque as colunas são `text`[^banco] |
| D17 | LangChain será o framework do agente. Nesta tarefa, as tools são métodos comuns, sem importar nenhum framework | Decisão do dono: considera tools e skills mais diretas nele. Versão e API são conferidas no spec do agente |
| D18 | `propose_protocol` valida e devolve a proposta, sem gravar. Rascunho e confirmação entram junto com a página de chat | Script novo em `db/init/` só roda em volume novo, o que exige `down -v` pelo dono, e sem a página ninguém confirma |
| D19 | `domain/ports.py` vira o pacote `domain/ports/`, com um módulo por área | Permite tarefas paralelas sem editar o mesmo arquivo. A frase do `CLAUDE.md` que cita `domain/ports.py` é atualizada em T4 |
| D20 | "Pagador próprio" é calculado na carga da sessão, em uma consulta privada sobre uma tabela local do SQLAlchemy Core, fora de `Base.metadata`. O resultado entra como `self_paid_contract_ids`, e `CustomerRow` segue sem `taxId` | FI-05 precisa comparar o CPF, e a arquitetura (5.4) proíbe `CustomerRow` de expor `taxId`. Dois models na mesma tabela conflitariam no `Base.metadata` |
| D21 | A tool de conta do AVA se chama `get_lms_account`, não `get_lms_access` | Ela devolve a situação da conta, não um acesso |

## 4. Escopo

### Dentro

- Classe `Ontology`, as 54 instâncias, os renderizadores e `docs/ontology.md` gerado.
- Correção de dívida e relógio injetado.
- `StudentSession` completa para os 4 sistemas, com ownership de todas as tabelas usadas.
- Envelope de resposta, paginação e registro de tools.
- As 19 tools, com domínio, repositórios e services.
- Mapa das 60 perguntas para tools e ontologias, testado, como semente do golden set.
- Testes de invariantes sobre todas as tools.

### Fora

| Item | Entra quando |
|---|---|
| Loop do agente e registro das tools no LangChain | No spec do agente. Troca `pydantic-ai-slim` em `pyproject.toml:14` e pede ao dono que ajuste `.importlinter:56` e `tests/lint/test_import_contracts.py:80`, que hoje protegem o domínio só contra `pydantic_ai` |
| Texto das skills e carregamento | No spec do agente; esta tarefa entrega `OntologyRenderer.for_skill` |
| Golden set com gabarito em SQL e execução de eval | Depois do agente; o mapa desta tarefa é o ponto de partida |
| `get_ontology` | Se o eval mostrar falha em CR, SR ou DU com só skills |
| Rascunho, confirmação e gravação do protocolo | Com a página de chat; exige `04_agent_schema.sql` e recarga pelo dono |
| `02_constraints.sql`, `03_indexes.sql`, `05_roles.sql` | Em tarefa própria; índices derivam das consultas criadas aqui |
| Evidência e citação na UI | No item "Contrato de resposta" das pendências |
| JWT e log estruturado | Em tarefa própria de produção |

## 5. Terreno: como a codebase faz hoje

**O bug de dívida:**

- `src/api/domain/invoice.py:17` e `:27` tratam toda `PARTIAL` como dívida. Das 6 faturas, 3 só vencem em 05/11/2026.[^banco]
- `src/api/application/dto/invoice_dto.py:24` devolve o líquido. A fatura `7067951` tem líquido de R$ 174,93 e R$ 81,01 pagos: o saldo é R$ 93,92.[^banco]
- `tests/unit/test_invoice.py:19` e `tests/integration/test_financial_service.py:35` afirmam o comportamento errado e precisam mudar junto.

**O que reaproveitar:**

- `RepositoryAdapter.fetch` (`src/api/persistence/repository_adapter.py:21`) aplica ownership em toda consulta. Ele usa `scalars`, então devolve só a primeira coluna: a consulta deve selecionar o model inteiro ou um único valor.
- `QueryGuard` (`src/api/persistence/query_guard.py:29`) permite `count`, `sum`, `min` e `max`. Testado contra o banco: `limit`, `offset`, `count` e `JOIN` passam. `sum` em coluna `text` falha no Postgres, e `cast` não está na lista de permitidos.
- `OwnershipRegistry` (`src/api/persistence/ownership_registry.py:8`) só conhece finance e sag. `ApiFactory` (`src/api/main.py:16`) recusa subir com tabela sem declaração.
- `SqlOracle` (`tests/integration/sql_oracle.py`) é o gabarito independente dos testes.
- `FinancialService` (`src/api/application/financial_service.py:5`) mostra o padrão: service recebe o port e devolve DTO.

**O que falta:**

- `StudentSession` (`src/api/domain/session.py:5`) só tem `person_ids` e `contract_ids`. A forma completa está na seção 5.2 da arquitetura.
- Não há `src/api/presentation/tools/`, `persistence/lms/` nem `persistence/secretary/`.

**Regras do linter que afetam o desenho:**

- Docstring só em `src/api/presentation/tools/` (`quality.toml:1`). É o único lugar da descrição de uma tool.
- Limites: 300 linhas por módulo, 150 por classe, 30 por função (`quality.toml:29`). As ontologias precisam de um módulo por área.
- O domínio só usa biblioteca padrão de uma lista, que inclui `dataclasses` e `enum` (`quality.toml:4`). Ler arquivo está fora, o que favorece declarar em Python.
- O framework do agente não pode entrar em domain nem persistence (`.importlinter`).

**Por que não há RAG:** a maior fonte de texto é `secretary.protocol_interaction.Message`, com 14.853 linhas, 75 textos distintos sem contar dígitos e 36 caracteres em média. Os comentários de pesquisa têm 5 textos distintos.[^banco]

**Volumes por aluno, que justificam a paginação:**[^banco]

| Conjunto | Máximo |
|---|---|
| Disciplinas cursadas por matrícula | 115 |
| Disciplinas por matriz | 40 |
| Faturas por contrato | 73 |
| Pagamentos por contrato | 76 |
| Eventos do AVA por conta de aluno | 592 |

## 6. Desenho

### 6.1 Ontologia

```python
DIVIDA = Ontology(
    key="divida",
    name="Dívida",
    area=Area.FINANCE,
    synonyms=("débito", "quanto devo", "em atraso"),
    definition="Faturas vencidas mais o saldo de parciais vencidas, com multa e juros. "
    "Não inclui faturas a vencer nem renegociadas.",
    source=System.FINANCE,
    origin=Origin.CONFIRMED,
    evidence="Bate com a posição de 31/10 em 273/273 contratos.",
    data=("finance.invoice", "finance.payment", "finance.late_charge"),
    caveat=None,
    never_say=("Somar mensalidade a vencer à dívida",),
    relations=(
        Relation(COMPOSED_OF, "multa_e_juros", note="Multa de 2% e juros de 1% ao mês."),
        Relation(
            NOT_IMPLIES,
            "bloqueio_de_diploma",
            note="Não afirme que a dívida impede o diploma.",
            evidence="14 formados têm dívida e diploma.",
        ),
    ),
)
```

| Campo | Conteúdo | Quem recebe |
|---|---|---|
| `key`, `name` | Identificador e nome, em português | Todos |
| `area` | Skill em que o conceito entra | Renderizador |
| `synonyms` | Como o aluno fala | Skill, eval |
| `definition` | O que significa | Skill, eval, documento |
| `source` | Sistema oficial do tema | Skill, documento |
| `origin` | Como sabemos | Eval, documento |
| `evidence` | Medição ou decisão que sustenta | Documento, nunca o modelo |
| `data` | Tabelas envolvidas | Documento, nunca o modelo |
| `caveat` | Aviso obrigatório quando a regra é usada | Skill, resultado de tool, eval |
| `never_say` | O que o agente não pode afirmar | Skill, juiz do eval |
| `relations` | Ligações com outras ontologias | Skill, eval, documento |

**Pontos debatidos e fechados:**

- **A tool declara a ontologia, não o contrário:** o domínio não pode conhecer a presentation. É a inversão do `answered_by` da pesquisa.
- **Conteúdo e `key` em português, campos em inglês:** segue o código existente e D3.
- **Sem campo `questions`:** o mapa de perguntas aponta para as ontologias (T10), o que evita duas listas.

**`Origin`:**

| Valor | Na resposta | No eval |
|---|---|---|
| `CONFIRMED` | Afirma | Compara com o gabarito em SQL |
| `INFERRED` | Afirma e dá o aviso | Reprova se faltar o aviso |
| `POLICY` | Aplica o limite | Juiz usa `never_say` |
| `ABSENT` | Diz que não tem e oferece um caminho | Reprova se inventar |

**As 54 ontologias:**

| Área | Qtd. | `key` (origem, quando não é `CONFIRMED`) |
|---|---|---|
| Acadêmico: vínculo | 12 | `matricula`, `rematricula`, `trancamento`, `matriz`, `pre_requisito`, `oferta`, `tcc_e_estagio`, `projeto_integrador`, `data_de_referencia` (`POLICY`), `regras_de_trancamento` (`ABSENT`), `calendario_2027` (`ABSENT`), `impedimento_por_pre_requisito` (`ABSENT`) |
| Acadêmico: desempenho | 10 | `resultado`, `av` (`INFERRED`), `media` (`INFERRED`), `criterio_de_aprovacao` (`INFERRED`), `frequencia` (`INFERRED`), `cr`, `conclusao`, `registro_oficial` (`POLICY`), `sala_e_horario` (`ABSENT`), `bloqueio_de_diploma` (`ABSENT`) |
| Financeiro | 14 | `divida`, `multa_e_juros`, `proximo_boleto`, `pagamento`, `estorno`, `bolsa`, `mensalidade`, `parcela_de_acordo`, `acordo`, `quitacao`, `pagador` (`POLICY`), `cobranca` (`POLICY`), `criterios_de_bolsa` (`ABSENT`), `negativacao` (`ABSENT`) |
| Protocolos | 6 | `protocolo`, `servico`, `prazo_de_atendimento`, `taxa_de_servico`, `documento_emitido`, `pedido_de_terceiro` (`POLICY`) |
| Ambiente virtual | 7 | `prova_online`, `nota_do_ava`, `visualizacao_de_material`, `tentativa` (`INFERRED`), `ultimo_acesso` (`INFERRED`), `gabarito` (`ABSENT`), `suspensao_do_ava` (`ABSENT`) |
| Visão geral | 2 | `periodo_coberto`, `pendencia` (`POLICY`) |
| Limites | 3 | Todas `POLICY`: `outros_alunos`, `dados_internos`, `identidade` |

As definições, os avisos e as evidências saem do catálogo, inclusive da seção "Origem das regras". Número usado em `evidence` é remedido no banco.

**As relações:**

| Tipo | Origem → destino | Perguntas |
|---|---|---|
| `COMPOSED_OF` | `divida` → `multa_e_juros`; `mensalidade` → `bolsa` | FI-01, FI-07 |
| `LEADS_TO` | `servico` → `taxa_de_servico`; `servico` → `acordo`; `acordo` → `parcela_de_acordo` | FI-08, CR-06, CR-08 |
| `NOT_IMPLIES` | `divida` → `bloqueio_de_diploma`; `divida` → `suspensao_do_ava`; `pre_requisito` → `impedimento_por_pre_requisito`; `protocolo` → `taxa_de_servico`; `trancamento` → `quitacao`; `matricula` → `quitacao`; `cobranca` → `negativacao` | CR-02, CR-03, DU-04, CR-05, CR-06, CR-07, CR-08, FI-09 |
| `NOT_SAME_AS` | `nota_do_ava` → `registro_oficial`; `parcela_de_acordo` → `mensalidade`; `tcc_e_estagio` → `projeto_integrador`; `estorno` → `pagamento`; `prazo_de_atendimento` → `regras_de_trancamento` | CR-04, CR-06, DU-03, FI-03, SR-02 |

**Validação:**

- `key` é única e todo destino de relação existe.
- `INFERRED` e `ABSENT` exigem `caveat`.
- `NOT_IMPLIES` exige `evidence` e `note`.
- Toda ontologia aparece em ao menos uma pergunta do mapa (T10).
- Toda ontologia `CONFIRMED` ou `INFERRED` é declarada por ao menos uma tool, salvo as usadas só como destino de relação, que ficam listadas explicitamente no teste.

### 6.2 Como a ontologia chega a cada consumidor

| Consumidor | O que recebe | Quem entrega |
|---|---|---|
| Prompt | Nada; só a regra geral de não afirmar sem fonte | Spec do agente |
| Descrição de tool | Nada; só o que a tool faz e quando chamar | Docstring |
| Resultado de tool | `caveat` da regra aplicada, só quando foi usada | Service, usando a ontologia |
| Skill | `name`, `synonyms`, `definition`, `caveat`, `never_say` e relações da área | `OntologyRenderer.for_skill(area)` |
| Documento | Tudo | `OntologyRenderer.for_document()` |
| Eval | Tudo, por `key` | Importação direta |

`for_skill` inclui relações em que o conceito é origem ou destino. Assim, a skill do AVA também mostra "dívida não implica suspensão", que nasce em `divida`. Ela não inclui `evidence` nem `data`, e um teste procura esses textos na saída.

### 6.3 Envelope de resposta

```json
{
  "status": "ok",
  "data": [],
  "page": {"offset": 0, "limit": 20, "total": 73, "next_offset": 20},
  "totals": {"net": "41234.50"},
  "caveats": [{"ontology": "criterio_de_aprovacao", "text": "Não há regulamento na base; é uma estimativa."}],
  "coverage": {"from": "2023-01-15", "note": "O ambiente virtual só tem registros a partir desta data."},
  "candidates": []
}
```

| Campo | Regra |
|---|---|
| `status` | `ok`, `empty`, `not_found`, `ambiguous` ou `refused` |
| `page` | Só em tools de lista. `limit` padrão 20, máximo 100. `next_offset` é nulo na última página |
| `totals` | Calculados sobre todo o conjunto filtrado, nunca sobre a página |
| `caveats` | Só quando a regra foi aplicada neste resultado |
| `coverage` | Quando o período pedido pode estar fora dos dados |
| `candidates` | Em `not_found` e `ambiguous`, com código e nome |

**Estado do dado:** valor que pode faltar usa `{"state": "recorded", "value": ...}`. Os outros estados são `not_yet` (AV2 ainda não aconteceu) e `not_recorded` (frequência em EAD). Vazio, zero e não registrado nunca se confundem.

**Mesma resposta:** dado de outra pessoa e dado inexistente devolvem o mesmo `not_found`, com os mesmos candidatos do próprio aluno.

**Ordem estável:** toda lista tem ordem total, terminando no identificador, para a paginação não repetir nem pular linhas.

### 6.4 As 19 tools

Paginadas têm `page: PageRequest = FIRST_PAGE`, com `offset` e `limit`, omitido abaixo. `enrollment` aceita a referência devolvida por `list_enrollments` e, sem ele, a tool cobre todas as matrículas e identifica cada resultado.

| Tool | Parâmetros | O que devolve | Ontologias | Perguntas |
|---|---|---|---|---|
| `get_academic_calendar` | `term?` | Períodos de AV e último semestre cadastrado | `data_de_referencia`, `calendario_2027`, `periodo_coberto` | DU-01, VA-09, SR-04 |
| `list_course_offers` (paginada) | `course?`, `modality?`, `unit?` | Oferta da marca do aluno, por unidade e turno | `oferta` | DU-05 |
| `list_services` | `area?` | Serviço, taxa, prazo e se o agente pode abrir | `servico`, `taxa_de_servico`, `prazo_de_atendimento` | DU-06, PR-06, CR-02 |
| `list_enrollments` | nenhum | Status, histórico, rematrícula, CR e conclusão | `matricula`, `rematricula`, `trancamento`, `cr`, `conclusao` | VA-01, VA-07, VA-09, PR-08, CR-03, CR-05, CR-06, CR-07 |
| `get_curriculum` (paginada) | `enrollment?`, `semester?`, `subject?`, `pending_only?` | Matriz com a situação do aluno e resumo de horas | `matriz`, `pre_requisito`, `tcc_e_estagio`, `projeto_integrador`, `conclusao` | DU-02, DU-03, DU-04, VA-08 |
| `list_subject_records` (paginada) | `enrollment?`, `term?`, `subject?` | Notas, frequência, resultado, turma, turno e AV2 necessária | `resultado`, `av`, `media`, `criterio_de_aprovacao`, `frequencia`, `registro_oficial` | VA-02 a VA-06, VA-09, PR-06, CR-08, SR-01 |
| `list_subject_professors` | `subject`, `term?` | Só nome e e-mail institucional, na marca do aluno | `dados_internos` | RE-04 |
| `get_financial_summary` | nenhum | Por contrato: dívida, próximo boleto, bolsas, tipo de pagador e situação | `divida`, `multa_e_juros`, `proximo_boleto`, `bolsa`, `pagador`, `cobranca` | FI-01, FI-02, FI-05, FI-06, FI-09, CR-02, CR-03, CR-05, CR-07, SR-03 |
| `list_invoices` (paginada) | `status?`, `kind?`, `period?` | Faturas com pagamentos, estornos e saldo | `mensalidade`, `parcela_de_acordo`, `estorno`, `pagamento`, `quitacao` | FI-03, PR-07, CR-05 |
| `list_payments` (paginada) | `year?` | Só confirmados, em horário de Brasília, com total e estornos à parte | `pagamento`, `estorno` | FI-04 |
| `get_tuition_changes` | nenhum | Cada mudança de valor, com a causa | `mensalidade`, `bolsa` | FI-07, SR-04 |
| `list_agreements` | nenhum | Parcelas pagas e restantes, valores e vencimentos | `acordo`, `parcela_de_acordo` | FI-08, CR-06 |
| `list_protocols` (paginada) | `status?`, `service?`, `period?` | Protocolos com situação de prazo e documentos | `protocolo`, `documento_emitido`, `prazo_de_atendimento`, `pedido_de_terceiro` | PR-02, PR-04, PR-08, CR-03, SR-05 |
| `get_protocol` | `number` | Andamento, prazo, mensagens públicas, documentos e taxa | `protocolo`, `documento_emitido`, `taxa_de_servico`, `dados_internos` | PR-01, PR-03, PR-09, CR-08, RE-05 |
| `propose_protocol` | `service`, `enrollment?`, `message` | Proposta para o aluno confirmar; recusa serviço com taxa e pedido duplicado | `servico`, `taxa_de_servico`, `prazo_de_atendimento` | PR-05, PR-07, PR-08, RE-08 |
| `list_online_exams` (paginada) | `subject?`, `term?` | Janela, duração, tentativas restantes, nota do AVA e nota oficial | `prova_online`, `tentativa`, `nota_do_ava`, `registro_oficial`, `gabarito` | DU-01, LM-01 a LM-03, CR-04, SR-05 |
| `get_lms_account` | nenhum | Por conta: se existe, se está suspensa e último acesso | `ultimo_acesso`, `suspensao_do_ava` | LM-04, CR-02 |
| `list_material_views` (paginada) | `subject`, `query?` | Material e acessos, sem o conteúdo | `visualizacao_de_material` | LM-05 |
| `get_pending_items` | nenhum | O que foi verificado nos 4 sistemas e o que merece atenção | `pendencia`, `matricula`, `divida`, `frequencia`, `protocolo`, `prova_online` | CR-01 |

**Sem tool:** SR-02, RE-01, RE-02, RE-03, RE-06, RE-07 e RE-09.

**Pontos debatidos e fechados:**

- **`get_pending_items`:** define "pendência" em um lugar só. Verifica matrícula e rematrícula, dívida, vencimentos dos próximos 30 dias, protocolos em andamento, disciplinas abaixo de 75% e provas com janela aberta, sempre devolvendo `checked`.
- **Regras de `propose_protocol`:** aceita só os 14 serviços sem taxa (B27). Com mais de uma matrícula e sem `enrollment`, devolve `ambiguous`. Com pedido igual em andamento, devolve `refused`. A mensagem é guardada como dado.
- **Descrição:** no máximo 200 caracteres. Um teste confere o limite e guarda um snapshot.

### 6.5 Busca por nome

`subject` e `course` são filtros de texto. A tool normaliza caixa e acento e compara com o código e o nome em inglês, só dentro do que o aluno pode ver.

| Situação | Resposta |
|---|---|
| Uma correspondência | `ok` |
| Várias, em uma tool que aceita várias (VA-03) | `ok` com todas |
| Várias, onde é preciso uma | `ambiguous`, com candidatos |
| Nenhuma | `not_found`, com as disciplinas do aluno como candidatos |

Exemplo: "Programação II" não casa com nada, a tool devolve a matriz do aluno (no máximo 40 itens), e o modelo escolhe `ADS0102` e chama de novo. O custo é uma ida e volta a mais, só nesse caso.

### 6.6 Sessão

`StudentSession` ganha os identificadores da seção 5.2 da arquitetura: `enrollment_keys`, `brands`, `lms_user_ids`, `protocol_ids` e `self_paid_contract_ids` (D20). Regras que não mudam:

- `protocol_ids` segue a cascata de A7 e *fail closed*: 3.882 de 3.933 protocolos resolvidos, 51 invisíveis (B28, B30).
- O CPF é normalizado e fica só nas consultas privadas da carga, com `repr=False`.
- Tabelas de catálogo da marca usam cláusula pela marca da sessão; `analyst` não é mapeada.

### 6.7 Relógio

Port `Clock` no domínio. A implementação lê `reference_date` de `Settings`, com padrão 2026-10-31, e os testes injetam a data. Datas em UTC viram horário de Brasília nos mappers, porque FI-04 e LM-04 dependem disso.

### 6.8 Testes

| Camada | O que prova |
|---|---|
| Unitário | Regras de domínio, validação da ontologia, renderizadores, página e envelope |
| Integração | Cada tool contra o banco, comparada ao `SqlOracle` e aos casos do catálogo |
| Invariantes | Seção 7, sobre todas as tools do registro |

## 7. Consequências

**Fica melhor:**

- O significado fica em um lugar só e abastece skills, evals e documento.
- As armadilhas entre sistemas viram relações testáveis.
- O agente chega a qualquer registro sem estourar o contexto.

**Fica pior ou mais caro, e aceitamos:**

- Sem tabela de tradução, o nome de uma disciplina pode variar entre respostas, e o eval precisa comparar código e valor, não texto.
- Sem `get_ontology`, a relação entre skills depende de `for_skill` trazer o destino. Medimos isso no eval.
- Paginar em memória lê o conjunto filtrado do aluno a cada chamada.
- As ontologias geram um volume grande de código declarativo, dividido por área.

**Riscos e mitigação:**

| Risco | Mitigação |
|---|---|
| O linter recusar a forma declarativa das ontologias | Relatar ao dono com o exemplo; nunca enfraquecer a regra |
| Modelo não chamar de novo depois de `not_found` | Medido no eval, com os casos de DU-04 e VA-03 |
| Definição ficar diferente do comportamento | Evals por ontologia e teste do mapa de perguntas |
| Skill grande demais com muitas ontologias | Medir o tamanho de `for_skill` por área em T1 e relatar |

**Não pode mudar:**

1. Nenhuma tool recebe identidade como parâmetro.
2. Parâmetros não ampliam resultados: um agente comprometido, chamando todas as tools com todos os argumentos, recebe zero linhas alheias.
3. Dado de outro aluno e dado inexistente têm a mesma resposta.
4. Nenhum CPF, nota interna, analista, dado do pagador ou etapa de cobrança aparece em DTO. De professor, só nome e e-mail (B35).
5. Nada de `evidence` ou `data` chega à saída de `for_skill` ou a um resultado de tool.
6. Paginar até o fim devolve exatamente o conjunto do `SqlOracle`, sem repetir nem pular, e `totals` não muda entre páginas.
7. Toda tabela mapeada tem ownership; a aplicação recusa subir sem isso.
8. Toda tool do registro tem descrição e ao menos uma ontologia.

## 8. Plano de implementação

| # | Tarefa | Depende de | Arquivos | Fronteira de teste | Pronto quando | Oráculo de verificação |
|---|---|---|---|---|---|---|
| T1 | `Ontology`, as 54 instâncias, validação, renderizadores e documento gerado | nenhuma | `domain/ontology/`, `tools/ontology_doc.py`, `docs/ontology.md`, `docs/index.md`, `tests/unit/test_ontology*.py` | Unitário | Validação e sincronia do documento verdes; o tamanho de `for_skill` foi relatado | Saída de `for_skill` sem texto de `evidence` ou `data`; números de `evidence` remedidos no banco |
| T2 | Corrigir dívida: `is_debt` com data, saldo por pagamentos confirmados, `Clock` e DTO | nenhuma | `domain/invoice.py`, `domain/ports.py`, `settings.py`, `application/financial_service.py`, `application/dto/invoice_dto.py`, `persistence/finance/models.py`, `persistence/finance/mappers.py`, `persistence/finance/repositories.py`, testes de fatura | Unitário e integração | Testes antigos corrigidos; `PARTIAL` a vencer fora da dívida | Principal e contagem batem com `receivable_snapshot` de 31/10 nos 273 contratos; a fatura `7067951` tem saldo de R$ 93,92 |
| T3 | Sessão completa e ownership de identidade dos 4 sistemas | nenhuma | `domain/session.py`, `persistence/student_session_repository.py`, `persistence/ownership_registry.py`, `persistence/lms/`, `persistence/secretary/`, `persistence/sag/*`, testes de sessão | Integração | Toda pessoa carrega sessão; partição provada | Reproduz A5: nenhuma linha em duas pessoas; 3.882 protocolos resolvidos; os 11 de terceiros invisíveis |
| T4 | Envelope, página, registro de tools, separação dos ports e esqueleto de services | T1 | `application/dto/tool_result.py`, `application/page.py`, `presentation/tools/registry.py`, `presentation/tools/*_tools.py` vazios, `domain/ports/`, novos `application/*_service.py` vazios, `CLAUDE.md` | Unitário | Página cobre início, meio, fim e vazio; registro valida descrição e ontologias | `make check` verde; imports de `domain.ports` atualizados |
| T5 | Tools acadêmicas e institucionais: calendário, ofertas, matrículas, matriz, disciplinas, professores | T3, T4 | `domain/academic*.py`, `domain/ports/academic.py`, `application/academic_service.py`, `application/dto/academic_*`, `persistence/sag/*`, `presentation/tools/academic_tools.py`, `tests/integration/test_academic_tools.py` | Integração | 6 tools no registro | VA-01 a VA-09, DU-01 a DU-05, RE-04 com os valores do catálogo; EAD devolve frequência `not_recorded` |
| T6 | Tools financeiras: resumo, faturas, pagamentos, mudanças de valor, acordos | T2, T3, T4 | `domain/finance*.py`, `domain/ports/finance.py`, `application/financial_service.py`, `application/dto/finance_*`, `persistence/finance/*`, `presentation/tools/finance_tools.py`, `tests/integration/test_finance_tools.py` | Integração | 5 tools no registro | FI-01 a FI-09 com os valores do catálogo, como R$ 277,05 em FI-01; FI-09 sem etapa de cobrança |
| T7 | Tools de protocolo e serviços, com `propose_protocol` sem gravar | T3, T4, T6 | `domain/protocol*.py`, `domain/ports/protocol.py`, `application/protocol_service.py`, `application/dto/protocol_*`, `persistence/secretary/*`, `presentation/tools/protocol_tools.py`, `tests/integration/test_protocol_tools.py` | Integração | 4 tools no registro | PR-01 a PR-09, DU-06; RE-05 sem nota interna ou analista; serviço com taxa `refused`; nenhuma escrita no banco |
| T8 | Tools do AVA: provas, conta, materiais | T3, T4, T5 | `domain/lms*.py`, `domain/ports/lms.py`, `application/lms_service.py`, `application/dto/lms_*`, `persistence/lms/*`, `presentation/tools/lms_tools.py`, `tests/integration/test_lms_tools.py` | Integração | 3 tools no registro | LM-01 a LM-05 e CR-04; horário convertido para Brasília; SR-05 devolve `coverage` |
| T9 | `get_pending_items` | T5, T6, T7, T8 | `application/overview_service.py`, `application/dto/overview_*`, `presentation/tools/overview_tools.py`, `tests/integration/test_overview_tools.py` | Integração | Tool no registro, com `checked` | CR-01 com `UniSaoPaulo:181820` igual ao catálogo; aluno sem pendências lista o que verificou |
| T10 | Mapa das 60 perguntas, fábrica das tools por sessão e testes de invariantes | T9 | `src/api/main.py`, `tests/agent_map.py`, `tests/integration/test_tool_invariants.py`, `tests/unit/test_agent_map.py` | Unitário e integração | Invariantes da seção 7 verdes, rodando contra `StudentToolsFactory` | 60/60 perguntas mapeadas; agente comprometido em todas as tools recebe zero linhas alheias; paginação até o fim igual ao oráculo |
| T11 | Propor as correções em `architecture.md` e marcar pendências | T10 | `docs/architecture.md`, `docs/pendencias.md` | Nenhuma | Dono aprovou | Seções 5.9 e 9 refletem D3, D9, D11 e D13; correção de sentido só com aprovação do dono |

### Ondas e paralelismo

- **Onda 0 (fundação):** T1, T2, T3. Arquivos disjuntos.
- **Onda 1:** T4.
- **Onda 2:** T5, T6. Arquivos disjuntos, graças a D19.
- **Onda 3:** T7 (usa a taxa do financeiro) e T8 (usa a nota oficial do acadêmico). Arquivos disjuntos, graças a D19.
- **Onda 4:** T9.
- **Onda 5:** T10.
- **Onda 6:** T11.

**Caminho crítico:** T1 → T4 → T6 → T7 → T9 → T10 → T11.

## 9. Para o agente executor

- **Comece por:** T1, T2 e T3.
- **Leia antes:** `CLAUDE.md`, seções 3, 5 e 6 de `docs/architecture.md`, `docs/question-catalog.md` e `docs/authoring-guide.md`.
- **Leia sempre:** este arquivo inteiro, com o Registro.
- **Não toque:** `ruff.toml`, `.flake8`, `.importlinter`, `mypy.ini`, `pyrightconfig.json`, `quality.toml`, `Makefile`, `tools/quality/` e `tests/lint/`. Se uma regra parecer errada, relate o exemplo e espere. Também não rode `docker compose down -v`.
- **Banco:** `docker compose up -d --wait api` sobe a API com o banco. Consultas de verificação são só de leitura.
- **Números:** `docs/eda.md` não é fonte. Remeça no banco o que for para ontologia ou teste. Valores do catálogo também são conferidos pelo `SqlOracle`.
- **Regras do repo:** sem comentários; docstring só em `presentation/tools/`; classes em vez de funções soltas; só a persistence importa SQLAlchemy; `relationship()` é proibido.
- **Gates:** commit local por tarefa aceita, feito só pelo condutor da execução, na branch `feat/ontologia-e-tools`, sem push; uma tarefa só termina com `make check` verde, e a saída é a prova; review por pontos numerados; decisão nova é confirmada com o dono, editada aqui e anotada no Registro antes de virar código.
- **Iteração:** perguntas em lote, numeradas, com a recomendação em cada uma.

## Notas de implementação

## Fontes

[^catalogo]: Catálogo de perguntas do aluno, inclusive as seções "Pedidos que o agente oferece" e "Origem das regras".
[^arquitetura]: Arquitetura do agente: B5, B7, B10, B26 a B28, B30, B35, A5, A7 e seções 5.2, 5.4 e 5.9.
[^auto-ontology]: NVIDIA Auto Ontology: `mcp/auto_ontology_mcp/tools.py` (descrição de tool como prompt), `mcp/auto_ontology_mcp/server.py` (`INSTRUCTIONS`) e `skills/nvidia-ontology-query/SKILL.md`.
[^banco]: Consultas de leitura de 2026-11-05 no banco local.

## Execução

### Execução de 2026-11-05

#### Registro de decisões

Repo: este, na branch `feat/ontologia-e-tools`, nascida da `main`.

Escopo, na ordem das ondas:

1. Ontologias, correção de dívida, sessão completa.
2. Envelope, paginação, registro de tools e separação dos ports (depois das ontologias).
3. Tools acadêmicas e tools financeiras (depois da sessão, do envelope e, nas financeiras, da dívida).
4. Tools de protocolo (depois das financeiras) e tools do AVA (depois das acadêmicas).
5. Lista de pendências (depois de todas as tools).
6. Mapa das 60 perguntas, fábrica das tools e invariantes.
7. Propostas em `architecture.md` e pendências, que dependem da sua aprovação.

Revisão por área, para economizar tokens: fundação; tools acadêmicas e financeiras, antes que as outras as imitem; tools restantes com invariantes.

| Decisão | Por quê | Quem decidiu | Tipo | Se mudar, afeta | Commit |
|---|---|---|---|---|---|
| Commit local por tarefa aceita, em branch própria, sem push | Isola o que cada revisão olha e permite desfazer uma tarefa. `git reset --soft main` devolve tudo ao working tree | você | pilar | Só o histórico | — |
| Modelo por risco: Opus em ontologias, sessão, envelope, tools acadêmicas, tools financeiras e invariantes; Sonnet em dívida, protocolos, AVA, pendências e textos | Pedido seu, para gastar Opus onde um erro se propaga | você | pilar | Custo e chance de retrabalho | — |
| Um revisor Opus por área pronta, não por tarefa, e o gate do condutor em toda tarefa | Orçamento de tokens limitado; o revisor sugere também refatorações | você | pilar | Profundidade da revisão | — |
| A fábrica `StudentToolsFactory` fica em `src/api/main.py`, criada na tarefa de invariantes; as tarefas de tools não tocam em `main.py` | Os invariantes provam a mesma montagem que o agente usará, e as ondas paralelas não disputam o arquivo | você | pilar | Tarefa de invariantes e spec do agente | — |
| Suas alterações em `docs/index.md` e `docs/pendencias.md` e a pasta `docs/plans/` ficam fora dos commits | São trabalho seu em andamento | você | detalhe | Só o histórico | — |
| As 9 ontologias ausentes ficam na área do tema, e "Ausentes" deixa de ser área | Só assim a skill do AVA mostra que dívida não implica suspensão, a armadilha da pergunta CR-02 | você | pilar | Ontologias e o conteúdo de cada skill | — |
| Nas 7 tools paginadas, `offset` e `limit` viram um único parâmetro `page` | `get_curriculum` passaria de 5 parâmetros, limite do linter; você preferiu a forma uniforme a aninhar só os filtros dela | você | pilar | O esquema das 7 tools e o `PageRequest` | — |
| Fatura cancelada ou renegociada tem saldo zero | Mostrar o líquido contaria em dobro com as parcelas do acordo (CR-06); são 98 canceladas e 196 renegociadas | o condutor, após a revisão | detalhe | `Invoice.balance` | — |
| `for_skill` mostra a `key` no título do conceito; `source` segue fora | Os avisos do envelope citam a ontologia por `key`, e §6.1 e §6.2 divergiam; custa cerca de 5 tokens por conceito | o condutor, após a revisão | detalhe | Uma linha em `SkillFormat` | — |
| Vazio tem uma forma só: `status: empty` com `data: []` | A primeira versão tinha duas formas, e uma lista sem itens saía como `ok` | o condutor, após a revisão | detalhe | Fábricas de `ToolResult` | — |
| O registro aceita só parâmetros de uma lista permitida, tirada das 19 tools | Lista de termos proibidos deixava passar `stu_id` e `aluno`, enfraquecendo a garantia de que nenhuma tool recebe identidade | o condutor, após a revisão | detalhe | `registry.py`; tool com parâmetro novo edita a lista | — |
| Próximo boleto é a primeira fatura em aberto ou parcial que vence depois da data de referência, cobrada pelo saldo | Em FI-02 equivale à "primeira em aberto" do catálogo; as 3 parciais de 05/11 passam a mostrar o que falta pagar | o implementador, conferido pelo condutor | detalhe | Ontologia `proximo_boleto` e resumo financeiro | c1974bf |
| As tools financeiras não emitem aviso de negativação no resultado; ele chega pela skill | As ontologias que elas declaram não têm aviso; declarar `negativacao` no resumo é escolha sua | o implementador | detalhe | `get_financial_summary` | c1974bf |
| Referência de matrícula é `marca de origem:RA`, como `UniMontanhas:070017` | É a forma que o catálogo usa | o implementador | detalhe | Parâmetro `enrollment` das tools acadêmicas e de protocolo | d60e449 |
| O teste que proíbe colunas de contato aceita só o e-mail do professor | O aluno vê nome e e-mail institucional do professor (B35, RE-04); o resto segue proibido | o condutor | detalhe | Um teste de ownership | d60e449 |
| O tipo de pagador volta a ser calculado na carga da sessão; `finance.customer` e `contract.customerid` saem do metadata comum | As tools financeiras tinham reaberto o vínculo com o pagador a qualquer consulta, contra a decisão sobre CPF e pagador | o condutor, após a revisão | detalhe | Sessão e repositório financeiro | — |
| "Não existe" é nulo ou situação explícita, nunca `not_recorded`: próximo boleto, fim de bolsa, disciplina não cursada | 409 contratos sem próximo boleto e 151 bolsas sem fim sairiam como "não tenho a informação" | o condutor, após a revisão | detalhe | DTOs do resumo financeiro e da matriz | — |
| Fatura em aberto que vence no dia de referência é o próximo boleto | Com dívida só para vencimento anterior, ela sumia do resumo no próprio dia | o condutor, após a revisão | detalhe | `Invoice.is_upcoming` | — |
| `period` compara ano ou mês exatos; `not_found` traz no máximo 40 candidatos | Prefixo fazia "2025-1" trazer outubro a dezembro; um erro de digitação devolvia até 78 candidatos | o condutor, após a revisão | detalhe | Filtros e busca por nome, também nas tools de protocolo e do AVA | — |
| A cobertura do AVA começa em 01/02/2023, início das salas de turma e do log, e não em 15/01/2023 | O catálogo cita só a data das 40 salas institucionais; provas e acessos só existem a partir de fevereiro | o condutor | detalhe | `coverage` das tools do AVA e SR-05 | 12dfa6c |
| Sala do AVA liga à disciplina pelo nome curto da sala, não pelo `idnumber` | 965 salas têm `idnumber` nulo, uma delas de aluno com turma | o implementador | detalhe | Mapper das provas | 12dfa6c |
| O aviso sobre tentativa abandonada só sai quando há tentativa abandonada no resultado | É quando a inferência sobre o limite foi aplicada | o implementador | detalhe | `list_online_exams` | 12dfa6c |
| Nota interna de protocolo nem chega a ser lida: a ownership das mensagens só deixa passar as públicas | Mais forte que filtrar no DTO; analista, autor e assinante não são mapeados | o implementador, conferido pelo condutor | detalhe | Mensagens de protocolo | e173cac |
| `propose_protocol` recusa mensagem em branco e serviço inativo, além de serviço com taxa e pedido duplicado | Não estava no spec; hoje todos os serviços estão ativos | o implementador | detalhe | Regras da proposta | e173cac |
| Protocolo que vence no dia de referência ainda está dentro do prazo | Mesma fronteira das faturas | o implementador | detalhe | Situação de prazo | e173cac |
| Pendência de matrícula é só trancada ou ativa sem rematrícula; de frequência, só disciplina em andamento abaixo de 75%; vencimentos são os próximos 30 dias, pelo saldo | Histórico reprovado e EAD sem frequência não são pendência | o implementador | detalhe | `get_pending_items` | 07c7ecf |
| `get_pending_items` repassa só os avisos das ontologias que declara | Sem o filtro, o histórico de um formado trazia avisos de média e AV2 que não se aplicam | o implementador | detalhe | `get_pending_items` | 07c7ecf |
| Uma fixture carrega as 1.000 sessões uma vez para os testes que varrem todos os alunos | O `make check` tinha chegado a 3min30, e metade disso eram quatro varreduras repetidas; caiu para 92s | o condutor, a seu pedido sobre o tempo | detalhe | Testes de integração | 7db58fb |
| `list_subject_professors` ignora turma sem professor | O invariante do agente comprometido achou um erro 500 em RE-04: 739 de 11.051 turmas não têm professor | o condutor | detalhe | Mapper de professores | 7db58fb |
| A montagem das tools fica no pacote `src/api/composition/`, uma camada abaixo de `main` | `main.py` passaria de 12 imports. `CLAUDE.md` ajustado; a linha no `.importlinter` fica com você | você | pilar | `.importlinter` e `CLAUDE.md` | 7db58fb |
| O saldo da fatura desconta o principal dos pagamentos confirmados, não o valor total pago; estornados ficam de fora | O valor total inclui multa e juros, e só o principal bate com a posição de 31/10 em 273 de 273 contratos | o implementador, conferido pelo condutor | detalhe | Saldo de fatura e dívida | 0b5c7dd |
| Fatura que vence exatamente na data de referência ainda não é dívida | "Vencida" é vencimento anterior à data. Não há fatura `OVERDUE` ou `PARTIAL` vencendo em 31/10, então o dado não distingue | o implementador, conferido pelo condutor | detalhe | Uma comparação em `Invoice.is_debt` | 0b5c7dd |
| O relógio `ReferenceClock` fica em `settings.py` | É a camada que conhece `Settings`; o domínio só vê o port `Clock` | o implementador | detalhe | Um import na composição | 0b5c7dd |
| Protocolo com ID que existe em qualquer matrícula não cai na regra por CPF, mesmo em outra marca | *Fail closed* mais estrito. Hoje são 0 linhas; o custo é esconder o pedido de quem digitou um ID que colide em outra marca | o implementador, conferido pelo condutor | detalhe | Cascata de protocolo em `secretary/dialect.py` | 482fddf |
| Contas do AVA ligam à pessoa só por `student_id` | Reproduz os 18.566 de 18.857 tentativas da arquitetura. Ficam invisíveis 7 contas sem `student_id` (65 tentativas) | o implementador, conferido pelo condutor | detalhe | Regra de `LmsDialect.account_of` e tools do AVA | 482fddf |
| CPF, dados do requerente e `contract.customerid` ficam em tabelas Core locais, fora de `Base.metadata` | Estende a decisão sobre pagador próprio a `sag.person` e `secretary.protocol`; o adapter recusa essas tabelas | o implementador, conferido pelo condutor | detalhe | `identity_tables.py` e `identity_queries.py` | 482fddf |

#### Plano de review

Resumo: as 11 tarefas ficaram prontas, em 14 commits locais na branch `feat/ontologia-e-tools`, sem push. São 54 ontologias, 19 tools, o envelope com paginação, a correção da dívida, a sessão dos 4 sistemas, o mapa das 60 perguntas e os 8 invariantes de segurança. `make check` verde com 606 testes em cerca de 2 minutos. Houve três revisões por área; elas acharam 5 bloqueantes, todos corrigidos com teste.

**Precisa da sua decisão**

1. Incluir `api.composition` no `.importlinter`, logo abaixo de `api.main`?
   O pacote monta as tools por aluno e hoje passa sem restrição de camada. O `CLAUDE.md` já cita o pacote.
   Recomendo: incluir. Talvez `tests/lint/test_import_contracts.py` precise registrar a camada.
2. Saldo zero para fatura cancelada ou renegociada, e próximo boleto incluindo parcial, cobrado pelo saldo?
   Sem isso, renegociadas somariam em dobro com as parcelas do acordo. Mudar custa uma regra em `Invoice`.
3. O aviso de negativação deve vir no resultado de `get_financial_summary`, e não só pela skill?
   Hoje nenhuma tool financeira emite aviso, porque as ontologias delas não têm `caveat`. Mudar custa declarar `negativacao` na tool.
4. A cobertura do AVA começa em 01/02/2023 (salas de turma e log), não em 15/01/2023, que é a data citada no catálogo para SR-05.
   O golden set de SR-05 deve seguir o banco.

**Onde olhar**

Segurança
- `src/api/persistence/secretary/ownership.py`: a nota interna é barrada dentro da regra de ownership das mensagens.
- `src/api/persistence/identity_tables.py` e `payer_queries.py`: CPF, requerente e pagador ficam fora do metadata comum.
- `tests/integration/test_tool_invariants.py` e `test_tool_volumes.py`: o agente comprometido e as contagens contra o SQL. Uma regra trocada por `Public()` deixa os testes vermelhos, conferido por mutação.

Contrato das tools
- `src/api/application/dto/tool_result.py` e `src/api/presentation/tools/registry.py`: é o que o agente LangChain vai consumir.

Dinheiro
- `src/api/domain/invoice.py`: saldo, dívida, próximo boleto e multa e juros. Oráculo: a posição de 31/10 nos 273 contratos.

**Pode pular**
Mappers, vocabulários de tradução da origem, DTOs e helpers de teste das áreas.

Simplificação possível, sem efeito: `ProtocolService` só repassa para `ProtocolQueries` e `ProtocolProposer`. As áreas de protocolo e de pendências têm muitas classes pequenas, para caber nos limites do linter.

Para consulta: registro de decisões acima e checkpoints no `## Registro`; o primeiro commit é 0b5c7dd e o último é 3309b5d.

## Registro

**Checkpoint de implementação** · 2026-11-05 · Propostas em `architecture.md` e pendências · 940be94

| Critério | Evidência |
|---|---|
| Dono aprovou | Os 10 itens aprovados na conversa, 2 deles mudando sentido: composição na árvore de camadas e RAG fechado |
| 5.9 e 9 refletem D3, D9, D11 e D13 | Parâmetros amigáveis, respostas das tools e a linha de RAG reescritos |
| Pendências marcadas | Ontologia, topologia de tools e contrato de resposta marcados; framework reescrito. `docs/pendencias.md` ficou fora do commit, junto com as alterações anteriores do dono |

**Correções da revisão final** · 2026-11-05 · 3309b5d

Os invariantes ganharam contagens contra o SQL para tentativas de prova, acessos a material, mensagens e histórico de protocolo. Duas mutações de ownership para `Public()` deixaram os testes vermelhos. A nota oficial do AVA passou a casar também pela marca; hoje não há colisão no banco. As pendências agora consultam as áreas em paralelo. `make check` verde com 606 testes.

**Checkpoint de implementação** · 2026-11-05 · Mapa, fábrica e invariantes · 7db58fb

| Critério | Evidência |
|---|---|
| 60/60 perguntas mapeadas | `tests/unit/test_agent_map.py`: códigos lidos do catálogo, tools iguais às do registro, até 3 por pergunta, 54 ontologias cobertas |
| Agente comprometido recebe zero linhas alheias | `test_compromised_agent_gets_no_identifier_of_other_people`, com controle positivo e as 19 tools chamadas para 5 pessoas que cobrem as 5 marcas, EAD, presencial, duas matrículas e responsável |
| Paginação até o fim igual ao oráculo | Limite 3 contra limite 100 nas 8 tools paginadas, e faturas, pagamentos, protocolos e registros contra o `SqlOracle` |
| Invariantes 3, 4, 5 e 8 | Testes dedicados em `test_tool_invariants.py`; o 7 já era coberto pelo teste de ownership |
| Fábrica | `StudentToolsFactory` em `src/api/composition/`, usada pelos testes de todas as áreas |
| Gate | `make check` verde com 601 testes em 92s, rodado pelo condutor; antes eram 3min30 |

O invariante do agente comprometido achou um erro 500 em `list_subject_professors` com turma sem professor, corrigido no mesmo commit com teste de regressão.

**Checkpoint de implementação** · 2026-11-05 · Lista de pendências · 07c7ecf

| Critério | Evidência |
|---|---|
| Tool no registro, com `checked` | `OverviewTools.get_pending_items`; aluno sem pendências (3000014) devolve as 6 áreas verificadas e nenhuma atenção |
| CR-01 com `UniSaoPaulo:181820` igual ao catálogo | `test_overview_tools.py`: matrícula ativa, sem dívida, taxa de R$ 20 em 01/11 e mensalidade de R$ 1.487,92 em 10/11, protocolo 20260024674, DIR0403 com 65,2% |
| Sem regra recalculada | Compõe os services das 4 áreas, sem consulta nova |
| Gate | `make check` verde com 578 testes, rodado pelo implementador; gate escopado e 12 testes rodados pelo condutor |

**Checkpoint de implementação** · 2026-11-05 · Tools de protocolo e serviços · e173cac

| Critério | Evidência |
|---|---|
| 4 tools no registro | `ProtocolTools` e snapshot das descrições |
| PR-01 a PR-09 e DU-06 com os valores do catálogo | `test_protocol_tools.py` e `test_protocol_tools_propose.py` (DU-06: 18 serviços, 14 que o agente pode abrir; CR-08: protocolo resolvido com taxa vencida) |
| RE-05 sem nota interna nem analista | A ownership das mensagens só lê as públicas; o JSON não contém nota, analista nem `changed_by` |
| Serviço com taxa recusado e nenhuma escrita | Os 4 serviços com taxa voltam `refused`; contagens de 6 tabelas iguais antes e depois |
| Gate da onda | `make check` verde com 571 testes, rodado pelo condutor |

**Checkpoint de implementação** · 2026-11-05 · Tools do ambiente virtual · 12dfa6c

| Critério | Evidência |
|---|---|
| 3 tools no registro | `LmsTools` e snapshot das descrições |
| LM-01 a LM-05 e CR-04 com os valores do catálogo | `test_lms_tools.py` e `test_lms_tools_account.py` (LM-02: 2 tentativas usadas, 1 restante, com aviso; CR-04: AVA 7,7 e oficial 10,0 lado a lado) |
| Horário em Brasília | LM-01 e LM-04 conferidos por SQL com `AT TIME ZONE` |
| SR-05 com `coverage` | `term=2022/1` devolve `empty` com `coverage.from=2023-02-01` |
| Gate escopado | ruff, flake8, `tools.quality`, `lint-imports`, mypy, pyright e 50 testes, rodados pelo condutor |

**Checkpoint de implementação** · 2026-11-05 · Tools acadêmicas e institucionais · d60e449

| Critério | Evidência |
|---|---|
| 6 tools no registro | `AcademicTools` aceito por `ToolRegistry`; snapshot das descrições |
| VA-01 a VA-09, DU-01 a DU-05, RE-04 com os valores do catálogo | `test_academic_tools.py` e `test_academic_tools_records.py`, contra o `SqlOracle` (ex.: VA-04 AV2 necessária 7,1; VA-07 CR 7,87; VA-08 89,71%) |
| EAD com frequência `not_recorded` | Teste dedicado, com o aviso `frequencia` |
| Gate da onda | `make check` verde com 490 testes, rodado pelo condutor |

**Checkpoint de implementação** · 2026-11-05 · Tools financeiras · c1974bf

| Critério | Evidência |
|---|---|
| 5 tools no registro | `FinanceTools` e snapshot das descrições |
| FI-01 a FI-09 com os valores do catálogo | `test_finance_tools.py` e `test_finance_tools_lists.py` (FI-01 R$ 277,05 = 268,85 + 8,20; FI-09 R$ 44.251,08 sem etapa de cobrança) |
| Oráculo de dívida mantido | 273 contratos e fatura `7067951` verdes, com o saldo somando só pagamentos confirmados no domínio |
| Gate da onda | `make check` verde com 490 testes |

**Mudança no spec** · 2026-11-05 · Paginação em objeto `page`

- **O quê:** as tools paginadas recebem `page: PageRequest = FIRST_PAGE`, em vez de `offset` e `limit` soltos. A resposta continua igual.
- **Por quê:** decisão do dono: `get_curriculum` teria 6 parâmetros, e o linter aceita 5.
- **Seções editadas:** §6.4, Execução.
- **Impacto na implementação:** `PageRequest` virou modelo pydantic, e as tarefas de tools usam a nova forma.

**Checkpoint de implementação** · 2026-11-05 · Ontologias, renderizadores e documento gerado · 5df0b8f

| Critério | Evidência |
|---|---|
| Validação e sincronia do documento verdes | `tests/unit/test_ontology.py` e `test_ontology_document.py`, com as 54 instâncias e as 17 relações contra o spec |
| Saída de `for_skill` sem `evidence` nem `data` | Canário, busca dos textos reais nas 7 áreas e busca de padrões, em `test_ontology_renderer.py` |
| Números de `evidence` remedidos no banco | Consultas de leitura do implementador; conferi a saída real da skill do AVA |
| Tamanho de `for_skill` relatado | Tokens aproximados: vínculo 1.042, desempenho 906, financeiro 1.253, protocolos 536, AVA 600, visão geral 173, limites 256 |
| Gate da onda | `make check` verde com 342 testes, rodado pelo condutor |

Achados: as salas de turma e o log do AVA começam em 01/02/2023, e só as 40 salas institucionais começam em 15/01/2023, data que o catálogo cita em SR-05. Isso afeta o `coverage` das tools do AVA. A linha da ontologia em `docs/index.md` ficou fora do commit, junto com a linha do dono no mesmo arquivo.

**Checkpoint de implementação** · 2026-11-05 · Sessão completa e ownership de identidade · 482fddf

| Critério | Evidência |
|---|---|
| Toda pessoa carrega sessão | `test_every_person_loads_a_session`, nas 1.000 pessoas |
| Partição provada | `test_session_partition.py`: nenhuma pessoa, matrícula, contrato, conta ou protocolo em duas pessoas |
| 3.882 protocolos resolvidos, 51 invisíveis, 11 de terceiros invisíveis | `test_protocols_resolve_to_the_expected_owner`, contra o `SqlOracle` |
| Cascata de protocolo | `test_protocol_cascade.py`: 19 casos sintéticos, porque o banco não tem todos os casos |
| Gate escopado | ruff, flake8, `tools.quality`, `lint-imports`, mypy, pyright e 55 testes verdes, rodados pelo condutor |

**Checkpoint de implementação** · 2026-11-05 · Correção de dívida · 0b5c7dd

| Critério | Evidência |
|---|---|
| `PARTIAL` a vencer fora da dívida | `test_partial_invoice_not_yet_due_is_not_debt`, com a pessoa 3003610 e o contrato CT00013240, confere contra o `SqlOracle` |
| Testes antigos corrigidos | `tests/unit/test_invoice.py` e `tests/integration/test_financial_service.py` afirmam a regra nova |
| Principal e contagem batem nos 273 contratos | `test_debt_matches_the_receivable_snapshot_contract_by_contract`, contrato a contrato |
| Fatura `7067951` com saldo de R$ 93,92 | `test_partial_invoice_balance_is_net_minus_confirmed_payments` |
| Gate escopado | ruff, flake8, `tools.quality`, mypy, pyright e 28 testes verdes, rodados pelo condutor |

Custo aceito: o teste contra a posição de 31/10 percorre as 1.000 pessoas e leva cerca de 35s. O `make check` completo roda ao fechar a onda.

**Mudança no spec** · 2026-11-05 · Área das ontologias ausentes

- **O quê:** as 9 ontologias `ABSENT` passam à área do tema. O total segue 54, e a distribuição fica 12, 10, 14, 6, 7, 2 e 3.
- **Por quê:** a tabela e a seção 6.2 se contradiziam sobre a relação de `divida` com `suspensao_do_ava`; decisão do dono.
- **Seções editadas:** §6.1, Execução.
- **Impacto na implementação:** não existe `Area.ABSENT`; o campo `area` dessas 9 instâncias muda, e os testes de `for_skill` cobrem o caso do AVA.

**Mudança no spec** · 2026-11-05 · Commits locais e fábrica das tools

- **O quê:** a regra "sem commit" virou commit local por tarefa aceita, em branch própria e sem push. A fábrica das tools por sessão entrou na tarefa de invariantes, com `src/api/main.py`. O snippet Python da seção 6.1 foi reindentado, porque `ruff format --check` também formata blocos de código em Markdown e deixava `make check` vermelho.
- **Por quê:** decisão do dono na abertura da execução; o spec não dizia onde as tools são montadas.
- **Seções editadas:** §6.1, §8, §9, Execução.
- **Impacto na implementação:** as tarefas de tools testam com montagem própria e não editam `main.py`.

**Mudança no spec** · 2026-11-05 · D16 a D21

- **O quê:** as seis pendências foram fechadas. O framework do agente passa a ser LangChain, em vez do Pydantic AI recomendado; as outras cinco seguem a recomendação.
- **Por quê:** decisão do dono na revisão.
- **Seções editadas:** Para o humano, §3.1, §3.2 (removida), §4, §6.6, §8.
- **Impacto na implementação:** nenhum nas tarefas desta fase, porque as tools não importam framework. O spec do agente faz a troca da dependência e pede ao dono o ajuste do contrato de importação.
