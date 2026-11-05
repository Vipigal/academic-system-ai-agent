---
type: Reference
title: Análise exploratória dos dados
description: Como os dados recebidos estão dispostos, como os sistemas se relacionam e quais inconsistências existem, sem recomendações de solução.
tags: [eda, dados, identidade, referencia]
status: stable
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T05:00:00Z }
sources:
  - id: readme
    resource: /README.md
    title: Enunciado do case
  - id: banco
    resource: /db/init/01_load.sh
    title: Consultas de 2026-11-05 no banco local, carregado por este script
---

# Análise exploratória dos dados

Foto dos dados recebidos, medida nos CSVs e no banco carregado.[^banco] A data de referência do case é 31/10/2026.[^readme]
Este documento só descreve os dados. O que fazer com eles está na [Arquitetura](/docs/architecture.md).

"Regra observada" significa que a relação vale nos dados, sem documento oficial que a confirme.

## 1. Panorama

- 47 tabelas em 4 sistemas: SAG (15), Financeiro (13), LMS (11) e Secretaria (8).
- 52 MB em CSV e 70 MB no Postgres, com todas as colunas em `text`.
- A maior tabela é `mdl_logstore_standard_log`, com 151.111 linhas.
- A dificuldade está entre os sistemas e na semântica, não em sujeira aleatória.

## 2. Integridade

- **PKs do README:** 47/47 sem duplicata e sem nulo.
- **FKs do README:** 69/74 sem violação. As 5 restantes:

| FK | Violações |
|---|---|
| `mdl_logstore_standard_log.courseid` | 27.322 valores `0` e 202 órfãos |
| `mdl_logstore_standard_log.userid` | 169 órfãos |
| `mdl_course_categories.parent` | 5 valores `0` (categorias raiz) |
| `protocol.demand_analyst` | 23 órfãos |
| `issued_document.signed_by` | 6 órfãos |

- **Faturas:** `net = gross - discount` em 25.931/25.931.

## 3. Identidade

### Pessoas e matrículas

- 1.037 matrículas, 1.015 `PERSON_ID` e 1.000 CPFs. 15 CPFs têm 2 `PERSON_ID`, com e-mail, telefone e CEP iguais; em 13 deles o nome varia.
- 963 CPFs têm 1 matrícula e 37 têm 2: 20 na mesma marca e modalidade, 17 em modalidades diferentes.
- Nenhum CPF de aluno atravessa marcas.

### Como cada sistema identifica o aluno

| Sistema | Chave | Exemplos | Correspondência com a matrícula |
|---|---|---|---|
| SAG | `BRAND` + `STUDENT_ID` | `UniSaoPaulo_EAD`, `011550` | Referência |
| Financeiro | `companyCode` + `businessArea` + `academicRef` | `18001-7`, `18015`, `1253-0`, ` 01233-5 ` | 1.065/1.065 contratos |
| LMS | `tenant_id` + `student_id` | `PRES_18199`, `EAD_01195`, `ead_01206` | 983/983 contas de aluno |
| Secretaria | `Unit_Code` + `Stu_ID` + `Requester_CPF` | `11924`, `180254`, nulo | Ver seção 4 |

### Estrutura do `STUDENT_ID`

- 5 dígitos de base e 1 verificador, módulo 11 com pesos 6-5-4-3-2, válido nos 739 IDs distintos.
- O prefixo indica a origem: `18` São Paulo, `07` Montanhas, `12` Litoral, `03` Atlântico, `09` Araucária e `01` em todas as marcas EAD.
- **Colisão:** 173 IDs se repetem entre marcas, sempre em pessoas diferentes. `011550` existe em 5 marcas.
- Sem a marca, 1.714 de 3.528 protocolos com ID e 483 de 1.065 contratos casam com mais de uma matrícula.

### Outras variações

| Entidade | Formas |
|---|---|
| Marca | `UniSaoPaulo_EAD`, `UniSaoPaulo`, `unisaopaulo`, `UNISAOPAULO`, `1010`, `Uni São Paulo` |
| Modalidade | `DL`/`CAMPUS`, `DIGITAL`/`PRESENCIAL`, `EAD_`/`PRES_`, `Polo EAD`/`Campus` |
| Unidade | `101` no SAG e `SPA-PAU` na secretaria; casam em 27/27 por marca, modalidade, cidade e UF, ignorando acentos |
| Curso | `Course_Label` tem 24 grafias para 8 cursos |
| Sala do LMS | `SAG-<CLASS_ID>` resolve 8.209/8.209; há 1.005 `idnumber` nulos, dos quais 965 têm correspondência única por `shortname`, ambiente e unidade, e 40 são salas institucionais. Com as duas regras, 9.174 salas casam 1:1 com turmas |
| Protocolo | `PRT-2022/0003091` e `20220003091`; 229/229 casam após extrair os dígitos |
| CPF | Com pontuação em `person`; sem zeros à esquerda em 315 protocolos |
| Taxa | `R$ 0,00` em `demand_type` |

