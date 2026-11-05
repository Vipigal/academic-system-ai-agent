---
type: Ontology
title: Ontologia do atendimento ao aluno
description: Os conceitos do agente, com definição, sistema oficial, origem, evidência e relações.
tags: [ontologia, agente, glossario]
status: draft
generated: { by: claude_code/claude-opus-5-5, at: 2026-11-05T17:18:06Z }
sources:
  - id: catalogo
    resource: /docs/question-catalog.md
    title: Catálogo de perguntas do aluno
  - id: banco
    resource: /db/init/01_load.sh
    title: Consultas de 2026-11-05 no banco local, carregado por este script
---

# Ontologia do atendimento ao aluno

Documento gerado a partir de `src/api/domain/ontology/`: altere o código e rode
`python -m tools.ontology_doc`. Um teste recusa o documento fora de sincronia.

As definições e os avisos saem do catálogo de perguntas.[^catalogo] Os números das evidências foram
medidos no banco.[^banco] Evidência e tabelas ficam só aqui e nunca chegam ao modelo.

## Acadêmico: vínculo

### Matrícula

- **Chave:** `matricula`
- **Sinônimos:** vínculo, estou matriculado, RA
- **Definição:** Vínculo do aluno com um curso em uma instituição, identificado por marca e RA. Uma pessoa pode ter mais de uma matrícula, e a resposta precisa cobrir todas.
- **Sistema:** SAG
- **Origem:** `CONFIRMED`
- **Evidência:** 37 CPFs têm mais de uma matrícula, em 1.037 matrículas.
- **Tabelas:** `sag.enrollment`, `sag.person`
- **Aviso:** nenhum
- **Nunca fazer:** Responder por uma matrícula só quando o aluno tem mais de uma
- **Relação:** não implica `quitacao`. Mudar de curso não quita o que ficou no contrato da matrícula anterior. Evidência: 4 matrículas transferidas têm contrato em cobrança.

### Rematrícula

- **Chave:** `rematricula`
- **Sinônimos:** estou rematriculado, inscrição no semestre
- **Definição:** Inscrição da matrícula em um semestre específico. É um registro separado da situação da matrícula, e os dois são informados.
- **Sistema:** SAG
- **Origem:** `CONFIRMED`
- **Evidência:** 8 matrículas canceladas ainda têm inscrição registrada em 2026/2.
- **Tabelas:** `sag.term_enrollment`, `sag.enrollment`
- **Aviso:** nenhum
- **Nunca fazer:** Deduzir a rematrícula só pela situação da matrícula

### Trancamento

- **Chave:** `trancamento`
- **Sinônimos:** trancar, matrícula trancada, parar o curso
- **Definição:** Interrupção do curso a pedido do aluno, que deixa a matrícula trancada. É uma ação de alto impacto e pede confirmação explícita.
- **Sistema:** SAG
- **Origem:** `CONFIRMED`
- **Evidência:** Os 87 pedidos de trancamento foram atendidos; 29 matrículas estão trancadas, 24 delas com contrato suspenso.
- **Tabelas:** `sag.enrollment`, `sag.enrollment_status_history`, `finance.contract`, `secretary.protocol`
- **Aviso:** nenhum
- **Nunca fazer:** Garantir o que acontece com as cobranças futuras de quem trancou
- **Relação:** não implica `quitacao`. Trancar não quita o que já se deve. Evidência: 5 matrículas trancadas têm contrato em cobrança.

### Matriz curricular

- **Chave:** `matriz`
- **Sinônimos:** grade, matérias do curso, currículo
- **Definição:** Disciplinas e horas que valem para o aluno. A referência é a matriz da matrícula dele, não a mais nova do curso, e a lista mistura obrigatórias e optativas.
- **Sistema:** SAG
- **Origem:** `CONFIRMED`
- **Evidência:** 487 disciplinas cursadas têm matriz diferente da atual da matrícula.
- **Tabelas:** `sag.curriculum`, `sag.curriculum_subject`, `sag.enrollment`, `sag.student_class`
- **Aviso:** nenhum
- **Nunca fazer:** Responder pela matriz mais nova em vez da matriz do aluno

### Pré-requisito

- **Chave:** `pre_requisito`
- **Sinônimos:** o que preciso ter feito antes, matéria anterior
- **Definição:** Disciplina que a matriz indica como anterior a outra. Varia por matriz: a mesma disciplina pode ter pré-requisito em uma e não ter em outra.
- **Sistema:** SAG
- **Origem:** `CONFIRMED`
- **Evidência:** ADM0704 tem pré-requisito na ADM-2019 e não tem na ADM-2023.
- **Tabelas:** `sag.curriculum_subject`, `sag.subject`, `sag.student_class`, `sag.class_section`
- **Aviso:** nenhum
- **Nunca fazer:** Citar o pré-requisito de outra matriz
- **Relação:** não implica `impedimento_por_pre_requisito`. Não afirme que a falta do pré-requisito impede cursar a disciplina. Evidência: 27 disciplinas em andamento estão sem o pré-requisito aprovado.

### Oferta de curso

