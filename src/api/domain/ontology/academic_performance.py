from api.domain.ontology.model import Area, Ontology

RESULTADO = Ontology(
    key="resultado",
    name="Resultado da disciplina",
    area=Area.ACADEMIC_PERFORMANCE,
    synonyms=("passei", "reprovei", "dispensa", "situação na matéria"),
    definition="Situação do aluno em uma disciplina: aprovado, reprovado por nota, reprovado por "
    "frequência, desistente, dispensado ou em andamento. Reprovar por nota e por frequência têm "
    "causas diferentes.",
    never_say=("Confirmar como definitiva uma reprovação lançada antes do fim do semestre",),
)

AV = Ontology(
    key="av",
    name="AV",
    area=Area.ACADEMIC_PERFORMANCE,
    synonyms=("prova", "AV1", "AV2", "AV3", "nota da prova"),
    definition="Avaliações da disciplina: AV1, AV2 e AV3. AV vazia em semestre aberto significa "
    "que ainda não aconteceu, não zero. A AV3, quando existe, substitui a menor nota se for maior.",
    caveat="A leitura de AV vazia e a regra da AV3 foram deduzidas dos registros.",
    never_say=("Tratar AV vazia como nota zero",),
)

MEDIA = Ontology(
    key="media",
    name="Média",
    area=Area.ACADEMIC_PERFORMANCE,
    synonyms=("nota final", "média da matéria"),
    definition="Média da disciplina: 40% da AV1 mais 60% da AV2, com uma casa decimal. "
    "Sem AV2, é 40% da AV1; sem nenhuma nota, é 0,0.",
    caveat="Essa conta foi deduzida dos registros e não é uma regra oficial.",
    never_say=("Apresentar a média calculada como regra oficial",),
)

CRITERIO_DE_APROVACAO = Ontology(
    key="criterio_de_aprovacao",
    name="Critério de aprovação",
    area=Area.ACADEMIC_PERFORMANCE,
    synonyms=("quanto preciso tirar", "nota para passar", "AV2 necessária"),
    definition="Padrão observado para aprovar: média 6 e frequência de 75%. "
    "A nota necessária na AV2 é calculada a partir dele.",
    caveat="Não há regulamento na base; é uma estimativa. Confirme com o professor.",
    never_say=(
        "Apresentar o critério como regra oficial",
        "Afirmar que 75% exatos garantem aprovação",
    ),
)

FREQUENCIA = Ontology(
    key="frequencia",
    name="Frequência",
    area=Area.ACADEMIC_PERFORMANCE,
    synonyms=("presença", "faltas", "quantas faltas posso ter"),
    definition="Percentual de presença na disciplina. O sistema guarda só o percentual, sem o "
    "número de aulas. Em disciplina online, a frequência não é registrada.",
    caveat="Frequência vazia em disciplina online significa não registrada, não 0%. "
    "O limite de 75% foi deduzido dos registros.",
    never_say=("Dizer quantas faltas restam", "Tratar frequência não registrada como 0%"),
)

CR = Ontology(
    key="cr",
    name="Coeficiente de rendimento",
    area=Area.ACADEMIC_PERFORMANCE,
    synonyms=("CR", "coeficiente", "média geral"),
    definition="Média simples das disciplinas com nota final, sem contar dispensas. É por "
    "matrícula, nunca por pessoa. Vazio significa sem nota final, não zero.",
    never_say=("Juntar o CR de matrículas diferentes", "Tratar CR vazio como zero"),
)

CONCLUSAO = Ontology(
    key="conclusao",
    name="Conclusão do curso",
    area=Area.ACADEMIC_PERFORMANCE,
    synonyms=("quanto falta para me formar", "matérias que faltam", "formatura"),
    definition="Horas aprovadas ou dispensadas da matriz atual sobre o total dela, optativas "
    "incluídas. Reprovação já superada não entra na lista do que falta.",
    never_say=("Contar disciplina de matriz antiga no percentual",),
)

REGISTRO_OFICIAL = Ontology(
    key="registro_oficial",
    name="Registro oficial",
    area=Area.ACADEMIC_PERFORMANCE,
    synonyms=("histórico", "histórico acadêmico", "qual nota vale"),
    definition="O histórico acadêmico é o registro oficial da vida acadêmica.",
    never_say=("Dizer que outro sistema está errado",),
)

SALA_E_HORARIO = Ontology(
    key="sala_e_horario",
    name="Sala e horário",
    area=Area.ACADEMIC_PERFORMANCE,
    synonyms=("que horas é a aula", "em que sala", "endereço do campus"),
    definition="Sala, horário de aula, endereço e telefone da unidade não estão na base. "
    "Há apenas turma e turno.",
    caveat="Não tenho o horário nem a sala; confirme com a secretaria do campus.",
    never_say=("Informar sala ou horário de aula",),
)

BLOQUEIO_DE_DIPLOMA = Ontology(
    key="bloqueio_de_diploma",
    name="Bloqueio de diploma",
    area=Area.ACADEMIC_PERFORMANCE,
    synonyms=("a dívida atrapalha o diploma", "diploma preso"),
    definition="Regra que impediria emitir o diploma por causa de dívida. "
    "Não há regra nem registro de bloqueio na base.",
    caveat="Não encontrei regra que relacione a dívida ao diploma.",
    never_say=("Afirmar que a dívida impede o diploma",),
)

ACADEMIC_PERFORMANCE_ONTOLOGIES = (
    RESULTADO,
    AV,
    MEDIA,
    CRITERIO_DE_APROVACAO,
    FREQUENCIA,
    CR,
    CONCLUSAO,
    REGISTRO_OFICIAL,
    SALA_E_HORARIO,
    BLOQUEIO_DE_DIPLOMA,
)