### Contas do LMS

| Tipo | Contas |
|---|---|
| Aluno com `student_id` | 983, sendo 8 com caixa baixa ou espaços no valor |
| Professor (`PROF_`) | 60 |
| Teste (`aluno.teste*`) | 12 |
| Sistema | 3 |
| Aluno sem `student_id` | 20, das quais só 7 têm CPF no perfil |

- 54 matrículas não têm conta com `student_id` no LMS, 12 delas ativas.
- 30 pessoas têm 2 contas de aluno.
- O e-mail do LMS difere do cadastro do SAG em 983/983 contas.

## 4. Secretaria

### Posse dos protocolos

Classificação dos 3.933 protocolos, a partir do ID, da marca e do CPF do requerente:

| Situação | Protocolos |
|---|---|
| ID, marca e CPF do requerente confirmam | 3.455 |
| ID e marca confirmam; o requerente é responsável | 73 |
| Sem ID válido; CPF e marca levam a 1 matrícula | 329 |
| Sem ID válido; CPF e marca levam a 2 matrículas da mesma pessoa | 25 |
| Responsável, pagador de 1 aluno na marca | 31 |
| Responsável, pagador de vários alunos | 9 |
| Terceiros, sem vínculo | 11 |

- 351 protocolos não têm ID e 54 trazem um ID que não existe em nenhuma matrícula (`13205` em vez de `013250`). Desses 54, 52 têm CPF que leva à matrícula, e 2 são de responsáveis sem esse vínculo.
- Por tipo de requerente: 3.675 `Student`, 134 `Alumni`, 113 `Guardian` e 11 `Third Party`.

### Serviços

| Código | Serviço | Taxa | SLA | Prioridade | Pedidos | Atendidos |
|---|---|---|---|---|---|---|
| `ACA-010` | Enrollment Lock | R$ 0 | 72 h | Normal | 87 | 87 |
| `ACA-011` | Enrollment Reactivation | R$ 0 | 72 h | Normal | 47 | 47 |
| `ACA-012` | Enrollment Cancellation | R$ 0 | 72 h | High | 35 | 35 |
| `ACA-013` | Internal Transfer | R$ 0 | 120 h | Normal | 20 | 20 |
| `ACA-014` | Curriculum Migration | R$ 0 | 120 h | Normal | 40 | 40 |
| `ACA-020` | Grade Review | R$ 0 | 168 h | Normal | 510 | 99 |
| `ACA-021` | Second-Call Exam | R$ 45 | 72 h | Normal | 526 | 501 |
| `DOC-001` | Enrollment Certificate | R$ 0 | 48 h | Low | 555 | 534 |
| `DOC-002` | Printed Transcript | R$ 20 | 72 h | Normal | 176 | 155 |
| `DOC-003` | Syllabus Package | R$ 30 | 120 h | Normal | 78 | 70 |
| `DOC-040` | Diploma Issuance | R$ 0 | 240 h | Normal | 132 | 120 |
| `DOC-041` | Diploma Second Copy | R$ 150 | 240 h | Normal | 2 | 2 |
| `FIN-030` | Payment Slip Reissue | R$ 0 | 48 h | Normal | 752 | 715 |
| `FIN-031` | Debt Renegotiation | R$ 0 | 72 h | High | 64 | 64 |
| `FIN-032` | Discount/Scholarship Request | R$ 0 | 120 h | Normal | 195 | 185 |
| `GEN-090` | General Information | R$ 0 | 72 h | Normal | 517 | 480 |
| `OUV-099` | Complaint | R$ 0 | 120 h | High | 80 | 73 |
| `TEC-060` | LMS Access Issue | R$ 0 | 48 h | Normal | 117 | 108 |

