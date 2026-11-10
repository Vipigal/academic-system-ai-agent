from api.domain.ontology.model import Area, Ontology, Relation, RelationKind

MATRICULA = Ontology(
    key="matricula",
    name="Matrícula",
    area=Area.ACADEMIC_ENROLLMENT,
    synonyms=("vínculo", "estou matriculado", "RA"),
    definition="Vínculo do aluno com um curso em uma instituição, identificado por marca e RA. "
    "Uma pessoa pode ter mais de uma matrícula, e a resposta precisa cobrir todas. O aluno também "
    "chama de matrícula a inscrição numa disciplina: confira de qual das duas ele fala.",
    never_say=("Responder por uma matrícula só quando o aluno tem mais de uma",),
    relations=(
        Relation(
            RelationKind.NOT_IMPLIES,
            "quitacao",
            note="Mudar de curso não quita o que ficou no contrato da matrícula anterior.",
        ),
    ),
)

REMATRICULA = Ontology(
    key="rematricula",
    name="Rematrícula",
    area=Area.ACADEMIC_ENROLLMENT,
    synonyms=("estou rematriculado", "inscrição no semestre"),
    definition="Inscrição da matrícula em um semestre específico. "
    "É um registro separado da situação da matrícula, e os dois são informados.",
    never_say=("Deduzir a rematrícula só pela situação da matrícula",),
)

TRANCAMENTO = Ontology(
    key="trancamento",
    name="Trancamento",
    area=Area.ACADEMIC_ENROLLMENT,
    synonyms=(
        "trancar o curso",
        "trancar a matrícula do curso",
        "parar o curso",
        "matrícula trancada",
    ),
    definition="Interrupção do curso inteiro a pedido do aluno, que deixa a matrícula trancada. "
    "Vale sempre para o curso inteiro, nunca para uma disciplina. É uma ação de alto impacto e "
    "pede confirmação explícita.",
    never_say=("Garantir o que acontece com as cobranças futuras de quem trancou",),
    relations=(
        Relation(
            RelationKind.NOT_IMPLIES,
            "quitacao",
            note="Trancar não quita o que já se deve.",
        ),
    ),
)

MATRICULA_EM_DISCIPLINA = Ontology(
    key="matricula_em_disciplina",
    name="Matrícula em disciplina",
    area=Area.ACADEMIC_ENROLLMENT,
    synonyms=(
        "trancar a disciplina",
        "trancar minha matrícula em uma disciplina",
        "cancelar a disciplina",
    ),
    definition="Inscrição do aluno numa disciplina do semestre, que ele também chama de "
    "matrícula. Não é um serviço: nenhum pedido tranca ou cancela uma disciplina, e trancamento e "
    "cancelamento valem para o curso inteiro.",
    never_say=(
        "Oferecer o trancamento ou o cancelamento de uma disciplina como serviço",
        "Propor trancar ou cancelar o curso sem o aluno dizer que quer o curso inteiro",
    ),
    relations=(
        Relation(
            RelationKind.NOT_SAME_AS,
            "trancamento",
            note="Trancar uma disciplina não é trancar o curso, e não há pedido para isso.",
        ),
    ),
)

MATRIZ = Ontology(
    key="matriz",
    name="Matriz curricular",
    area=Area.ACADEMIC_ENROLLMENT,
    synonyms=("grade", "matérias do curso", "currículo"),
    definition="Disciplinas e horas que valem para o aluno. A referência é a matriz da matrícula "
    "dele, não a mais nova do curso, e a lista mistura obrigatórias e optativas.",
    never_say=("Responder pela matriz mais nova em vez da matriz do aluno",),
)

PRE_REQUISITO = Ontology(
    key="pre_requisito",
    name="Pré-requisito",
    area=Area.ACADEMIC_ENROLLMENT,
    synonyms=("o que preciso ter feito antes", "matéria anterior"),
    definition="Disciplina que a matriz indica como anterior a outra. Varia por matriz: a mesma "
    "disciplina pode ter pré-requisito em uma e não ter em outra.",
    never_say=("Citar o pré-requisito de outra matriz",),
    relations=(
        Relation(
            RelationKind.NOT_IMPLIES,
            "impedimento_por_pre_requisito",
            note="Não afirme que a falta do pré-requisito impede cursar a disciplina.",
        ),
    ),
)

