from api.domain.ontology import tables
from api.domain.ontology.model import Area, Ontology, Origin, Relation, RelationKind, System

PAGAMENTO = Ontology(
    key="pagamento",
    name="Pagamento",
    area=Area.FINANCE,
    synonyms=("quanto paguei", "paguei", "comprovante"),
    definition="Valor recebido em uma fatura, com multa e juros incluídos. Só conta pagamento "
    "confirmado, na data de Brasília. Com outro pagador, o aluno pode não ter pago pessoalmente.",
    source=System.FINANCE,
    origin=Origin.CONFIRMED,
    evidence="24.265 pagamentos confirmados e 115 estornados; 3 confirmados de 01/11 em UTC são "
    "de 31/10 em Brasília.",
    data=(tables.FINANCE_PAYMENT, tables.FINANCE_INVOICE),
    never_say=("Somar pagamento estornado ao total pago",),
)

ESTORNO = Ontology(
    key="estorno",
    name="Estorno",
    area=Area.FINANCE,
    synonyms=("paguei e aparece vencido", "pagamento devolvido"),
    definition="Pagamento desfeito. A fatura continua devida, e o motivo não está registrado.",
    source=System.FINANCE,
    origin=Origin.CONFIRMED,
    evidence="26 faturas vencidas só têm pagamento estornado; em 89 pagas houve estorno e novo "
    "pagamento.",
    data=(tables.FINANCE_PAYMENT, tables.FINANCE_INVOICE),
    never_say=(
        "Dizer que não consta pagamento quando houve estorno",
        "Informar o motivo do estorno",
    ),
    relations=(
        Relation(
            RelationKind.NOT_SAME_AS,
            "pagamento",
            note="Estorno não quita a fatura, mas também não é falta de pagamento.",
        ),
    ),
)

QUITACAO = Ontology(
    key="quitacao",
    name="Quitação",
    area=Area.FINANCE,
    synonyms=("estou em dia", "quitei", "não devo nada"),
    definition="Situação em que nada mais é devido em um contrato. Vem do pagamento: "
    "trancar, transferir ou encerrar o curso não apaga o que já se deve.",
    source=System.FINANCE,
    origin=Origin.CONFIRMED,
    evidence="Contratos encerrados ainda têm 10 faturas em aberto.",
    data=(tables.FINANCE_INVOICE, tables.FINANCE_CONTRACT),
    never_say=("Dizer que não há nada a pagar olhando só a matrícula atual",),
)

PAGADOR = Ontology(
    key="pagador",
    name="Pagador",
    area=Area.FINANCE,
    synonyms=("quem paga", "no nome de quem", "responsável financeiro"),
    definition="Responsável financeiro do contrato. "
    "Só se informa o tipo: o próprio aluno, outra pessoa ou empresa.",
    source=System.FINANCE,
    origin=Origin.POLICY,
    evidence="Decisão na FI-05; 167 contratos têm pagador diferente do aluno, 24 deles empresas.",
    data=(tables.FINANCE_CONTRACT, tables.FINANCE_CUSTOMER, tables.SAG_PERSON),
    never_say=(
        "Informar nome, documento ou contato do pagador",
        "Informar outros alunos do mesmo pagador",
    ),
)

COBRANCA = Ontology(
    key="cobranca",
    name="Cobrança",
    area=Area.FINANCE,
    synonyms=("contrato em cobrança", "estou sendo cobrado"),
    definition="Situação de cobrança do contrato. O aluno só fica sabendo que o contrato está "
    "em cobrança, sem as etapas internas.",
    source=System.FINANCE,
    origin=Origin.POLICY,
    evidence="Decisão na FI-09; 188 contratos em cobrança.",
    data=(tables.FINANCE_CONTRACT, tables.FINANCE_RECEIVABLE_SNAPSHOT),
    never_say=("Mostrar a etapa interna de cobrança", "Dizer que uma dívida foi perdoada"),
    relations=(
        Relation(
            RelationKind.NOT_IMPLIES,
            "negativacao",
            note="Não afirme que estar em cobrança significa ter o nome negativado.",
            evidence="Nenhuma tabela registra negativação; 55 contratos estão na etapa "
            "CREDIT_BUREAU em 31/10.",
        ),
    ),
)

NEGATIVACAO = Ontology(
    key="negativacao",
    name="Negativação",
    area=Area.FINANCE,
    synonyms=("SPC", "Serasa", "nome sujo"),
    definition="Se o nome do aluno está em um cadastro de inadimplentes não está na base.",
    source=None,
    origin=Origin.ABSENT,
    evidence="Nenhuma tabela registra negativação; a etapa de cobrança é interna.",
    data=(tables.FINANCE_RECEIVABLE_SNAPSHOT,),
    caveat="Não consigo confirmar se seu nome foi negativado, "
    "porque essa informação não está nos meus dados.",
    never_say=("Afirmar ou negar que o nome foi negativado",),
)

FINANCE_SETTLEMENT_ONTOLOGIES = (PAGAMENTO, ESTORNO, QUITACAO, PAGADOR, COBRANCA, NEGATIVACAO)
