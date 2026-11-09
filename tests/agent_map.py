from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MappedQuestion:
    code: str
    tools: tuple[str, ...]
    ontologies: tuple[str, ...]


QUESTIONS = (
    MappedQuestion(
        "DU-01",
        ("get_academic_calendar", "list_online_exams"),
        ("data_de_referencia", "prova_online"),
    ),
    MappedQuestion("DU-02", ("get_curriculum",), ("matriz",)),
    MappedQuestion("DU-03", ("get_curriculum",), ("tcc_e_estagio", "projeto_integrador")),
    MappedQuestion(
        "DU-04", ("get_curriculum",), ("pre_requisito", "impedimento_por_pre_requisito", "matriz")
    ),
    MappedQuestion("DU-05", ("list_course_offers",), ("oferta",)),
    MappedQuestion(
        "DU-06", ("list_services",), ("servico", "taxa_de_servico", "prazo_de_atendimento")
    ),
    MappedQuestion("VA-01", ("list_enrollments",), ("matricula", "rematricula")),
    MappedQuestion("VA-02", ("list_subject_records",), ("resultado",)),
    MappedQuestion("VA-03", ("list_subject_records",), ("av",)),
    MappedQuestion("VA-04", ("list_subject_records",), ("media", "criterio_de_aprovacao", "av")),
    MappedQuestion(
        "VA-05", ("list_subject_records",), ("resultado", "frequencia", "criterio_de_aprovacao")
    ),
    MappedQuestion("VA-06", ("list_subject_records",), ("frequencia",)),
    MappedQuestion("VA-07", ("list_enrollments",), ("cr",)),
    MappedQuestion("VA-08", ("get_curriculum",), ("conclusao", "matriz")),
    MappedQuestion(
        "VA-09",
        ("get_academic_calendar", "list_enrollments", "list_subject_records"),
        ("resultado", "registro_oficial", "matricula", "data_de_referencia"),
    ),
    MappedQuestion("FI-01", ("get_financial_summary",), ("divida", "multa_e_juros")),
    MappedQuestion("FI-02", ("get_financial_summary",), ("proximo_boleto", "parcela_de_acordo")),
    MappedQuestion("FI-03", ("list_invoices",), ("estorno", "pagamento", "multa_e_juros")),
    MappedQuestion("FI-04", ("list_payments",), ("pagamento", "estorno")),
    MappedQuestion("FI-05", ("get_financial_summary",), ("pagador",)),
    MappedQuestion("FI-06", ("get_financial_summary",), ("bolsa", "mensalidade")),
    MappedQuestion("FI-07", ("get_tuition_changes",), ("mensalidade", "bolsa")),
    MappedQuestion("FI-08", ("list_agreements",), ("acordo", "parcela_de_acordo")),
    MappedQuestion("FI-09", ("get_financial_summary",), ("cobranca", "negativacao", "divida")),
    MappedQuestion(
        "PR-01",
        ("get_protocol",),
        ("protocolo", "prazo_de_atendimento", "taxa_de_servico", "dados_internos"),
    ),
    MappedQuestion("PR-02", ("list_protocols",), ("protocolo", "prazo_de_atendimento")),
    MappedQuestion("PR-03", ("get_protocol",), ("protocolo",)),
    MappedQuestion("PR-04", ("list_protocols",), ("documento_emitido",)),
    MappedQuestion("PR-05", ("propose_protocol",), ("servico", "matricula")),
    MappedQuestion(
        "PR-06", ("list_services", "list_subject_records"), ("servico", "taxa_de_servico", "av")
    ),
    MappedQuestion(
        "PR-07", ("list_invoices", "propose_protocol"), ("servico", "mensalidade", "divida")
    ),
    MappedQuestion(
        "PR-08",
        ("list_enrollments",),
        ("trancamento", "matricula_em_disciplina", "servico", "prazo_de_atendimento"),
    ),
    MappedQuestion("PR-09", ("get_protocol",), ("pedido_de_terceiro", "protocolo")),
    MappedQuestion("LM-01", ("list_online_exams",), ("prova_online",)),
    MappedQuestion("LM-02", ("list_online_exams",), ("tentativa",)),
    MappedQuestion(
        "LM-03", ("list_online_exams",), ("nota_do_ava", "prova_online", "registro_oficial")
    ),
    MappedQuestion("LM-04", ("get_lms_account",), ("ultimo_acesso",)),
    MappedQuestion("LM-05", ("list_material_views",), ("visualizacao_de_material",)),
    MappedQuestion(
        "CR-01",
        ("get_pending_items",),
        ("pendencia", "matricula", "divida", "frequencia", "protocolo", "proximo_boleto"),
    ),
    MappedQuestion(
        "CR-02",
        ("list_services", "get_financial_summary", "get_lms_account"),
        ("suspensao_do_ava", "divida", "ultimo_acesso", "servico"),
    ),
    MappedQuestion(
        "CR-03",
        ("list_enrollments", "get_financial_summary", "list_protocols"),
        ("conclusao", "documento_emitido", "divida", "bloqueio_de_diploma"),
    ),
    MappedQuestion("CR-04", ("list_online_exams",), ("nota_do_ava", "registro_oficial")),
    MappedQuestion(
        "CR-05",
        ("list_enrollments", "get_financial_summary", "list_invoices"),
        ("trancamento", "quitacao", "mensalidade"),
    ),
    MappedQuestion(
        "CR-06",
        ("list_enrollments", "list_agreements"),
        ("parcela_de_acordo", "mensalidade", "acordo", "matricula", "quitacao"),
    ),
    MappedQuestion(
        "CR-07",
        ("list_enrollments", "get_financial_summary"),
        ("matricula", "divida", "quitacao"),
    ),
    MappedQuestion(
        "CR-08",
        ("list_subject_records", "get_protocol"),
        ("taxa_de_servico", "protocolo", "multa_e_juros", "av"),
    ),
    MappedQuestion("SR-01", ("list_subject_records",), ("sala_e_horario",)),
    MappedQuestion("SR-02", (), ("regras_de_trancamento", "prazo_de_atendimento")),
    MappedQuestion("SR-03", ("get_financial_summary",), ("criterios_de_bolsa", "bolsa")),
    MappedQuestion(
        "SR-04",
        ("get_academic_calendar", "get_tuition_changes"),
        ("calendario_2027", "mensalidade", "periodo_coberto"),
    ),
    MappedQuestion("SR-05", ("list_protocols", "list_online_exams"), ("periodo_coberto",)),
    MappedQuestion("RE-01", (), ("outros_alunos",)),
    MappedQuestion("RE-02", (), ("identidade",)),
    MappedQuestion("RE-03", (), ("outros_alunos", "pagador")),
    MappedQuestion("RE-04", ("list_subject_professors",), ("dados_internos",)),
    MappedQuestion("RE-05", ("get_protocol",), ("dados_internos",)),
    MappedQuestion("RE-06", (), ("outros_alunos",)),
    MappedQuestion("RE-07", (), ("dados_internos",)),
    MappedQuestion("RE-08", ("propose_protocol",), ("servico", "bolsa")),
    MappedQuestion("RE-09", (), ("gabarito", "registro_oficial", "quitacao")),
)
