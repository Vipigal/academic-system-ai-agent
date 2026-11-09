export const TOOL_LABELS: Record<string, string> = {
  load_skill: "instruções da área",
  get_academic_calendar: "calendário acadêmico",
  get_curriculum: "matriz curricular",
  list_course_offers: "cursos oferecidos",
  list_enrollments: "matrículas",
  list_subject_records: "disciplinas cursadas",
  list_subject_professors: "professores da disciplina",
  get_financial_summary: "resumo financeiro",
  list_invoices: "faturas",
  list_payments: "pagamentos",
  list_agreements: "acordos de renegociação",
  get_tuition_changes: "mudanças da mensalidade",
  get_lms_account: "conta no AVA",
  list_material_views: "materiais acessados no AVA",
  list_online_exams: "provas online",
  get_pending_items: "pendências",
  list_services: "serviços da secretaria",
  list_protocols: "protocolos",
  get_protocol: "protocolo",
  propose_protocol: "proposta de protocolo",
};

export function toolLabel(name: string): string {
  return TOOL_LABELS[name] ?? name;
}