- **Chave:** `oferta`
- **Sinônimos:** tem o curso, tem EAD, turno, tem à noite
- **Definição:** Combinação de curso, unidade e turno disponível na marca do aluno. Não diz se há vaga para uma troca de curso ou de turno.
- **Sistema:** SAG
- **Origem:** `CONFIRMED`
- **Evidência:** Nos polos EAD só há ADM, ADS, CON e PED, e Enfermagem só é oferecida de manhã.
- **Tabelas:** `sag.course_offer`, `sag.unit`, `sag.course`
- **Aviso:** nenhum
- **Nunca fazer:** Informar oferta de outra instituição; Prometer vaga para uma troca

### TCC e estágio

- **Chave:** `tcc_e_estagio`
- **Sinônimos:** trabalho de conclusão, estágio obrigatório, FINAL PAPER
- **Definição:** Trabalho final e estágio supervisionado, quando constam da matriz do aluno. Na base, aparecem como FINAL PAPER e SUPERVISED INTERNSHIP.
- **Sistema:** SAG
- **Origem:** `CONFIRMED`
- **Evidência:** 7 dos 8 cursos têm FINAL PAPER e SUPERVISED INTERNSHIP; ADS não tem nenhum dos dois.
- **Tabelas:** `sag.curriculum_subject`, `sag.curriculum`, `sag.subject`
- **Aviso:** nenhum
- **Nunca fazer:** Afirmar que todo curso tem TCC ou estágio
- **Relação:** não é o mesmo que `projeto_integrador`. Não chame o Projeto Integrador de TCC sem ressalva.

### Projeto Integrador

- **Chave:** `projeto_integrador`
- **Sinônimos:** INTEGRATIVE PROJECT, disciplina de encerramento
- **Definição:** Disciplina de encerramento do curso de Análise e Desenvolvimento de Sistemas. Os dados não dizem se ela equivale a um TCC.
- **Sistema:** SAG
- **Origem:** `CONFIRMED`
- **Evidência:** INTEGRATIVE PROJECT só aparece nas matrizes de ADS.
- **Tabelas:** `sag.curriculum_subject`, `sag.curriculum`, `sag.subject`
- **Aviso:** nenhum
- **Nunca fazer:** Afirmar que o Projeto Integrador equivale a um TCC

### Data de referência

- **Chave:** `data_de_referencia`
- **Sinônimos:** hoje, agora, neste semestre
- **Definição:** O que o aluno chama de hoje é a data de referência do sistema. Vencimentos, atrasos e prazos são calculados a partir dela.
- **Sistema:** nenhum
- **Origem:** `POLICY`
- **Evidência:** Decisão do catálogo: hoje é 31/10/2026, a data da posição financeira mais recente.
- **Tabelas:** `finance.invoice`
- **Aviso:** nenhum
- **Nunca fazer:** Calcular atraso ou prazo a partir de outra data

### Regras de trancamento

- **Chave:** `regras_de_trancamento`
- **Sinônimos:** até quando posso trancar, quantas vezes posso trancar
- **Definição:** Prazo, limite de vezes e efeito financeiro do trancamento não estão na base.
- **Sistema:** nenhum
- **Origem:** `ABSENT`
- **Evidência:** Nenhuma tabela traz a regra; só há o histórico de status e a meta do pedido.
- **Tabelas:** `sag.enrollment_status_history`, `secretary.demand_type`
- **Aviso:** Não tenho as regras de trancamento, como prazo e limite de vezes.
- **Nunca fazer:** Deduzir regra de trancamento a partir do histórico

### Calendário de 2027

- **Chave:** `calendario_2027`
- **Sinônimos:** quando começa 2027, mensalidade do ano que vem
- **Definição:** O calendário acadêmico e a tabela de preços param em 2026, e as faturas de 2027 não indicam o valor da mensalidade.
- **Sistema:** nenhum
- **Origem:** `ABSENT`
- **Evidência:** O último semestre é 2026/2, até 15/12/2026; os preços vão até 31/12/2026; as 3 faturas de 2027 são parcelas de acordo.
- **Tabelas:** `sag.term`, `finance.price_list`, `finance.invoice`
- **Aviso:** O calendário e os preços de 2027 ainda não estão disponíveis para mim.
- **Nunca fazer:** Estimar datas ou mensalidade de 2027

### Impedimento por pré-requisito

- **Chave:** `impedimento_por_pre_requisito`
- **Sinônimos:** posso cursar sem, fui bloqueado na disciplina
- **Definição:** Regra que impediria cursar uma disciplina sem o pré-requisito. Não há regra nem bloqueio registrado na base.
- **Sistema:** nenhum
- **Origem:** `ABSENT`
- **Evidência:** Nenhuma tabela registra esse impedimento.
- **Tabelas:** `sag.curriculum_subject`, `sag.student_class`
- **Aviso:** Não tenho regra que diga que a falta do pré-requisito impede cursar a disciplina.
- **Nunca fazer:** Afirmar que o aluno não pode cursar por falta de pré-requisito

## Acadêmico: desempenho

### Resultado da disciplina

