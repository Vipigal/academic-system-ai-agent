import { ApiError, describeError } from "./api";
import { flag, recordOf, text } from "./guards";

export interface ConfirmationPrompt {
  question: string;
  effect: string;
  limit: string;
  word: string;
}

export interface Proposal {
  token: string;
  title: string;
  enrollment: string;
  course: string;
  effect: string;
  subject: string;
  requiresMessage: boolean;
  requestText: string;
  confirmation: ConfirmationPrompt | null;
}

const REASONS: Record<string, string> = {
  service_has_fee: "Este serviço tem taxa e não pode ser aberto pelo assistente.",
  service_inactive: "Este serviço não está disponível.",
  empty_message: "Escreva o seu pedido antes de confirmar.",
  message_too_long: "O pedido passou de 4.000 caracteres. Encurte o texto.",
  confirmation_word: "A palavra de confirmação não confere.",
  enrollment_status: "A situação da matrícula não permite este pedido.",
  subject_not_supported: "Este pedido vale para o curso inteiro, e não para uma disciplina.",
  duplicate_in_progress: "Já existe um pedido em andamento para este serviço.",
};

function confirmationOf(clientOnly: unknown): ConfirmationPrompt | null {
  const block = recordOf(clientOnly, "confirmation");
  const word = text(block, "word");
  if (!word) return null;
  return { question: text(block, "question"), effect: text(block, "effect"), limit: text(block, "limit"), word };
}

export function parseProposal(output: Record<string, unknown>): Proposal | null {
  const token = text(output.client_only, "token");
  if (output.status !== "ok" || !token) return null;
  const data = output.data;
  return {
    token,
    title: text(data, "title"),
    enrollment: text(data, "enrollment"),
    course: text(data, "course_name_pt") || text(data, "course_name"),
    effect: text(data, "effect"),
    subject: text(data, "subject"),
    requiresMessage: flag(data, "requires_student_message"),
    requestText: text(data, "request_text"),
    confirmation: confirmationOf(output.client_only),
  };
}

export function refusalText(reason: string): string {
  return REASONS[reason] ?? "O pedido foi recusado.";
}

export function confirmationError(failure: unknown): string {
  if (failure instanceof ApiError && failure.status === 422) return refusalText(failure.detail);
  return describeError(failure);
}
