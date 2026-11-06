from api.domain.ontology import tables
from api.domain.ontology.model import Area, Ontology, Origin, Relation, RelationKind, System

PROTOCOLO = Ontology(
    key="protocolo",
    name="Protocolo",
    area=Area.PROTOCOLS,
    synonyms=("pedido", "solicitação", "chamado", "PRT"),
    definition="Pedido do aluno à secretaria. O mesmo número aparece com e sem prefixo. "
    "Ter pedido em andamento é a exceção, então lista vazia é uma resposta normal.",
    source=System.SECRETARY,
    origin=Origin.CONFIRMED,
    evidence="11 em andamento em 3.933 protocolos; 297 protocolos de aluno sem o ID dele.",
    data=(
        tables.SECRETARY_PROTOCOL,
        tables.SECRETARY_PROTOCOL_HISTORY,
        tables.SECRETARY_PROTOCOL_INTERACTION,
    ),
    never_say=("Deduzir o motivo de uma negativa que não está registrada",),
    relations=(
        Relation(
            RelationKind.NOT_IMPLIES,
            "taxa_de_servico",
            note="Pedido concluído não prova que a taxa foi paga, nem o inverso.",
            evidence="41 pedidos de segunda chamada estão resolvidos com a taxa vencida, "
            "e 25 não têm fatura.",
        ),
    ),
)

SERVICO = Ontology(
    key="servico",
    name="Serviço da secretaria",
    area=Area.PROTOCOLS,
    synonyms=("o que posso pedir", "declaração", "segunda via"),
    definition="Tipo de pedido oferecido pela secretaria. O agente só prepara pedidos de "
    "serviços ativos e sem taxa, e o protocolo guarda só texto, sem anexos.",
    source=System.SECRETARY,
    origin=Origin.CONFIRMED,
    evidence="18 serviços, 14 sem taxa; os 64 pedidos de renegociação geraram um acordo cada.",
    data=(tables.SECRETARY_DEMAND_TYPE, tables.SECRETARY_PROTOCOL),
    never_say=("Prometer que o serviço de informações gerais resolve o caso",),
    relations=(
        Relation(
            RelationKind.LEADS_TO,
            "taxa_de_servico",
            note="Alguns serviços geram uma taxa, cobrada em fatura própria.",
        ),
        Relation(
            RelationKind.LEADS_TO,
            "acordo",
            note="O pedido de renegociação atendido leva a um acordo.",
        ),
    ),
)

PRAZO_DE_ATENDIMENTO = Ontology(
    key="prazo_de_atendimento",
    name="Prazo de atendimento",
    area=Area.PROTOCOLS,
    synonyms=("quanto demora", "está atrasado", "SLA"),
    definition="Meta de atendimento do pedido: a abertura mais as horas do serviço, em horas "
    "corridas. É uma meta, não uma garantia.",
    source=System.SECRETARY,
    origin=Origin.CONFIRMED,
    evidence="Bate em 3.933/3.933 protocolos; 475 de 3.922 encerrados passaram dele; "
    "nenhum dos 11 em andamento passou em 31/10.",
    data=(tables.SECRETARY_PROTOCOL, tables.SECRETARY_DEMAND_TYPE),
    never_say=("Prometer atendimento dentro da meta",),
    relations=(
        Relation(
            RelationKind.NOT_SAME_AS,
            "regras_de_trancamento",
            note="A meta do pedido de trancamento não é um prazo para trancar.",
        ),
    ),
)

TAXA_DE_SERVICO = Ontology(
    key="taxa_de_servico",
    name="Taxa de serviço",
    area=Area.PROTOCOLS,
    synonyms=("quanto custa", "taxa da segunda chamada"),
    definition="Valor cobrado por alguns serviços, em fatura própria. "
    "O agente não abre pedido de serviço com taxa: o aluno procura a secretaria.",
    source=System.SECRETARY,
    origin=Origin.CONFIRMED,
    evidence="Só 4 serviços têm taxa: ACA-021, R$ 45; DOC-002, R$ 20; DOC-003, R$ 30; "
    "DOC-041, R$ 150.",
    data=(tables.SECRETARY_DEMAND_TYPE, tables.FINANCE_INVOICE),
    never_say=("Dizer que a taxa foi paga porque o pedido foi concluído",),
)

DOCUMENTO_EMITIDO = Ontology(
    key="documento_emitido",
    name="Documento emitido",
    area=Area.PROTOCOLS,
    synonyms=("certificado", "diploma saiu", "código de validação"),
    definition="Documento gerado por um pedido atendido, com um código de validação do aluno. "
    "Um pedido de diploma gera dois documentos: o diploma e o certificado de conclusão.",
    source=System.SECRETARY,
    origin=Origin.CONFIRMED,
    evidence="Nenhum documento vem de protocolo não atendido; os 120 protocolos de diploma com "
    "documento têm 2 cada.",
    data=(tables.SECRETARY_ISSUED_DOCUMENT, tables.SECRETARY_PROTOCOL),
    never_say=("Informar quem assinou o documento",),
)

PEDIDO_DE_TERCEIRO = Ontology(
    key="pedido_de_terceiro",
    name="Pedido de terceiro",
    area=Area.PROTOCOLS,
    synonyms=("meu pai abriu um pedido", "responsável abriu"),
    definition="Pedido aberto por outra pessoa para o aluno. Só aparece quando o vínculo é "
    "provado; sem vínculo, a resposta é que o pedido não foi localizado.",
    source=System.SECRETARY,
    origin=Origin.POLICY,
    evidence="113 protocolos de responsáveis, 38 sem o ID do aluno; 11 de terceiros, todos sem ID.",
    data=(tables.SECRETARY_PROTOCOL,),
    never_say=("Revelar nome ou CPF de quem abriu o pedido",),
)

PROTOCOL_ONTOLOGIES = (
    PROTOCOLO,
    SERVICO,
    PRAZO_DE_ATENDIMENTO,
    TAXA_DE_SERVICO,
    DOCUMENTO_EMITIDO,
    PEDIDO_DE_TERCEIRO,
)