- **Prioridade:** cada serviço tem uma só prioridade em todos os protocolos.
- **Solicitante:** `DOC-040` e `DOC-041` só têm `Alumni`; serviços acadêmicos só têm `Student`; `Guardian` só aparece em `FIN-030`, `FIN-031` e `FIN-032`.
- **Taxa:** serviços sem taxa nunca têm fatura. Dos 782 pedidos com taxa, 732 têm fatura `SERVICE_FEE`.
- **Efeito:** os 229 pedidos de `ACA-010` a `ACA-014` foram atendidos e geraram mudança em `enrollment_status_history`. Os 64 de `FIN-031` foram atendidos e têm acordo; 1 dos 65 acordos não tem protocolo.
- **Documentos:** os 1.001 documentos saem só de protocolos `Granted` de `DOC-*`. Em 120 protocolos de diploma, há 2 documentos: diploma e certificado de conclusão.
- **Texto:** cada serviço tem um só modelo de mensagem inicial. Em `GEN-090`, os 517 pedidos falam do calendário acadêmico.

### Andamento

- Todo protocolo nasce com um histórico `Open` (`changed_by = system`) e uma mensagem do requerente, em 3.933/3.933.
- `SLA_Due_At` é a abertura mais `SLA_Hours`, em horas corridas, em 3.933/3.933.
- `Open` não tem analista (2/2).
- 3.725 estão `Resolved`, 197 `Cancelled`, 9 `In Analysis` e 2 `Open`. Em 31/10, nenhum dos 11 em andamento passou do prazo.
- `sla_breached` coincide com o fechamento depois do prazo; são 475 de 3.922 encerrados.
- 974 protocolos passaram por `Pending Requester`, com pedido de documento. O protocolo só guarda texto, sem coluna de anexo.
- 180 protocolos passaram por `Reopened`, e não há serviço de reabertura no catálogo.
- As 390 negativas são todas de `ACA-020`, sem motivo registrado. Analistas usam só 3 mensagens, e uma delas é a nota interna.

## 5. Dados sensíveis

| Dado | Onde |
|---|---|
| CPF | `person`, `professor`, `customer`, `protocol`, `mdl_user_info_data` |
| Contato do pagador | `customer`: `email`, `phone`, endereço |
| Requerente | `protocol`: nome e CPF |
| Funcionários | `analyst`, `professor`, `Signed_By`, `Author`, `Changed_By`, `Demand_Analyst` |
| Notas internas | 759 linhas com `Is_Internal_Note = True` |
| Acesso | `ip` e `other` no log do LMS |

**Professores:** os 60 e-mails são institucionais (`@prof.<marca>.example`), e cada professor leciona só na própria marca. Em 2026/2, 227 de 964 combinações de disciplina e marca têm mais de um professor.

**Pagadores:**

- 167 contratos, de 162 matrículas, têm pagador diferente do aluno; 24 deles têm empresa como pagadora.
- 17 pagadores (7 empresas e 10 pessoas físicas) cobrem 42 pessoas, 44 matrículas e 1.182 faturas. 5 pagadores atravessam marcas.

**Texto livre:** as mensagens se reduzem a 25 modelos benignos, com variações de RA, e os comentários de pesquisa a 5. Não contêm CPF, e-mail
ou telefone, nem injeção plantada.

## 6. Financeiro

| Status da fatura | Faturas | Vencimentos |
|---|---|---|
| `PAID` | 23.552 | 2021-01-05 a 2026-11-05 |
| `OPEN` | 1.298 | 2026-11-01 a 2027-03-28 |
| `OVERDUE` | 781 | 2021-10-15 a 2026-10-20 |
| `RENEGOTIATED` | 196 | 2021-09-10 a 2026-10-10 |
| `CANCELLED` | 98 | 2021-09-10 a 2026-12-15 |
| `PARTIAL` | 6 | 2026-09-10 a 2026-11-05 |

**Dívida**

- **Posição de 31/10:** para os 273 contratos, `OVERDUE` mais o saldo de `PARTIAL` vencida bate em contagem e principal. As linhas de `late_charge` de 31/10 batem em multa e juros, e o total é a soma dos três.
- **`OPEN`** só tem vencimentos a partir de 01/11/2026, ou seja, depois da data de referência.
- **Multa e juros:** nas 781 faturas vencidas, a multa é 2% do líquido e os juros são 1% ao mês, proporcionais a 30 dias.
- **Linhas de `late_charge`:** 119 faturas têm 2 linhas. Em 118 `PAID`, cada linha corresponde a um pagamento. Na `PARTIAL`, a linha mais antiga já foi paga.
- **Multas dispensadas:** 145 de 5.241 `late_charge` têm `waived = True`, todas em faturas `RENEGOTIATED`.
- **Etapas em 31/10:** `REMINDER` 65, `AGENCY` 20, `CREDIT_BUREAU` 55 e `WRITE_OFF` 133. As duas últimas só aparecem em contratos `IN_COLLECTION`.