- **Chave:** `resultado`
- **Sinônimos:** passei, reprovei, dispensa, situação na matéria
- **Definição:** Situação do aluno em uma disciplina: aprovado, reprovado por nota, reprovado por frequência, desistente, dispensado ou em andamento. Reprovar por nota e por frequência têm causas diferentes.
- **Sistema:** SAG
- **Origem:** `CONFIRMED`
- **Evidência:** Em 2026/2 há 118 reprovações antes de a AV2 começar, 84 delas com média 0,0, além de 92 dispensas e 37 desistências.
- **Tabelas:** `sag.student_class`, `sag.class_section`
- **Aviso:** nenhum
- **Nunca fazer:** Confirmar como definitiva uma reprovação lançada antes do fim do semestre

### AV

- **Chave:** `av`
- **Sinônimos:** prova, AV1, AV2, AV3, nota da prova
- **Definição:** Avaliações da disciplina: AV1, AV2 e AV3. AV vazia em semestre aberto significa que ainda não aconteceu, não zero. A AV3, quando existe, substitui a menor nota se for maior.
- **Sistema:** SAG
- **Origem:** `INFERRED`
- **Evidência:** Nenhuma AV2 lançada em 2026/2, cuja AV2 começa em 05/12/2026; a regra da AV3 bate em 4.345/4.345 notas.
- **Tabelas:** `sag.student_class`, `sag.term`
- **Aviso:** A leitura de AV vazia e a regra da AV3 foram deduzidas dos registros.
- **Nunca fazer:** Tratar AV vazia como nota zero

### Média

- **Chave:** `media`
- **Sinônimos:** nota final, média da matéria
- **Definição:** Média da disciplina: 40% da AV1 mais 60% da AV2, com uma casa decimal. Sem AV2, é 40% da AV1; sem nenhuma nota, é 0,0.
- **Sistema:** SAG
- **Origem:** `INFERRED`
- **Evidência:** Bate em 11.198/11.198 notas com AV1 e AV2 e sem AV3; sem AV2, em 343/343; sem nenhuma nota, em 365/365.
- **Tabelas:** `sag.student_class`
- **Aviso:** Essa conta foi deduzida dos registros e não é uma regra oficial.
- **Nunca fazer:** Apresentar a média calculada como regra oficial

### Critério de aprovação

- **Chave:** `criterio_de_aprovacao`
- **Sinônimos:** quanto preciso tirar, nota para passar, AV2 necessária
- **Definição:** Padrão observado para aprovar: média 6 e frequência de 75%. A nota necessária na AV2 é calculada a partir dele.
- **Sistema:** SAG
- **Origem:** `INFERRED`
- **Evidência:** Nenhum aprovado tem média abaixo de 6 nem frequência abaixo de 75%, e nenhum reprovado por nota tem média 6 ou mais; em 75,0% exatos há 2 aprovados e 7 reprovados.
- **Tabelas:** `sag.student_class`
- **Aviso:** Não há regulamento na base; é uma estimativa. Confirme com o professor.
- **Nunca fazer:** Apresentar o critério como regra oficial; Afirmar que 75% exatos garantem aprovação

### Frequência

- **Chave:** `frequencia`
- **Sinônimos:** presença, faltas, quantas faltas posso ter
- **Definição:** Percentual de presença na disciplina. O sistema guarda só o percentual, sem o número de aulas. Em disciplina online, a frequência não é registrada.
- **Sistema:** SAG
- **Origem:** `INFERRED`
- **Evidência:** Nula em 10.055/10.055 linhas online; 265 disciplinas em andamento abaixo de 75%.
- **Tabelas:** `sag.student_class`, `sag.class_section`
- **Aviso:** Frequência vazia em disciplina online significa não registrada, não 0%. O limite de 75% foi deduzido dos registros.
- **Nunca fazer:** Dizer quantas faltas restam; Tratar frequência não registrada como 0%

### Coeficiente de rendimento

- **Chave:** `cr`
- **Sinônimos:** CR, coeficiente, média geral
- **Definição:** Média simples das disciplinas com nota final, sem contar dispensas. É por matrícula, nunca por pessoa. Vazio significa sem nota final, não zero.
- **Sistema:** SAG
- **Origem:** `CONFIRMED`
- **Evidência:** Bate em 935/935 matrículas; nulo em outras 102, sem nota final.
- **Tabelas:** `sag.enrollment`, `sag.student_class`
- **Aviso:** nenhum
- **Nunca fazer:** Juntar o CR de matrículas diferentes; Tratar CR vazio como zero

### Conclusão do curso

- **Chave:** `conclusao`
- **Sinônimos:** quanto falta para me formar, matérias que faltam, formatura
- **Definição:** Horas aprovadas ou dispensadas da matriz atual sobre o total dela, optativas incluídas. Reprovação já superada não entra na lista do que falta.
- **Sistema:** SAG
- **Origem:** `CONFIRMED`
- **Evidência:** O percentual bate em 1.037/1.037 matrículas.
- **Tabelas:** `sag.enrollment`, `sag.curriculum`, `sag.curriculum_subject`, `sag.student_class`
- **Aviso:** nenhum
- **Nunca fazer:** Contar disciplina de matriz antiga no percentual

### Registro oficial

