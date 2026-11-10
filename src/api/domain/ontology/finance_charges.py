from api.domain.ontology.model import Area, Ontology, Relation, RelationKind

DIVIDA = Ontology(
    key="divida",
    name="Dívida",
    area=Area.FINANCE,
    synonyms=("débito", "quanto devo", "em atraso"),
    definition="Faturas vencidas mais o saldo de parciais vencidas, com multa e juros. "
    "Não inclui faturas a vencer nem renegociadas.",
    never_say=("Somar mensalidade a vencer à dívida",),
    relations=(
        Relation(
            RelationKind.COMPOSED_OF,
            "multa_e_juros",
            note="Multa de 2% e juros de 1% ao mês.",
        ),
        Relation(
            RelationKind.NOT_IMPLIES,
            "bloqueio_de_diploma",
            note="Não afirme que a dívida impede o diploma.",
        ),
        Relation(
            RelationKind.NOT_IMPLIES,
            "suspensao_do_ava",
            note="Não afirme que a dívida suspende o acesso ao ambiente virtual.",
        ),
    ),
)

MULTA_E_JUROS = Ontology(
    key="multa_e_juros",
    name="Multa e juros",
    area=Area.FINANCE,
    synonyms=("encargos", "acréscimo", "por que aumentou o boleto vencido"),
    definition="Encargos de fatura vencida: multa de 2% e juros de 1% ao mês, proporcionais a "
    "30 dias. Em fatura paga em parte, a multa já paga não é somada de novo.",
    never_say=("Somar todas as linhas de encargo de uma fatura parcial",),
)

PROXIMO_BOLETO = Ontology(
    key="proximo_boleto",
    name="Próximo boleto",
    area=Area.FINANCE,
    synonyms=("quando vence", "próxima mensalidade", "de quanto é o boleto"),
    definition="Primeira fatura em aberto que vence depois de hoje, pelo saldo: o valor líquido, "
    "menos o já pago em fatura parcial. Pode ser parcela de acordo, não mensalidade.",
    never_say=("Chamar parcela de acordo de mensalidade",),
)

MENSALIDADE = Ontology(
    key="mensalidade",
    name="Mensalidade",
    area=Area.FINANCE,
    synonyms=("boleto do mês", "por que aumentou", "reajuste"),
    definition="Fatura mensal do curso. O valor bruto segue a tabela de preços, e o líquido "
    "desconta as bolsas. Ela pode mudar por reajuste anual ou por fim de bolsa.",
    never_say=("Atribuir um aumento a uma causa sem verificar reajuste e fim de bolsa",),
    relations=(
        Relation(
            RelationKind.COMPOSED_OF,
            "bolsa",
            note="O valor líquido desconta as bolsas vigentes, que se somam.",
        ),
    ),
)

BOLSA = Ontology(
    key="bolsa",
    name="Bolsa",
    area=Area.FINANCE,
    synonyms=("desconto", "ProUni", "benefício"),
    definition="Desconto no contrato, com tipo, percentual e validade. Descontos vigentes se "
    "somam. ProUni de 100% não gera mensalidade: não ter boleto é benefício, não falha.",
    never_say=("Tratar a falta de boleto de ProUni 100% como falha",),
)

CRITERIOS_DE_BOLSA = Ontology(
    key="criterios_de_bolsa",
    name="Critérios de bolsa",
    area=Area.FINANCE,
    synonyms=("perco a bolsa se reprovar", "como consigo uma bolsa"),
    definition="Os critérios para manter ou conseguir uma bolsa não estão na base. "
    "Há apenas tipos e datas.",
    caveat="Não tenho os critérios para manter ou conseguir uma bolsa.",
    never_say=("Deduzir critério de bolsa a partir dos dados",),
)

PARCELA_DE_ACORDO = Ontology(
    key="parcela_de_acordo",
    name="Parcela de acordo",
    area=Area.FINANCE,
    synonyms=("parcela", "boleto do acordo"),
    definition="Fatura de uma parcela de renegociação. "
    "Continua sendo cobrada mesmo depois que o contrato é encerrado.",
    never_say=("Dizer que contrato encerrado não tem nada a pagar",),
    relations=(
        Relation(
            RelationKind.NOT_SAME_AS,
            "mensalidade",
            note="Parcela é cobrança da renegociação, não mensalidade do curso.",
        ),
    ),
)

ACORDO = Ontology(
    key="acordo",
    name="Acordo",
    area=Area.FINANCE,
    synonyms=("renegociação", "parcelamento da dívida"),
    definition="Renegociação de uma dívida em parcelas. Ativo não significa em dia. Em acordo "
    "quebrado, as faturas originais seguem renegociadas, e a consequência não está na base.",
    never_say=("Dizer o que acontece se o acordo for quebrado",),
    relations=(
        Relation(
            RelationKind.LEADS_TO,
            "parcela_de_acordo",
            note="O acordo gera uma fatura para cada parcela.",
        ),
    ),
)

FINANCE_CHARGES_ONTOLOGIES = (
    DIVIDA,
    MULTA_E_JUROS,
    PROXIMO_BOLETO,
    MENSALIDADE,
    BOLSA,
    CRITERIOS_DE_BOLSA,
    PARCELA_DE_ACORDO,
    ACORDO,
)