**Valores**

- **Preço:** o bruto das mensalidades segue a tabela em 24.930/24.930.
- **Descontos:** a soma das taxas vigentes explica o desconto em 4.390/4.390 mensalidades, e 54 contratos têm mais de um desconto.
- **`PROUNI_100`:** 34 contratos, sem mensalidade e sem data de fim; 19 não têm nenhuma fatura, e os demais só têm taxas de serviço.
- **Impostos:** 25.564 faturas têm 3 linhas; parcelas de acordo e faturas canceladas não têm imposto.

**Pagamentos e acordos**

- **Estornos:** 115 pagamentos `REVERSED`. 26 faturas `OVERDUE` só têm pagamento estornado, e 89 `PAID` têm um estorno no histórico.
- **Acordos:** 65. `originalDebtCents` é a soma líquida mais multa e juros, `agreedAmountCents` é o original menos o abatimento, e parcelas e total batem, em 65/65.
- **`RENEGOTIATED`:** as 196 faturas estão em acordos, e as parcelas dos acordos também são faturas. Nos 18 acordos `BROKEN`, as originais continuam `RENEGOTIATED`.

**Contrato e matrícula**

- **Vários contratos:** 28 matrículas têm 2 contratos.
- **Status cruzado:** contratos `IN_COLLECTION` por status da matrícula: 100 `DROPOUT`, 50 `ACTIVE`, 17 `GRADUATED`, 12 `CANCELLED`, 5 `LOCKED` e 4 `TRANSFERRED`.
- **Trancamento:** nenhuma matrícula `LOCKED` tem mensalidade vencendo depois da data do status, e 24 têm contrato `SUSPENDED`.
- **Contrato encerrado:** há 10 faturas `OPEN` em contratos `TERMINATED`, todas parcelas de acordo.

## 7. Acadêmico

| Resultado em `student_class` | Linhas |
|---|---|
| `APPROVED` | 12.427 |
| `IN_PROGRESS` | 2.989 |
| `FAILED` | 2.296 |
| `FAILED_ATTENDANCE` | 1.528 |
| `EXEMPT` | 865 |
| `WITHDRAWN` | 172 |

**Regras observadas**

- **Média:** `0,4·AV1 + 0,6·AV2`, arredondada em 1 casa, em 11.198/11.198 notas com as duas provas.
- **AV3:** substitui a menor nota quando é maior, em 4.345/4.345. 4.198 têm média abaixo de 6 antes da AV3, 147 têm 6 ou mais, e 557 com média abaixo de 6 não têm AV3.
- **Sem AV2:** a média é `0,4·AV1` em 343/343. Sem nenhuma nota, é 0,0 em 365/365.
- **Por professor:** nos 60, o peso calculado da AV1 fica entre 0,397 e 0,402.
- **Aprovação:** nenhum `APPROVED` tem média abaixo de 6 ou frequência abaixo de 75%, e nenhum `FAILED` tem média 6 ou mais. `FAILED_ATTENDANCE` vai até 75,0%, e `FAILED` começa em 75,1%. Com exatamente 75,0%, há 2 `APPROVED`, 7 `FAILED_ATTENDANCE` e 3 `IN_PROGRESS`; 6 desses reprovados têm média 6 ou mais.
- **GPA:** é a média simples das disciplinas com nota final, em 935/935. Está nulo em 102 matrículas, nenhuma com nota final.
- **Conclusão:** `current_curriculum_completion` é a soma das horas aprovadas ou dispensadas da matriz atual sobre o total dela, em 1.037/1.037. O total inclui as 2 optativas de cada matriz.
- **Semestre:** `semester` é o maior `semester_level` da matrícula, em 1.037/1.037.

**Outros fatos**

