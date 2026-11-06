from api.domain.ontology import tables
from api.domain.ontology.model import Area, Ontology, Origin, Relation, RelationKind, System

PROVA_ONLINE = Ontology(
    key="prova_online",
    name="Prova online",
    area=Area.LMS,
    synonyms=("AV online", "simulado", "até quando posso fazer", "janela da prova"),
    definition="AV ou simulado no ambiente virtual, com janela, duração e número de tentativas. "
    "AV online é de turma online, e simulado é de turma presencial.",
    source=System.LMS,
    origin=Origin.CONFIRMED,
    evidence="Nas 11.081 provas de salas ligadas direto à turma, as 5.744 de turmas online são "
    "AV, e as 5.337 de turmas presenciais são simulados.",
    data=(tables.LMS_QUIZ, tables.LMS_COURSE, tables.SAG_CLASS_SECTION),
    never_say=("Dizer que turma presencial não tem prova",),
)

NOTA_DO_AVA = Ontology(
    key="nota_do_ava",
    name="Nota do AVA",
    area=Area.LMS,
    synonyms=("nota no ambiente virtual", "nota da prova online"),
    definition="Nota de uma tentativa no ambiente virtual, de 0 a 10. "
    "Pode ser diferente da que está no histórico acadêmico.",
    source=System.LMS,
    origin=Origin.CONFIRMED,
    evidence="156 divergências em 15.471 provas comparadas com o histórico.",
    data=(tables.LMS_QUIZ_ATTEMPTS, tables.LMS_QUIZ, tables.SAG_STUDENT_CLASS),
    never_say=("Explicar a causa da diferença entre as duas notas",),
    relations=(
        Relation(
            RelationKind.NOT_SAME_AS,
            "registro_oficial",
            note="O histórico é o registro oficial, mas não diga que o AVA está errado.",
        ),
    ),
)

VISUALIZACAO_DE_MATERIAL = Ontology(
    key="visualizacao_de_material",
    name="Visualização de material",
    area=Area.LMS,
    synonyms=("já vi o material", "acessei a aula"),
    definition="Registro de acesso a um material do ambiente virtual. Falta de registro não "
    "prova que o aluno não viu, e o conteúdo do material não está na base.",
    source=System.LMS,
    origin=Origin.CONFIRMED,
    evidence="35 de 21.265 visualizações de página não casam com um módulo da sala.",
    data=(tables.LMS_COURSE_MODULES, tables.LMS_LOG),
    never_say=("Afirmar que o aluno não viu o material", "Resumir o conteúdo do material"),
)

TENTATIVA = Ontology(
    key="tentativa",
    name="Tentativa",
    area=Area.LMS,
    synonyms=("quantas tentativas tenho", "abandonei o simulado", "perdi a tentativa"),
    definition="Cada início de uma prova no ambiente virtual. "
    "Tentativa abandonada fica sem nota e parece contar para o limite.",
    source=System.LMS,
    origin=Origin.INFERRED,
    evidence="168 tentativas abandonadas, todas sem nota; nenhum registro chega à 3ª tentativa.",
    data=(tables.LMS_QUIZ_ATTEMPTS, tables.LMS_QUIZ),
    caveat="Pela numeração, a tentativa abandonada parece contar para o limite; "
    "não há regra confirmada.",
    never_say=("Garantir quantas tentativas restam",),
)

ULTIMO_ACESSO = Ontology(
    key="ultimo_acesso",
    name="Último acesso",
    area=Area.LMS,
    synonyms=("quando entrei no AVA", "último login"),
    definition="Último acesso à conta do ambiente virtual, no horário de Brasília. "
    "Conta sem acesso registrado nunca entrou.",
    source=System.LMS,
    origin=Origin.INFERRED,
    evidence="9 contas de aluno têm último acesso zero, nenhuma com evento no log.",
    data=(tables.LMS_USER, tables.LMS_LOG),
    caveat="A leitura de acesso zerado como nunca acessou foi deduzida dos registros.",
    never_say=("Tratar acesso zerado como uma data",),
)

GABARITO = Ontology(
    key="gabarito",
    name="Gabarito",
    area=Area.LMS,
    synonyms=("respostas da prova", "questões da prova"),
    definition="Questões e gabaritos das provas não estão na base.",
    source=None,
    origin=Origin.ABSENT,
    evidence="O ambiente virtual guarda a prova e as tentativas, sem as questões.",
    data=(tables.LMS_QUIZ,),
    caveat="Não tenho questões nem gabaritos.",
    never_say=("Inventar ou fornecer gabarito",),
)

SUSPENSAO_DO_AVA = Ontology(
    key="suspensao_do_ava",
    name="Suspensão do AVA",
    area=Area.LMS,
    synonyms=("não consigo entrar no AVA", "AVA bloqueado", "conta suspensa"),
    definition="Regra que suspenderia a conta do ambiente virtual por causa de dívida. "
    "Não há essa regra na base, e a causa de uma suspensão não é registrada.",
    source=None,
    origin=Origin.ABSENT,
    evidence="Suspensão só aparece em matrícula encerrada: nenhuma conta de matrícula ativa ou "
    "trancada está suspensa.",
    data=(tables.LMS_USER, tables.SAG_ENROLLMENT, tables.FINANCE_INVOICE),
    caveat="Não encontrei nada que ligue a dívida ao problema de acesso.",
    never_say=("Afirmar a causa do problema de acesso",),
)

LMS_ONTOLOGIES = (
    PROVA_ONLINE,
    NOTA_DO_AVA,
    VISUALIZACAO_DE_MATERIAL,
    TENTATIVA,
    ULTIMO_ACESSO,
    GABARITO,
    SUSPENSAO_DO_AVA,
)