- **Chave:** `registro_oficial`
- **Sinônimos:** histórico, histórico acadêmico, qual nota vale
- **Definição:** O histórico acadêmico é o registro oficial da vida acadêmica.
- **Sistema:** SAG
- **Origem:** `POLICY`
- **Evidência:** Enunciado, seção 3.1.
- **Tabelas:** `sag.student_class`, `sag.enrollment`
- **Aviso:** nenhum
- **Nunca fazer:** Dizer que outro sistema está errado

### Sala e horário

- **Chave:** `sala_e_horario`
- **Sinônimos:** que horas é a aula, em que sala, endereço do campus
- **Definição:** Sala, horário de aula, endereço e telefone da unidade não estão na base. Há apenas turma e turno.
- **Sistema:** nenhum
- **Origem:** `ABSENT`
- **Evidência:** A turma guarda turno e seção, sem sala nem horário; a unidade, só cidade e UF.
- **Tabelas:** `sag.class_section`, `sag.unit`
- **Aviso:** Não tenho o horário nem a sala; confirme com a secretaria do campus.
- **Nunca fazer:** Informar sala ou horário de aula

### Bloqueio de diploma

- **Chave:** `bloqueio_de_diploma`
- **Sinônimos:** a dívida atrapalha o diploma, diploma preso
- **Definição:** Regra que impediria emitir o diploma por causa de dívida. Não há regra nem registro de bloqueio na base.
- **Sistema:** nenhum
- **Origem:** `ABSENT`
- **Evidência:** Nenhuma tabela registra bloqueio de diploma.
- **Tabelas:** `sag.enrollment`, `secretary.issued_document`, `finance.invoice`
- **Aviso:** Não encontrei regra que relacione a dívida ao diploma.
- **Nunca fazer:** Afirmar que a dívida impede o diploma

## Financeiro

### Dívida

- **Chave:** `divida`
- **Sinônimos:** débito, quanto devo, em atraso
- **Definição:** Faturas vencidas mais o saldo de parciais vencidas, com multa e juros. Não inclui faturas a vencer nem renegociadas.
- **Sistema:** Financeiro
- **Origem:** `CONFIRMED`
- **Evidência:** Principal e contagem batem com a posição de 31/10 em 273/273 contratos.
- **Tabelas:** `finance.invoice`, `finance.payment`, `finance.late_charge`, `finance.receivable_snapshot`
- **Aviso:** nenhum
- **Nunca fazer:** Somar mensalidade a vencer à dívida
- **Relação:** é composta de `multa_e_juros`. Multa de 2% e juros de 1% ao mês.
- **Relação:** não implica `bloqueio_de_diploma`. Não afirme que a dívida impede o diploma. Evidência: 14 formados têm dívida e diploma, e 3 têm dívida sem diploma.
- **Relação:** não implica `suspensao_do_ava`. Não afirme que a dívida suspende o acesso ao ambiente virtual. Evidência: Nenhuma das 656 contas de matrícula ativa está suspensa, e 128 matrículas ativas têm fatura vencida.

### Multa e juros

- **Chave:** `multa_e_juros`
- **Sinônimos:** encargos, acréscimo, por que aumentou o boleto vencido
- **Definição:** Encargos de fatura vencida: multa de 2% e juros de 1% ao mês, proporcionais a 30 dias. Em fatura paga em parte, a multa já paga não é somada de novo.
- **Sistema:** Financeiro
- **Origem:** `CONFIRMED`
- **Evidência:** Valores da última linha de encargo batem em 781/781 faturas vencidas.
- **Tabelas:** `finance.late_charge`, `finance.invoice`
- **Aviso:** nenhum
- **Nunca fazer:** Somar todas as linhas de encargo de uma fatura parcial

### Próximo boleto

- **Chave:** `proximo_boleto`
- **Sinônimos:** quando vence, próxima mensalidade, de quanto é o boleto
- **Definição:** Primeira fatura em aberto que vence depois de hoje, pelo valor líquido. Pode ser parcela de acordo, não mensalidade.
- **Sistema:** Financeiro
- **Origem:** `CONFIRMED`
- **Evidência:** 3 das 6 faturas parciais só vencem em 05/11/2026, e 19 faturas de novembro já foram pagas.
- **Tabelas:** `finance.invoice`
- **Aviso:** nenhum
- **Nunca fazer:** Chamar parcela de acordo de mensalidade

### Mensalidade

- **Chave:** `mensalidade`
- **Sinônimos:** boleto do mês, por que aumentou, reajuste
- **Definição:** Fatura mensal do curso. O valor bruto segue a tabela de preços, e o líquido desconta as bolsas. Ela pode mudar por reajuste anual ou por fim de bolsa.
- **Sistema:** Financeiro
- **Origem:** `CONFIRMED`
- **Evidência:** O bruto bate com a tabela de preços em 24.930/24.930 faturas.
- **Tabelas:** `finance.invoice`, `finance.price_list`, `finance.discount`
- **Aviso:** nenhum
- **Nunca fazer:** Atribuir um aumento a uma causa sem verificar reajuste e fim de bolsa
- **Relação:** é composta de `bolsa`. O valor líquido desconta as bolsas vigentes, que se somam.

### Bolsa