OFERTA = Ontology(
    key="oferta",
    name="Oferta de curso",
    area=Area.ACADEMIC_ENROLLMENT,
    synonyms=("tem o curso", "tem EAD", "turno", "tem à noite"),
    definition="Combinação de curso, unidade e turno disponível na marca do aluno. "
    "Não diz se há vaga para uma troca de curso ou de turno.",
    never_say=("Informar oferta de outra instituição", "Prometer vaga para uma troca"),
)

TCC_E_ESTAGIO = Ontology(
    key="tcc_e_estagio",
    name="TCC e estágio",
    area=Area.ACADEMIC_ENROLLMENT,
    synonyms=("trabalho de conclusão", "estágio obrigatório", "FINAL PAPER"),
    definition="Trabalho final e estágio supervisionado, quando constam da matriz do aluno. "
    "Na base, aparecem como FINAL PAPER e SUPERVISED INTERNSHIP.",
    never_say=("Afirmar que todo curso tem TCC ou estágio",),
    relations=(
        Relation(
            RelationKind.NOT_SAME_AS,
            "projeto_integrador",
            note="Não chame o Projeto Integrador de TCC sem ressalva.",
        ),
    ),
)

PROJETO_INTEGRADOR = Ontology(
    key="projeto_integrador",
    name="Projeto Integrador",
    area=Area.ACADEMIC_ENROLLMENT,
    synonyms=("INTEGRATIVE PROJECT", "disciplina de encerramento"),
    definition="Disciplina de encerramento do curso de Análise e Desenvolvimento de Sistemas. "
    "Os dados não dizem se ela equivale a um TCC.",
    never_say=("Afirmar que o Projeto Integrador equivale a um TCC",),
)

DATA_DE_REFERENCIA = Ontology(
    key="data_de_referencia",
    name="Data de referência",
    area=Area.ACADEMIC_ENROLLMENT,
    synonyms=("hoje", "agora", "neste semestre"),
    definition="O que o aluno chama de hoje é a data de hoje, informada pelo sistema. "
    "Vencimentos, atrasos e prazos são calculados a partir dela.",
    never_say=("Calcular atraso ou prazo a partir de outra data",),
)

REGRAS_DE_TRANCAMENTO = Ontology(
    key="regras_de_trancamento",
    name="Regras de trancamento",
    area=Area.ACADEMIC_ENROLLMENT,
    synonyms=("até quando posso trancar", "quantas vezes posso trancar"),
    definition="Prazo, limite de vezes e efeito financeiro do trancamento não estão na base.",
    caveat="Não tenho as regras de trancamento, como prazo e limite de vezes.",
    never_say=("Deduzir regra de trancamento a partir do histórico",),
)

CALENDARIO_2027 = Ontology(
    key="calendario_2027",
    name="Calendário de 2027",
    area=Area.ACADEMIC_ENROLLMENT,
    synonyms=("quando começa 2027", "mensalidade do ano que vem"),
    definition="O calendário acadêmico e a tabela de preços param em 2026, "
    "e as faturas de 2027 não indicam o valor da mensalidade.",
    caveat="O calendário e os preços de 2027 ainda não estão disponíveis para mim.",
    never_say=("Estimar datas ou mensalidade de 2027",),
)

IMPEDIMENTO_POR_PRE_REQUISITO = Ontology(
    key="impedimento_por_pre_requisito",
    name="Impedimento por pré-requisito",
    area=Area.ACADEMIC_ENROLLMENT,
    synonyms=("posso cursar sem", "fui bloqueado na disciplina"),
    definition="Regra que impediria cursar uma disciplina sem o pré-requisito. "
    "Não há regra nem bloqueio registrado na base.",
    caveat="Não tenho regra que diga que a falta do pré-requisito impede cursar a disciplina.",
    never_say=("Afirmar que o aluno não pode cursar por falta de pré-requisito",),
)

ACADEMIC_ENROLLMENT_ONTOLOGIES = (
    MATRICULA,
    REMATRICULA,
    TRANCAMENTO,
    MATRICULA_EM_DISCIPLINA,
    MATRIZ,
    PRE_REQUISITO,
    OFERTA,
    TCC_E_ESTAGIO,
    PROJETO_INTEGRADOR,
    DATA_DE_REFERENCIA,
    REGRAS_DE_TRANCAMENTO,
    CALENDARIO_2027,
    IMPEDIMENTO_POR_PRE_REQUISITO,
)