- **Frequência:** nula em 10.055/10.055 turmas `ONLINE`, e presente em todas as 9.357 `IN_PERSON`.
- **`EXEMPT`:** as 865 linhas não têm nota nem frequência. Turmas de dispensa não têm professor (739/739).
- **2026/2:** há 118 resultados `FAILED` ou `FAILED_ATTENDANCE` de matrículas `ACTIVE`, 84 deles com média 0,0, embora o semestre esteja em andamento e AV2 só comece em 05/12/2026. As demais 2.989 linhas em andamento têm AV1 e nenhuma tem AV2.
- **Reprovações:** de 2.845 pares de matrícula e disciplina reprovados, 1.068 foram aprovados depois, 525 estão em andamento e 1.252 seguem pendentes.
- **Pré-requisito:** 27 disciplinas em andamento estão sem o pré-requisito aprovado.
- **Matriz:** 487 linhas de `student_class` têm matriz diferente da atual da matrícula.
- **Matrículas por status:** 668 `ACTIVE`, 132 `DROPOUT`, 132 `GRADUATED`, 56 `CANCELLED`, 29 `LOCKED` e 20 `TRANSFERRED`.
- **Rematrícula em 2026/2:** 8 matrículas `CANCELLED` têm `REGISTERED`.
- **Oferta:** EAD só tem ADM, ADS, CON e PED. ADS não tem estágio nem `FINAL PAPER`.

## 8. Entre sistemas

- **Cobertura temporal:** faturas e matrículas desde 12/2020, protocolos desde 03/2022, salas do LMS desde 15/01/2023 e log desde 02/2023.
- **Provas no LMS:** AV1 e AV2 online só existem em salas EAD, com 90 minutos e 1 tentativa. Simulados só existem em salas presenciais, com 60 minutos e limite de 3. Nenhum registro chega à 3ª tentativa, e os 168 abandonos são de simulados, sem nota.
- **Janelas de 2026/2:** AV1 de 03/10 a 10/10, simulado até 21/11 e AV2 de 05/12 a 12/12, com fechamento às 23:59 no Brasil.
- **Notas LMS e SAG:** em 15.471 provas comparadas, 156 divergem. Toda nota de AV online de aluno com conta tem tentativa no LMS; 17 notas de AV1 em 2026/2 são de alunos sem conta.
- **Suspensão no LMS:** só aparece em matrícula encerrada: 110 `DROPOUT`, 89 `GRADUATED`, 45 `CANCELLED` e 16 `TRANSFERRED`. Nenhuma das 656 contas de matrícula `ACTIVE` nem das 29 `LOCKED` está suspensa, embora 128 matrículas ativas tenham fatura vencida.
- **Nunca acessou:** 9 contas de aluno têm `lastaccess = 0`, sem evento no log.
- **Diploma e dívida:** dos 132 formados, 120 têm pedido de diploma atendido e 12 só têm pedido cancelado. 17 têm dívida, 14 deles com diploma.
- **Fuso:** eventos chegam a cerca de 03h de 01/11/2026 em UTC, que ainda é 31/10 no Brasil. 3 pagamentos estão nessa situação.
- **Idioma:** cursos, disciplinas, serviços e status estão em inglês.
- **Regulamentos:** nenhuma tabela traz regras de aprovação, trancamento, bolsa ou semelhantes.

## 9. Casos de exemplo

| Caso | Referência |
|---|---|
| ID em 5 marcas | `011550` em qualquer marca EAD |
| Duas matrículas e dois `PERSON_ID` | CPF `95347704853`: `UniAraucaria_EAD:011541` e `UniAraucaria:090697` |
| Pagador empresa em várias marcas | `C0004244`: 7 matrículas em 3 marcas, entre elas `UniSaoPaulo_EAD:012157` e `UniLitoral_EAD:012220` |
| Pagador pessoa física com dois alunos | `C0005104`: `UniSaoPaulo:180548` e `UniSaoPaulo:180823` |
| Fatura vencida com estorno | `UniSaoPaulo_EAD:012955`, fatura `7025510` |
| Trancamento financeiro | `UniSaoPaulo:180882`, protocolo `PRT-2024/0000454` |
| Acordo ativo | `UniSaoPaulo:180696`, `AG2026000122` |
| Acordo ativo com parcela vencida | `UniAraucaria_EAD:011991`, `AG2026000304` |
| Formado em cobrança | `UniLitoral:120057`, `CT00010681` |
| Protocolo em andamento | `UniSaoPaulo_EAD:012831`, `20260024630` |
| `FAILED` em semestre corrente | `UniAraucaria_EAD:012661` |

## 10. Limites desta exploração

- `mdl_course_modules`, `mdl_user_info_data` e `mdl_course_categories` tiveram verificação superficial.
- Regras observadas podem não valer fora desta base.
- Os dados não provam escala, por serem pequenos.

[^readme]: Enunciado do case, introdução da seção "Contexto".
[^banco]: Consultas de 2026-11-05 no banco local.