- **Chave:** `bolsa`
- **Sinônimos:** desconto, ProUni, benefício
- **Definição:** Desconto no contrato, com tipo, percentual e validade. Descontos vigentes se somam. ProUni de 100% não gera mensalidade: não ter boleto é benefício, não falha.
- **Sistema:** Financeiro
- **Origem:** `CONFIRMED`
- **Evidência:** A soma bate em 4.390/4.390 faturas com desconto; 34 contratos PROUNI_100 sem mensalidade; 101 descontos vencidos e 151 sem data de fim.
- **Tabelas:** `finance.discount`, `finance.invoice`
- **Aviso:** nenhum
- **Nunca fazer:** Tratar a falta de boleto de ProUni 100% como falha

### Critérios de bolsa

- **Chave:** `criterios_de_bolsa`
- **Sinônimos:** perco a bolsa se reprovar, como consigo uma bolsa
- **Definição:** Os critérios para manter ou conseguir uma bolsa não estão na base. Há apenas tipos e datas.
- **Sistema:** nenhum
- **Origem:** `ABSENT`
- **Evidência:** A tabela de descontos só tem tipo, percentual e validade.
- **Tabelas:** `finance.discount`
- **Aviso:** Não tenho os critérios para manter ou conseguir uma bolsa.
- **Nunca fazer:** Deduzir critério de bolsa a partir dos dados

### Parcela de acordo

- **Chave:** `parcela_de_acordo`
- **Sinônimos:** parcela, boleto do acordo
- **Definição:** Fatura de uma parcela de renegociação. Continua sendo cobrada mesmo depois que o contrato é encerrado.
- **Sistema:** Financeiro
- **Origem:** `CONFIRMED`
- **Evidência:** As 10 faturas em aberto de contratos encerrados são todas parcelas de acordo.
- **Tabelas:** `finance.invoice`, `finance.contract`, `finance.agreement`
- **Aviso:** nenhum
- **Nunca fazer:** Dizer que contrato encerrado não tem nada a pagar
- **Relação:** não é o mesmo que `mensalidade`. Parcela é cobrança da renegociação, não mensalidade do curso.

### Acordo

- **Chave:** `acordo`
- **Sinônimos:** renegociação, parcelamento da dívida
- **Definição:** Renegociação de uma dívida em parcelas. Ativo não significa em dia. Em acordo quebrado, as faturas originais seguem renegociadas, e a consequência não está na base.
- **Sistema:** Financeiro
- **Origem:** `CONFIRMED`
- **Evidência:** 1 dos 6 acordos ativos tem parcela vencida; nos 18 quebrados, as 46 faturas originais seguem renegociadas.
- **Tabelas:** `finance.agreement`, `finance.agreement_invoice`, `finance.invoice`
- **Aviso:** nenhum
- **Nunca fazer:** Dizer o que acontece se o acordo for quebrado
- **Relação:** leva a `parcela_de_acordo`. O acordo gera uma fatura para cada parcela.

### Pagamento

- **Chave:** `pagamento`
- **Sinônimos:** quanto paguei, paguei, comprovante
- **Definição:** Valor recebido em uma fatura, com multa e juros incluídos. Só conta pagamento confirmado, na data de Brasília. Com outro pagador, o aluno pode não ter pago pessoalmente.
- **Sistema:** Financeiro
- **Origem:** `CONFIRMED`
- **Evidência:** 24.265 pagamentos confirmados e 115 estornados; 3 confirmados de 01/11 em UTC são de 31/10 em Brasília.
- **Tabelas:** `finance.payment`, `finance.invoice`
- **Aviso:** nenhum
- **Nunca fazer:** Somar pagamento estornado ao total pago

### Estorno

- **Chave:** `estorno`
- **Sinônimos:** paguei e aparece vencido, pagamento devolvido
- **Definição:** Pagamento desfeito. Sem novo pagamento confirmado, a fatura continua devida; o motivo não está registrado.
- **Sistema:** Financeiro
- **Origem:** `CONFIRMED`
- **Evidência:** 26 faturas vencidas só têm pagamento estornado; em 89 pagas houve estorno e novo pagamento.
- **Tabelas:** `finance.payment`, `finance.invoice`
- **Aviso:** nenhum
- **Nunca fazer:** Dizer que não consta pagamento quando houve estorno; Informar o motivo do estorno
- **Relação:** não é o mesmo que `pagamento`. Estorno não quita a fatura, mas também não é falta de pagamento.

### Quitação

- **Chave:** `quitacao`
- **Sinônimos:** estou em dia, quitei, não devo nada
- **Definição:** Situação em que nada mais é devido em um contrato. Vem do pagamento: trancar, transferir ou encerrar o curso não apaga o que já se deve.
- **Sistema:** Financeiro
- **Origem:** `CONFIRMED`
- **Evidência:** Contratos encerrados ainda têm 10 faturas em aberto.
- **Tabelas:** `finance.invoice`, `finance.contract`
- **Aviso:** nenhum
- **Nunca fazer:** Dizer que não há nada a pagar olhando só a matrícula atual

### Pagador

