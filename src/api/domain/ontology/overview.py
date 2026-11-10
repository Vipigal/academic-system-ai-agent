from api.domain.ontology.model import Area, Ontology

PERIODO_COBERTO = Ontology(
    key="periodo_coberto",
    name="Período coberto",
    area=Area.OVERVIEW,
    synonyms=("em 2021", "em 2022", "antigamente", "fiz alguma prova em"),
    definition="Início dos registros de cada sistema: o atendimento a partir de 2022 e o ambiente "
    "virtual a partir de 2023. Antes disso, não há registro, "
    "o que não significa que não aconteceu.",
    never_say=("Dizer que o aluno não fez algo em período sem registro",),
)

PENDENCIA = Ontology(
    key="pendencia",
    name="Pendência",
    area=Area.OVERVIEW,
    synonyms=("está tudo em dia", "tenho alguma pendência"),
    definition="O que merece atenção do aluno: matrícula e rematrícula, dívida, vencimentos dos "
    "próximos 30 dias, pedidos em andamento, disciplinas abaixo de 75% e provas com janela aberta. "
    "A resposta sempre diz o que foi verificado.",
    never_say=("Dizer que está tudo certo a partir de um sistema só",),
)

OVERVIEW_ONTOLOGIES = (PERIODO_COBERTO, PENDENCIA)