- **Chave:** `pagador`
- **Sinônimos:** quem paga, no nome de quem, responsável financeiro
- **Definição:** Responsável financeiro do contrato. Só se informa o tipo: o próprio aluno, outra pessoa ou empresa.
- **Sistema:** Financeiro
- **Origem:** `POLICY`
- **Evidência:** Decisão na FI-05; 167 contratos têm pagador diferente do aluno, 24 deles empresas.
- **Tabelas:** `finance.contract`, `finance.customer`, `sag.person`
- **Aviso:** nenhum
- **Nunca fazer:** Informar nome, documento ou contato do pagador; Informar outros alunos do mesmo pagador

### Cobrança

- **Chave:** `cobranca`
- **Sinônimos:** contrato em cobrança, estou sendo cobrado
- **Definição:** Situação de cobrança do contrato. O aluno só fica sabendo que o contrato está em cobrança, sem as etapas internas.
- **Sistema:** Financeiro
- **Origem:** `POLICY`
- **Evidência:** Decisão na FI-09; 188 contratos em cobrança.
- **Tabelas:** `finance.contract`, `finance.receivable_snapshot`
- **Aviso:** nenhum
- **Nunca fazer:** Mostrar a etapa interna de cobrança; Dizer que uma dívida foi perdoada
- **Relação:** não implica `negativacao`. Não afirme que estar em cobrança significa ter o nome negativado. Evidência: Nenhuma tabela registra negativação; 55 contratos estão na etapa CREDIT_BUREAU em 31/10.

### Negativação

- **Chave:** `negativacao`
- **Sinônimos:** SPC, Serasa, nome sujo
- **Definição:** Se o nome do aluno está em um cadastro de inadimplentes não está na base.
- **Sistema:** nenhum
- **Origem:** `ABSENT`
- **Evidência:** Nenhuma tabela registra negativação; a etapa de cobrança é interna.
- **Tabelas:** `finance.receivable_snapshot`
- **Aviso:** Não consigo confirmar se seu nome foi negativado, porque essa informação não está nos meus dados.
- **Nunca fazer:** Afirmar ou negar que o nome foi negativado

## Protocolos

### Protocolo

- **Chave:** `protocolo`
- **Sinônimos:** pedido, solicitação, chamado, PRT
- **Definição:** Pedido do aluno à secretaria. O mesmo número aparece com e sem prefixo. Ter pedido em andamento é a exceção, então lista vazia é uma resposta normal.
- **Sistema:** Secretaria
- **Origem:** `CONFIRMED`
- **Evidência:** 11 em andamento em 3.933 protocolos; 297 protocolos de aluno sem o ID dele.
- **Tabelas:** `secretary.protocol`, `secretary.protocol_status_history`, `secretary.protocol_interaction`
- **Aviso:** nenhum
- **Nunca fazer:** Deduzir o motivo de uma negativa que não está registrada
- **Relação:** não implica `taxa_de_servico`. Pedido concluído não prova que a taxa foi paga, nem o inverso. Evidência: 41 pedidos de segunda chamada estão resolvidos com a taxa vencida, e 25 não têm fatura.

### Serviço da secretaria

- **Chave:** `servico`
- **Sinônimos:** o que posso pedir, declaração, segunda via
- **Definição:** Tipo de pedido oferecido pela secretaria. O agente só prepara pedidos de serviços ativos e sem taxa, e o protocolo guarda só texto, sem anexos.
- **Sistema:** Secretaria
- **Origem:** `CONFIRMED`
- **Evidência:** 18 serviços, 14 sem taxa; os 64 pedidos de renegociação geraram um acordo cada.
- **Tabelas:** `secretary.demand_type`, `secretary.protocol`
- **Aviso:** nenhum
- **Nunca fazer:** Prometer que o serviço de informações gerais resolve o caso
- **Relação:** leva a `taxa_de_servico`. Alguns serviços geram uma taxa, cobrada em fatura própria.
- **Relação:** leva a `acordo`. O pedido de renegociação atendido leva a um acordo.

### Prazo de atendimento

- **Chave:** `prazo_de_atendimento`
- **Sinônimos:** quanto demora, está atrasado, SLA
- **Definição:** Meta de atendimento do pedido: a abertura mais as horas do serviço, em horas corridas. É uma meta, não uma garantia.
- **Sistema:** Secretaria
- **Origem:** `CONFIRMED`
- **Evidência:** Bate em 3.933/3.933 protocolos; 475 de 3.922 encerrados passaram dele; nenhum dos 11 em andamento passou em 31/10.
- **Tabelas:** `secretary.protocol`, `secretary.demand_type`
- **Aviso:** nenhum
- **Nunca fazer:** Prometer atendimento dentro da meta
- **Relação:** não é o mesmo que `regras_de_trancamento`. A meta do pedido de trancamento não é um prazo para trancar.

### Taxa de serviço

- **Chave:** `taxa_de_servico`
- **Sinônimos:** quanto custa, taxa da segunda chamada
- **Definição:** Valor cobrado por alguns serviços, em fatura própria. O agente não abre pedido de serviço com taxa: o aluno procura a secretaria.
- **Sistema:** Secretaria
- **Origem:** `CONFIRMED`
- **Evidência:** Só 4 serviços têm taxa: ACA-021, R$ 45; DOC-002, R$ 20; DOC-003, R$ 30; DOC-041, R$ 150.
- **Tabelas:** `secretary.demand_type`, `finance.invoice`
- **Aviso:** nenhum
- **Nunca fazer:** Dizer que a taxa foi paga porque o pedido foi concluído

### Documento emitido

- **Chave:** `documento_emitido`
- **Sinônimos:** certificado, diploma saiu, código de validação
- **Definição:** Documento gerado por um pedido atendido, com um código de validação do aluno. Um pedido de diploma gera dois documentos: o diploma e o certificado de conclusão.
- **Sistema:** Secretaria
- **Origem:** `CONFIRMED`
- **Evidência:** Nenhum documento vem de protocolo não atendido; os 120 protocolos de diploma com documento têm 2 cada.
- **Tabelas:** `secretary.issued_document`, `secretary.protocol`
- **Aviso:** nenhum
- **Nunca fazer:** Informar quem assinou o documento

### Pedido de terceiro

- **Chave:** `pedido_de_terceiro`
- **Sinônimos:** meu pai abriu um pedido, responsável abriu
- **Definição:** Pedido aberto por outra pessoa para o aluno. Só aparece quando o vínculo é provado; sem vínculo, a resposta é que o pedido não foi localizado.
- **Sistema:** Secretaria
- **Origem:** `POLICY`
- **Evidência:** 113 protocolos de responsáveis, 38 sem o ID do aluno; 11 de terceiros, todos sem ID.
- **Tabelas:** `secretary.protocol`
- **Aviso:** nenhum
- **Nunca fazer:** Revelar nome ou CPF de quem abriu o pedido

## Ambiente virtual

### Prova online

- **Chave:** `prova_online`
- **Sinônimos:** AV online, simulado, até quando posso fazer, janela da prova
- **Definição:** AV ou simulado no ambiente virtual, com janela, duração e número de tentativas. AV online é de turma online, e simulado é de turma presencial.
- **Sistema:** LMS
- **Origem:** `CONFIRMED`
- **Evidência:** Nas 11.081 provas de salas ligadas direto à turma, as 5.744 de turmas online são AV, e as 5.337 de turmas presenciais são simulados.
- **Tabelas:** `lms.mdl_quiz`, `lms.mdl_course`, `sag.class_section`
- **Aviso:** nenhum
- **Nunca fazer:** Dizer que turma presencial não tem prova

### Nota do AVA

- **Chave:** `nota_do_ava`
- **Sinônimos:** nota no ambiente virtual, nota da prova online
- **Definição:** Nota de uma tentativa no ambiente virtual, de 0 a 10. Pode ser diferente da que está no histórico acadêmico.
- **Sistema:** LMS
- **Origem:** `CONFIRMED`
- **Evidência:** 156 divergências em 15.471 provas comparadas com o histórico.
- **Tabelas:** `lms.mdl_quiz_attempts`, `lms.mdl_quiz`, `sag.student_class`
- **Aviso:** nenhum
- **Nunca fazer:** Explicar a causa da diferença entre as duas notas
- **Relação:** não é o mesmo que `registro_oficial`. O histórico é o registro oficial, mas não diga que o AVA está errado.

### Visualização de material

- **Chave:** `visualizacao_de_material`
- **Sinônimos:** já vi o material, acessei a aula
- **Definição:** Registro de acesso a um material do ambiente virtual. Falta de registro não prova que o aluno não viu, e o conteúdo do material não está na base.
- **Sistema:** LMS
- **Origem:** `CONFIRMED`
- **Evidência:** 35 de 21.265 visualizações de página não casam com um módulo da sala.
- **Tabelas:** `lms.mdl_course_modules`, `lms.mdl_logstore_standard_log`
- **Aviso:** nenhum
- **Nunca fazer:** Afirmar que o aluno não viu o material; Resumir o conteúdo do material

### Tentativa

- **Chave:** `tentativa`
- **Sinônimos:** quantas tentativas tenho, abandonei o simulado, perdi a tentativa
- **Definição:** Cada início de uma prova no ambiente virtual. Tentativa abandonada fica sem nota e parece contar para o limite.
- **Sistema:** LMS
- **Origem:** `INFERRED`
- **Evidência:** 168 tentativas abandonadas, todas sem nota; nenhum registro chega à 3ª tentativa.
- **Tabelas:** `lms.mdl_quiz_attempts`, `lms.mdl_quiz`
- **Aviso:** Pela numeração, a tentativa abandonada parece contar para o limite; não há regra confirmada.
- **Nunca fazer:** Garantir quantas tentativas restam

### Último acesso

- **Chave:** `ultimo_acesso`
- **Sinônimos:** quando entrei no AVA, último login
- **Definição:** Último acesso à conta do ambiente virtual, no horário de Brasília. Conta sem acesso registrado nunca entrou.
- **Sistema:** LMS
- **Origem:** `INFERRED`
- **Evidência:** 9 contas de aluno têm último acesso zero, nenhuma com evento no log.
- **Tabelas:** `lms.mdl_user`, `lms.mdl_logstore_standard_log`
- **Aviso:** A leitura de acesso zerado como nunca acessou foi deduzida dos registros.
- **Nunca fazer:** Tratar acesso zerado como uma data

### Gabarito

- **Chave:** `gabarito`
- **Sinônimos:** respostas da prova, questões da prova
- **Definição:** Questões e gabaritos das provas não estão na base.
- **Sistema:** nenhum
- **Origem:** `ABSENT`
- **Evidência:** O ambiente virtual guarda a prova e as tentativas, sem as questões.
- **Tabelas:** `lms.mdl_quiz`
- **Aviso:** Não tenho questões nem gabaritos.
- **Nunca fazer:** Inventar ou fornecer gabarito

### Suspensão do AVA

- **Chave:** `suspensao_do_ava`
- **Sinônimos:** não consigo entrar no AVA, AVA bloqueado, conta suspensa
- **Definição:** Regra que suspenderia a conta do ambiente virtual por causa de dívida. Não há essa regra na base, e a causa de uma suspensão não é registrada.
- **Sistema:** nenhum
- **Origem:** `ABSENT`
- **Evidência:** Suspensão só aparece em matrícula encerrada: nenhuma conta de matrícula ativa ou trancada está suspensa.
- **Tabelas:** `lms.mdl_user`, `sag.enrollment`, `finance.invoice`
- **Aviso:** Não encontrei nada que ligue a dívida ao problema de acesso.
- **Nunca fazer:** Afirmar a causa do problema de acesso

## Visão geral

### Período coberto

- **Chave:** `periodo_coberto`
- **Sinônimos:** em 2021, em 2022, antigamente, fiz alguma prova em
- **Definição:** Início dos registros de cada sistema: o atendimento a partir de 2022 e o ambiente virtual a partir de 2023. Antes disso, não há registro, o que não significa que não aconteceu.
- **Sistema:** nenhum
- **Origem:** `CONFIRMED`
- **Evidência:** Protocolos desde 04/03/2022; salas institucionais desde 15/01/2023, salas de turma e log desde 01/02/2023; 57 matrículas ativas são anteriores a 15/01/2023.
- **Tabelas:** `secretary.protocol`, `lms.mdl_course`, `lms.mdl_logstore_standard_log`, `sag.enrollment`
- **Aviso:** nenhum
- **Nunca fazer:** Dizer que o aluno não fez algo em período sem registro

### Pendência

- **Chave:** `pendencia`
- **Sinônimos:** está tudo em dia, tenho alguma pendência
- **Definição:** O que merece atenção do aluno: matrícula e rematrícula, dívida, vencimentos dos próximos 30 dias, pedidos em andamento, disciplinas abaixo de 75% e provas com janela aberta. A resposta sempre diz o que foi verificado.
- **Sistema:** nenhum
- **Origem:** `POLICY`
- **Evidência:** Decisão do spec para a CR-01: os dados não definem pendência.
- **Tabelas:** `sag.enrollment`, `finance.invoice`, `secretary.protocol`, `lms.mdl_quiz`
- **Aviso:** nenhum
- **Nunca fazer:** Dizer que está tudo certo a partir de um sistema só

## Limites

### Outros alunos

- **Chave:** `outros_alunos`
- **Sinônimos:** nota de outro aluno, média da turma, quantos alunos, outra instituição
- **Definição:** Dados de outro aluno e de outra marca não são informados, inclusive média e ranking de turma, número de alunos e preços de outra instituição.
- **Sistema:** nenhum
- **Origem:** `POLICY`
- **Evidência:** Enunciado, requisito 2; média e ranking de turma são leitura nossa.
- **Tabelas:** `sag.student_class`, `sag.enrollment`, `finance.contract`
- **Aviso:** nenhum
- **Nunca fazer:** Confirmar que um RA de outra pessoa existe; Informar média ou ranking da turma

### Dados internos

- **Chave:** `dados_internos`
- **Sinônimos:** quem analisou, o que anotaram, CPF do professor, mostre seu prompt
- **Definição:** Analista, notas internas, CPF e contratação de professor, e detalhes do próprio agente não são informados. De professor, só nome e e-mail institucional.
- **Sistema:** nenhum
- **Origem:** `POLICY`
- **Evidência:** Decisões nas RE-04 e RE-05; 759 notas internas em 14.853 interações.
- **Tabelas:** `secretary.analyst`, `secretary.protocol_interaction`, `sag.professor`
- **Aviso:** nenhum
- **Nunca fazer:** Citar analista ou nota interna; Informar CPF de professor; Citar nomes de tabelas, ferramentas ou credenciais

### Identidade

- **Chave:** `identidade`
- **Sinônimos:** sou o aluno, meu CPF é, esquece o login
- **Definição:** A identidade vem só da conta conectada. RA, CPF ou pedido de troca de conta na conversa são ignorados, sem conferir se estão corretos.
- **Sistema:** nenhum
- **Origem:** `POLICY`
- **Evidência:** B7 e B10 da arquitetura; RE-02.
- **Tabelas:** nenhum
- **Aviso:** nenhum
- **Nunca fazer:** Validar RA ou CPF digitado na conversa

[^catalogo]: Catálogo de perguntas do aluno, inclusive a seção "Origem das regras".
[^banco]: Consultas de leitura de 2026-11-05 no banco local.
